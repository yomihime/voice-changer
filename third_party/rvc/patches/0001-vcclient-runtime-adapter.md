# VCClient runtime adapter patch

This patch is intentionally described at the semantic level because the
vendored tree is an extracted runtime slice rather than a Git subtree.

Files changed from upstream commit `81eed5e8f68b6bed1789f682fe78cdd324495afc`:

- `infer/rtrvc.py`: use package-relative imports; accept `hubert_path`,
  `rmvpe_path`, `speaker_id`, and `protect`; use the selected speaker tensor;
  apply the official protect blend around indexed features; re-raise load
  and retrieval failures instead of silently continuing with a bad index;
  probe up to eight IVF lists so sparse populated indexes can return all eight
  neighbors required by realtime retrieval.
- `infer/hubert.py`: accept an explicit local Transformers model directory.
- `infer/rmvpe.py`, `infer/fcpe.py`, `infer/module/*.py`, `i18n/i18n.py`: use
  package-relative imports; resolve locale resources relative to the vendored
  module instead of the process working directory.
- package `__init__.py` files: allow loading under the private
  `vcclient_official_rvc` namespace.
- `tools/cuda_graph.py`: cache capability/enabled state per explicit device so
  a prior CPU load cannot globally disable a later `cuda:N` load; release graph
  caches on backend teardown and fall back to eager execution on capture or
  replay failure.

Why required: upstream assumes its repository is the process working directory,
uses generic top-level packages named `infer` and `tools`, hard-codes runtime
asset paths, fixes realtime speaker id to zero, and does not expose realtime
protect. Those assumptions violate the VCClient host boundary.

Removal condition: delete each item when upstream provides an embeddable Python
package with explicit resource paths, speaker/protect realtime arguments, and
proper error propagation.
