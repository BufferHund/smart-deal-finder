# Guide to the Data

## Overview
This directory contains the dataset used for the Smart Deal Finder project.
The goal of the dataset is to provide high-quality supermarket brochure pages with structured product-level information, enabling benchmarking of OCR, layout understanding, and multimodal extraction models. A synthetic dataset with machine-generated synthetic brochures is also provide, with which a model for Smart Deal Finder can be fine-tuned.
Each page contains multiple product deals, each annotated with:

- Product name
- Price
- Discount (if available)
- Unit / package information
- Original price (if available)
- Bounding box around the product region

The dataset supports tasks such as:

- Document layout segmentation
- Product offer extraction
- Multimodal brochure understanding
- Benchmarking LLM-based extraction vs. rule-based or OCR-based pipelines

## Data Sources

The images in this dataset were manually collected from German supermarket chains, primarily:
- REWE
- Aldi Süd
- Edeka
- Kaufland
- Netto
- Penny
- Rossmann

### Human-validated Machine-labeled Data
All brochure pages and other materials are publicly accessible promotional materials and are used solely for research and educational purposes.
PDFs were preprocessed into uniform PNG format and stored under [image_uniform](images_uniform), for example, the PNGs of Rewe brochures are stored under [image_uniform/rewe](images_uniform/rewe), while the annotated JSON files under [image_uniform/rewe_annotated](images_uniform/rewe_annotated)
```text
project/
├── data/
│   ├── image_uniform/
│   │   ├── rewe # uniform PNG (1024 x 1448)
│   │   ├── rewe_annotated # annotation for each PNG (JSON files)
│   │   ├── ...
```
### Synthetic data
For some other models that needs a task-specific fine-tuning process, we also provide synthetic data. 

