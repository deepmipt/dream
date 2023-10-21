from deeppavlov.core.models.component import Component
from deeppavlov.core.common.registry import register
from deeppavlov.models.torch_bert.torch_transformers_classifier import TorchTransformersClassifierModel

from typing import Dict, Union, List
import json
import numpy as np
import torch
import logging

from flask import Flask, request, jsonify
import sentry_sdk

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logger = logging.getLogger(__name__)


@register("dnnc_preparer")
class dnnc_preparer(Component):
    def __init__(self, **kwargs):
        self.data = json.load(open("data_full.json", "r"))

    def __call__(self, texts):
        datasets = self.data["train"] + self.data["oos_train"]
        return texts, datasets


@register('torch_transformers_classifier_batch1')
class TorchTransformersClassifierModelBatch1(TorchTransformersClassifierModel):
    def __call__(self, features: Dict[str, torch.tensor]) -> Union[List[int], List[List[float]]]:
        """Make prediction for given features (texts).

        Args:
            features: batch of InputFeatures

        Returns:
            predicted classes or probabilities of each class

        """
        answer = []
        logger.info(len(features))
        for i in range(len(features)):
            _input = {key: value[i].unsqueeze(0).to(self.device)
                      for key, value in features.items()}
    
            with torch.no_grad():
                tokenized = {key: value for (key, value) in _input.items()
                             if key in self.accepted_keys}
    
                # Forward pass, calculate logit predictions
                logits = self.model(**tokenized)
                logits = logits[0]
    
            if self.return_probas:
                if self.is_binary:
                    pred = torch.sigmoid(logits).squeeze(1)
                elif not self.multilabel:
                    pred = torch.nn.functional.softmax(logits, dim=-1)
                else:
                    pred = torch.nn.functional.sigmoid(logits)
                pred = pred.detach().cpu().numpy()
            elif self.n_classes > 1:
                logits = logits.detach().cpu().numpy()
                pred = np.argmax(logits, axis=1)
            # regression
            else:
                pred = logits.squeeze(-1).detach().cpu().numpy()
            answer.append(pred)
        answer = np.concatenate(answer)
        logger.info(answer)
        logger.info(answer.shape)
        return answer
