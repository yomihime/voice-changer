# VCClient runtime adapter patch

This file inventories the retained semantic delta because the vendored tree is
an extracted runtime slice rather than a Git subtree. M3 removed the previously
listed algorithm extensions.

Files changed from upstream commit `81eed5e8f68b6bed1789f682fe78cdd324495afc`:

- `infer/rtrvc.py`: **keep** package-relative imports, explicit `hubert_path`
  and `rmvpe_path`, selected `speaker_id`, and constructor error propagation.
  Retrieval, feature blending, and IVF search policy match the pinned source.
- `infer/hubert.py`: accept an explicit local Transformers model directory.
- `infer/rmvpe.py`, `infer/fcpe.py`, `infer/module/*.py`, `i18n/i18n.py`: use
  package-relative imports; resolve locale resources relative to the vendored
  module instead of the process working directory.
- package `__init__.py` files: allow loading under the private
  `vcclient_official_rvc` namespace.
- `tools/cuda_graph.py`: **keep** the per-device capability and enabled state,
  backend teardown, and eager fallback. M2 proved switching and ownership
  safety; M4 makes the import and verification replayable.

Why the retained items are required: upstream assumes its repository is the
process working directory, uses generic top-level packages named `infer` and
`tools`, hard-codes runtime asset paths, and fixes realtime speaker id to zero.
Those assumptions violate the VCClient host boundary. Lack of a realtime
`protect` argument is treated as an upstream capability boundary, not a reason
to extend the Official algorithm locally.

Removal condition for retained items: delete each item when upstream provides
an embeddable Python package with explicit resource paths, realtime speaker
selection, device-scoped CUDA Graph lifecycle, and proper error propagation.
