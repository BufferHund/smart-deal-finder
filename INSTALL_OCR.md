# OCR Dependencies Installation Guide

完整的OCR引擎安装指南。

## 快速安装（推荐）

### 自动安装脚本

```bash
# 1. 确保在项目目录
cd /Users/zack/Documents/smartdeal

# 2. 激活虚拟环境（如果有）
source venv/bin/activate  # 或者 conda activate base

# 3. 运行安装脚本
./install_ocr_dependencies.sh
```

这个脚本会自动安装：
- ✅ Tesseract OCR（系统依赖）
- ✅ Tesseract语言包（包括德语）
- ✅ pytesseract（Python包）
- ✅ PaddleOCR（Python包）
- ✅ EasyOCR（Python包）

## 手动安装步骤

如果自动安装失败，可以手动安装：

### 1. 安装Tesseract（系统依赖）

#### macOS (使用Homebrew)

```bash
# 安装Homebrew（如果还没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装Tesseract
brew install tesseract

# 安装语言包（包括德语）
brew install tesseract-lang

# 验证安装
tesseract --version
```

#### Linux (Ubuntu/Debian)

```bash
# 更新包列表
sudo apt-get update

# 安装Tesseract
sudo apt-get install tesseract-ocr

# 安装德语语言包
sudo apt-get install tesseract-ocr-deu

# 验证安装
tesseract --version
```

#### Windows

1. 下载安装包：https://github.com/UB-Mannheim/tesseract/wiki
2. 运行安装程序
3. 添加到系统PATH：
   ```
   C:\Program Files\Tesseract-OCR
   ```
4. 在命令提示符中验证：
   ```cmd
   tesseract --version
   ```

### 2. 安装Python包

#### 选项A：安装所有OCR包（推荐）

```bash
# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 安装所有OCR包
pip install pytesseract
pip install paddlepaddle paddleocr
pip install easyocr
```

#### 选项B：只安装必需的包

如果你只想用一个OCR引擎，可以选择性安装：

**仅Tesseract（最轻量）：**
```bash
pip install pytesseract
```

**仅PaddleOCR（最准确）：**
```bash
pip install paddlepaddle
pip install paddleocr
```

**仅EasyOCR（最易用）：**
```bash
pip install easyocr
```

## 分步安装命令

### 第一步：安装Tesseract系统依赖

```bash
# macOS
brew install tesseract tesseract-lang

# 验证
tesseract --version
# 应该显示类似：tesseract 5.x.x
```

### 第二步：安装pytesseract

```bash
pip install pytesseract

# 测试
python -c "import pytesseract; print('pytesseract OK')"
```

### 第三步：安装PaddleOCR

```bash
# 先安装paddlepaddle
pip install paddlepaddle

# 再安装paddleocr
pip install paddleocr

# 测试
python -c "from paddleocr import PaddleOCR; print('PaddleOCR OK')"
```

**注意**：PaddleOCR首次运行时会自动下载模型文件（约100MB），请确保网络连接。

### 第四步：安装EasyOCR

```bash
pip install easyocr

# 测试
python -c "import easyocr; print('EasyOCR OK')"
```

**注意**：EasyOCR首次使用时会下载模型文件（约50-100MB）。

## 验证安装

运行验证脚本检查所有依赖：

```bash
python verify_setup.py
```

你应该看到类似输出：

```
============================================================
 Python Packages
============================================================
✅ pytesseract: x.x.x
✅ paddleocr: x.x.x
✅ easyocr: x.x.x

============================================================
 System Dependencies
============================================================
✅ Tesseract: tesseract 5.x.x
```

## 常见问题

### 问题1: "tesseract is not installed"

**原因**: Tesseract未安装或不在PATH中

**解决方案**:
```bash
# macOS
brew install tesseract

# 检查安装位置
which tesseract

# 应该显示类似：/opt/homebrew/bin/tesseract
```

### 问题2: "ModuleNotFoundError: No module named 'pytesseract'"

