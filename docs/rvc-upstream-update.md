# Updating the vendored Official RVC runtime

1. Fetch `RVC-Project/Retrieval-based-Voice-Conversion-WebUI` and choose an
   explicit commit. Never track a floating branch at runtime.
2. Review upstream changes in `infer/rtrvc.py`, `infer/hubert.py`,
   `infer/rmvpe.py`, `infer/fcpe.py`, `infer/module/`, and
   `tools/cuda_graph.py`.
3. Refresh the runtime slice in `third_party/rvc` without importing WebUI,
   Gradio, audio-device, training, or VST application code.
4. Reapply or retire each item documented in
   `third_party/rvc/patches/0001-vcclient-runtime-adapter.md`. Keep changes
   package-relative and avoid `sys.path`, `os.chdir`, or environment-based GPU
   selection.
5. Update repository, commit, commit date, import date, and patch notes in
   `third_party/rvc/UPSTREAM.md`; preserve upstream `LICENSE`.
6. Compare upstream dependency files with `server/requirements/windows-cuda.in`
   and `server/requirements/windows-cuda.lock` (see [Windows setup](windows-setup.md)). Do not
   install the upstream requirements wholesale. Update the compatibility table
   in `docs/rvc-upstream-integration.md` for every resolution.
7. Run backend, mapping, device, metadata, and import tests. Then run the normal
   server and client build/smoke checks.
8. On a Windows NVIDIA machine, run the same model/index/input through Legacy,
   Official eager, and Official CUDA Graph. Record output length, model SR,
   mean/P50/P95 inference time, VRAM, and approximate realtime latency.
9. Complete a ten-minute microphone-to-output and LAN test. Watch for growing
   buffers, latency, VRAM, periodic artifacts, cache errors, and device mismatch.
10. Package and test on a clean Windows machine with no system Python. Confirm
    the vendor tree, Transformers HuBERT resources, RMVPE resource, and license
    notices are present.

An upstream update is complete only when Legacy regression checks still pass
and an explicitly selected `gpu=N` is proven by logs and runtime inspection to
execute every Official model component on `cuda:N`.
