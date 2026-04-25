import { useEffect, useState } from "react";

const SearchIcon = () => (
  <svg className="w-5 h-5 text-stone-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
  </svg>
);

const ShieldIcon = () => (
  <svg className="w-4 h-4 mr-1 text-emerald-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>
  </svg>
);

const DocumentIcon = () => (
  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
  </svg>
);

const apiBase = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "";

function endpoint(path) {
  return `${apiBase}${path}`;
}

function confidenceMeta(confidence) {
  if (typeof confidence === "number") {
    if (confidence >= 0.8) return { label: "高", value: confidence, color: "bg-emerald-700" };
    if (confidence >= 0.5) return { label: "中", value: confidence, color: "bg-amber-500" };
    return { label: "低", value: confidence, color: "bg-red-500" };
  }
  if (confidence === "high") return { label: "高", value: 0.9, color: "bg-emerald-700" };
  if (confidence === "medium") return { label: "中", value: 0.65, color: "bg-amber-500" };
  if (confidence === "low") return { label: "低", value: 0.35, color: "bg-red-500" };
  return { label: "待生成", value: 0, color: "bg-stone-200" };
}

function renderMultiline(text) {
  return text.split("\n").map((line, index) => (
    <p key={index} className={index === 0 ? "" : "mt-2"}>
      {line}
    </p>
  ));
}

async function readNdjsonStream(response, onEvent) {
  if (!response.body) {
    throw new Error("浏览器当前不支持流式读取。");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    let boundary = buffer.indexOf("\n");
    while (boundary >= 0) {
      const line = buffer.slice(0, boundary).trim();
      buffer = buffer.slice(boundary + 1);
      if (line) {
        onEvent(JSON.parse(line));
      }
      boundary = buffer.indexOf("\n");
    }
    if (done) {
      break;
    }
  }

  const tail = buffer.trim();
  if (tail) {
    onEvent(JSON.parse(tail));
  }
}

