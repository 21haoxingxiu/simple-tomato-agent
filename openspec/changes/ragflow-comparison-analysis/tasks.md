## 1. DeepDoc 模块基础设施

- [x] 1.1 创建 `agent/deepdoc/` 模块目录结构
- [x] 1.2 实现 OCR 基类和接口定义（`agent/deepdoc/ocr/base.py`）
- [x] 1.3 集成 PaddleOCR 实现（`agent/deepdoc/ocr/paddle_ocr.py`）
- [x] 1.4 集成 Tesseract OCR 实现（`agent/deepdoc/ocr/tesseract_ocr.py`）
- [x] 1.5 实现 OCR 引擎自动选择和降级逻辑
- [x] 1.6 添加 OCR 相关依赖到 `requirements.txt`（pytesseract, paddleocr, opencv-python）

## 2. 布局识别和表格结构识别

- [x] 2.1 创建视觉模块目录（`agent/deepdoc/vision/`）
- [x] 2.2 实现布局识别功能（`agent/deepdoc/vision/layout.py`）
- [x] 2.3 集成 HuggingFace 布局识别模型（layoutlm-base-uncased）
- [x] 2.4 实现表格结构识别功能（`agent/deepdoc/vision/tsr.py`）
- [x] 2.5 集成表格结构识别模型（table-transformer-detection）
- [x] 2.6 实现表格到自然语言的转换逻辑
- [x] 2.7 实现表格自动旋转功能

## 3. 文档解析器升级

- [x] 3.1 创建解析器基类（`agent/deepdoc/parser/base.py`）
- [x] 3.2 实现增强的 PDF 解析器（`agent/deepdoc/parser/pdf_parser.py`）
  - 集成 OCR 和布局识别
  - 支持扫描件 PDF
  - 支持复杂布局
- [x] 3.3 实现图片解析器（`agent/deepdoc/parser/image_parser.py`）
- [x] 3.4 更新现有文档解析流程，集成 DeepDoc
- [x] 3.5 添加解析级别配置（基础/标准/完整）
- [x] 3.6 实现解析结果缓存机制

## 4. 切片模板系统

- [ ] 4.1 创建切片模板基类（`agent/rag/splitter/base.py`）
- [ ] 4.2 重构现有递归切片为模板模式
- [ ] 4.3 实现语义切片模板（`agent/rag/splitter/semantic.py`）
- [ ] 4.4 实现 Q&A 切片模板（`agent/rag/splitter/templates/qa_template.py`）
- [ ] 4.5 实现简历切片模板（`agent/rag/splitter/templates/resume_template.py`）
- [ ] 4.6 实现论文切片模板（`agent/rag/splitter/templates/paper_template.py`）
- [ ] 4.7 实现表格切片模板（`agent/rag/splitter/templates/table_template.py`）
- [ ] 4.8 创建切片模板管理器（`agent/rag/chunk_manager.py`）
- [ ] 4.9 实现切片质量评估和推荐功能

## 5. 切片预览和干预界面

- [ ] 5.1 添加切片预览 API 端点（`/api/knowledge/bases/{id}/preview-chunks`）
- [ ] 5.2 实现切片预览数据结构（包含 chunk 内容、边界、元数据）
- [ ] 5.3 实现手动合并/拆分切片的 API
- [ ] 5.4 创建前端切片预览组件（`frontend/src/components/ChunkPreview.tsx`）
- [ ] 5.5 实现可视化切片编辑器（支持拖拽、合并、拆分）
- [ ] 5.6 集成到知识库创建流程

## 6. Agent 记忆系统

- [ ] 6.1 创建记忆模块目录（`agent/memory/`）
- [ ] 6.2 定义记忆数据模型（`agent/memory/schemas.py`）
- [ ] 6.3 实现短期记忆管理器（`agent/memory/short_term.py`）
  - 内存存储
  - 可选 Redis 持久化
  - TTL 过期机制
- [ ] 6.4 实现长期记忆管理器（`agent/memory/long_term.py`）
  - Postgres 存储
  - 向量化存储
  - 记忆检索
