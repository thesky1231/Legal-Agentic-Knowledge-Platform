# 项目拆解与讲解手册

这份文档的目标不是再介绍一遍 README，而是帮你真正把项目讲顺、讲稳、讲得像自己做出来的一样。

## 一句话先讲清楚

这个项目是一套面向法律知识问答场景的 `Agentic Knowledge Platform`。  
它把文档解析、知识入库、RAG 检索、严格引用回答、拒答控制、多 Agent 协作、运行审计和可观测性做成了一套 Python/FastAPI 后端。

如果你只能先背一句话，就背这句。

## 这个项目解决什么问题

法律和企业文档类问答有几个天然难点：

- 文档长，结构复杂，不能只按纯文本胡乱切块。
- 用户对答案的可信度要求高，最好能给出依据和引用。
- 不是什么问题都应该强答，证据不足时要保守拒答。
- 如果要对外提供服务，还要考虑模型路由、稳定性、监控和审计。

这个项目就是围绕这几件事搭起来的。

## 你可以把系统分成 5 层来理解

### 1. 文档理解层

负责把输入文档变成后面能检索和回答的结构化内容。

- `services/parsing.py`
- `services/chunking.py`

你讲的时候可以说：

“我不是把整篇文档直接扔进向量库，而是先做结构化解析，保留章节、来源和模态信息，再做按结构优先的切块。”

### 2. 检索与回答层

负责把问题变成 grounded answer，而不是普通生成。

- `services/embeddings.py`
- `services/vector_store.py`
- `services/rag.py`
- `services/knowledge_base.py`
- `services/query_policy.py`

这一层最重要的逻辑是：

- 先检索
- 再重排
- 再根据证据组织回答
- 如果证据弱，就降级或拒答

你讲的时候可以说：

“我做的是 citation-driven RAG，不是让模型凭记忆自由发挥。回答前必须先拿证据，证据不足时会触发保守策略。”

### 3. 模型编排层

负责让不同任务走不同模型能力，同时控制稳定性。

- `services/model_router.py`
- `core/resilience.py`

你讲的时候可以说：

“总结、问答、讲解脚本这几类任务我没有混在一起，而是通过路由层统一封装，并在这里做限流、重试、熔断和 fallback。”

### 4. Agent 执行层

负责把检索、回答、审核、讲解串成步骤化流程。

- `agents/react.py`
- `agents/single.py`
- `agents/team.py`
- `workflows/tutor.py`

这里的关键区别是：

- `single agent` 适合快速演示
- `team agent` 更像真实业务质量链路

团队模式的链路是：

```text
react-agent -> review-agent -> narration-agent
```

你讲的时候可以说：

“我不是只做了一个 agent 壳子，而是把检索、审核、讲解拆成不同角色，让 reviewer 负责检查 grounded 和 citation 质量。”

### 5. 服务与运维层

负责把整个系统变成对外可用的服务，而不只是本地脚本。

- `main.py`
- `container.py`
- `services/run_store.py`
- `services/observability.py`
- `core/logging.py`

这层对应的能力是：

- FastAPI 服务入口
- 依赖装配
- 运行审计
- `/health`
- `/ops/overview`
- `/metrics`

你讲的时候可以说：

“这个项目不是只停在 notebook 或 CLI，而是对外暴露成了服务，并且补了审计记录、指标和运维接口。”

## 一次请求在系统里怎么走

这是你最该吃透的一部分。

### 文档入库

```text
document -> parser -> structured elements -> chunker -> embeddings -> vector store
```

你要理解的是：

- parser 负责保留结构
- chunker 负责让检索粒度合理
- embedding 把 chunk 变成向量
- vector store 负责后续召回

### RAG 问答

```text
query -> query policy -> retrieve -> rerank -> grounded answer -> citations
```

这里最值钱的是 `query policy`：

- 判断题型
- 给出置信方向
- 决定是否该拒答

### Single Agent

```text
retrieve -> answer with citations -> voice narration -> run audit
```

### Team Agent

```text
react-agent -> review-agent -> narration-agent -> run audit
```

你面试时如果被问“多 Agent 和单 Agent 的区别”，可以回答：

“单 Agent 更轻量，适合直接完成 retrieval + answer；团队 Agent 则在回答和交付之间多了一层 reviewer，用来做 grounded 和 citation 质量兜底。”

## 项目里最该记住的模块职责

### `main.py`

API 入口。  
负责暴露路由、中间件、鉴权和 observability 接口。

### `container.py`

依赖装配中心。  
负责把 parser、vector store、router、agent、run store 等对象接起来。

### `types.py`

统一数据模型。  
这是整个项目的“协议层”，很多对象之间就是靠这些 dataclass / 类型定义在传数据。

### `services/knowledge_base.py`

