# Synthesis Flyer Generation
import os
import random
import json
import io
from icrawler.builtin import BingImageCrawler
from rembg import remove
from PIL import Image, ImageDraw, ImageFont, ImageColor

# ------ Configurations ------

# basic paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "data", "assets")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")  
PIC_DIR = os.path.join(BASE_DIR, "data", "pictures")
ANNOTATION_DIR = os.path.join(BASE_DIR, "data", "annotations")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(ASSET_DIR, exist_ok=True)
os.makedirs(PIC_DIR, exist_ok=True)
os.makedirs(ANNOTATION_DIR, exist_ok=True)

# Color palettes
LIGHT_BGS = ["#FFFFFF", "#F8F9FA", "#FFF5EE", "#F0F8FF", "#FFFFF0", "#FFFACD"]

DARK_BGS = ["#C00000", "#005293", "#007D3D", "#FF6600"]

# Color block themes
BLOCK_THEMES = [
    ("#C00000", "#FFD700", "diagonal_red_yellow"), # typical sale
    ("#005293", "#FFFFFF", "split_blue_white"),    # fresh style
    ("#FF4500", "#FFFFFF", "top_banner_orange"),   # warm highlight
]

# Header texts
HEADER_TEXTS = [
    "WOCHENANGEBOTE", "SUPERKNÜLLER", "AKTIONSPREISE", 
    "FRISCH & LECKER", "NUR FÜR KURZE ZEIT", "TOP-DEALS DER WOCHE"
]

# Load Units DB
units_path = os.path.join(DATA_DIR, "units_db.json")
with open(units_path, 'r', encoding='utf-8') as f:
    UNITS_DB = json.load(f)

# Load Product Catalog
catalog_path = os.path.join(DATA_DIR, "product_catalog.json")
with open(catalog_path, 'r', encoding='utf-8') as f:
    PRODUCT_CATALOG = json.load(f)

print(f"Load: {len(UNITS_DB)} kinds of unit, {len(PRODUCT_CATALOG)} products.")

