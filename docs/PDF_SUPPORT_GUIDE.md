# PDF Support Guide

SmartDeal now supports PDF file uploads! This guide explains how to use the PDF processing features.

## 功能概览

✅ **PDF文件上传**: 直接上传PDF格式的超市传单
✅ **页面选择**: 多页PDF可选择特定页面处理
✅ **自动转换**: PDF自动转换为图片后进行OCR
✅ **完整支持**: 所有OCR和实体提取功能均可用

## 快速开始

### 1. 启动应用

```bash
./run_app.sh
# 或
streamlit run src/app/enhanced_app.py
```

### 2. 上传PDF文件

1. 打开Web应用 (http://localhost:8501)
2. 点击 "Browse files" 按钮
3. 选择PDF文件（支持 .pdf 格式）
4. 应用会自动检测这是PDF文件

### 3. 选择页面（多页PDF）

如果PDF有多个页面：
- 会显示页面总数
- 使用滑块选择要处理的页面
- 页面编号从1开始
- 预览会实时更新

### 4. 处理PDF页面

- 点击 "Extract Information" 按钮
- PDF页面会自动转换为图片
- 使用OCR提取文本
- 显示识别结果和边界框

## 功能详解

### PDF页面预览

```
📄 PDF file detected
📊 PDF has 8 page(s)

Select page to process: [slider: 1-8]

[PDF页面预览图]
Page 1 of 8
```

### 支持的PDF库

应用支持三个PDF处理库（按优先级）：

1. **pypdfium2** (推荐)
   - 最快速
   - 无外部依赖
   - 安装: `pip install pypdfium2`

2. **pdf2image**
   - 需要系统Poppler
   - 质量好
   - 安装: `pip install pdf2image`

3. **PyPDF2**
   - 仅读取页数
   - 不支持图片转换
   - 安装: `pip install PyPDF2`

### 安装PDF处理库

**推荐方式（pypdfium2）：**
```bash
pip install pypdfium2
```

**备选方式（pdf2image）：**
```bash
# macOS
brew install poppler
pip install pdf2image

# Ubuntu/Debian
sudo apt-get install poppler-utils
pip install pdf2image
```

## 使用场景

### 场景1: 单页PDF

```
1. 上传单页PDF
2. 自动显示该页
3. 点击 "Extract Information"
4. 查看提取结果
```

### 场景2: 多页PDF手册

```
1. 上传多页PDF（如8页传单）
2. 使用滑块浏览不同页面
3. 选择感兴趣的页面（如第3页）
4. 点击 "Extract Information"
5. 仅处理选中的页面
```

### 场景3: 批量处理（命令行）

```bash
# 转换单个PDF所有页面
python src/preprocessing/pdf_processor.py \
    --input brochure.pdf \
    --output output_dir/

# 转换特定页面
python src/preprocessing/pdf_processor.py \
    --input brochure.pdf \
    --output output_dir/ \
    --pages 1 3 5

# 批量处理整个目录
python src/preprocessing/pdf_processor.py \
    --input pdf_directory/ \
    --output output_dir/
```

## 工作流程

### Web应用工作流

```
PDF上传
    ↓
检测页数
    ↓
选择页面 (如果多页)
    ↓
PDF → 图片转换 (DPI: 300)
    ↓
OCR处理
    ↓
实体提取
    ↓
优惠识别
    ↓
结果显示 & 导出
```

### 转换参数

默认DPI设置:
- **Web应用**: 300 DPI
- **命令行**: 可自定义 (`--dpi 300`)

推荐设置:
- 快速预览: 150 DPI
- 标准处理: 300 DPI (默认)
- 高质量: 600 DPI

## API使用

### Python脚本中使用

```python
from preprocessing.pdf_processor import PDFProcessor

# 初始化处理器
processor = PDFProcessor(dpi=300)

# 获取页数
page_count = processor.get_page_count('brochure.pdf')
print(f"PDF has {page_count} pages")

# 转换特定页面
images = processor.pdf_to_images(
    'brochure.pdf',
    page_numbers=[1, 2, 3]
)

# 获取单个页面
first_page = processor.get_page_image('brochure.pdf', 1)

# 保存为图片
processor.pdf_to_images(
    'brochure.pdf',
    output_dir='output/',
    page_numbers=[1, 2]
)
```

### 与OCR Pipeline集成

```python
from preprocessing.pdf_processor import PDFProcessor
from preprocessing.ocr_pipeline import OCRPipeline

# 转换PDF
pdf_processor = PDFProcessor()
images = pdf_processor.pdf_to_images('brochure.pdf')

# 对每页进行OCR
ocr = OCRPipeline(ocr_engine='paddleocr')

for i, image in enumerate(images, start=1):
    # 保存临时图片
    temp_path = f'/tmp/page_{i}.jpg'
    import cv2
    cv2.imwrite(temp_path, image)

    # OCR处理
    result = ocr.process_image(temp_path)
    print(f"Page {i}: {result['num_boxes']} text boxes found")
```

## 文件要求

### PDF规格
- **格式**: PDF (.pdf)
- **版本**: PDF 1.0 - 1.7
- **大小**: 建议 < 10MB
- **页数**: 无限制（建议一次处理1页）

### 推荐来源
- 超市官网下载的PDF
- 邮件中的PDF附件
- 扫描的传单（作为PDF保存）

## 性能考虑

### 处理时间

单页PDF处理时间（300 DPI）：
- PDF转图片: 0.5-2秒
- OCR处理: 1-5秒（取决于OCR引擎）
- **总计**: 约2-7秒/页

### 内存使用

每页PDF（300 DPI）：
- 图片大小: 约2-5MB
- 内存占用: 约10-20MB
- 建议RAM: 4GB+

### 优化建议

1. **减少DPI**: 150-200 DPI对OCR通常足够
2. **单页处理**: 一次处理一页而非整个PDF
3. **关闭预览**: 处理时隐藏大图片预览
4. **使用pypdfium2**: 比pdf2image更快

## 故障排除

### 问题1: "Error reading PDF"

**原因**: PDF处理库未安装

**解决**:
```bash
pip install pypdfium2
```

### 问题2: "Failed to convert PDF page to image"

**原因**:
- PDF损坏
- 不支持的PDF版本
- 缺少依赖

**解决**:
1. 检查PDF是否能在其他软件中打开
2. 尝试重新下载PDF
3. 安装额外库:
   ```bash
   pip install pdf2image
   brew install poppler  # macOS
   ```

### 问题3: 转换很慢

**原因**:
- DPI设置过高
- PDF文件太大
- 页面太多

**解决**:
1. 降低DPI (150或200)
2. 一次处理一页
3. 使用pypdfium2而非pdf2image

### 问题4: OCR识别效果差

**原因**:
- DPI太低
- PDF扫描质量差
- 图片模糊

**解决**:
1. 提高DPI到300-400
2. 使用原始PDF而非扫描版
3. 尝试不同的OCR引擎

## 最佳实践

### ✅ 推荐做法

1. **使用原始PDF**: 优先使用从官网下载的PDF
2. **300 DPI**: 标准OCR处理使用300 DPI
3. **单页处理**: 一次处理一页以提高速度
4. **预览检查**: 处理前预览确认页面正确
5. **保存结果**: 及时导出处理结果

### ❌ 避免做法

1. ❌ 不要上传大文件 (>20MB)
2. ❌ 不要同时处理多个PDF
3. ❌ 不要使用过高DPI (>600)
4. ❌ 不要处理加密PDF
5. ❌ 不要处理低质量扫描件

## 命令行工具

### PDF转图片工具

```bash
# 基本用法
python src/preprocessing/pdf_processor.py \
    --input input.pdf \
    --output output_dir/

# 选项说明
--input    # 输入PDF文件或目录
--output   # 输出目录
--pages    # 要转换的页码（可选）
--dpi      # DPI设置（默认300）

# 示例
# 转换第1,3,5页
python src/preprocessing/pdf_processor.py \
    --input brochure.pdf \
    --output images/ \
    --pages 1 3 5

# 使用200 DPI
python src/preprocessing/pdf_processor.py \
    --input brochure.pdf \
    --output images/ \
    --dpi 200

# 批量处理
python src/preprocessing/pdf_processor.py \
    --input pdfs/ \
    --output images/
```

## 示例代码

### 完整处理流程

```python
#!/usr/bin/env python
"""完整的PDF处理示例"""

from preprocessing.pdf_processor import PDFProcessor
from preprocessing.ocr_pipeline import OCRPipeline
from app.utils import extract_entities, create_deals_from_entities
import json

# 1. 初始化
pdf_processor = PDFProcessor(dpi=300)
ocr = OCRPipeline(ocr_engine='paddleocr')

# 2. 处理PDF
pdf_path = 'brochure.pdf'
page_count = pdf_processor.get_page_count(pdf_path)

print(f"Processing {page_count} pages...")

all_deals = []

for page_num in range(1, page_count + 1):
    print(f"\nPage {page_num}/{page_count}")

    # 3. 转换页面
    image = pdf_processor.get_page_image(pdf_path, page_num)

    # 4. OCR
    import cv2
    temp_path = f'/tmp/page_{page_num}.jpg'
    cv2.imwrite(temp_path, image)
    ocr_result = ocr.process_image(temp_path)

    # 5. 提取实体
    entities = extract_entities(ocr_result['text_boxes'])

    # 6. 创建优惠
    deals = create_deals_from_entities(entities)
    all_deals.extend(deals)

    print(f"  Found {len(deals)} deals")

# 7. 保存结果
with open('deals.json', 'w', encoding='utf-8') as f:
    json.dump(all_deals, f, indent=2, ensure_ascii=False)

print(f"\n✅ Total: {len(all_deals)} deals saved to deals.json")
```

## 技术细节

### PDF处理库对比

| 特性 | pypdfium2 | pdf2image | PyPDF2 |
|-----|-----------|-----------|--------|
| 速度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 质量 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | N/A |
| 安装 | 简单 | 需Poppler | 简单 |
| 图片转换 | ✅ | ✅ | ❌ |
| 推荐 | ✅ | 备用 | 仅查看 |

### DPI对比

| DPI | 文件大小 | OCR速度 | 识别精度 | 推荐场景 |
|-----|---------|---------|----------|----------|
| 150 | 小 | 快 | 中 | 快速预览 |
| 200 | 中 | 中 | 好 | 一般处理 |
| 300 | 大 | 慢 | 很好 | 标准处理⭐ |
| 400 | 很大 | 很慢 | 优秀 | 高质量需求 |
| 600 | 巨大 | 极慢 | 优秀 | 特殊需求 |

## 更新日志

### v1.1 (Current)
- ✅ Added PDF upload support
- ✅ Added page selection for multi-page PDFs
- ✅ Integrated pypdfium2, pdf2image, PyPDF2
- ✅ Added command-line PDF converter
- ✅ Added batch processing support

### Planned v1.2
- [ ] Multi-page batch processing in web UI
- [ ] PDF preview thumbnails
- [ ] Bookmark/annotation support
- [ ] Encrypted PDF support

## 常见问题 (FAQ)

### Q: 支持哪些PDF版本？
A: PDF 1.0-1.7，大多数标准PDF都支持。

### Q: 可以处理扫描的PDF吗？
A: 可以，但质量取决于扫描清晰度。推荐300 DPI以上的扫描件。

### Q: 支持加密的PDF吗？
A: 当前版本不支持。请先解密PDF。

### Q: 为什么处理慢？
A: 检查DPI设置和PDF大小。降低DPI或使用pypdfium2可提速。

### Q: 可以一次处理整个PDF吗？
A: 命令行工具支持，Web应用建议单页处理以获得更好体验。

### Q: 识别率低怎么办？
A: 提高DPI、尝试不同OCR引擎、使用图片预处理。

## 获取帮助

- **文档**: README.md, WEB_APP_GUIDE.md
- **示例**: 查看代码中的docstring
- **问题**: 联系团队 Liyang, Zhaokun

---

**PDF支持已完成！** 🎉

现在可以直接上传和处理PDF格式的超市传单了！