export default function LegalAssistant() {
  const [systemState, setSystemState] = useState({ status: "initializing", message: "正在初始化知识库..." });
  const [mode, setMode] = useState("auto");
  const [query, setQuery] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState(null);
  const [expandedSteps, setExpandedSteps] = useState(false);

  const sampleQuestions = ["抢劫与抢夺的区别", "证据不足时如何保守回答", "多 Agent 如何做审核"];

  useEffect(() => {
    let cancelled = false;
    let timer = null;

    const pollBootstrap = async () => {
      try {
        const res = await fetch(endpoint("/showcase/bootstrap"), { method: "POST" });
        const data = await res.json();
        if (cancelled) return;
        if (data.ready) {
          setSystemState({ status: "ready", message: "" });
          return;
        }
        if (data.status === "failed") {
          setSystemState({ status: "error", message: data.error || "知识库初始化失败，请稍后重试。" });
          return;
        }
        setSystemState({
          status: "initializing",
          message: `知识库准备中：已导入 ${data.document_count ?? 0} 份文档，已建立 ${data.vector_count ?? 0} 条向量。`,
        });
        timer = window.setTimeout(pollBootstrap, 2000);
      } catch (_err) {
        if (!cancelled) {
          setSystemState({ status: "error", message: "暂时无法连接后端服务，请稍后重试。" });
        }
      }
    };

    const bootstrapSystem = async () => {
      try {
        const res = await fetch(endpoint("/showcase/bootstrap"), { method: "POST" });
        const data = await res.json();
        if (!res.ok) {
          setSystemState({ status: "error", message: "知识库初始化失败，请刷新重试。" });
          return;
        }
        if (data.ready) {
          setSystemState({ status: "ready", message: "" });
          return;
        }
        if (data.status === "failed") {
          setSystemState({ status: "error", message: data.error || "知识库初始化失败，请稍后重试。" });
          return;
        }
        setSystemState({
          status: "initializing",
          message: `知识库准备中：已导入 ${data.document_count ?? 0} 份文档，已建立 ${data.vector_count ?? 0} 条向量。`,
        });
        timer = window.setTimeout(pollBootstrap, 2000);
      } catch (_err) {
        setSystemState({ status: "error", message: "暂时无法连接后端服务，请稍后重试。" });
      }
    };
    bootstrapSystem();

    return () => {
      cancelled = true;
      if (timer) {
        window.clearTimeout(timer);
      }
    };
  }, []);

  const handleSubmit = async (event) => {
    event?.preventDefault();
    if (!query.trim() || systemState.status !== "ready") return;

    setIsGenerating(true);
    setResult(null);
    setExpandedSteps(false);

    let route = "";
    let payload = {};

    if (mode === "auto") {
      route = "/agent/auto/run";
      payload = { query, tenant_id: "demo", speak_response: false };
    } else if (mode === "rag") {
      route = "/rag/query";
      payload = { question: query, tenant_id: "demo", top_k: 8 };
    } else if (mode === "single") {
      route = "/agent/run";
      payload = { query, tenant_id: "demo", speak_response: true };
    } else {
      route = "/agent/team/run";
      payload = { query, tenant_id: "demo" };
    }

    try {
      if (mode === "rag") {
        const response = await fetch(endpoint("/rag/query/stream"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!response.ok) {
          throw new Error(`请求失败：${response.status}`);
        }
        await readNdjsonStream(response, (eventPayload) => {
          if (eventPayload.type === "meta" && eventPayload.result) {
            setResult(eventPayload.result);
            return;
          }
          if (eventPayload.type === "delta") {
            setResult((current) => {
              if (!current) return current;
              const sections = Array.isArray(current.answer_sections) ? [...current.answer_sections] : [];
              if (sections.length === 0) {
                sections.push({ title: "结论", body: "" });
              }
              sections[0] = {
                ...sections[0],
                body: `${sections[0].body || ""}${eventPayload.delta || ""}`,
              };
              return {
                ...current,
                answer_sections: sections,
                answer: `${current.answer || ""}${eventPayload.delta || ""}`,
              };
            });
            return;
          }
          if (eventPayload.type === "done" && eventPayload.result) {
            setResult(eventPayload.result);
            return;
          }
          if (eventPayload.type === "error") {
            throw new Error(eventPayload.message || "流式输出失败。");
          }
        });
      } else {
        const response = await fetch(endpoint(route), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await response.json();
        setResult(data);
      }
    } catch (error) {
      setResult({
        answer: `请求失败：${error instanceof Error ? error.message : "未能拿到后端返回结果。"}`,
        grounded: false,
        confidence: "low",
        question_type: "request_error",
        citations: [],
        review_summary: null,
        voice_job: null,
        steps: [],
        refusal_triggered: true,
        answer_sections: [],
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const confidence = confidenceMeta(result?.confidence);
  const answerSections = Array.isArray(result?.answer_sections) ? result.answer_sections : [];

  return (
    <div className="min-h-dvh bg-[#FDFCFB] text-stone-800 font-sans selection:bg-emerald-100">
      {systemState.status !== "ready" && (
        <div className={`sticky top-0 z-20 w-full px-4 py-2 text-center text-xs font-medium shadow-sm transition-colors sm:text-sm ${systemState.status === "initializing" ? "bg-amber-50 text-amber-700" : "bg-red-50 text-red-700"}`}>
          {systemState.status === "initializing" ? "系统准备中：正在挂载法律知识库..." : systemState.message}
        </div>
      )}

      <main className="safe-bottom mx-auto max-w-4xl px-4 pt-6 sm:px-6 sm:py-12 md:py-20">
        <div className="mb-8 text-left sm:mb-16 sm:text-center">
          <h1 className="mb-3 font-serif text-[2.35rem] leading-[1.08] tracking-tight text-stone-900 sm:mb-4 sm:text-4xl md:text-5xl">法律知识助手</h1>
          <p className="mb-5 max-w-2xl text-[15px] leading-7 text-stone-500 sm:mx-auto sm:mb-8 sm:text-lg sm:leading-relaxed">
            基于法条证据和结构化检索构建，支持引用溯源、保守拒答与多智能体审核。
          </p>
          <div className="hide-scrollbar -mx-4 flex snap-x gap-2 overflow-x-auto px-4 pb-1 sm:mx-0 sm:flex-wrap sm:justify-center sm:gap-3 sm:overflow-visible sm:px-0 sm:pb-0">
            {["Grounded Answer", "Citation Trace", "Conservative Refusal", "Reviewer Agent", "Voice-ready Workflow"].map((tag) => (
              <span key={tag} className="snap-start whitespace-nowrap rounded-md border border-stone-200 bg-white px-2.5 py-1.5 text-[10px] uppercase tracking-wider text-stone-500 shadow-sm sm:px-3 sm:text-[11px]">
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div className="mb-8 rounded-2xl border border-stone-100 bg-white p-3 shadow-[0_2px_20px_-4px_rgba(0,0,0,0.05)] sm:mb-12 sm:p-6 md:p-8">
          <div className="hide-scrollbar -mx-1 mb-4 flex justify-start overflow-x-auto px-1 sm:mb-8 sm:justify-center">
            <div className="inline-flex min-w-max bg-stone-100 p-1 rounded-lg">
              {[
                { id: "auto", label: "自动模式" },
                { id: "rag", label: "引用问答" },
                { id: "single", label: "单 Agent 解析" },
                { id: "team", label: "Team 审核模式" },
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => setMode(item.id)}
                  className={`min-h-11 shrink-0 rounded-md px-4 py-2 text-sm font-medium transition-all sm:min-h-0 sm:px-6 ${mode === item.id ? "bg-white text-stone-800 shadow-sm" : "text-stone-500 hover:text-stone-700"}`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="mb-4 flex flex-col gap-3 sm:relative sm:mb-6 sm:block">
            <div className="relative">
              <div className="pointer-events-none absolute left-4 top-4 sm:inset-y-0 sm:top-auto sm:flex sm:items-center">
                <SearchIcon />
              </div>
              <textarea
                rows={2}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={systemState.status !== "ready" || isGenerating}
                placeholder="输入你的法律问题，例如：抢劫与抢夺的区别是什么？"
                className="min-h-[96px] w-full resize-none rounded-xl border border-stone-200 bg-stone-50 py-4 pl-12 pr-4 text-base leading-7 text-stone-800 placeholder-stone-400 transition-all focus:border-emerald-800 focus:outline-none focus:ring-2 focus:ring-emerald-800/20 disabled:bg-stone-100 disabled:opacity-50 sm:min-h-0 sm:overflow-hidden sm:py-4 sm:pr-32 sm:leading-6"
              />
            </div>
            <button
              type="submit"
              disabled={systemState.status !== "ready" || isGenerating || !query.trim()}
              className="flex min-h-12 w-full items-center justify-center rounded-xl bg-[#21352A] px-6 py-3 text-sm font-medium text-white shadow-lg shadow-emerald-950/10 transition-colors hover:bg-[#16251C] disabled:cursor-not-allowed disabled:opacity-50 sm:absolute sm:inset-y-2 sm:right-2 sm:h-auto sm:w-auto sm:rounded-lg sm:py-0"
            >
              {isGenerating ? "处理中..." : "生成回答"}
            </button>
          </form>

          <div className="hide-scrollbar -mx-3 flex snap-x items-center gap-2 overflow-x-auto px-3 pb-1 text-sm sm:mx-0 sm:flex-wrap sm:gap-3 sm:overflow-visible sm:px-0 sm:pb-0">
            <span className="shrink-0 text-stone-400 font-medium">示例提问：</span>
            {sampleQuestions.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setQuery(item)}
                className="min-h-9 shrink-0 snap-start rounded-full border border-stone-200 bg-stone-50 px-3 py-1 text-stone-600 transition-colors hover:bg-stone-100"
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        {result && (
          <div className="space-y-4 sm:space-y-6">
            <div className="grid grid-cols-3 gap-2 sm:gap-4">
              <div className="flex min-h-[86px] flex-col justify-center rounded-xl border border-stone-100 bg-white p-3 shadow-sm sm:p-4">
                <span className="text-[11px] text-stone-400 uppercase tracking-widest mb-1">Current Mode</span>
                <span className="break-words text-sm font-medium text-stone-700">
                  {mode === "auto"
                    ? result?.agent_mode || "自动路由"
                    : mode === "rag"
                      ? "RAG 检索增强"
                      : mode === "single"
                        ? "Single Agent"
                        : "Team Agent 交叉审核"}
                </span>
              </div>
              <div className="flex min-h-[86px] flex-col justify-center rounded-xl border border-stone-100 bg-white p-3 shadow-sm sm:p-4">
                <span className="text-[11px] text-stone-400 uppercase tracking-widest mb-1">Grounded</span>
                <div className="flex items-center">
                  {result.grounded ? <ShieldIcon /> : null}
                  <span className={`text-sm font-medium ${result.grounded ? "text-emerald-700" : "text-amber-600"}`}>
                    {result.grounded ? "事实具备依据" : "证据不足，已保守处理"}
                  </span>
                </div>
              </div>
              <div className="flex min-h-[86px] flex-col justify-center rounded-xl border border-stone-100 bg-white p-3 shadow-sm sm:p-4">
                <span className="text-[11px] text-stone-400 uppercase tracking-widest mb-1">Confidence</span>
                <div className="flex items-center justify-between gap-3 mt-1">
                  <div className="w-full bg-stone-100 rounded-full h-1.5">
                    <div className={`h-1.5 rounded-full ${confidence.color}`} style={{ width: `${confidence.value * 100}%` }}></div>
                  </div>
                  <span className="text-sm font-medium text-stone-700 whitespace-nowrap">{confidence.label}</span>
                </div>
              </div>
            </div>

            <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
              <div className="flex flex-col items-start gap-2 border-b border-stone-100 bg-stone-50 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6 sm:py-4">
                <h3 className="font-serif text-lg text-stone-800">综合解答</h3>
                {result.voice_job && (
                  <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-[#F2F0EB] text-[#6A604A]">
                    语音讲解已生成
                  </span>
                )}
              </div>
              {answerSections.length > 0 ? (
                <div className="space-y-3 p-3 sm:space-y-5 sm:p-6">
                  {answerSections.map((section, index) => (
                    <section
                      key={`${section.title}-${index}`}
                      className={`rounded-xl border px-3 py-3 break-words sm:px-4 sm:py-4 ${
                        section.title === "结论"
                          ? "border-stone-200 bg-white"
                          : section.title === "法条依据"
                            ? "border-emerald-100 bg-emerald-50/40"
                            : "border-amber-100 bg-amber-50/40"
                      }`}
                    >
                      <h4 className="text-sm font-semibold text-stone-800 mb-2">{section.title}</h4>
                      <div className="text-[15px] leading-7 text-stone-700 sm:leading-8">{renderMultiline(section.body)}</div>
                    </section>
                  ))}
                </div>
              ) : (
                <div className="break-words p-4 text-[15px] leading-7 text-stone-700 sm:p-6 sm:leading-loose whitespace-pre-wrap">{result.answer}</div>
              )}
            </div>

            {result.refusal_triggered && (
              <div className="rounded-xl border border-amber-200/70 bg-amber-50/70 px-4 py-4 sm:px-5 text-sm leading-6 text-amber-900">
                当前回答走的是保守策略。系统优先确保引用和证据边界，不会在证据不足时继续强行推断。
              </div>
            )}

            {result.review_summary && (
              <div className="bg-amber-50/50 rounded-xl border border-amber-200/50 p-4 sm:p-5 flex items-start">
                <svg className="w-5 h-5 text-amber-700 mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                <div>
                  <h4 className="text-sm font-semibold text-amber-900 mb-1">Reviewer Agent 审核说明</h4>
                  <p className="text-sm text-amber-800/80 leading-relaxed">{result.review_summary}</p>
                </div>
              </div>
            )}

            {result.citations && result.citations.length > 0 && (
              <div className="space-y-3 pt-2">
                <h4 className="text-sm font-medium text-stone-500 uppercase tracking-widest flex items-center">
                  <DocumentIcon />
                  引用依据
                </h4>
                <div className="hide-scrollbar -mx-4 flex snap-x gap-3 overflow-x-auto px-4 pb-2 md:mx-0 md:grid md:grid-cols-2 md:overflow-visible md:px-0 md:pb-0">
                  {result.citations.map((cite, index) => (
                    <div key={`${cite.chunk_id}-${index}`} className="min-w-[82vw] snap-start rounded-xl border border-stone-200 bg-white p-4 transition-colors hover:border-emerald-700/30 md:min-w-0">
                      <div className="flex flex-col gap-2 mb-2 sm:flex-row sm:items-start sm:justify-between sm:gap-3">
                        <div className="text-sm font-semibold text-stone-800 break-words" title={cite.section || cite.title}>
                          {cite.section || cite.title}
                        </div>
                        <span className="w-fit shrink-0 rounded-full bg-stone-100 px-2 py-0.5 text-[11px] text-stone-500">证据 {index + 1}</span>
                      </div>
                      <div className="text-[11px] uppercase tracking-wider text-stone-400 mb-2 break-words">{cite.title}</div>
                      <div className="text-xs text-stone-600 leading-6 break-words">{cite.snippet}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.steps && result.steps.length > 0 && (
              <div className="pt-4 border-t border-stone-100">
                <button
                  onClick={() => setExpandedSteps((value) => !value)}
                  className="text-xs font-medium text-stone-400 hover:text-stone-600 flex items-center transition-colors"
                >
                  <svg className={`w-3 h-3 mr-1 transform transition-transform ${expandedSteps ? "rotate-90" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path></svg>
                  {expandedSteps ? "隐藏执行链路" : "查看底层执行链路"}
                </button>
                {expandedSteps && (
                  <div className="mt-4 max-h-64 space-y-3 overflow-y-auto rounded-lg border border-[#E5E5E5] bg-[#F2F2F2] p-3 font-mono text-[11px] text-stone-600 sm:max-h-none sm:p-4">
                    {result.steps.map((step, index) => (
                      <div key={`${step.action}-${index}`} className="flex flex-col gap-1 sm:flex-row">
                        <span className="w-auto shrink-0 text-emerald-700 font-semibold sm:w-24">[{step.action}]</span>
                        <span className="break-words">{step.observation || step.detail || step.thought}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
