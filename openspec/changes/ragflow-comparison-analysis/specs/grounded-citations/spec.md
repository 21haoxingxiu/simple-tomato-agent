## ADDED Requirements

### Requirement: 引用标记和溯源

系统 SHALL 在回答中标记引用来源，并支持溯源到原文位置。

#### Scenario: 引用标记
- **WHEN** Agent 生成回答并使用了检索到的知识时
- **THEN** 系统 SHALL 在回答中标记引用来源
- **AND** 使用上标数字或方括号标注引用编号
- **AND** 关联到具体的 chunk_id

#### Scenario: 引用详情展示
- **WHEN** 用户查看回答时
- **THEN** 系统 SHALL 展示引用详情卡片
- **AND** 显示：来源文档名、页码、原文片段、相关度评分
- **AND** 支持展开查看完整上下文

#### Scenario: 引用位置跳转
- **WHEN** 用户点击引用标记时
- **THEN** 系统 SHALL 跳转到原文位置
- **AND** 高亮显示引用片段
- **AND** 对于 PDF，定位到具体页面和文本框

### Requirement: 置信度评分

系统 SHALL 为每个回答提供置信度评分，标识答案的可靠性。

#### Scenario: 置信度计算
- **WHEN** Agent 生成回答后
- **THEN** 系统 SHALL 计算置信度评分（0-1）
- **AND** 基于以下因素：
  - 检索结果的相关度评分
  - 检索上下文的覆盖度
  - 回答与检索内容的一致性

#### Scenario: 低置信度提示
- **WHEN** 置信度评分 < 0.6 时
- **THEN** 系统 SHALL 显示警告提示
- **AND** 建议"答案可能不准确，请参考原始文档"
- **OR** 标注为"不确定"或"部分确定"

#### Scenario: 无引用答案标记
- **WHEN** 回答未使用任何检索到的知识时
- **THEN** 系统 SHALL 标记为"模型自有知识"
- **AND** 提示可能存在幻觉风险

### Requirement: 幻觉检测

系统 SHALL 检测回答中的潜在幻觉内容并提示用户。

#### Scenario: 事实性检查
- **WHEN** Agent 生成回答后
- **THEN** 系统 SHALL 检查回答中的事实陈述
- **AND** 验证是否在检索上下文中有支持
- **AND** 标记无支持的事实陈述

#### Scenario: 矛盾检测
- **WHEN** 回答内容与检索上下文存在矛盾时
- **THEN** 系统 SHALL 标记矛盾部分
- **AND** 提示用户"可能与原文不符"

### Requirement: 多引用聚合

系统 SHALL 支持从多个来源聚合引用信息。

#### Scenario: 多来源引用
- **WHEN** 回答基于多个检索结果时
- **THEN** 系统 SHALL 聚合所有引用来源
- **AND** 按相关度排序展示
- **AND** 去重相似来源

#### Scenario: 引用冲突提示
- **WHEN** 不同来源的信息存在冲突时
- **THEN** 系统 SHALL 提示用户存在冲突
- **AND** 展示各来源的不同说法
- **AND** 让用户自行判断

### Requirement: 引用可视化

系统 SHALL 提供引用的可视化界面，提升用户体验。

#### Scenario: 引用图谱
- **WHEN** 用户查看回答详情时
- **THEN** 系统 SHALL 显示引用关系图谱
- **AND** 展示问题、回答、引用来源的关系
- **AND** 支持交互式探索

#### Scenario: 文档热力图
- **WHEN** 用户查看知识库文档时
- **THEN** 系统 SHALL 显示引用热力图
- **AND** 高亮被频繁引用的段落
- **AND** 帮助用户识别关键信息

### Requirement: 引用历史追踪

系统 SHALL 追踪引用的使用历史，支持回溯分析。

#### Scenario: 引用统计
- **WHEN** 用户查看文档统计时
- **THEN** 系统 SHALL 显示该文档被引用的次数
- **AND** 显示引用该文档的问答列表

#### Scenario: 引用变更追踪
- **WHEN** 文档内容更新时
- **THEN** 系统 SHALL 标记基于旧版本的引用
- **AND** 提示可能已过时
