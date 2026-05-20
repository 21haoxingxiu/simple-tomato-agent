## Context

当前 AgentStudio 项目采用基础的文档解析和 RAG 流程：
- 使用 PyMuPDF/pdfplumber 进行 PDF 文本提取
- 采用 RecursiveCharacterTextSplitter 固定切片
- 无 OCR 能力，对扫描件 PDF 无能为力
- 缺少记忆管理，每次会话独立
- 切片策略单一，不适应多样化文档类型

RAGFlow 提供了成熟的 DeepDoc 模块，包含：
- OCR（基于 PaddleOCR 或 Tesseract）
- 布局识别（Layout Recognition）
- 表格结构识别（Table Structure Recognition）
- 模板化切片策略
- Agent 记忆管理

**约束条件：**
- 需要向后兼容现有 API
- 不能强制依赖重型服务（保持可选）
- 需要支持降级模式（API Key 缺失时）
- 内存和计算资源有限

## Goals / Non-Goals

**Goals:**

1. **提升复杂文档解析准确度**
   - 支持 OCR 处理扫描件和图片 PDF
   - 识别文档布局（标题、正文、表格、图片等）
   - 准确解析表格结构并转换为可检索文本

2. **实现智能切片系统**
   - 支持多种文档类型专用切片模板
   - 提供切片预览和人工干预能力
   - 提升检索召回率和准确率

3. **添加 Agent 记忆能力**
   - 支持短期记忆（当前会话上下文）
   - 支持长期记忆（跨会话知识保留）
   - 提供记忆检索和注入机制

4. **增强问答质量**
   - 提供引用可视化
   - 减少模型幻觉
   - 支持跨语言查询

**Non-Goals:**

- 不实现完整的 Agent 工作流编排系统（保持简单）
- 不实现多数据源同步（留作后续独立 feature）
- 不实现 MCP 协议支持（留作后续独立 feature）
- 不实现代码执行沙箱（超出当前范围）

## Decisions

### 决策 1: 文档解析引擎选择

**选择**: 自建轻量级 DeepDoc 模块，借鉴 RAGFlow 架构

**理由**:
- 直接集成 RAGFlow 的 DeepDoc 会引入大量依赖（Elasticsearch、Infinity 等）
- 可以复用其开源模型（布局识别、TSR 模型在 HuggingFace 上可用）
- 保持项目的轻量级特性

**技术栈**:
- OCR: PaddleOCR（中文友好）或 Tesseract（英文优先）
- 布局识别: 使用 HuggingFace 模型 `microsoft/layoutlm-base-uncased` 或类似
- 表格结构识别: 使用 `microsoft/table-transformer-detection` 或类似模型

**架构设计**:

```
agent/deepdoc/
├── __init__.py
├── ocr/
│   ├── __init__.py
│   ├── base.py          # OCR 基类
│   ├── paddle_ocr.py    # PaddleOCR 实现
│   └── tesseract_ocr.py # Tesseract 实现
├── vision/
│   ├── __init__.py
│   ├── layout.py        # 布局识别
│   └── tsr.py           # 表格结构识别
├── parser/
│   ├── __init__.py
│   ├── pdf_parser.py    # PDF 解析器（集成 OCR 和布局识别）
│   ├── docx_parser.py   # DOCX 解析器
│   └── image_parser.py  # 图片解析器
└── models/              # 模型下载和管理
    └── model_manager.py
```

### 决策 2: 切片策略系统设计

**选择**: 插件化切片模板系统

**理由**:
- 不同文档类型需要不同的切片策略
- 插件化设计便于扩展新模板
- 用户可以选择和自定义模板

**切片模板分类**:

1. **通用模板**
   - 递归字符切片（兼容现有逻辑）
   - 语义切片（基于 embedding 相似度）

2. **专用模板**
   - Q&A 模板：识别问答对，按问答单元切片
   - 简历模板：按章节（教育、工作经历等）切片
   - 论文模板：按摘要、方法、结论等章节切片
   - 手册模板：按标题层级和步骤切片
   - 表格模板：保持表格完整性，转换为自然语言

**架构设计**:

```
agent/rag/
├── splitter/
│   ├── __init__.py
│   ├── base.py              # 切片基类
│   ├── recursive.py         # 递归切片（现有）
│   ├── semantic.py          # 语义切片
│   └── templates/           # 专用模板
│       ├── __init__.py
│       ├── qa_template.py
│       ├── resume_template.py
│       ├── paper_template.py
│       └── table_template.py
└── chunk_manager.py         # 切片管理和预览
```

### 决策 3: Agent 记忆系统设计

**选择**: 分层记忆架构（短期 + 长期）

**理由**:
- 短期记忆：当前会话上下文，保持对话连贯性
- 长期记忆：跨会话知识保留，支持个性化
- 参考 LangGraph 的记忆管理最佳实践

**架构设计**:

```
agent/memory/
├── __init__.py
├── base.py              # 记忆基类
├── short_term.py        # 短期记忆（内存 + Redis）
├── long_term.py         # 长期记忆（Postgres + 向量化）
├── memory_manager.py    # 记忆管理器
└── schemas.py           # 记忆数据模型
```

**记忆存储策略**:

1. **短期记忆**
   - 存储：内存（可选 Redis 持久化）
   - TTL：会话结束或 24 小时后过期
   - 内容：最近 N 轮对话、当前上下文

2. **长期记忆**
   - 存储：Postgres + 向量库（Chroma/Milvus）
   - 内容：重要对话片段、用户偏好、知识摘要
   - 检索：基于语义相似度

**记忆注入流程**:

```
用户提问 → 检索长期记忆 → 注入上下文 → 检索知识库 → LLM 回答
                ↓
         更新短期记忆 → 定期归档到长期记忆
```

