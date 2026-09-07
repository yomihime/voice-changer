import torch
from contextlib import nullcontext
from torch import device
from voice_changer.RVC.embedder.Embedder import Embedder
from fairseq import checkpoint_utils
from fairseq.data.dictionary import Dictionary


class FairseqHubert(Embedder):
    def loadModel(self, file: str, dev: device, isHalf: bool = True) -> Embedder:
        super().setProps("hubert_base", file, dev, isHalf)

        # HuBERT checkpoints contain this fairseq metadata type. Keep modern
        # torch's weights-only loader; do not disable it globally for user models.
        safe_globals = getattr(torch.serialization, "safe_globals", None)
        with safe_globals([Dictionary]) if safe_globals else nullcontext():
            models, saved_cfg, task = checkpoint_utils.load_model_ensemble_and_task(
                [file],
                suffix="",
            )
        model = models[0]
        model.eval()

        model = model.to(dev)
        if isHalf:
            model = model.half()

        self.model = model
        return self

    def extractFeatures(
        self, feats: torch.Tensor, embOutputLayer=9, useFinalProj=True
    ) -> torch.Tensor:
        padding_mask = torch.BoolTensor(feats.shape).to(self.dev).fill_(False)

        # オリジナル_v1は L9にfinal_projをかけていた。(-> 256)
        # オリジナル_v2は L12にfinal_projをかけない。(-> 768)

        inputs = {
            "source": feats.to(self.dev),
            "padding_mask": padding_mask,
            "output_layer": embOutputLayer,  # 9 or 12
        }

        with torch.no_grad():
            logits = self.model.extract_features(**inputs)
            if useFinalProj:
                feats = self.model.final_proj(logits[0])
            else:
                feats = logits[0]
        return feats
