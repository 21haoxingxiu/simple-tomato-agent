#!/usr/bin/env python3
"""
DeepDoc 简单测试脚本

测试核心功能不依赖复杂配置。
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试模块导入")
    print("=" * 60)

    modules = [
        "deepdoc.ocr.base",
        "deepdoc.ocr.paddle_ocr",
        "deepdoc.ocr.tesseract_ocr",
        "deepdoc.ocr_selector",
        "deepdoc.vision.layout",
        "deepdoc.vision.tsr",
        "deepdoc.parser.base",
        "deepdoc.parser.pdf_parser",
        "deepdoc.parser.image_parser",
    ]

    for module in modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except Exception as e:
            print(f"  ✗ {module}: {e}")

    print()


def test_ocr_availability():
    """测试 OCR 引擎可用性"""
    print("=" * 60)
    print("测试 OCR 引擎可用性")
    print("=" * 60)

    try:
        from deepdoc.ocr.paddle_ocr import PaddleOCREngine
        from deepdoc.ocr.tesseract_ocr import TesseractOCREngine

        # 测试 PaddleOCR
        print("\nPaddleOCR:")
        try:
            paddle = PaddleOCREngine()
            if paddle.is_available():
                print(f"  ✓ 可用")
            else:
                print(f"  ✗ 不可用（需要安装 paddleocr）")
        except Exception as e:
            print(f"  ✗ 错误: {e}")

        # 测试 Tesseract
        print("\nTesseract:")
        try:
            tesseract = TesseractOCREngine()
            if tesseract.is_available():
                print(f"  ✓ 可用")
            else:
                print(f"  ✗ 不可用（需要安装 tesseract）")
        except Exception as e:
            print(f"  ✗ 错误: {e}")

    except Exception as e:
        print(f"  ✗ 导入失败: {e}")

    print()


def test_table_conversion():
    """测试表格转换功能"""
    print("=" * 60)
    print("测试表格转换功能")
    print("=" * 60)

    try:
        from deepdoc.vision.tsr import TableStructure, TableCell

        # 创建测试表格
        table = TableStructure(
            cells=[
                TableCell(text="姓名", row=0, col=0, is_header=True),
                TableCell(text="年龄", row=0, col=1, is_header=True),
                TableCell(text="张三", row=1, col=0),
                TableCell(text="25", row=1, col=1),
            ],
            num_rows=2,
            num_cols=2
        )

        print("\nMarkdown 格式:")
        print(table.to_markdown())

        print("\n自然语言描述:")
        print(table.to_natural_language())

        print("\n  ✓ 表格转换成功")

    except Exception as e:
        print(f"  ✗ 测试失败: {e}")

    print()


def test_parser_creation():
    """测试解析器创建"""
    print("=" * 60)
    print("测试解析器创建")
    print("=" * 60)

    try:
        from deepdoc.parser.pdf_parser import PDFParser
        from deepdoc.parser.image_parser import ImageParser
        from deepdoc.parser.base import ParsingLevel

        # 创建 PDF 解析器
        print("\nPDF 解析器:")
        pdf_parser = PDFParser(parsing_level=ParsingLevel.STANDARD)
        print(f"  ✓ 已创建，支持格式: {pdf_parser.supported_formats()}")

        # 创建图片解析器
        print("\n图片解析器:")
        img_parser = ImageParser()
        print(f"  ✓ 已创建，支持格式: {img_parser.supported_formats()}")

    except Exception as e:
        print(f"  ✗ 测试失败: {e}")

    print()


def test_vision_availability():
    """测试视觉识别模块可用性"""
    print("=" * 60)
    print("测试视觉识别模块")
    print("=" * 60)

    try:
        from deepdoc.vision.layout import LayoutRecognizer
        from deepdoc.vision.tsr import TableStructureRecognizer

        print("\n布局识别器:")
        layout = LayoutRecognizer()
        if layout.is_available():
            print(f"  ✓ 可用（需要 transformers + torch）")
        else:
            print(f"  ⚠ 基础模式（ML 模型未加载）")

        print("\n表格结构识别器:")
        tsr = TableStructureRecognizer()
        if tsr.is_available():
            print(f"  ✓ 可用（需要 transformers + torch）")
        else:
            print(f"  ⚠ 基础模式（ML 模型未加载）")

    except Exception as e:
        print(f"  ✗ 测试失败: {e}")

    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("DeepDoc 功能测试套件")
    print("=" * 60 + "\n")

    # 运行测试
    test_imports()
    test_ocr_availability()
    test_table_conversion()
    test_parser_creation()
    test_vision_availability()

    print("=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n提示:")
    print("  - 要启用 OCR，安装: pip install paddleocr 或 tesseract")
    print("  - 要启用布局识别，安装: pip install transformers torch")
    print("  - 查看文档: agent/deepdoc/README.md")
    print()


if __name__ == "__main__":
    main()
