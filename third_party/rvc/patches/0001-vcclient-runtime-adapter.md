# VCClient runtime adapter patch

This file inventories the current semantic delta because the vendored tree is
an extracted runtime slice rather than a Git subtree. Status labels below were
decided in M1. They are inputs to M2/M3, not evidence that scheduled removals
have already happened.

Files changed from upstream commit `81eed5e8f68b6bed1789f682fe78cdd324495afc`:

- `infer/rtrvc.py`: **keep** package-relative imports, explicit `hubert_path`
  and `rmvpe_path`, selected `speaker_id`, and constructor error propagation;
  **remove in M3** the locally exposed `protect` blend, forced IVF `nprobe`,
  and retrieval search-policy changes.
- `infer/hubert.py`: accept an explicit local Transformers model directory.
- `infer/rmvpe.py`, `infer/fcpe.py`, `infer/module/*.py`, `i18n/i18n.py`: use
  package-relative imports; resolve locale resources relative to the vendored
  module instead of the process working directory.
- package `__init__.py` files: allow loading under the private
  `vcclient_official_rvc` namespace.
- `tools/cuda_graph.py`: **keep provisionally** the per-device capability and
  enabled state, backend teardown, and eager fallback. M2 must prove switching
  and ownership safety; M4 must make the verification replayable.

Why the retained items are required: upstream assumes its repository is the
process working directory, uses generic top-level packages named `infer` and
`tools`, hard-codes runtime asset paths, and fixes realtime speaker id to zero.
Those assumptions violate the VCClient host boundary. Lack of a realtime
`protect` argument is treated as an upstream capability boundary, not a reason
to extend the Official algorithm locally.

Removal condition for retained items: delete each item when upstream provides
an embeddable Python package with explicit resource paths, realtime speaker
selection, device-scoped CUDA Graph lifecycle, and proper error propagation.
