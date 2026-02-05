# Guide to Fine-tuning

## Code Source
The fine-tuning code is adapted from [Unsloth](https://unsloth.ai/docs). Evaluation and some code to fit our data are added to the code. Training configurations are also adapted.

## Evaluation
After fine-tuning, we evaluate the model’s extraction performance at the item level, jointly considering text correctness and spatial localization quality.

For each page, predicted products are first matched to ground-truth items using name similarity based on normalized string matching (SequenceMatcher). A prediction is considered a true positive if the name similarity exceeds a predefined threshold.

Given a successful name match, we further assess:
- Price accuracy, by exact match after normalization.
- Bounding box accuracy, using Intersection over Union (IoU) between predicted and ground-truth boxes. A bounding box is counted as correct if its IoU exceeds a fixed threshold.

Overall performance is reported using Precision, Recall, and F1 score over item matching. In addition, we report Price Accuracy, Bounding Box Accuracy, and Mean IoU, all computed conditioned on correctly matched items, to disentangle extraction quality from localization errors.