### 决策 4: 引用溯源增强

**选择**: 可视化引用链 + 置信度评分

**实现方式**:

1. **引用可视化**
   - 在回答中标记引用来源（chunk_id）
   - 前端支持点击跳转到原文位置
   - 高亮显示引用片段

2. **置信度评分**
   - 计算回答与检索上下文的相似度
   - 标注低置信度回答（可能存在幻觉）
   - 提供"不确定"标记

**数据模型扩展**:

```python
class RetrievedChunk(BaseModel):
    id: str
    content: str
    source: str
    page: Optional[int]
    bbox: Optional[Dict]  # 文本框位置
    score: float
    template_type: Optional[str]  # 切片模板类型

class ChatResponse(BaseModel):
    content: str
    chunks: List[RetrievedChunk]
    confidence: float  # 置信度评分
    memory_used: bool  # 是否使用了记忆
```

### 决策 5: 跨语言查询支持

**选择**: 查询翻译 + 多语言向量空间

**实现方式**:

1. **查询翻译**
   - 检测查询语言
   - 翻译为知识库主要语言
   - 同时检索原文和翻译结果

2. **多语言向量空间**
   - 使用多语言 embedding 模型（如 multilingual-e5）
   - 或为不同语言维护独立向量库

### 决策 6: 多模态理解

**选择**: 可选的多模态支持

**实现方式**:

1. **图片理解**
   - 使用多模态 LLM（GPT-4V、LLaVA 等）理解图片内容
   - 提取图片描述和文本
   - 将图片描述作为元数据存储

2. **图片检索**
   - 存储图片 embedding
   - 支持以图搜图
   - 支持图文混合检索

## Risks / Trade-offs

### 风险 1: 性能和资源消耗

**风险**: OCR 和深度学习模型增加内存和计算消耗

**缓解措施**:
- 将 DeepDoc 处理设为可选，默认关闭
- 提供轻量级模式（仅文本提取）和完整模式（OCR + 布局识别）
- 支持异步处理，后台解析大文档
- 模型懒加载，按需加载到内存

### 风险 2: 向后兼容性

**风险**: 新的切片策略可能影响现有知识库

**缓解措施**:
- 保留现有递归切片作为默认选项
- 知识库级别设置切片模板
- 提供迁移工具，支持重新切片

### 风险 3: 记忆隐私问题

**风险**: 长期记忆可能存储敏感信息

**缓解措施**:
- 记忆数据加密存储
- 用户可删除记忆
- 支持记忆过期设置
- 敏感信息过滤

### 风险 4: 复杂度增加

**风险**: 新功能增加系统复杂度和维护成本

**缓解措施**:
- 模块化设计，功能可插拔
- 完善的配置选项，用户可按需启用
- 保持降级模式，核心功能不依赖新模块

## Migration Plan

### 阶段 1: 文档解析增强（Week 1-2）

1. 创建 `deepdoc` 模块骨架
2. 集成 OCR 能力（PaddleOCR）
3. 实现基础布局识别
4. 添加 PDF 解析器升级
5. 更新上传接口，支持解析选项

**回滚策略**:
- 保留原有 PDF 解析逻辑
- 通过环境变量 `ENABLE_DEEPDOC=false` 切换

### 阶段 2: 切片系统重构（Week 3-4）

1. 创建切片模板基类和接口
2. 实现 3 种核心模板（通用、Q&A、表格）
3. 添加切片预览 API
4. 前端增加切片预览界面
5. 更新知识库创建流程

**回滚策略**:
- 现有知识库继续使用递归切片
- 新知识库可选择切片模板

### 阶段 3: 记忆系统集成（Week 5-6）

1. 创建记忆管理模块
2. 实现短期记忆存储
3. 实现长期记忆存储和检索
4. 集成到聊天 Agent
5. 添加记忆管理 API 和前端界面

**回滚策略**:
- 通过 `ENABLE_MEMORY=false` 禁用记忆
- 记忆数据独立存储，可单独清理

### 阶段 4: 引用和可视化增强（Week 7-8）

1. 扩展回答数据模型
2. 实现置信度评分
3. 前端引用可视化
4. 添加引用跳转功能
5. 实现跨语言查询

**回滚策略**:
- 前端降级为简单引用显示
- 后端保持数据结构兼容

## Open Questions

1. **OCR 引擎选择**: PaddleOCR vs Tesseract vs EasyOCR？
   - PaddleOCR: 中文识别好，但依赖较重
   - Tesseract: 轻量，但中文需要额外训练
   - EasyOCR: 平衡，但性能一般
   - **建议**: 默认 PaddleOCR，提供 Tesseract 作为备选

2. **布局识别模型**: 使用预训练模型还是自训练？
   - 预训练模型: 快速集成，但可能不适配特定领域
   - 自训练: 效果好，但需要标注数据和训练成本
   - **建议**: 初期使用预训练，后续可微调

3. **记忆存储选择**: 独立向量库还是复用知识库向量库？
   - 独立: 隔离性好，但增加维护成本
   - 复用: 节省资源，但可能相互影响
   - **建议**: 复用向量库，使用不同的 collection

4. **多模态模型选择**: GPT-4V vs LLaVA vs Qwen-VL？
   - GPT-4V: 效果最好，但成本高
   - LLaVA: 开源，但效果一般
   - Qwen-VL: 中文友好，效果较好
   - **建议**: 支持配置，默认 GPT-4V（如果 API Key 可用）

5. **切片模板优先级**: 哪些模板应该优先实现？
   - 需要根据用户反馈和常见文档类型决定
   - **建议**: 通用、Q&A、表格优先，其他按需添加
