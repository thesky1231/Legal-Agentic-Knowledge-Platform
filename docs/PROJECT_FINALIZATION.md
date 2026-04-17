# Project Finalization

## 项目最终定位

这个项目现在的最终定位不是“通用 AI Demo”，而是：

`一个面向法律知识问答场景的 Agentic Knowledge Platform`

它同时覆盖了下面几层能力：

- 文档解析与知识入库
- RAG 检索、重排与严格引用回答
- 多模型路由、限流、重试、熔断与 fallback
- 单 Agent 与多 Agent 协作
- 拒答控制、低置信兜底、运行审计与离线评测
- API 服务化、鉴权、结构化日志、指标观测

## 求职时对外怎么定义

优先使用下面这句：

`我做了一套面向法律场景的 Agent 知识库后端平台，覆盖文档入库、RAG 检索、严格引用回答、多 Agent 协作、离线评测、运行审计和服务可观测性。`

不要再把它拆成：

- 一个通用 Agent 项目
- 一个 Legal RAG 项目

统一讲成一个主项目，效果更强。

## 项目价值主张

这个项目的价值不在“功能多”，而在“像真实交付”：

1. 有明确业务场景
法律问答比通用知识问答风险更高，更能说明你理解引用、拒答和幻觉控制的重要性。

2. 有完整技术链路
不是只做了聊天入口，而是覆盖了解析、切块、Embedding、检索、重排、回答、引用、Agent、评测和服务化。

3. 有工程化表达
有限流、熔断、fallback、API Key、运行审计、结构化日志和 Prometheus 风格指标。

4. 有评测与历史指标
合并了原法律项目里的回答级和检索级评测资产，能够证明不是只做了“能跑”的功能。

## 你在面试里应该强调的结果

- 合并后的主项目不再是 Demo 拼盘，而是一个统一的垂直领域案例。
- 历史法律评测快照显示：
  - answer dataset size = `15`
  - answer correct rate = `100%`
  - citation correct rate = `100%`
  - hallucination rate = `0%`
  - refusal appropriate rate = `100%`
- 历史检索评测快照显示：
  - retrieval dataset size = `20`
  - Vector Recall@3 = `95%`
  - Vector Recall@5 = `95%`
  - Hybrid Recall@3 = `95%`
  - Hybrid Recall@5 = `95%`

这些数字要作为“历史 benchmark 快照”去讲，不要说成当前线上 SLA。

## 项目封版后的讲法边界

从现在开始，这个项目对外就按下面的范围讲，不再扩成新的大项目：

- 主场景：法律知识问答 / 法条检索 / 保守拒答
- 主链路：入库 -> 检索 -> 回答 -> 引用 -> 审核 -> 讲解
- 主工程点：服务化、评测、审计、观测、鉴权、fallback

不要主动把重点转移到：

- 前端页面设计
- 花哨的多模态 UI
- 训练或微调大模型
- 与主项目无关的新副项目

## 封版后你手里应该有的交付件

1. 项目源码仓库
2. `README`
3. `docs/LEGAL_CASE_STUDY.md`
4. `docs/PROJECT_FINALIZATION.md`
5. `docs/RESUME_REWRITE_ZH.md`
6. `docs/INTERVIEW_SCRIPT_ZH.md`
7. 一段 2 到 4 分钟 demo 视频

## 投递时一句话版本

`这是我当前最核心的主项目：一个面向法律场景的 Agent 知识库后端平台，重点解决引用溯源、拒答控制、评测和工程化落地问题。`