def prepare_assets():
    """
    Prepare product image assets: download and remove background
    """
    print(">>> Prepare materials...")
    
    for product in PRODUCT_CATALOG:
        key_name = product["name_en"].replace(" ", "_").lower()
        processed_path = os.path.join(ASSET_DIR, f"{key_name}.png")
        
        if os.path.exists(processed_path):
            print(f"    [Already exists] {product['name_de']}")
            continue

        # Crawl image from Bing
        print(f"    [Downloading] {product['name_en']} ...")
        temp_dir = os.path.join(RAW_DIR, key_name)
        crawler = BingImageCrawler(storage={'root_dir': temp_dir})
        crawler.crawl(keyword=f"{product['name_en']} product white background", max_num=1)
        
        # Read downloaded image
        try:
            # Get downloaded file (usually 000001.jpg)
            downloaded_files = [f for f in os.listdir(temp_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
            if not downloaded_files:
                print(f"    [Error] Didn't Find downloaded pictures: {key_name}")
                continue
                
            raw_img_path = os.path.join(temp_dir, downloaded_files[0])
            
            # Remove background (Rembg)
            print(f"    [Removing background] processing...")
            with open(raw_img_path, 'rb') as i:
                input_data = i.read()
                output_data = remove(input_data)
                
            # Save as transparent PNG
            image = Image.open(io.BytesIO(output_data)).convert("RGBA")
            image.save(processed_path)
            print(f"    [Saved] File: {processed_path}")
            
        except Exception as e:
            print(f"    [Failed] Processing {key_name} failed: {e}")

# ------ Auxiliary Functions (Colors and Fonts) ------

def generate_price_data():
    """
    Generate realistic price data with possible discounts
    """
    current_val = random.choice([0.99, 1.49, 1.79, 1.99, 2.49, 3.99, 4.99, 9.99, 14.99, 19.99, 29.99, 49.99, 199.99])
    
    # Determine if there is a discount (60% chance)
    has_discount = random.random() < 0.5
    
    if not has_discount:
        # Without discount
        return {
            "price": f"{current_val:.2f}", # "1.99"
            "original_price": None,        # JSON null
            "discount": None               # JSON null
        }

    # Calculate original price based on discount rate
    discount_rate = random.choice([0.10, 0.20, 0.25, 0.33, 0.50])
    original_val = current_val / (1 - discount_rate)
    
    return {
        "price": f"{current_val:.2f}",
        "original_price": f"{original_val:.2f}",
        "discount": f"{int(discount_rate * 100)}" # "33"
    }

def draw_strikethrough_text(draw, x, y, text, font, fill="black"):
    """
    Draw text with a strikethrough line
    """
    # Draw the text
    draw.text((x, y), text, font=font, fill=fill)
    
    # Calculate text bounding box
    bbox = draw.textbbox((x, y), text, font=font)
    x0, y0, x1, y1 = bbox
    
    # Draw strikethrough line
    mid_y = (y0 + y1) / 2
    draw.line([x0, mid_y, x1, mid_y], fill=fill, width=2)
    
    return bbox

def draw_discount_badge(draw, x, y, discount_str, font):
    """
    Draw a discount badge with red background and white text
    """
    text = f"-{discount_str}%"
    
    bbox = draw.textbbox((0,0), text, font=font)
    w = bbox[2] - bbox[0] + 10
    h = bbox[3] - bbox[1] + 6
    
    draw.rectangle([x, y, x+w, y+h], fill="#D00000")
    draw.text((x+5, y+3), text, font=font, fill="white", stroke_width=0)
    
    return [x, y, x+w, y+h]

def normalize_bbox(bbox, img_w, img_h):
    return [
        bbox[0] / img_w,
        bbox[1] / img_h,
        bbox[2] / img_w,
        bbox[3] / img_h
    ]

def get_font(size, bold=False):
    try:
        font_name = "Impact.ttf" if bold else "Arial.ttf"
        return ImageFont.truetype(font_name, size)
    except:
        return ImageFont.load_default()

def get_contrasting_text_color(hex_bg_color):
    """
    Calculate contrasting text color (black or white) based on background color
    """
    try:
        rgb = ImageColor.getrgb(hex_bg_color)
        luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
        return "white" if luminance < 140 else "black"
    except:
        return "black" # Fallback

# ------ Core Flyer Generation Logic ------

def draw_dynamic_background(W, H):
    """
    Generate a dynamic background with either solid color or color blocks
    """
    canvas = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(canvas)
    main_bg_color = "#FFFFFF"

    # 30% probability for blocks, 70% for solid color
    strategy = random.choices(["blocks", "solid"], weights=[0.3, 0.7])[0]

    if strategy == "solid":
        main_bg_color = random.choice(LIGHT_BGS + DARK_BGS)
        draw.rectangle([0, 0, W, H], fill=main_bg_color)
        
    else:
        c1, c2, theme = random.choice(BLOCK_THEMES)
        main_bg_color = c2
        
        if theme == "diagonal_red_yellow":
            draw.polygon([(0,0), (W,0), (0,H)], fill=c1)
            draw.polygon([(W,0), (W,H), (0,H)], fill=c2)
        elif theme == "split_blue_white":
            split_y = H // 3
            draw.rectangle([0, 0, W, split_y], fill=c1)
            draw.rectangle([0, split_y, W, H], fill=c2)
        elif theme == "top_banner_orange":
            draw.rectangle([0, 0, W, H], fill=c2)
            draw.rectangle([0, 0, W, 150], fill=c1)

    return canvas, draw, main_bg_color

def draw_price_text(draw, x, y, price_str, font):
    """
    Draw price text with red fill and white stroke
    """
    text_color = "#D00000"
    stroke_color = "white"
    stroke_width = 3
    draw.text((x, y), price_str, font=font, fill=text_color, 
              stroke_width=stroke_width, stroke_fill=stroke_color)
    bbox = draw.textbbox((x, y), price_str, font=font, stroke_width=stroke_width)
    return [bbox[0], bbox[1], bbox[2], bbox[3]]

# ------ Layout Synthesis Function ------
def create_flyer(flyer_id=1):
    print(f"\n>>> Generating Flyer #{flyer_id} ...")
    
    W, H = 1024, 1448
    
    # Background
    canvas, draw, main_bg_color = draw_dynamic_background(W, H)
    
    # Text colors
    default_text_color = get_contrasting_text_color(main_bg_color)
    desc_text_color = "#E0E0E0" if default_text_color == "white" else "#555555"

    product_annotations = []
    
    # Draw Header
    PAGE_MARGIN_X = 40
    PAGE_MARGIN_Y = 30

    header_bg = random.choice(["#D00000", "#FFCC00", "#005293", "#E60000"])
    header_text = random.choice(HEADER_TEXTS)
    header_text_color = get_contrasting_text_color(header_bg)
    

    draw.rectangle([PAGE_MARGIN_X-10, PAGE_MARGIN_Y, W-PAGE_MARGIN_X+10, PAGE_MARGIN_Y+70], fill=header_bg)
    header_font = get_font(48, True)
    try: wb = draw.textbbox((0,0), header_text, font=header_font); h_w=wb[2]-wb[0]
    except: h_w = 200
    draw.text(((W-h_w)//2, PAGE_MARGIN_Y+10), header_text, font=header_font, fill=header_text_color)

    # Main Content Area
    current_y = PAGE_MARGIN_Y + 100
    COL_GAP = 30
    ROW_GAP = 50

    BOTTOM_SAFE_MARGIN = 80 
    MIN_ROW_HEIGHT = 280

    while current_y + MIN_ROW_HEIGHT < (H - BOTTOM_SAFE_MARGIN):
        max_possible_height = H - BOTTOM_SAFE_MARGIN - current_y
        row_height = random.randint(MIN_ROW_HEIGHT, min(350, max_possible_height))
        num_cols = random.choices([2, 3], weights=[0.4, 0.6])[0]

        available_width = W - (2 * PAGE_MARGIN_X) - ((num_cols - 1) * COL_GAP)
        cell_w = int(available_width / num_cols)

        for c in range(num_cols):
            cell_x = PAGE_MARGIN_X + c * (cell_w + COL_GAP)
            cell_y = current_y
            
            group_min_x, group_min_y = W, H
            group_max_x, group_max_y = 0, 0
            
            def update_group_bbox(box):
                nonlocal group_min_x, group_min_y, group_max_x, group_max_y
                group_min_x = min(group_min_x, box[0])
                group_min_y = min(group_min_y, box[1])
                group_max_x = max(group_max_x, box[2])
                group_max_y = max(group_max_y, box[3])

            # Prepare product item
            item = random.choice(PRODUCT_CATALOG)
            key_name = item["name_en"].replace(" ", "_").lower()
            img_path = os.path.join(ASSET_DIR, f"{key_name}.png")
            if not os.path.exists(img_path): continue
            
            # Generate price data
            price_data = generate_price_data()

            # Layout decision
            layout_side = random.choices(["bottom", "top", "left", "right"], weights=[0.5, 0.2, 0.15, 0.15])[0]
            
            img_rect = [0,0,0,0] # x,y,w,h
            text_area_rect = [0,0,0,0]
            price_safe_zones = []
            padding = 15

            item = random.choice(PRODUCT_CATALOG)
            key_name = item["name_en"].replace(" ", "_").lower()
            img_path = os.path.join(ASSET_DIR, f"{key_name}.png")
            if not os.path.exists(img_path): continue
            price_data = generate_price_data()

            if layout_side in ["bottom", "top"]:
                img_target_w = int(cell_w * 0.85)
                img_target_h = int(row_height * 0.55)
                img_rect[2], img_rect[3] = img_target_w, img_target_h
                img_rect[0] = cell_x + (cell_w - img_target_w) // 2
                
                text_area_w = cell_w
                text_area_h = row_height * 0.35
                text_area_rect[2], text_area_rect[3] = text_area_w, text_area_h
                text_area_rect[0] = cell_x

                if layout_side == "bottom":
                    img_rect[1] = cell_y + padding
                    text_area_rect[1] = img_rect[1] + img_rect[3] + padding
                    price_safe_zones = ["top_left", "top_right", "on_image_top_left", "on_image_top_right"]
                else:
                    text_area_rect[1] = cell_y + padding
                    img_rect[1] = text_area_rect[1] + text_area_rect[3] + padding
                    price_safe_zones = ["bottom_left", "bottom_right", "on_image_bottom_left", "on_image_bottom_right"]
            else:
                img_target_w = int(cell_w * 0.50)
                img_target_h = int(row_height * 0.75)
                img_rect[2], img_rect[3] = img_target_w, img_target_h
                img_rect[1] = cell_y + (row_height - img_target_h) // 2
                
                text_area_w = cell_w - img_target_w - padding
                text_area_h = img_target_h
                text_area_rect[2], text_area_rect[3] = text_area_w, text_area_h
                text_area_rect[1] = img_rect[1]

                if layout_side == "left":
                    text_area_rect[0] = cell_x + padding
                    img_rect[0] = text_area_rect[0] + text_area_w + padding
                    price_safe_zones = ["top_right", "bottom_right", "on_image_right"]
                else:
                    img_rect[0] = cell_x + padding
                    text_area_rect[0] = img_rect[0] + img_rect[2] + padding
                    price_safe_zones = ["top_left", "bottom_left", "on_image_left"]

            # Render product image
            prod_img = Image.open(img_path).rotate(random.randint(-5, 5), resample=Image.BICUBIC, expand=True)
            prod_img.thumbnail((int(img_rect[2]), int(img_rect[3])), Image.LANCZOS)
            
            actual_img_x = int(img_rect[0] + (img_rect[2] - prod_img.width) // 2)
            actual_img_y = int(img_rect[1] + (img_rect[3] - prod_img.height) // 2)

            if actual_img_y + prod_img.height > H - 10: 
                continue # If image exceeds bottom, skip this cell
            
            canvas.paste(prod_img, (actual_img_x, actual_img_y), prod_img)
            update_group_bbox([actual_img_x, actual_img_y, actual_img_x+prod_img.width, actual_img_y+prod_img.height])

            # Render text area
            tx, ty, tw, th = text_area_rect
            text_cursor_y = ty + 10
            center_x_text = tx + tw // 2
            
            name_font = get_font(24, bold=True)
            desc_font = get_font(16)

            # Name
            try: wb=draw.textbbox((0,0),item["name_de"],font=name_font); w_txt=wb[2]-wb[0]
            except: w_txt=100
            if w_txt > tw: name_font = get_font(20, bold=True) 

            if text_cursor_y + 25 < H - 10:
                name_box = [center_x_text-w_txt//2, text_cursor_y, center_x_text+w_txt//2, text_cursor_y+26]
                draw.text((name_box[0], name_box[1]), item["name_de"], font=name_font, fill=default_text_color)
                update_group_bbox(name_box)
            
            text_cursor_y += 30
            try: wb=draw.textbbox((0,0),item["desc"],font=desc_font); w_txt=wb[2]-wb[0]
            except: w_txt=80

            if text_cursor_y + 20 < H - 10:
                draw.text((center_x_text-w_txt//2, text_cursor_y), item["desc"], font=desc_font, fill=desc_text_color)
            
            text_cursor_y += 20
            unit_str = random.choice(UNITS_DB.get(item["type"], ["je Stück"]))
            try: wb=draw.textbbox((0,0),unit_str,font=desc_font); w_txt=wb[2]-wb[0]
            except: w_txt=50

            if text_cursor_y + 18 < H - 10:
                unit_box = [center_x_text-w_txt//2, text_cursor_y, center_x_text+w_txt//2, text_cursor_y+18]
                draw.text((unit_box[0], unit_box[1]), unit_str, font=desc_font, fill=default_text_color)
                update_group_bbox(unit_box)

            # Render price info
            price_str = f"{price_data['price']} €"
            price_font = get_font(40, bold=True)
            orig_font = get_font(20, bold=True)
            
            chosen_zone = random.choice(price_safe_zones)
            px, py = 0, 0
            margin = 10
            
            if chosen_zone == "top_left":
                px, py = cell_x + margin, cell_y + margin
            elif chosen_zone == "top_right":
                px, py = cell_x + cell_w - 90, cell_y + margin
            elif chosen_zone == "bottom_left":
                px, py = cell_x + margin, cell_y + row_height - 60
            elif chosen_zone == "bottom_right":
                px, py = cell_x + cell_w - 90, cell_y + row_height - 60
            elif "on_image" in chosen_zone:
                if "top_left" in chosen_zone: px, py = actual_img_x - 10, actual_img_y - 10
                elif "top_right" in chosen_zone: px, py = actual_img_x + prod_img.width - 70, actual_img_y - 10
                elif "bottom_left" in chosen_zone: px, py = actual_img_x - 10, actual_img_y + prod_img.height - 40
                elif "bottom_right" in chosen_zone: px, py = actual_img_x + prod_img.width - 70, actual_img_y + prod_img.height - 40
                else: px, py = actual_img_x + prod_img.width - 70, actual_img_y # fallback

            px = max(cell_x, min(px, cell_x + cell_w - 80))
            py = max(cell_y, min(py, cell_y + row_height - 50))

            p_bbox = draw_price_text(draw, px, py, price_str, price_font)
            update_group_bbox(p_bbox)
            

            if price_data["original_price"]:
                orig_str = str(price_data['original_price'])
                orig_x = px + 5
                orig_y = py - 20
                orig_bbox = draw_strikethrough_text(draw, orig_x, orig_y, orig_str, orig_font, fill="#333")
                update_group_bbox(orig_bbox)
            
            if price_data["discount"]:
                
                badge_x = actual_img_x + prod_img.width - 15
                badge_y = actual_img_y - 15
                
                badge_x = min(badge_x, cell_x + cell_w - 40)
                badge_y = max(badge_y, cell_y)
                
                disc_bbox = draw_discount_badge(draw, badge_x, badge_y, price_data["discount"], orig_font)
                update_group_bbox(disc_bbox)

            # Annotate
            if group_max_x > group_min_x and group_max_y > group_min_y:
                norm_bbox = normalize_bbox(
                    [max(0, group_min_x), max(0, group_min_y), min(W, group_max_x), min(H, group_max_y)], 
                    W, H
                )
                
                product_annotations.append({
                    "product_name": item["name_de"],
                    "price": price_data["price"],
                    "discount": price_data["discount"],
                    "unit": unit_str,
                    "original_price": price_data["original_price"],
                    "bbox": norm_bbox
                })

        current_y += row_height + ROW_GAP

    # Save output image and annotations
    image_filename = f"flyer_full_{flyer_id:03d}.jpg"
    canvas.save(os.path.join(PIC_DIR, image_filename))

    json_path = os.path.join(ANNOTATION_DIR, f"flyer_full_{flyer_id:03d}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(product_annotations, f, indent=2, ensure_ascii=False)
        
    print(f"[Finished] Full Flyer: {image_filename}")

if __name__ == "__main__":
    prepare_assets()
    for i in range(1, 5001):
        create_flyer(flyer_id=i)