The generation method is inspired by *SynthTIGER* from [Yim et al](https://arxiv.org/abs/2107.09313).

We have prepared the materials (products crawled from internet) for you to generate, you only need to run the generation code.
```bash
python3 synthesis_flyer.py --num_flyers
```

The dataset is hosted on Google Drive due to size/license constraints. You can directly download with Google Drive [syn_data_1](https://drive.google.com/file/d/1E4nCnD1LgnlhfHW199trpqQhqA_zyL0V/view?usp=drive_link) and [syn_data_2](https://drive.google.com/file/d/1fx-dQHXKCJxRcTJAcdXDghrVYGBU7yDb/view?usp=drive_link). And unzip them yourself. Access: read-only  

## Data Statistics

### Human-validated Machine-labeled Data

#### Numbers of Brochure pages from Each Supermarket

There are totally 231 brochure pages from 7 supermarket. And their distribution are shown as followed:

![](README_pics/pages_per_supermarket_pie.png)

#### Average Number of Products per Page

The figure below shows the average number of annotated product deals per brochure page.

![Avg products per page](README_pics/avg_products_per_page_bar.png)

#### Product Count Distribution

The distribution shows that most brochure pages contain between 4 and 10 products, with a clear right-skewed long tail, indicating the presence of a small number of highly dense pages.

![Product Count Distribution](README_pics/product_count_distribution.png)

#### Spatial Distribution of Product Deals

The figures visualize the spatial distribution of product bounding boxes across all brochure pages.
Each point corresponds to the center of a product deal region, projected onto a normalized page layout
(1024 × 1448).

A clear layout bias can be observed, reflecting common brochure design patterns such as column-based layouts
and central content concentration.

<p align="center">
  <img src="README_pics/bbox_center_scatter.png" width="45%" />
  <img src="README_pics/bbox_center_heatmap.png" width="45%" />
</p>

### Synthetic Data

#### Average Number of Products per Page

![Average Product pro pages](README_pics/avg_products_per_page_bar_syn.png)

#### Product Count Distribution

Ignoring the data on the right-skewed long tail of distribution from human-validated machine-labeled data, this distribution resembles the upper one.

![Product Count Distribution](README_pics/product_count_distribution_syn.png)

#### Spatial Distribution of Product Deals

The distribution follows the pattern of the real-world data, namely column-based layouts
and central content concentration.

<p align="center">
  <img src="README_pics/bbox_center_scatter_syn.png" width="45%" />
  <img src="README_pics/bbox_center_heatmap_syn.png" width="45%" />
</p>

## Recommended Data Usage and Model

Through a series of controlled fine-tuning experiments, we observe that most modern vision-language models **already possess sufficient visual understanding for this task**, and that performance is primarily limited by output consistency and schema adherence, rather than recognition capability.

### Effect of Fine-Tuning on Output Normalization

Take the output of Llama3.2 (11B) of the same input picture and prompt as example. 

Wanted json format:
```text
[
  {
    "product_name": "REWE Bio Wiener Würstchen",
    "price": "2.59",
    "discount": null,
    "unit": "je 200-g-Pckg.",
    "original_price": null,
    "bbox": [
      0.11771347871297452,
      0.539411765286409,
      0.6245741593501881,
      0.7534985024672453
    ]
  },
  ...
]
```

Before Fine-tuning

```text
The image shows a German supermarket brochure page with various products and their prices. The products are arranged in a grid, with each product having its own section with a picture, name, price, and other details.

Here is the extracted information in the requested format:

[
  {{
    "product_name": "REWE Bio Wiener Würstchen",
    "price": "2.59",
    "discount": null,
    "unit": "je 200-g-Pckg.",
    "original_price": null,
    "bbox": [0.12, 0.30, 0.28, 0.71]
  }},
  {{
    "product_name": "REWE Bio Baguette Salami",
    "price": "1.59",
    "discount": null,
    "unit": "je 80-g-Pckg.",
    "original_price": null,
    "bbox": [0.42, 0.18, 0.57, 0.55]
  }},
  {{
    "product_name": "REWE Bio Schinkenwurst",
    "price": "1.29",
    "discount": null,
    "unit": "je 100-g-Pckg.",
    "original_price": null,
    "bbox": [0.12, 0.30, 0.28, 0.71]
  }},
  {{
    "product_name": "REWE Bio Hirtenkäse",
    "price": "1.79",
    "discount": null,
    "unit": "45% Fett i.Tr., je 200-g-Pckg.",
    "original_price": null,
    "bbox": [0.42, 0.18, 0.57, 0.55]
  }}
]
```

After Fine-tuning

```text
[{"product_name": "REWE Bio Wiener Würstchen", "price": "2.59", "discount": null, "unit": "je 200-g-Pckg.", "original_price": null, "bbox": [0.12199999999999998, 0.5279999999999999, 0.4819999999999999, 0.8049999999999999]}, {"product_name": "REWE Bio Baguette Salami", "price": "1.59", "discount": null, "unit": "je 80-g-Pckg.", "original_price": null, "bbox": [0.5049999999999999, 0.5279999999999999, 0.8819999999999999, 0.8049999999999999]}, {"product_name": "REWE Bio Schinkenwurst", "price": "1.29", "discount": null, "unit": "je 100-g-Pckg.", "original_price": null, "bbox": [0.12199999999999998, 0.8089999999999999, 0.4819999999999999, 0.9609999999999999]}, {"product_name": "REWE Bio Hirtenkäse", "price": "1.79", "discount": null, "unit": "je 200-g-Pckg.", "original_price": null, "bbox": [0.5049999999999999, 0.8089999999999999, 0.8819999999999999, 0.9609999999999999]}]
```
After fine-tuning, the output becomes more appropriate: the formatted results follow the correct JSON structure and no longer contain unwanted tokens. In addition, the predicted bounding boxes are placed more accurately.

### Recommendations on Model Choice
**Mid-sized vision-language models (around 7B) are generally sufficient**, with larger models (11B) offering limited additional benefit for this dataset. These models have already good ability on recognizing difficult brochure layout - only a few steps of fine-tuning can help them normalize their outputs. Smaller models like Paddle-OCR (1B) and Deepseek-OCR (3B) in contrast show lower ability on this task.

### Recommended Data Usage

To find out the best data mixing strategy for fine-tuning, following data strategies are tested on two models:

**Llama3.2 (11B)**

| Training Data (Quantity)        | Real : Synthetic | F1    | Precision | Recall | Price Acc. | BBox Acc. | Mean IoU |
|----------------------|------------------|-------|-----------|--------|------------|-----------|----------|
| Real only (174)      | 100% : 0%        | 88.70 | 89.62     | 87.80  | 59.85      | 21.62     | 0.27     |
| Synthetic only (5000)| 0% : 100%        | 86.85 | 76.96     | **99.66**  | 52.72      | 3.40      | 0.16     |
| Mixed (1912)         | 10% : 90%        | 90.47 | 86.42     | 94.92  | 61.07      | 23.93    | 0.29     |
| Mixed (1912)         | 20% : 80%        | 89.18 | 86.35     | 92.20  | 61.76      | 28.68    | 0.30     |
| ✨**Mixed (1912)**  | **40% : 60%**    | **91.61** | **90.70** | 92.54 | 63.37 | 39.19 | **0.37** |
| Real only (87)       | 100% : 0%        | 87.94 | **92.19**     | 84.07  | **66.94**      | **41.94**    | **0.37**     |
| ✨**Real only (20)**   | 100% : 0%  | **92.86** | 89.10 | **96.95** | **63.64** | **50.70** | **0.40** |

**Qwen2.5-VL (7B)**

| Training Data (Quantity)      | Real : Synthetic | F1    | Precision | Recall | Price Acc. | BBox Acc. | Mean IoU |
|----------------------|------------------|-------|-----------|--------|------------|-----------|----------|
| Real only (174)      | 100% : 0%        | 90.07 | 88.03     | 92.20  | 56.99      | 5.51      | 0.13     |
| Synthetic only (5000)| 0% : 100%        | 89.43 | 81.56     | **98.98**  | 41.10      | 1.37      | 0.07     |
| Mixed (1912)         | 10% : 90%        | 88.15 | 82.54     | **94.58**  | 55.56      | **14.34**    | **0.23**     |
| Mixed (1912)         | 20% : 80%        | 71.91 | **96.57**     | 57.29  | 66.86      | 1.78     | 0.08     | 
| Mixed (1912)         | 40% : 60%        | 49.25 | 95.15     | 33.22  | 51.02      | **12.24**    | **0.22**     |
| ✨**Real only (87)**   | 100% : 0%      | **92.28** | 95.64 | 89.15 | **70.34** | 5.70 | 0.15 |
| ✨**Real only (20)**   | 100% : 0%  | **92.69** | **97.74** | 88.14 | **71.15** | 8.85 | 0.14 |

From the experiment results, the following takeaways are concluded for data users:
- **Real data is critical for output normalization and localization.** Even 20 real samples can strongly stabilize F1, JSON structure, and BBox alignment.
- **Synthetic data should be used as a complement, not a replacement.** Training on synthetic data alone leads to high recall but poor precision and localization, especially for prices and bounding boxes.
- **Balanced mixing yields the best results, but only up to a point.** For LLaMA-11B, a moderate real-to-synthetic ratio (≈40% : 60%) provides the best overall trade-off, while excessive synthetic data introduces noise and degrades spatial accuracy.

## Annotation Methods
Annotations were created using **Label Studio** and **Gemini 2.5 pro** with the following labeling interface:
- A RectangleLabels tool for marking each product deal region (bounding box region).
- Multiple TextArea fields for structured metadata:
  - product_name
  - price
  - discount
  - unit
  - original_price

## Annotation Workflow
1. Create annotations for each brochure images with the help of Gemini
2. Convert the annotations into JSON files
3. Upload brochure images and corresponding Json annotations into a Label Studio project.
4. For each product card:
   - Check if bounding box covering the entire deal region.
     - Bounding boxes should just cover the deal region with all the information included.
     - Bounding boxes are stored as percentages (0–100) in Label Studio coordinates, but later they will be standardized into the 0-1.
   - Check product information in the corresponding text fields.
     - Prices include only numeric characters (e.g., "1.79" instead of "€1.79").
     - Discounts exclude the percent symbol (e.g., "20" not "-20%").
     - Units follow the complete description on the brochure.
     - Unavailable fields are stored as empty strings ("") or null.
5. Save the annotation, then export all labeled tasks as JSON.
6. Convert the JSON exported from Label Studio into a required structure like [rewe_annotated/example](images_uniform/rewe_annotated/rewe_10112025_page_1.json).

Here are the same brochure page before and after annotation:

<table>
  <tr>
    <td align="center"><b>Gemini Annotation</b></td>
    <td align="center"><b>Human Annotation After</b></td>
  </tr>
  <tr>
    <td><img src="README_pics/annotation_before.png" width=907></td>
    <td><img src="README_pics/annotation_after.png" width=726></td>
  </tr>
</table>


## Exported and Normalized Annotation Format
Label Studio exports each annotated page as a dictionary inside a JSON list.
```json
{
  "image": "/dataset/upload/2/0453b2be-rewe_10112025_page_1.png",
  "id": 36,
  "deal": [
    {
      "x": 12.13,
      "y": 27.21,
      "width": 24.24,
      "height": 19.88,
      "rotation": 0,
      "rectanglelabels": ["Deal"],
      "original_width": 1024,
      "original_height": 1448
    }
  ],
  "product_name": ["Monster Energy Drink"],
  "price": ["0.77"],
  "discount": [""],
  "original_price": [""],
  "unit": ["je 0,5-l-Dose"]
}
```
For downstream processing and benchmarking, each page is converted into a clean JSON list where each product is represented as a single object:
```json
[
  {
    "product_name": "Monster Energy Drink",
    "price": "0.77",
    "discount": null,
    "unit": "je 0,5-l-Dose",
    "original_price": null,
    "bbox": [0.12, 0.27, 0.36, 0.46]
  },
]
```
Data without deal information are annotated as:
```json
null
```

## Limitations and Future Work

While the dataset covers a diverse set of supermarket brochures, it is limited to a fixed page resolution and a single document type. Layout patterns and product representations may therefore not fully generalize to other promotional formats or regions. In addition, some pages contain no valid product deals, and certain fields (e.g., discounts) are sparsely populated, which may affect model performance and evaluation stability. 

The annotation workflow is also not perfect. The annotation only by one person is exhausted and therefore problematic to some degree.

If we have more (unlimited) time and resource. We will annotate more data and with a more proper way. More supermarkets and pages will be included. An more correct approach to make sure the correctness of the annotations will also be introduced.

## License and Usage
The dataset is intended solely for academic research and educational purposes, not for commercial redistribution.
Please ensure compliance with the terms of supermarket promotional material usage in your jurisdiction.

## Contact
For questions regarding the dataset format or annotation pipeline:

Liyang Deng

Email: <liyang.deng@stud.uni-heidelberg.de>
