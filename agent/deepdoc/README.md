# DeepDoc - 深度文档解析模块

DeepDoc 是 AgentStudio 的增强文档解析模块，提供 OCR、布局识别和表格结构识别能力。

## 功能特性

### 1. OCR 文本识别
- 支持多种 OCR 引擎（PaddleOCR、Tesseract）
- 自动引擎选择和降级
- 支持扫描件 PDF 和图片文档
- 提供置信度评分

### 2. 布局识别
- 识别文档元素类型（标题、正文、表格、图片等）
- 使用 HuggingFace LayoutLM 模型
- 支持 10+ 种布局元素类型

### 3. 表格结构识别
- 检测表格行列结构
- 支持跨行跨列单元格
- 自动表格旋转校正
- 转换为 Markdown、HTML 和自然语言

### 4. 智能解析
- 三级解析强度（basic/standard/enhanced）
- 可选功能开关
- 结果缓存机制

## 快速开始

### 安装依赖

```bash
# 基础依赖
pip install PyMuPDF Pillow pytesseract opencv-python langdetect

# OCR 引擎（选择一个或两个）
pip install paddleocr paddlepaddle  # 推荐，中文友好
# 或
brew install tesseract  # macOS
apt-get install tesseract-ocr  # Ubuntu

# 布局识别（可选）
pip install transformers torch
```

### 配置

在 `.env` 文件中启用 DeepDoc：

```bash
# 启用 DeepDoc
ENABLE_DEEPDOC=true

# 解析级别 (basic|standard|enhanced)
DOCUMENT_PARSING_LEVEL=enhanced

# OCR 引擎选择 (paddleocr|tesseract|auto)
OCR_ENGINE=auto

# 启用特定功能
ENABLE_OCR=true
ENABLE_LAYOUT_RECOGNITION=true
ENABLE_TABLE_STRUCTURE_RECOGNITION=true
```

### 使用示例

```python
from rag.splitter import parse_file, ParsingLevel

# 读取文件
with open("document.pdf", "rb") as f:
    content = f.read()

# 标准解析
text = parse_file("document.pdf", content)

# 增强解析（使用 DeepDoc）
text = parse_file(
    "document.pdf",
    content,
    parsing_level=ParsingLevel.ENHANCED,
    enable_ocr=True
)
```

### 直接使用 DeepDoc API

```python
from deepdoc.parser.pdf_parser import PDFParser
from deepdoc.parser.base import ParsingLevel

# 创建解析器
parser = PDFParser(parsing_level=ParsingLevel.FULL)

# 解析文档
result = parser.parse("document.pdf")

# 访问结果
print(f"总页数: {result.total_pages}")
print(f"文本内容: {result.text_content}")

# 访问表格
for table in result.get_table_elements():
    print(table.metadata["markdown"])
    print(table.metadata.get("natural_language"))
```

### OCR 使用

```python
from deepdoc.ocr_selector import OCREngineSelector

# 自动选择最佳引擎
selector = OCREngineSelector(language="ch")
result = selector.recognize_image("scanned_document.png")

# 查看结果
for block in result.text_blocks:
    print(f"{block.text} (置信度: {block.confidence})")
```

### 表格结构识别

```python
from deepdoc.vision.tsr import TableStructureRecognizer

recognizer = TableStructureRecognizer()
table = recognizer.recognize_table("table_image.png")

# 输出为不同格式
print(table.to_markdown())
print(table.to_html())
print(table.to_natural_language())
```

## 测试

运行测试脚本：

```bash
cd agent
python test_deepdoc.py
```

## 性能优化

### 缓存

DeepDoc 会自动缓存解析结果：

```bash
# 设置缓存目录
DEEPDOC_CACHE_DIR=/path/to/cache

# 或使用默认位置 ./cache/deepdoc
```

### 资源需求

- **基础模式**: 2GB 内存
- **标准模式**: 4GB 内存
- **增强模式**: 8GB+ 内存（加载 ML 模型）

### GPU 支持

如果有 GPU，可以加速模型推理：

```python
from deepdoc.vision.layout import LayoutRecognizer

# 使用 GPU
recognizer = LayoutRecognizer(device="cuda")
```

## 故障排除

### OCR 引擎不可用

```bash
# 检查 Tesseract
tesseract --version

# 检查 PaddleOCR
python -c "from paddleocr import PaddleOCR; print('OK')"
```

### 模型下载慢

使用 HuggingFace 镜像：

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

### 内存不足

- 使用 `ParsingLevel.STANDARD` 而不是 `ENHANCED`
- 禁用不需要的功能
- 处理较小的文档或分页处理

## 架构

```
deepdoc/
├── ocr/              # OCR 引擎
│   ├── base.py       # OCR 基类
│   ├── paddle_ocr.py # PaddleOCR 实现
│   └── tesseract_ocr.py # Tesseract 实现
├── vision/           # 视觉识别
│   ├── layout.py     # 布局识别
│   └── tsr.py        # 表格结构识别
├── parser/           # 文档解析器
│   ├── base.py       # 解析器基类
│   ├── pdf_parser.py # PDF 解析器
│   └── image_parser.py # 图片解析器
├── models/           # 模型管理
│   └── model_manager.py
├── config.py         # 配置管理
└── cache_manager.py  # 缓存管理
```

## 对比 RAGFlow

| 特性 | AgentStudio DeepDoc | RAGFlow DeepDoc |
|------|-------------------|----------------|
| OCR 引擎 | PaddleOCR + Tesseract | PaddleOCR |
| 布局识别 | ✓ LayoutLM | ✓ LayoutLM |
| 表格结构识别 | ✓ Table Transformer | ✓ TSR |
| 模型管理 | ✓ 简单缓存 | ✓ 完整管理 |
| 依赖要求 | 轻量级可选 | 较重（Elasticsearch） |
| 配置灵活性 | ✓ 多级别可选 | ✓ 完整配置 |

## 许可证

MIT License
