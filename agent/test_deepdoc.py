#!/usr/bin/env python3
"""
DeepDoc 功能测试脚本

测试 OCR、布局识别和文档解析功能。
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_ocr_engines():
    """测试 OCR 引擎可用性"""
    print("=" * 60)
    print("测试 OCR 引擎")
    print("=" * 60)

    from deepdoc.ocr_selector import OCREngineSelector

    # 列出可用引擎
    availability = OCREngineSelector.list_available_engines()
    print(f"\n可用的 OCR 引擎:")
    for engine, available in availability.items():
        status = "✓ 可用" if available else "✗ 不可用"
        print(f"  - {engine}: {status}")

    # 测试引擎选择
    print(f"\n自动选择的引擎:")
    try:
        selector = OCREngineSelector(language="ch")
        engine = selector.get_engine()
        print(f"  ✓ 已选择: {engine}")
    except Exception as e:
        print(f"  ✗ 选择失败: {e}")

    print()


def test_ocr_basic():
    """测试基础 OCR 功能"""
    print("=" * 60)
    print("测试基础 OCR 功能")
    print("=" * 60)

    # 创建测试图片
    print("\n创建测试图片...")
    try:
        from PIL import Image, ImageDraw, ImageFont

        # 创建一个简单的测试图片
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)

        # 添加文字
        text = "Hello World\n你好世界"
        draw.text((50, 50), text, fill='black')

        # 保存测试图片
        test_image_path = "/tmp/test_ocr.png"
        img.save(test_image_path)
        print(f"  ✓ 测试图片已创建: {test_image_path}")

        # 测试 OCR
        from deepdoc.ocr_selector import OCREngineSelector

        selector = OCREngineSelector(language="ch")
        result = selector.recognize_image(test_image_path)

        print(f"\nOCR 结果:")
        print(f"  - 识别到的文本块数量: {len(result.text_blocks)}")
        print(f"  - 平均置信度: {result.average_confidence:.2f}")
        print(f"  - 完整文本:")
        for block in result.text_blocks:
            print(f"    '{block.text}' (置信度: {block.confidence:.2f})")

        # 清理
        os.unlink(test_image_path)

    except ImportError as e:
        print(f"  ✗ 缺少依赖: {e}")
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")

    print()


def test_layout_recognition():
    """测试布局识别"""
    print("=" * 60)
    print("测试布局识别")
    print("=" * 60)

    try:
        from deepdoc.vision.layout import LayoutRecognizer

        recognizer = LayoutRecognizer()

        print(f"\n布局识别器状态:")
        print(f"  - 可用: {recognizer.is_available()}")

        if recognizer.is_available():
            print(f"  ✓ 布局识别模型已加载")
        else:
            print(f"  ⚠ 布局识别模型未加载（需要 transformers）")

    except Exception as e:
        print(f"  ✗ 测试失败: {e}")

    print()


def test_table_structure():
    """测试表格结构识别"""
    print("=" * 60)
    print("测试表格结构识别")
    print("=" * 60)

    try:
        from deepdoc.vision.tsr import TableStructureRecognizer

        recognizer = TableStructureRecognizer()

        print(f"\n表格结构识别器状态:")
        print(f"  - 可用: {recognizer.is_available()}")

        if recognizer.is_available():
            print(f"  ✓ 表格结构识别模型已加载")
        else:
            print(f"  ⚠ 表格结构识别模型未加载（需要 transformers）")

        # 测试表格转换
        from deepdoc.vision.tsr import TableStructure, TableCell

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

        print(f"\n测试表格转换:")
        print(f"\nMarkdown 格式:")
        print(table.to_markdown())

        print(f"\n自然语言描述:")
        print(table.to_natural_language())

    except Exception as e:
        print(f"  ✗ 测试失败: {e}")

    print()


def test_config():
    """测试配置加载"""
    print("=" * 60)
    print("测试配置加载")
    print("=" * 60)

    from deepdoc.config import get_deepdoc_config

    config = get_deepdoc_config()

    print(f"\nDeepDoc 配置:")
    print(f"  - 启用 DeepDoc: {config.enable_deepdoc}")
    print(f"  - 启用 OCR: {config.enable_ocr}")
    print(f"  - 启用布局识别: {config.enable_layout_recognition}")
    print(f"  - 启用表格结构识别: {config.enable_table_structure_recognition}")
    print(f"  - OCR 引擎: {config.ocr_engine}")
    print(f"  - 解析级别: {config.parsing_level}")
    print(f"  - DeepDoc 已启用: {config.is_deepdoc_enabled()}")

    print()


def test_integration():
    """测试集成功能"""
    print("=" * 60)
    print("测试集成功能")
    print("=" * 60)

    try:
        from rag.splitter import parse_file, ParsingLevel

        # 测试标准解析
        print("\n测试标准解析...")
        test_content = b"Hello World\nThis is a test document."
        result = parse_file(
            "test.txt",
            test_content,
            parsing_level=ParsingLevel.STANDARD
        )
        print(f"  ✓ 标准解析成功，文本长度: {len(result)}")

        # 测试增强解析（如果可用）
        if os.getenv("ENABLE_DEEPDOC", "false").lower() == "true":
            print("\n测试增强解析...")
            # 这里可以测试 PDF 或图片
            print(f"  ✓ 增强解析已启用")
        else:
            print("\n增强解析未启用（设置 ENABLE_DEEPDOC=true 以启用）")

    except Exception as e:
        print(f"  ✗ 测试失败: {e}")

    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("DeepDoc 功能测试套件")
    print("=" * 60 + "\n")

    # 运行测试
    test_config()
    test_ocr_engines()

    # 仅在有依赖时运行这些测试
    try:
        test_ocr_basic()
    except Exception:
        pass

    test_layout_recognition()
    test_table_structure()
    test_integration()

    print("=" * 60)
    print("测试完成！")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
