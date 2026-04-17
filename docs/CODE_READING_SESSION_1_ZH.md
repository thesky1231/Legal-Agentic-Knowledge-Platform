# 第一节读码：从入口到核心问答链路

这份文档是你真正开始“吃透项目”的第一节。

目标只有一个：

把下面这条 runtime 主线讲顺。

```text
FastAPI entry -> container wiring -> knowledge base answer -> agent flow -> metrics / audit
```

## 先记住真实运行路径

如果面试官问你“这个系统真正跑起来时从哪开始”，你先按这条路径回答：

1. [`main.py#create_app`](../src/agentic_knowledge_platform/main.py#L23-L307)
2. [`container.py#build_container`](../src/agentic_knowledge_platform/container.py#L46-L113)
3. [`knowledge_base.py#answer`](../src/agentic_knowledge_platform/services/knowledge_base.py#L132-L205)
4. [`agents/single.py#ReActAgent.run`](../src/agentic_knowledge_platform/agents/single.py#L6-L63)
5. [`agents/team.py#CollaborativeTeamAgent.run`](../src/agentic_knowledge_platform/agents/team.py#L17-L68)
6. [`observability.py#MetricsCollector`](../src/agentic_knowledge_platform/services/observability.py#L13-L261)

这就是第一节你最该掌握的部分。

## 一个很容易绕晕你的点

仓库里有一个 [`agents/react.py`](../src/agentic_knowledge_platform/agents/react.py#L1-L52)，里面也有 `ReActAgent`。

但真正被 runtime 接线使用的是：

- [`container.py`](../src/agentic_knowledge_platform/container.py#L5-L6)
- [`agents/__init__.py`](../src/agentic_knowledge_platform/agents/__init__.py#L1-L6)
- [`agents/single.py`](../src/agentic_knowledge_platform/agents/single.py#L6-L63)

所以你现在复习时，先把 `single.py` 当成真实实现来理解，`react.py` 可以当作较早版本或备用实现，不要把注意力放散。

## 第一步：服务入口在做什么

看 [`create_app`](../src/agentic_knowledge_platform/main.py#L23-L307)。

这个函数的职责可以概括成三句话：

1. 拿到容器，把所有服务对象接入 FastAPI。
2. 注册中间件、鉴权和观测逻辑。
3. 把知识库、Agent、评测、运行记录能力暴露成 HTTP API。

你讲的时候可以直接说：

“`main.py` 不是业务实现本身，而是系统入口。它负责把 container 里的能力挂到 FastAPI 上，并统一处理 API Key、请求指标和 pipeline 指标。”

### 这里最该看哪几段

- 应用创建和容器装配：[`main.py#L23-L33`](../src/agentic_knowledge_platform/main.py#L23-L33)
- HTTP metrics 中间件：[`main.py#L34-L64`](../src/agentic_knowledge_platform/main.py#L34-L64)
- API Key 校验：[`main.py#L65-L70`](../src/agentic_knowledge_platform/main.py#L65-L70)
- pipeline 指标记录：[`main.py#L71-L97`](../src/agentic_knowledge_platform/main.py#L71-L97)
- 核心业务接口：[`main.py#L134-L305`](../src/agentic_knowledge_platform/main.py#L134-L305)

## 第二步：container 真正把什么接起来了

看 [`build_container`](../src/agentic_knowledge_platform/container.py#L46-L113)。

这一步是你讲“工程化”的关键，因为它说明这个项目不是一坨耦合代码，而是分模块接起来的系统。

在这个函数里，系统按顺序被装起来：

1. `parser`
2. `chunker`
3. `embeddings`
4. `vector_store`
5. `model_router`
6. `knowledge_base`
7. `voice_pipeline`
8. `agent`
9. `team_agent`
10. `run_store`
11. `metrics`
12. `evaluation_service`
13. `workflow`

你讲的时候可以说：

“我用 container 做依赖装配，这样 parser、vector store、model router、knowledge base、agent、run store 都是独立组件，离线模式和真实服务模式都可以通过配置切换。”

### 这里最值钱的三个点

#### 1. 模型和 Embedding 都是可替换的

- Embedding 选择逻辑：[`container.py#L116-L127`](../src/agentic_knowledge_platform/container.py#L116-L127)
- 模型客户端选择逻辑：[`container.py#L142-L167`](../src/agentic_knowledge_platform/container.py#L142-L167)

这说明项目不是写死单一 provider。

#### 2. 向量库是可替换的

- [`container.py#L130-L139`](../src/agentic_knowledge_platform/container.py#L130-L139)

默认是内存模式，也可以切到 Qdrant。

#### 3. Run store 也是可替换的

- [`container.py#L170-L173`](../src/agentic_knowledge_platform/container.py#L170-L173)

这就是你讲“审计”和“生产感”的抓手之一。

## 第三步：真正的问答核心在 `knowledge_base.answer`

看 [`knowledge_base.py#answer`](../src/agentic_knowledge_platform/services/knowledge_base.py#L132-L205)。

这是整套系统最关键的函数之一。

你可以把它拆成 5 个动作：

1. 先分类问题
2. 再决定 `top_k`
3. 然后检索并生成 citations
4. 再判断 grounded / low confidence / refusal
5. 最后才调用模型生成回答

### 代码顺序怎么理解

#### 1. 问题分类

- [`knowledge_base.py#L138-L140`](../src/agentic_knowledge_platform/services/knowledge_base.py#L138-L140)

这里会先调用 `question_policy.classify(question)`。

这一步很重要，因为它决定了这个问题后面走的是普通回答、定义类回答、混淆类回答、复杂推理，还是应该保守拒答。

#### 2. 检索和 citation 组装

- 检索：[`knowledge_base.py#L140`](../src/agentic_knowledge_platform/services/knowledge_base.py#L140)
- citation 组装：[`knowledge_base.py#L141-L151`](../src/agentic_knowledge_platform/services/knowledge_base.py#L141-L151)

你讲的时候要强调：

“这个项目不是模型直接生成答案，而是先把 evidence 命中结果显式转成 citations，再附着到 answer 上。”

#### 3. grounded 判断

- [`knowledge_base.py#L152-L157`](../src/agentic_knowledge_platform/services/knowledge_base.py#L152-L157)

这里的 grounded 判断本质上是：

- 有命中
- 且 top hit 分数超过阈值

这就是系统为什么能区分“有证据支撑”与“证据不足”。

#### 4. refusal 和 low-confidence 分支

- policy refusal：[`knowledge_base.py#L158-L168`](../src/agentic_knowledge_platform/services/knowledge_base.py#L158-L168)
- insufficient evidence：[`knowledge_base.py#L169-L179`](../src/agentic_knowledge_platform/services/knowledge_base.py#L169-L179)

这是你面试时最能拉开差距的一段。

因为很多 demo 到这里都是“没查到也强答”，而你这里有显式降级策略。

#### 5. 真正调用模型回答

- [`knowledge_base.py#L181-L205`](../src/agentic_knowledge_platform/services/knowledge_base.py#L181-L205)

这里先把 hit 变成 `context_blocks`，再通过 `model_router.generate(...)` 去生成回答。

你讲的时候可以说：

“模型在这里不是起点，而是后处理层。它只能基于已检索证据组织 grounded answer。”

## 第四步：为什么 `query_policy` 是法律场景差异化重点

看 [`query_policy.py`](../src/agentic_knowledge_platform/services/query_policy.py#L8-L123)。

这个服务做了三件事：

1. `classify`
2. `top_k_for`
3. `is_low_confidence`

### 它为什么值钱

因为法律场景不是“只要检索到就回答”。

这里的策略把问题区分成：

- `direct_answer`
- `definition`
- `confusing`
- `complex_reasoning`
- `should_refuse`

你要特别记住这两个点：

- 遇到“能不能直接认定”“一定会判几年”这类问题，会进入 `should_refuse`
- 问题越复杂，对证据长度和充分性的要求越高

这就是为什么这个项目比普通通用问答更像一个法律场景系统。

## 第五步：Single Agent 到底做了什么

看 [`agents/single.py#ReActAgent.run`](../src/agentic_knowledge_platform/agents/single.py#L11-L63)。

这条链路很干净：

```text
retrieve -> answer_with_citations -> optional voice_narration
```

### 每一步对应什么含义

- 第一步：检索证据块
- 第二步：形成 grounded answer，并把 grounded / citations / question_type / confidence / refusal 都写进 step observation
- 第三步：如果用户要求语音且答案 grounded，才触发 voice pipeline

你讲的时候可以说：

“single agent 的重点不在复杂协作，而在把 retrieval、grounded answer、voice narration 串成可观察的步骤执行链。”

## 第六步：Team Agent 为什么更像真实业务

看 [`agents/team.py#CollaborativeTeamAgent.run`](../src/agentic_knowledge_platform/agents/team.py#L23-L68)。

它的核心是：

1. 先调用 single agent 拿到基础回答
2. 再由 `review-agent` 做质量审核
3. 最后在需要时再做 narration

真正的 reviewer 判断逻辑在：

- [`team.py#L6-L15`](../src/agentic_knowledge_platform/agents/team.py#L6-L15)

这个 reviewer 会检查：

- grounded 是否通过
- 是否带 citation
- citation 数量够不够

你可以这样讲：

“team agent 的价值不只是多一个 agent 名字，而是把质量检查显式拆成 reviewer 角色，让 grounded 和 citation sufficiency 变成可审计的中间环节。”

## 第七步：可观测性不是装饰，是入口层真实记录的

看 [`observability.py#MetricsCollector`](../src/agentic_knowledge_platform/services/observability.py#L13-L261)。

这里面你最需要理解两类指标：

### HTTP 指标

- `record_http(...)`：[`observability.py#L30-L59`](../src/agentic_knowledge_platform/services/observability.py#L30-L59)

记录：

- method
- path
- status_code
- latency
- recent requests

### pipeline 指标

- `record_pipeline_run(...)`：[`observability.py#L60-L80`](../src/agentic_knowledge_platform/services/observability.py#L60-L80)

记录：

- workflow
- mode
- grounded
- citation_count
- latency
- voice_enabled

这就是为什么 `/ops/overview` 和 `/metrics` 能给出真正像服务系统一样的观测结果。

## 第八步：类型模型帮你理解系统“在传什么”

看 [`types.py`](../src/agentic_knowledge_platform/types.py#L17-L223)。

你最该记住的是这些对象：

- `DocumentIngestRequest`
- `ChunkRecord`
- `Citation`
- `AnswerResult`
- `AgentRequest`
- `AgentResponse`
- `RunRecord`
- `EvalRun`

你可以把它理解成：

“这些 dataclass 就是系统内部的协议层。模块之间不是乱传 dict，而是按统一数据结构在传。”

## 第九步：你现在应该能讲的 3 条请求链路

### 1. `/rag/query`

入口：

- [`main.py#L150-L172`](../src/agentic_knowledge_platform/main.py#L150-L172)

链路：

```text
HTTP request -> knowledge_base.answer -> AnswerResult -> record_pipeline
```

### 2. `/agent/run`

入口：

- [`main.py#L174-L201`](../src/agentic_knowledge_platform/main.py#L174-L201)

链路：

```text
HTTP request -> AgentRequest -> single agent -> run_store.save -> record_pipeline
```

### 3. `/agent/team/run`

入口：

- [`main.py#L203-L230`](../src/agentic_knowledge_platform/main.py#L203-L230)

链路：

```text
HTTP request -> AgentRequest -> team agent -> run_store.save -> record_pipeline
```

如果面试官问你“那 workflow demo 呢”，你就补一句：

“`/workflow/demo` 会把入库和问答串成一次端到端流程，适合演示 document -> ingest -> agent response 这条完整链路。”

对应代码：

- [`main.py#L255-L287`](../src/agentic_knowledge_platform/main.py#L255-L287)

## 第十步：这一节你要背下来的说法

### 最短版本

“系统从 `main.py` 的 FastAPI 入口进来，通过 `container.py` 装配 parser、vector store、model router、knowledge base 和 agent。真正的回答核心在 `knowledge_base.answer`，先做 query policy、retrieve、rerank、citation 和 grounded 判断，再决定是保守拒答还是调用模型生成 grounded answer。single agent 会把这条链路步骤化，team agent 再在上面加 reviewer 和 narration，最后所有运行会进入 audit 和 metrics。”

### 如果你只能记 5 个代码点

1. [`main.py#create_app`](../src/agentic_knowledge_platform/main.py#L23-L307)
2. [`container.py#build_container`](../src/agentic_knowledge_platform/container.py#L46-L113)
3. [`knowledge_base.py#answer`](../src/agentic_knowledge_platform/services/knowledge_base.py#L132-L205)
4. [`query_policy.py`](../src/agentic_knowledge_platform/services/query_policy.py#L8-L123)
5. [`agents/team.py#CollaborativeTeamAgent.run`](../src/agentic_knowledge_platform/agents/team.py#L23-L68)

## 这节结束后你要做什么

先不要继续乱翻代码。

你应该按这个顺序自己再看一遍：

1. `main.py`
2. `container.py`
3. `knowledge_base.py`
4. `query_policy.py`
5. `agents/single.py`
6. `agents/team.py`
7. `observability.py`

如果你愿意，下一节我会继续带你读：

- 文档入库链路
- rerank 和 grounded score 是怎么来的
- model router 的 retry / circuit breaker / fallback 是怎么跑的
