# 企业知识库 Agent 平台交付手册

## 1. 文档解析与清洗

平台统一接收 Markdown、OCR 文本和会议转写，输出章节、段落、表格与公式块。所有解析结果都带 `document_id`、`section`、`source`、`modality` 元数据，方便后续引用溯源与审计。

| 模块 | 输入 | 输出 |
| --- | --- | --- |
| Parser | PDF / OCR / 录音转写 | 标准化元素 |
| Cleaner | 原始文本 | 可检索 chunk |
| Metadata Builder | 元数据与标签 | 可追踪知识单元 |

$$
final_score = 0.65 * vector_score + 0.35 * rerank_score
$$

## 2. RAG 服务设计

切块策略以章节优先，单个 chunk 控制在 450 字以内，并保留 80 字 overlap。检索链路是 `embedding -> vector search -> rerank -> grounded answer`。如果 top1 分数低于阈值，服务会明确返回“证据不足”，避免幻觉输出。

- 检索前对问题做轻量归一化；
- 检索后输出标准 citation；
- 回答阶段强制带引用片段与 section 信息。

## 3. 模型编排

问答优先走主模型；若发生限流、超时或熔断，则 fallback 到备用模型。统一封装 `summary`、`qa`、`speech_script` 三类任务，便于在多模型之间做任务路由。

## 4. Agent 工作流

Agent 的动作包括 `retrieve`、`answer_with_citations`、`voice_narration`。每一步都会记录 `thought`、`action`、`observation`，便于调试、审计和监控。整个链路可以扩展成多 Agent 体系，例如“检索 Agent + 审核 Agent + 讲解 Agent”。

## 5. 语音讲解链路

回答生成后可转成 60 到 90 秒讲解脚本，再调用 TTS 和 A2F 渲染。A2F 接口输出 `avatar_job_id`，方便前端轮询表情与唇形状态，从而把文档问答延伸到数字人讲解场景。

## 6. 工程化要求

服务侧需要重点关注限流、重试、熔断、日志、监控和横向扩展。若上线到 GPU 集群，可以把 OCR、Embedding、Rerank、TTS 拆成独立任务队列，以便做资源隔离和任务调度。
