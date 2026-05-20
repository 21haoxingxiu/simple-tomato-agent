## ADDED Requirements

### Requirement: 查询语言检测

系统 SHALL 能够自动检测用户查询的语言。

#### Scenario: 语言自动识别
- **WHEN** 用户输入查询时
- **THEN** 系统 SHALL 自动检测查询语言
- **AND** 返回语言代码（zh、en、ja 等）
- **AND** 置信度评分

#### Scenario: 多语言混合查询
- **WHEN** 查询包含多种语言时
- **THEN** 系统 SHALL 识别主要语言
- **AND** 提取各语言片段

### Requirement: 查询翻译

系统 SHALL 支持将查询翻译为知识库的主要语言。

#### Scenario: 自动翻译
- **WHEN** 查询语言与知识库主要语言不同时
- **THEN** 系统 SHALL 将查询翻译为知识库主要语言
- **AND** 同时使用原文和翻译进行检索
- **AND** 融合检索结果

#### Scenario: 翻译质量检查
- **WHEN** 完成查询翻译后
- **THEN** 系统 SHALL 评估翻译质量
- **AND** 低质量翻译时提示用户
- **AND** 提供原文查询选项

### Requirement: 多语言向量空间

系统 SHALL 支持多语言向量空间，实现跨语言语义检索。

#### Scenario: 多语言 embedding 模型
- **WHEN** 创建多语言知识库时
- **THEN** 系统 SHALL 使用多语言 embedding 模型
- **AND** 支持 100+ 种语言
- **AND** 保持跨语言语义相似度

#### Scenario: 语言无关检索
- **WHEN** 用户用中文查询英文知识库时
- **THEN** 系统 SHALL 直接在多语言向量空间中检索
- **AND** 返回语义相关的英文 chunks
- **AND** 可选择翻译返回结果

### Requirement: 回答语言适配

系统 SHALL 支持将回答翻译为用户查询的语言。

#### Scenario: 自动回译
- **WHEN** 检索结果语言与查询语言不同时
- **THEN** 系统 SHALL 将检索结果翻译为查询语言
- **AND** 保持引用的原始语言
- **AND** 提供原文参考

#### Scenario: 混合语言回答
- **WHEN** 用户请求保留原文时
- **THEN** 系统 SHALL 生成混合语言回答
- **AND** 引用部分保留原文
- **AND** 解析和总结使用查询语言

### Requirement: 跨语言配置

系统 SHALL 提供灵活的跨语言查询配置选项。

#### Scenario: 语言对配置
- **WHEN** 配置知识库时
- **THEN** 系统 SHALL 支持设置支持的语言列表
- **AND** 设置默认查询语言
- **AND** 启用/禁用自动翻译

#### Scenario: 翻译服务选择
- **WHEN** 配置跨语言功能时
- **THEN** 系统 SHALL 支持多种翻译服务：
  - OpenAI Translation
  - Google Translate API
  - DeepL API
  - 本地翻译模型

### Requirement: 跨语言性能优化

系统 SHALL 优化跨语言查询的性能。

#### Scenario: 翻译缓存
- **WHEN** 相同查询重复出现时
- **THEN** 系统 SHALL 使用缓存的翻译结果
- **AND** 减少翻译 API 调用

#### Scenario: 并行处理
- **WHEN** 执行跨语言检索时
- **THEN** 系统 SHALL 并行执行多语言检索
- **AND** 并行翻译查询
- **AND** 合并结果

#### Scenario: 延迟控制
- **WHEN** 跨语言查询耗时较长时
- **THEN** 系统 SHALL 显示处理进度
- **AND** 提供快速模式（仅单语言检索）