知识库回答核心。  
这是“检索出来之后怎么组织 grounded answer”的关键位置。

### `services/query_policy.py`

法律场景差异化的重点。  
这里决定问题类型、置信方向和是否该保守拒答。

### `agents/team.py`

多 Agent 协作入口。  
它让这个项目不只是一个普通 RAG 服务，而是更接近 agent workflow。

### `services/observability.py`

生产感的重要来源。  
它负责让你不仅能回答问题，还能看到请求数量、延迟、pipeline 指标。

## 指标这块你必须讲准确

你仓库里的这些数字可以讲，但一定要讲法准确：

- `Recall@3 / Recall@5 = 92.5% - 95%`
- `Answer Correct = 100%`
- `Citation Correct = 100%`
- `Refusal Appropriate = 100%`
- `Hallucination = 0%`

准确讲法是：

“这些是从原法律 RAG 项目导入的离线 benchmark snapshot，用于说明这个系统在法律场景下的评测方向和已有结果，不是线上生产流量指标。”

不要讲成：

- 在线服务真实用户指标
- 长期稳定线上数据
- 大规模生产 SLA

## 面试时怎么讲

### 30 秒版本

“我做了一套法律知识问答 Agent 平台，核心是把结构化文档解析、RAG 检索、严格引用回答、保守拒答和多 Agent 协作做成了 FastAPI 后端，同时补了评测、运行审计和可观测性，不是单纯的聊天 demo。”

### 2 分钟版本

“这个项目的业务场景是法律知识问答。前面先做文档解析和结构化切块，把文本、OCR、转写统一入库；中间是 grounded RAG 链路，包括 embedding、向量检索、重排和 citation-driven answer；为了降低幻觉，我额外做了 query policy，对问题分类、低置信场景和拒答进行控制。后面我又把它做成 agent workflow，既支持 single agent，也支持 react-agent、review-agent、narration-agent 的 team agent，并且通过 FastAPI 暴露成服务，补了 run audit、metrics 和 ops overview。整个项目我想表达的是，不只是会调大模型 API，而是能把它做成一个有评测、有稳定性设计、有服务接口的后端系统。”

### 5 分钟版本

按这个顺序讲最稳：

1. 业务场景：为什么选法律知识问答
2. 文档理解：为什么不能粗暴切块
3. RAG 主链路：retrieve、rerank、citation
4. 安全控制：refusal、confidence、policy
5. Agent：single vs team
6. 服务化：FastAPI、审计、metrics、ops
7. 评测：历史 benchmark snapshot

## 高频追问怎么答

### 问：为什么要做 refusal control？

答：

“法律场景对错误答案的容忍度低，所以我不希望模型在证据不足时也强答。这个项目里会根据检索证据和问题类型决定是正常回答、降级回答还是直接拒答。”

### 问：为什么还要 reviewer agent？

答：

“单 Agent 可以完成任务，但 reviewer agent 让质量控制更显式。它可以在交付前检查 grounded 状态和 citation 数量，这样更接近实际业务里的审核链路。”

### 问：这个项目和普通 LangChain demo 有什么不同？

答：

“我不是用一个通用链路直接拼起来，而是把 parser、knowledge base、router、agent、run store、observability 分成了明确的后端组件，还补了 refusal、评测和审计，所以它更像服务系统，而不是工具调用演示。”

### 问：如果真的上线，你下一步会补什么？

答：

“我会优先补真实 OCR/ASR、持久化数据库、鉴权/RBAC、任务队列、Tracing、以及更完整的线上评测和告警，而不是先堆更多模型能力。”

## 你应该怎么现场演示

最稳的演示链路就是：

1. 打开 GitHub README，先讲业务定位和能力面
2. 运行 `python scripts/demo_showcase.py`
3. 指着输出讲 4 个点：
   - chunk 入库
   - citations
   - reviewer summary
   - ops / runs
4. 最后再讲一句 “这个系统已经被做成了 FastAPI 服务和可观测后端”

## 你自己复习项目时的阅读顺序

建议你按下面顺序读代码：

1. `README.md`
2. `src/agentic_knowledge_platform/main.py`
3. `src/agentic_knowledge_platform/container.py`
4. `src/agentic_knowledge_platform/services/knowledge_base.py`
5. `src/agentic_knowledge_platform/services/query_policy.py`
6. `src/agentic_knowledge_platform/agents/single.py`
7. `src/agentic_knowledge_platform/agents/team.py`
8. `src/agentic_knowledge_platform/services/observability.py`
9. `tests/`

这样你会先抓到入口，再抓主链路，再抓差异化亮点。

## 最后记住一句话

你不是在讲“我做了一个大模型项目”，而是在讲：

“我把法律场景下的 RAG、拒答控制、Agent 协作、评测和服务化做成了一套后端系统。”