- [ ] 6.5 实现记忆管理器（`agent/memory/memory_manager.py`）
  - 记忆注入策略
  - 记忆去重
  - 记忆归档
- [ ] 6.6 实现记忆隐私保护（加密、脱敏、访问控制）
- [ ] 6.7 添加记忆管理 API（`agent/routers/memory.py`）
  - 记忆列表查询
  - 记忆删除
  - 记忆导出

## 7. 记忆集成到聊天 Agent

- [ ] 7.1 更新聊天 Agent 集成记忆管理器
- [ ] 7.2 实现记忆注入到 LangGraph 流程
- [ ] 7.3 更新对话数据模型，添加记忆使用标记
- [ ] 7.4 实现对话结束后的记忆归档逻辑
- [ ] 7.5 添加记忆统计和分析功能
- [ ] 7.6 创建前端记忆管理界面

## 8. 引用溯源和置信度评分

- [ ] 8.1 扩展 `RetrievedChunk` 数据模型，添加位置信息和置信度
- [ ] 8.2 实现 chunk 位置信息提取（PDF 页码、文本框坐标）
- [ ] 8.3 实现回答置信度评分算法
- [ ] 8.4 添加幻觉检测逻辑
- [ ] 8.5 更新 `ChatResponse` 数据模型，添加置信度和引用详情
- [ ] 8.6 实现引用标记生成（上标数字、方括号）

## 9. 引用可视化前端

- [ ] 9.1 创建引用详情卡片组件（`frontend/src/components/CitationCard.tsx`）
- [ ] 9.2 实现引用位置跳转功能（定位到原文）
- [ ] 9.3 创建置信度指示器组件
- [ ] 9.4 实现低置信度警告提示
- [ ] 9.5 创建引用图谱可视化组件
- [ ] 9.6 集成到聊天界面

## 10. 跨语言查询支持

- [ ] 10.1 集成语言检测库（langdetect 或 fasttext）
- [ ] 10.2 实现查询翻译服务接口
- [ ] 10.3 集成翻译 API（OpenAI Translation / Google Translate / DeepL）
- [ ] 10.4 实现多语言 embedding 模型支持（multilingual-e5）
- [ ] 10.5 更新检索流程支持跨语言查询
- [ ] 10.6 实现翻译缓存机制
- [ ] 10.7 添加跨语言查询配置界面

## 11. 多模态理解支持

- [ ] 11.1 创建多模态处理模块（`agent/multimodal/`）
- [ ] 11.2 集成图片编码器（CLIP 或类似）
- [ ] 11.3 实现图片描述生成功能
- [ ] 11.4 实现图片 OCR 提取（复用 DeepDoc OCR）
- [ ] 11.5 更新文档解析流程，支持图片处理
- [ ] 11.6 实现图片 embedding 存储和检索
- [ ] 11.7 添加多模态模型配置选项
- [ ] 11.8 实现图片处理缓存

## 12. 测试和文档

- [ ] 12.1 为 DeepDoc 模块编写单元测试
- [ ] 12.2 为切片模板编写单元测试
- [ ] 12.3 为记忆系统编写单元测试
- [ ] 12.4 为引用溯源编写单元测试
- [ ] 12.5 编写集成测试
- [ ] 12.6 更新 API 文档（OpenAPI）
- [ ] 12.7 更新 README.md，添加新功能说明
- [ ] 12.8 编写迁移指南（如何升级现有知识库）
- [ ] 12.9 编写性能基准测试和优化

## 13. 部署和配置

- [ ] 13.1 更新 Docker Compose 配置，添加可选依赖
- [ ] 13.2 添加环境变量配置示例（`.env.example`）
- [ ] 13.3 实现功能开关（通过环境变量启用/禁用）
- [ ] 13.4 更新系统要求文档（内存、磁盘建议）
- [ ] 13.5 编写部署指南
- [ ] 13.6 性能测试和资源优化

## 14. 用户反馈和迭代

- [ ] 14.1 收集用户对新切片模板的反馈
- [ ] 14.2 优化 OCR 准确率
- [ ] 14.3 优化记忆检索效果
- [ ] 14.4 优化置信度评分算法
- [ ] 14.5 根据反馈调整切片模板参数
