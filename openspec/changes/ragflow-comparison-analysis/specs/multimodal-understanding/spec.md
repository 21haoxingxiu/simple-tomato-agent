## ADDED Requirements

### Requirement: 图片内容理解

系统 SHALL 能够理解文档中的图片内容并提取有用信息。

#### Scenario: 图片描述生成
- **WHEN** 文档包含图片时
- **THEN** 系统 SHALL 使用多模态 LLM 分析图片
- **AND** 生成图片的文字描述
- **AND** 将描述作为图片的元数据存储

#### Scenario: 图片文本提取
- **WHEN** 图片中包含文字时
- **THEN** 系统 SHALL 使用 OCR 提取图片中的文字
- **AND** 将文字内容与图片描述合并
- **AND** 支持文字内容的检索

#### Scenario: 图表理解
- **WHEN** 图片为图表（柱状图、折线图、饼图等）时
- **THEN** 系统 SHALL 识别图表类型
- **AND** 提取图表数据和趋势
- **AND** 生成自然语言描述

### Requirement: 多模态文档解析

系统 SHALL 支持解析包含文字、图片、表格等多模态内容的文档。

#### Scenario: 混合内容文档解析
- **WHEN** 解析包含文字和图片的文档时
- **THEN** 系统 SHALL 并行处理文字和图片
- **AND** 保持文字和图片的位置关系
- **AND** 将图片描述嵌入到文档流中

#### Scenario: 多模态检索
- **WHEN** 用户查询涉及图片内容时
- **THEN** 系统 SHALL 检索相关的图片描述
- **AND** 在回答中引用图片
- **AND** 展示图片缩略图

### Requirement: 图片检索

系统 SHALL 支持基于图片的检索能力。

#### Scenario: 图片向量化
- **WHEN** 文档包含图片时
- **THEN** 系统 SHALL 使用图片编码器生成 embedding
- **AND** 存储到向量库
- **AND** 支持基于图片相似度的检索

#### Scenario: 以图搜图
- **WHEN** 用户上传查询图片时
- **THEN** 系统 SHALL 检索相似的图片
- **AND** 返回图片所在的文档和上下文

#### Scenario: 图文混合检索
- **WHEN** 用户查询包含文字和图片时
- **THEN** 系统 SHALL 同时检索相关的文字和图片
- **AND** 融合检索结果
- **AND** 按相关度排序

### Requirement: 多模态模型配置

系统 SHALL 支持配置不同的多模态模型。

#### Scenario: 模型选择
- **WHEN** 配置多模态能力时
- **THEN** 系统 SHALL 支持以下模型选项：
  - OpenAI GPT-4V
  - LLaVA
  - Qwen-VL
  - 自定义模型（通过 API）
- **AND** 允许设置模型优先级

#### Scenario: 模型降级
- **WHEN** 多模态模型不可用时
- **THEN** 系统 SHALL 降级到仅 OCR 提取
- **AND** 记录降级事件

#### Scenario: 成本控制
- **WHEN** 使用付费多模态 API 时
- **THEN** 系统 SHALL 统计 API 调用次数和成本
- **AND** 支持设置调用频率限制

### Requirement: 多模态缓存

系统 SHALL 缓存多模态处理结果以节省成本。

#### Scenario: 图片描述缓存
- **WHEN** 图片被处理过后
- **THEN** 系统 SHALL 缓存图片描述和 embedding
- **AND** 避免重复调用多模态 API
- **AND** 支持缓存过期设置

#### Scenario: 增量处理
- **WHEN** 文档更新时
- **THEN** 系统 SHALL 仅处理新增或修改的图片
- **AND** 复用已缓存的图片处理结果

### Requirement: 隐私保护

系统 SHALL 保护多模态处理中的隐私信息。

#### Scenario: 敏感图片过滤
- **WHEN** 文档包含敏感图片（身份证、护照等）
- **THEN** 系统 SHALL 检测并标记敏感图片
- **AND** 可选择不处理或脱敏处理
- **AND** 不发送到外部 API

#### Scenario: 本地处理选项
- **WHEN** 配置为隐私模式时
- **THEN** 系统 SHALL 使用本地多模态模型
- **AND** 不调用外部 API
- **AND** 确保数据不出域