**原因**: pytesseract Python包未安装

**解决方案**:
```bash
# 确保在正确的虚拟环境中
pip install pytesseract

# 验证
pip show pytesseract
```

### 问题3: PaddleOCR安装失败

**原因**: paddlepaddle依赖问题

**解决方案**:
```bash
# 方法1: 先安装paddlepaddle
pip install paddlepaddle==2.5.0
pip install paddleocr==2.7.0

# 方法2: 如果还是失败，尝试CPU版本
pip uninstall paddlepaddle
pip install paddlepaddle -i https://mirror.baidu.com/pypi/simple
```

### 问题4: EasyOCR安装很慢

**原因**: 依赖包较多

**解决方案**:
```bash
# 使用国内镜像加速
pip install easyocr -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题5: 权限错误

**解决方案**:
```bash
# 不要使用sudo pip install
# 而是使用虚拟环境
python -m venv venv
source venv/bin/activate
pip install pytesseract paddleocr easyocr
```

## 最小安装（如果空间有限）

只安装Tesseract（最小依赖）：

```bash
# 系统依赖
brew install tesseract

# Python包
pip install pytesseract

# 测试
python -c "import pytesseract; print('OK')"
```

这样可以让应用运行，其他OCR引擎可以后续添加。

## 推荐安装顺序

1. **第一优先级**: Tesseract + pytesseract
   - 最稳定、最快
   - 必需的系统依赖

2. **第二优先级**: PaddleOCR
   - 准确度最高
   - 对中文和德文支持好

3. **第三优先级**: EasyOCR
   - 可选的备用引擎
   - 易于使用

## 测试安装

创建测试脚本：

```python
# test_ocr.py
import sys

print("Testing OCR installations...\n")

# Test 1: pytesseract
try:
    import pytesseract
    print("✅ pytesseract:", pytesseract.__version__ if hasattr(pytesseract, '__version__') else "OK")
except ImportError:
    print("❌ pytesseract: Not installed")

# Test 2: PaddleOCR
try:
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR: OK")
except ImportError:
    print("❌ PaddleOCR: Not installed")

# Test 3: EasyOCR
try:
    import easyocr
    print("✅ EasyOCR:", easyocr.__version__ if hasattr(easyocr, '__version__') else "OK")
except ImportError:
    print("❌ EasyOCR: Not installed")

# Test 4: Tesseract system
try:
    result = pytesseract.get_tesseract_version()
    print("✅ Tesseract system:", result)
except:
    print("❌ Tesseract system: Not found")

print("\nAll tests completed!")
```

运行测试：
```bash
python test_ocr.py
```

## 卸载（如果需要）

```bash
# 卸载Python包
pip uninstall pytesseract paddleocr paddlepaddle easyocr

# 卸载Tesseract系统依赖
brew uninstall tesseract tesseract-lang  # macOS
```

## 磁盘空间要求

- Tesseract: ~10 MB
- pytesseract: <1 MB
- PaddleOCR: ~500 MB (包括模型)
- EasyOCR: ~300 MB (包括模型)

**总计**: 约 800 MB - 1 GB

## 下一步

安装完成后：

1. **运行验证**:
   ```bash
   python verify_setup.py
   ```

2. **测试OCR**:
   ```bash
   # 使用sample图片测试
   python src/preprocessing/ocr_pipeline.py --input sample.jpg --output results/
   ```

3. **启动Web应用**:
   ```bash
   ./run_app.sh
   ```

## 获取帮助

如果遇到问题：
1. 检查Python版本: `python --version` (需要3.8+)
2. 检查pip版本: `pip --version`
3. 更新pip: `pip install --upgrade pip`
4. 查看详细错误: 在命令后添加 `-v` 参数
5. 查阅文档: README.md, QUICK_START.md

---

**安装脚本**: `./install_ocr_dependencies.sh`
**验证脚本**: `python verify_setup.py`
**问题反馈**: 联系团队 Liyang, Zhaokun
