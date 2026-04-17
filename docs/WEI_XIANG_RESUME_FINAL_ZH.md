# 魏翔

15972903791 | 1370471602@qq.com | GitHub: github.com/thesky1231

**目标岗位：AI应用后端工程师 / Agent工程师（Python / FastAPI / RAG）**

## 个人简介

软件工程本科，专业排名 1/218（Top 0.5%），具备扎实的工程基础与竞赛训练背景。聚焦 AI 应用后端、Agent 与 RAG 工程方向，主导完成一套面向法律知识问答场景的 Agent 平台，覆盖文档解析、知识入库、严格引用回答、拒答控制、离线评测、服务化部署与可观测性建设，能够将大模型能力封装为可演示、可评测、可服务化交付的后端系统。

## 教育背景

**武汉商学院** | 软件工程（本科） | 2021.09 - 2025.06

专业排名：**1/218（Top 0.5%）** | ICPC 亚洲区域赛（上海）银奖 | CCPC 全国邀请赛（山东）银奖 | 蓝桥杯全国总决赛二等奖

## 项目经历

**法律知识问答 Agent 平台（Legal Agentic Knowledge Platform）** | 核心项目

技术栈：Python / FastAPI / RAG / Agent / Chroma / Qdrant / Docker / Docker Compose / Evaluation

- 面向法律知识问答场景构建统一后端平台，将文档解析、知识入库、RAG 检索、严格引用回答与 Agent 工作流整合为一套可服务化系统，而不是单点聊天 Demo。
- 构建结构化切块、Embedding、向量检索、重排与 citation grounding 链路，支持问题分类、保守拒答和低置信兜底，降低高风险知识问答场景下的幻觉与误判。
- 完成两套检索级评测，Dense Retrieval 在 Recall@3 / Recall@5 上达到 **92.5% - 95%**；同时构建回答级评测框架，从答案正确性、法条引用准确性、幻觉率与拒答合理性等维度输出 JSON / CSV 结果。
- 在当前自建回答级测试集上实现 **100% Answer Correct / Citation Correct / Refusal Appropriate**，**Hallucination 0%**；并将历史法律 benchmark 资产并入当前主项目，用于验证检索与回答质量。
- 实现多模型路由与服务治理能力，支持 retry、rate limiting、circuit breaker 与 fallback；补充 API Key 鉴权、运行审计、结构化日志、`/ops/overview`、`/metrics` 与 Docker / Compose 部署，增强项目的工程化与生产化表达。
- 扩展单 Agent 与多 Agent 协作模式，支持 `react-agent -> review-agent -> narration-agent` 执行链路，使回答过程具备检索、审核与讲解能力。

**基于粒子群算法优化的 BP 神经网络预测模型** | 2023.03 - 2023.08

- 使用 Python、PSO 与 BP 神经网络完成水质预测建模与实验验证，提升模型收敛速度与预测精度，作为建模能力与科研训练的辅助证明。

## 技术能力

- **后端与服务**：Python、FastAPI、REST API、SSE、SQLite、Docker、Docker Compose
- **LLM / RAG**：RAG、Dense Retrieval、rerank、citation grounding、refusal control、检索级评测、回答级评测
- **Agent 与工程化**：ReAct、多 Agent 协作、model routing、retry、rate limiting、circuit breaker、fallback、structured logging、metrics / observability
- **工具与基础设施**：Git、Linux、HuggingFace、Chroma、Qdrant、OpenAI-compatible API、Streamlit

## 成果背书

论文 2 篇（国际期刊 1、EI 会议 1） | 实用新型专利 1 项 | 软件著作权 2 项
