# Official RVC upstream

- Repository: https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI
- Commit: `81eed5e8f68b6bed1789f682fe78cdd324495afc`
- Commit date: 2026-08-04
- Imported: 2026-09-05
- Runtime assets: `lj1995/VoiceConversionWebUI` revision
  `e6d0c1a17da07c33557852f9dfa2bd44cc75737d`
- Import form: vendored runtime slice (`infer/`, realtime support tools, i18n,
  configs, license, README, and upstream dependency manifests)

The upstream WebUI, audio-device GUI, training code, and VST project are not
packaged because VCClient remains the application and audio host.

## Local patches

`vendor-manifest.json` maps every imported path to its exact upstream path and
SHA-256. `patches/0001-vcclient-runtime-adapter.patch` is the machine-applicable
delta, while `patches/0001-vcclient-runtime-adapter.md` explains why each
retained difference exists:

- package-relative imports so the runtime can be loaded under a collision-free
  namespace without `sys.path` or current-working-directory changes;
- explicit HuBERT and RMVPE paths supplied by VCClient;
- speaker id exposed by realtime inference;
- constructor failures re-raised so the Adapter can translate them into
  backend errors instead of leaving a partially initialized object.

Per-device CUDA Graph ownership remains a host-lifecycle patch and must be
verified on every upstream refresh. M3 removed the former realtime protect
blend, forced FAISS `nprobe`, and retrieval-error policy changes; the vendored
search and feature path now follows the pinned upstream algorithm. Host chunk
framing and PCM unit conversion remain outside this vendor directory and are
documented in `docs/rvc-upstream-integration.md`.

No VCClient audio-device, network, UI, model-slot, or stream-stitching code is
present in this vendor directory.

Run `python scripts/vendor_rvc.py check --upstream <checkout>` to extract the
pinned commit with `git show`, verify every source checksum, apply the actual
patch in an isolated directory, and compare the rebuilt runtime with this tree.
