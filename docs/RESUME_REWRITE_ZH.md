# Resume Rewrite ZH

## 目标岗位标题

简历标题建议直接收敛到下面之一：

- `AI应用后端工程师`
- `Agent工程师（Python / FastAPI / RAG）`
- `RAG / Agent 后端工程师`

不要再把标题打散成：

- Python 后端
- 大模型应用开发
- 算法工程师

你的卖点应该是“AI 应用后端 + Agent + RAG”，不是泛技术栈。

## 抬头摘要

下面这段可以直接作为简历开头的个人简介：

`聚焦 AI 应用后端与 Agent 工程方向，具备 Python / FastAPI / RAG / 多 Agent 协作项目经验。主导完成一套面向法律知识问答场景的 Agentic Knowledge Platform，覆盖文档解析、知识入库、Embedding 检索、严格引用回答、拒答控制、离线评测、运行审计与服务可观测性，能够将大模型能力封装为可演示、可评测、可服务化交付的后端系统。`

## 技能栈写法

技能栈建议写成下面这版：

### 核心语言与框架

- Python
- FastAPI
- SQLAlchemy 或 SQLite
- Docker

### LLM 应用能力

- RAG
- chunking
- embedding
- vector search
- rerank
- citation grounding
- refusal control
- evals

### Agent 与服务工程

- ReAct
- multi-agent collaboration
- model routing
- retry / rate limiting / circuit breaker / fallback
- API key auth
- structured logging
- metrics / observability

### 可替换基础设施

- OpenAI-compatible API
- Qdrant
- Redis
- Postgres

如果简历版面有限，优先保留前 3 组。

## 主项目写法

项目名称建议统一为：

`Legal Agentic Knowledge Platform`

或中文：

`法律知识问答 Agent 平台`

### 项目简介版

`基于 Python / FastAPI 构建面向法律知识问答场景的 Agentic Knowledge Platform，将原有 Legal RAG 项目与通用 Agent 后端平台合并为统一主项目，覆盖文档解析、知识入库、RAG 检索、严格引用回答、多 Agent 协作、拒答控制、离线评测、运行审计与服务可观测性。`

### 简历项目 bullet 版

- 设计并实现面向法律知识问答场景的 Agentic Knowledge Platform，使用 Python / FastAPI 将文档解析、知识入库、RAG 检索、严格引用回答与多 Agent 工作流整合为统一后端服务。
- 构建结构化切块、Embedding、向量检索、重排与 citation grounding 链路，并通过题型分类、低置信兜底与拒答策略降低法律问答场景下的幻觉风险。
- 实现多模型路由层，支持按任务类型进行模型编排，并提供 rate limiting、retry、circuit breaker 与 fallback 能力，增强服务稳定性与可替换性。
- 实现单 Agent 与团队 Agent 两种执行模式，支持 `react-agent -> review-agent -> narration-agent` 协作链路，并保留运行审计记录用于调试与复盘。
- 增加 API Key 鉴权、结构化日志、Prometheus 风格指标与运行概览接口，补齐服务化与可观测性表达。
- 继承原 Legal RAG 项目的评测资产，导入法律回答评测集与检索黄金集；历史 benchmark 快照显示回答正确率、引用正确率、拒答适当率均为 `100%`，检索任务在 `20` 条样本上的 Vector/Hybrid `Recall@3/5` 达到 `95%`。

## 如果你要压缩成 4 条

- 设计并实现面向法律知识问答场景的 Agentic Knowledge Platform，覆盖文档解析、知识入库、RAG 检索、严格引用回答与多 Agent 后端工作流。
- 构建 citation grounding、题型分类、拒答控制与低置信兜底机制，降低高风险知识问答场景下的幻觉与误判。
- 实现模型路由、rate limiting、retry、circuit breaker、fallback、API Key 鉴权、结构化日志和指标观测，提升服务工程化程度。
- 导入原 Legal RAG 项目的法律评测集与黄金检索集，历史 benchmark 快照显示回答正确率、引用正确率、拒答适当率均为 `100%`，检索 Recall@3/5 达到 `95%`。

## 项目排序建议

项目经历里，这个项目必须放第一。

排序建议：

1. `Legal Agentic Knowledge Platform`
2. 你原先更弱但还能证明能力的项目
3. 竞赛或课程项目

低相关项目不要占太多篇幅。

## 投递不同岗位时的项目名微调

如果岗位偏：

- `AI应用后端`
  用 `法律知识问答 Agent 平台`
- `Agent工程师`
  用 `Legal Agentic Knowledge Platform`
- `RAG工程师`
  用 `法律 RAG 与多 Agent 后端平台`

本质是一个项目，只改标题，不改内容。

## 简历禁忌

- 不要写“做了一个聊天机器人”
- 不要把项目拆成两个零散 demo
- 不要过度强调前端或界面
- 不要把历史 benchmark 说成线上生产指标
- 不要把“会调 API”写成核心卖点
