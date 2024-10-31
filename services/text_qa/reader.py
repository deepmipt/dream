from transformers import DPRReader, DPRReaderTokenizer
import numpy as np
import torch
from typing import List, Tuple

class Reader:
    def __init__(self):
        self.tokenizer = DPRReaderTokenizer.from_pretrained("facebook/dpr-reader-single-nq-base")
        self.model = DPRReader.from_pretrained("facebook/dpr-reader-single-nq-base")
        self.softmax = lambda x: np.exp(x)/sum(np.exp(x))
        self.model.to('cuda')
        

    def answer_question(self, question, text_titles, texts):
        
        encoded_inputs = self.tokenizer(
            questions=question,
            texts=texts,
            titles=text_titles,
            return_tensors="pt",
            padding=True
        )
        encoded_inputs.to('cuda')

        outputs = self.model(**encoded_inputs)
        start_logits = outputs.start_logits
        end_logits = outputs.end_logits
        relevance_logits = outputs.relevance_logits

        relevance_logits = relevance_logits.cpu().detach().numpy()
        print(relevance_logits.shape)
        print(self.softmax(relevance_logits))
        passage_idx = np.argmax(relevance_logits)
        relevance_score = self.softmax(relevance_logits)[passage_idx]

        start_logits = start_logits.cpu().detach().numpy()
        end_logits = end_logits.cpu().detach().numpy()

        answer_spans = self.compute_best_answer_spans(encoded_inputs.input_ids[passage_idx], encoded_inputs.attention_mask[passage_idx], start_logits[passage_idx], end_logits[passage_idx], top_n=1)
        _, start_token, end_token = answer_spans[0]
        answer = self.tokenizer.decode(encoded_inputs.input_ids[passage_idx][start_token:end_token+1])
        reference_passage  = texts[passage_idx]
        return [answer, float(relevance_score), int(passage_idx), reference_passage]


    def compute_best_answer_spans(
        self,
        input_ids: torch.Tensor,
        answer_mask: torch.Tensor,
        start_logits: torch.Tensor,
        end_logits: torch.Tensor,
        top_n: int,
        ) -> List[Tuple[float, int, int]]:

        
        candidate_spans = [
            (start_logit.item() + end_logit.item(), i, i + j)
            for i, start_logit in enumerate(start_logits)
            for j, end_logit in enumerate(end_logits[i : i + 350])
        ]
        candidate_spans = sorted(candidate_spans, key=lambda o: o[0], reverse=True)

        selected_spans = []


        def is_subword_id(token_id: int) -> bool:
            return self.tokenizer.convert_ids_to_tokens([token_id])[0].startswith("##")

        for score, start_index, end_index in candidate_spans:
            if start_index == 0 or end_index == 0:  # [CLS]
                continue

            if not all(answer_mask[start_index : end_index + 1]):
                continue

            if start_index > end_index:
                continue

            if any(
                start_index <= selected_start_index <= selected_end_index <= end_index
                or selected_start_index <= start_index <= end_index <= selected_end_index
                for _, selected_start_index, selected_end_index in selected_spans
            ):
                continue

            while (
                is_subword_id(input_ids[start_index].item()) and start_index > 0 and answer_mask[start_index - 1] == 1
            ):
                start_index -= 1

            while (
                is_subword_id(input_ids[end_index + 1].item())
                and end_index < len(answer_mask) - 1
                and answer_mask[end_index + 1] == 1
            ):
                end_index += 1

            selected_spans.append((score, start_index, end_index))
            if len(selected_spans) == top_n:
                break

        return selected_spans