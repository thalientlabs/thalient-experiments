# Modal Pitfalls

Things that have bitten us. Reference this before launching runs.

## Volume I/O Hangs

`vol.commit()` and `vol.reload()` can block indefinitely during GPU training. FUSE filesystem stalls under concurrent CUDA workloads. GPU drops to 0%, process hangs, no error message.

**Fix:** Never call volume I/O synchronously during training.
- Checkpoint commits: background thread (`threading.Thread(target=vol.commit, daemon=True)`)
- Shard rotation: disable if single shard covers token budget, or do it between runs
- If you must reload, stop GPU work first (call `torch.cuda.synchronize()`, pause training)

## Copy Data to /tmp at Startup

Modal volumes go through FUSE -> page cache -> network. Local SSD (`/tmp`) is dramatically faster. Copy all training data to `/tmp/` before starting CUDA work:

```python
import shutil
LOCAL_DIR = "/tmp/shards"
os.makedirs(LOCAL_DIR, exist_ok=True)
for f in sorted(glob.glob(f"{SHARD_DIR}/*_shard*.pt")):
    dst = os.path.join(LOCAL_DIR, os.path.basename(f))
    if not os.path.exists(dst):
        shutil.copy2(f, dst)  # ~32s for 80GB at 2.5 GB/s
```

Eliminates all FUSE overhead for the entire run. Default ephemeral disk is 512GB â€” plenty of room. This also means you never need `vol_datasets.reload()` during training.

## PYTHONIOENCODING

Modal CLI outputs Unicode (checkmarks, arrows) that Windows charmap can't encode. Every `modal` command crashes without this:

```bash
PYTHONIOENCODING=utf-8 modal run --detach script.py
PYTHONIOENCODING=utf-8 modal app list
```

No exceptions.

## Log Streaming Looks Dead

Logs appear missing or garbled. The app is fine â€” it's Windows terminal encoding. Don't kill the app. Check actual state:

```bash
PYTHONIOENCODING=utf-8 modal app list          # Is it running?
PYTHONIOENCODING=utf-8 modal volume ls vol ...  # New checkpoints?
```

## Monitoring: Mandatory 10-Minute Checks

Hangs are silent â€” no error, no log, GPU just drops to 0%. The ONLY way to catch them early is active monitoring with timestamps.

**After every launch, start a background check loop:**

```bash
# Check every 10 minutes: is the app alive? Are new checkpoints appearing?
while true; do
    ts=$(date '+%H:%M:%S')
    state=$(PYTHONIOENCODING=utf-8 modal app list 2>/dev/null | grep "APP_ID")
    echo "$ts â€” $state"
    PYTHONIOENCODING=utf-8 modal volume ls vol-name checkpoint/dir/ 2>/dev/null | tail -3
    sleep 600
done
```

**Timestamp awareness is critical.** When checking logs, always compute:
- When was the last log line printed? (based on step number and tok/s)
- How long ago should the next log have appeared?
- If the gap is >2x the expected interval, the run is likely hung.

Example: at 440K tok/s with batch=288, ga=4, seq=512:
- Tokens per step = 288 Ã— 4 Ã— 512 = 589,824
- Seconds per step = 589,824 / 440,000 = 1.34s
- LOG_INTERVAL=500 â†’ 500 Ã— 1.34s = **~11 minutes between logs**
- If 25+ minutes since last log â†’ something is wrong

**When you suspect a hang:**
1. Check `modal app list` â€” is the task count still 1?
2. Check volume for new checkpoints â€” has a new one appeared since last check?
3. If app running but no progress for 20+ min â†’ kill and investigate
4. Never wait more than 30 minutes to check. The B200 costs $6.25/hr.

## OOM Corrupts GPU State

One OOM doesn't just fail â€” it poisons the CUDA context. Subsequent operations on the same GPU fail with mysterious errors (cuDNN failures, MMU faults, XID 31). The only recovery is process restart.

**Fix:** After any OOM in a benchmark, `del model; torch.cuda.empty_cache(); gc.collect()` is not enough. Exit the function or stop trying larger configs. Don't sweep batch sizes in ascending order and continue after OOM.

## CUDA Graphs + TE NVFP4

`cudaErrorStreamCaptureInvalidated` â€” unrecoverable. TE's NVFP4 quantization + attention checkpointing is fundamentally incompatible with CUDA graph capture. Don't attempt this.

## 88GB Merged Data Files

Single large files on Modal volumes cause NFS page cache pollution â†’ 3x throughput drop. Use shard-based loading (10 Ã— 8GB files, not 1 Ã— 88GB file).

## VOCAB Alignment

VOCAB must be 128-aligned for NVFP4 tensor cores. 50277 vs 50304 = 3x throughput difference. Pad to nearest multiple of 128.

## Background Thread CUDA Ops

Calling `.to(device)` in a background thread competes for the CUDA context with the training loop. Can deadlock, especially with `grad_accum > 1` where the main thread does rapid sequential GPU ops.

**Fix:** Keep background threads CPU-only. Do GPU transfers in the main thread.

## Async Prefetcher with grad_accum > 1

The prefetcher queue drains 4x faster with ga=4 than ga=1. Size the queue accordingly (8+ items). And if the prefetcher thread dies silently (bare `except: break`), the training loop blocks on `queue.get(timeout=30)` â€” 30 seconds of dead GPU per call, 4 calls per step = 2 minutes wasted per step before fallback kicks in.

**Fix:** Log exceptions in the prefetcher thread instead of silently breaking. Use a larger queue. Consider removing the prefetcher entirely for short runs â€” the CPUâ†’GPU transfer time is negligible (<1ms).

## Duplicate Runs

Modal apps accumulate silently. Always check before launching:

```bash
PYTHONIOENCODING=utf-8 modal app list | grep "your-app-name"
```

Kill old ones explicitly.

## Checkpoint Collision

Different experiments sharing the same volume path will try to resume each other's checkpoints. KeyError on missing fields. Use unique paths per experiment (e.g., `BLITZ_1B_v2/checkpoints` not `BLITZ_1B/checkpoints`).

## Checkpoint Writes to Volume

Write checkpoints to `/tmp/` first (fast, local SSD), then copy to volume mount path, then async commit. Don't `torch.save()` directly to the FUSE-mounted volume path â€” it's slower and can interact badly with concurrent reads.

```python
# Fast: save to /tmp, copy to volume, async commit
torch.save(ckpt, f"/tmp/step_{step}.pt")
shutil.copy2(f"/tmp/step_{step}.pt", f"{CHECKPOINT_DIR}/step_{step}.pt")
threading.Thread(target=vol_checkpoints.commit, daemon=True).start()
```

## SM90 Cluster Kernels (Modal H100)

DSMEM operations crash with XID 13 on Modal H100s. Container runtime doesn't guarantee GPC-co-located CTA scheduling. Cluster barriers work but shared memory access across CTAs doesn't. Dead end â€” don't revisit.

## nvcc SM90a Stub Bug

nvcc generates broken C stub files for template `__global__` kernels targeting SM90a. Use non-template wrappers and separate compilation. See `feedback_nvcc_sm90a_stub_bug.md` in memory.

## Volumes v2

Modal has a Volumes v2 (open beta since Oct 2025) with higher throughput, faster commits/reloads. If you haven't opted in, consider it. But copying to `/tmp/` still beats any volume for read-heavy workloads.
