import json
import os
import re

# JSON file path
INPUT_JSON = "all_annotations_penny_10112025.json"

# Output dir
OUTPUT_DIR = "per_image_json_penny"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def convert_bbox_ls_to_norm(bbox):
    """
    将 Label Studio 的百分比 bbox
    (x, y, width, height) 转回标准化 0–1 bbox:
    [x_min, y_min, x_max, y_max]
    """
    x = bbox["x"] / 100.0
    y = bbox["y"] / 100.0
    w = bbox["width"] / 100.0
    h = bbox["height"] / 100.0

    return [
        x,
        y,
        x + w,
        y + h
    ]


def process_one_task(task_dict):
    """
    输入：Label Studio 导出的一个 dict（你截图里的那种）
    输出：该图片的所有商品的整理后 JSON list
    """
    try:
        deals = task_dict["deal"]
        names = task_dict["product_name"]
        prices = task_dict["price"]
        discounts = task_dict["discount"]
        units = task_dict["unit"]
        original_prices = task_dict["original_price"]
        print(deals)
        if type(names) is str:
            names = [names]
            prices = [prices]
            discounts = [discounts]
            units = [units]
            original_prices = [original_prices]
        assert len(deals) == len(names) == len(prices) == len(discounts) == len(units) == len(original_prices)

        results = []

        for i in range(len(deals)):
            bbox_ls = deals[i]
            bbox_norm = convert_bbox_ls_to_norm(bbox_ls)

            entry = {
                "product_name": names[i] if names[i] != "" else None,
                "price": prices[i] if prices[i] != "" else None,
                "discount": discounts[i] if discounts[i] != "" and discounts[i] != "null" else None,
                "unit": units[i] if units[i] != "" and units[i] != "null" else None,
                "original_price": original_prices[i] if original_prices[i] != "" and original_prices[i] != "null" else None,
                "bbox": bbox_norm
            }

            results.append(entry)

        return results

    except KeyError:
        print(f"No Deals in {task_dict}!")


def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)  # 这是一个 list，每个元素是一个 dict

    for task in data:
        task_name = re.search(r"[a-z]*_\d{8}_page_\d+", task["image"]).group()

        per_image_list = process_one_task(task)

        out_path = os.path.join(OUTPUT_DIR, f"{task_name}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(per_image_list, f, indent=2, ensure_ascii=False)

        print(f"生成文件: {out_path}")


if __name__ == "__main__":
    main()
