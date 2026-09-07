# Updating the vendored Official RVC runtime

1. Fetch `RVC-Project/Retrieval-based-Voice-Conversion-WebUI` into a separate
   checkout and choose an explicit 40-character commit. Never track a floating
   branch at runtime.
2. Refresh the source manifest from that immutable commit:

   ```powershell
   python scripts/vendor_rvc.py refresh-manifest `
     --upstream E:\path\to\Retrieval-based-Voice-Conversion-WebUI `
     --commit <40-character-commit>
   ```

3. Review upstream changes in `infer/rtrvc.py`, `infer/hubert.py`,
   `infer/rmvpe.py`, `infer/fcpe.py`, `infer/module/`, and
   `tools/cuda_graph.py`.
4. Materialize the pinned source slice plus the currently retained patch into
   an empty review directory:

   ```powershell
   python scripts/vendor_rvc.py materialize `
     --upstream E:\path\to\Retrieval-based-Voice-Conversion-WebUI `
     --output E:\temp\rvc-replay
   ```

   The command applies the currently checked-in patch. When advancing the pin,
   patch conflicts are an explicit review gate rather than a reason to copy a
   dirty upstream working tree.
5. Reapply or retire each item documented in
   `third_party/rvc/patches/0001-vcclient-runtime-adapter.md`. Keep changes
   package-relative and avoid `sys.path`, `os.chdir`, or environment-based GPU
   selection.
6. Copy the reviewed runtime slice into `third_party/rvc`, then regenerate the
   machine patch and prove a clean replay:

   ```powershell
   python scripts/vendor_rvc.py refresh-patch `
     --upstream E:\path\to\Retrieval-based-Voice-Conversion-WebUI
   python scripts/vendor_rvc.py check `
     --upstream E:\path\to\Retrieval-based-Voice-Conversion-WebUI
   ```

   `check` reads source bytes with `git show <commit>:<path>`, verifies SHA-256,
   applies the patch in an isolated temporary directory, and compares every
   runtime file. Uncommitted files in the upstream checkout cannot enter the
   vendor tree.
7. Update repository, commit, commit date, import date, and patch notes in
   `third_party/rvc/UPSTREAM.md`; preserve upstream `LICENSE`.
8. Compare upstream dependency files with `server/requirements/windows-cuda.in`
   and `server/requirements/windows-cuda.lock` (see [Windows setup](windows-setup.md)). Do not
   install the upstream requirements wholesale. Update the compatibility table
   in `docs/rvc-upstream-integration.md` for every resolution.
9. Run backend, mapping, device, metadata, and import tests. Then run the normal
   server and client build/smoke checks.
10. On a Windows NVIDIA machine, run the same model/index/input through Legacy,
   Official eager, and Official CUDA Graph. Record output length, model SR,
   mean/P50/P95 inference time, VRAM, and approximate realtime latency.
11. Complete a ten-minute microphone-to-output and LAN test with
    `server/tools/soak_rvc_runtime.py`. Watch for growing
   buffers, latency, VRAM, periodic artifacts, cache errors, and device mismatch.
12. Package and test on a clean Windows machine with no system Python. Confirm
    the vendor tree, Transformers HuBERT resources, RMVPE resource, and license
    notices are present.

An upstream update is complete only when Legacy regression checks still pass
and an explicitly selected `gpu=N` is proven by logs and runtime inspection to
execute every Official model component on `cuda:N`.
