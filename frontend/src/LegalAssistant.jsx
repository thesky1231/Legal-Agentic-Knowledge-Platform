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

function normalizeConfidence(confidence) {
  if (typeof confidence === "number") return confidence;
  if (confidence === "high") return 0.9;
  if (confidence === "medium") return 0.65;
  if (confidence === "low") return 0.35;
  return 0;
}

export default function LegalAssistant() {
  const [systemState, setSystemState] = useState({ status: "initializing", message: "正在初始化知识库..." });
  const [mode, setMode] = useState("rag");
  const [query, setQuery] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState(null);
  const [expandedSteps, setExpandedSteps] = useState(false);

  const sampleQuestions = [
    "抢劫与抢夺的区别",
    "证据不足时如何保守回答",
    "多 Agent 如何做审核"
  ];

  useEffect(() => {
    const bootstrapSystem = async () => {
      try {
        const res = await fetch(endpoint("/showcase/bootstrap"), { method: "POST" });
        if (res.ok) {
          setSystemState({ status: "ready", message: "" });
        } else {
          setSystemState({ status: "error", message: "知识库初始化失败，请刷新重试。" });
        }
      } catch (_err) {
        setTimeout(() => setSystemState({ status: "ready", message: "" }), 1500);
      }
    };
    bootstrapSystem();
  }, []);

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim() || systemState.status !== "ready") return;

    setIsGenerating(true);
    setResult(null);
    setExpandedSteps(false);

    let route = "";
    let payload = {};

    if (mode === "rag") {
      route = "/rag/query";
      payload = { question: query, tenant_id: "demo", top_k: 4 };
    } else if (mode === "single") {
      route = "/agent/run";
      payload = { query: query, tenant_id: "demo", speak_response: true };
    } else if (mode === "team") {
      route = "/agent/team/run";
      payload = { query: query, tenant_id: "demo" };
    }

    try {
      const response = await fetch(endpoint(route), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      setResult(data);
      setIsGenerating(false);
    } catch (error) {
      setResult({
        answer: `请求失败：${error instanceof Error ? error.message : "前端未能拿到后端返回结果。"}`,
        grounded: false,
        confidence: 0,
        question_type: "request_error",
        citations: [],
        review_summary: null,
        voice_job: null,
        steps: [],
        refusal_triggered: true
      });
      setIsGenerating(false);
    }
  };

  const handleSampleClick = (question) => {
    setQuery(question);
  };

  const confidenceValue = normalizeConfidence(result?.confidence);

  return (
    <div className="min-h-screen bg-[#FDFCFB] text-stone-800 font-sans selection:bg-emerald-100">
      {systemState.status !== "ready" && (
        <div className={`w-full text-center py-2 text-sm font-medium transition-colors ${systemState.status === "initializing" ? "bg-amber-50 text-amber-700" : "bg-red-50 text-red-700"}`}>
          {systemState.status === "initializing" ? "系统准备中：正在挂载本地法律知识库..." : systemState.message}
        </div>
      )}

      <main className="max-w-4xl mx-auto px-6 py-12 md:py-20">
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-5xl font-serif text-stone-900 tracking-tight mb-4">
            法律知识助手
          </h1>
          <p className="text-stone-500 text-lg mb-8 max-w-2xl mx-auto leading-relaxed">
            基于严谨法条与专业文献构建，支持多智能体交叉审核，
            <br />
            在证据不足时严格保守拒答。
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            {["Grounded Answer", "Citation Trace", "Conservative Refusal", "Reviewer Agent", "Voice-ready Workflow"].map((tag) => (
              <span key={tag} className="px-3 py-1.5 text-[11px] uppercase tracking-wider text-stone-500 border border-stone-200 rounded-md bg-white shadow-sm">
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-[0_2px_20px_-4px_rgba(0,0,0,0.05)] border border-stone-100 p-6 md:p-8 mb-12">
          <div className="flex justify-center mb-8">
            <div className="inline-flex bg-stone-100 p-1 rounded-lg">
              {[
                { id: "rag", label: "引用问答" },
                { id: "single", label: "单 Agent 解析" },
                { id: "team", label: "Team 审核模式" }
              ].map((m) => (
                <button
                  key={m.id}
                  onClick={() => setMode(m.id)}
                  className={`px-6 py-2 text-sm font-medium rounded-md transition-all ${mode === m.id ? "bg-white text-stone-800 shadow-sm" : "text-stone-500 hover:text-stone-700"}`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="relative mb-6">
            <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
              <SearchIcon />
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={systemState.status !== "ready" || isGenerating}
              placeholder="输入您的法律问题，例如：抢劫与抢夺在量刑上的区别？"
              className="w-full pl-12 pr-32 py-4 bg-stone-50 border border-stone-200 rounded-xl text-stone-800 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-800/20 focus:border-emerald-800 transition-all text-base disabled:opacity-50 disabled:bg-stone-100"
            />
            <div className="absolute inset-y-2 right-2">
              <button
                type="submit"
                disabled={systemState.status !== "ready" || isGenerating || !query.trim()}
                className="h-full px-6 bg-[#21352A] hover:bg-[#16251C] text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {isGenerating ? "处理中..." : "生成回答"}
              </button>
            </div>
          </form>

          <div className="flex flex-wrap items-center gap-3 text-sm">
            <span className="text-stone-400 font-medium">示例提问：</span>
            {sampleQuestions.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSampleClick(q)}
                className="px-3 py-1 bg-stone-50 text-stone-600 rounded-md hover:bg-stone-100 transition-colors border border-stone-200"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {result && (
          <div className="space-y-6">
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white border border-stone-100 rounded-xl p-4 shadow-sm flex flex-col justify-center">
                <span className="text-[11px] text-stone-400 uppercase tracking-widest mb-1">Current Mode</span>
                <span className="text-sm font-medium text-stone-700">
                  {mode === "rag" ? "RAG 检索增强" : mode === "single" ? "Single Agent" : "Team Agent 交叉审核"}
                </span>
              </div>
              <div className="bg-white border border-stone-100 rounded-xl p-4 shadow-sm flex flex-col justify-center">
                <span className="text-[11px] text-stone-400 uppercase tracking-widest mb-1">Grounded</span>
                <div className="flex items-center">
                  {result.grounded ? <ShieldIcon /> : null}
                  <span className={`text-sm font-medium ${result.grounded ? "text-emerald-700" : "text-amber-600"}`}>
                    {result.grounded ? "事实具备依据" : "缺乏充分依据 (保守拒绝)"}
                  </span>
                </div>
              </div>
              <div className="bg-white border border-stone-100 rounded-xl p-4 shadow-sm flex flex-col justify-center">
                <span className="text-[11px] text-stone-400 uppercase tracking-widest mb-1">Confidence</span>
                <div className="flex items-center mt-1">
                  <div className="w-full bg-stone-100 rounded-full h-1.5 mr-3">
                    <div
                      className={`h-1.5 rounded-full ${confidenceValue > 0.8 ? "bg-emerald-700" : confidenceValue > 0.5 ? "bg-amber-500" : "bg-red-500"}`}
                      style={{ width: `${confidenceValue * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium text-stone-700">{Math.round(confidenceValue * 100)}%</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-stone-200 overflow-hidden">
              <div className="bg-stone-50 border-b border-stone-100 px-6 py-4 flex justify-between items-center">
                <h3 className="font-serif text-lg text-stone-800">综合解答</h3>
                {result.voice_job && (
                  <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-[#F2F0EB] text-[#6A604A]">
                    <svg className="w-3 h-3 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"></path></svg>
                    语音生成已就绪
                  </span>
                )}
              </div>
              <div className="p-6 text-stone-700 leading-loose text-[15px] whitespace-pre-wrap">
                {result.answer}
              </div>
            </div>

            {result.review_summary && (
              <div className="bg-amber-50/50 rounded-xl border border-amber-200/50 p-5 flex items-start">
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
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {result.citations.map((cite, i) => (
                    <div key={i} className="p-4 rounded-xl border border-stone-200 bg-white hover:border-emerald-700/30 transition-colors">
                      <div className="text-sm font-semibold text-stone-800 mb-2 truncate" title={cite.title}>
                        {cite.title}
                      </div>
                      <div className="text-xs text-stone-500 leading-relaxed">
                        "{cite.snippet}"
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.steps && result.steps.length > 0 && (
              <div className="pt-4 border-t border-stone-100">
                <button
                  onClick={() => setExpandedSteps(!expandedSteps)}
                  className="text-xs font-medium text-stone-400 hover:text-stone-600 flex items-center transition-colors"
                >
                  <svg className={`w-3 h-3 mr-1 transform transition-transform ${expandedSteps ? "rotate-90" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path></svg>
                  {expandedSteps ? "隐藏执行链详细步骤" : "查看底层执行链路"}
                </button>

                {expandedSteps && (
                  <div className="mt-4 p-4 bg-[#F2F2F2] rounded-lg border border-[#E5E5E5] space-y-2 font-mono text-[11px] text-stone-600">
                    {result.steps.map((step, idx) => (
                      <div key={idx} className="flex">
                        <span className="w-20 text-emerald-700 font-semibold">[{step.action}]</span>
                        <span>{step.detail || step.observation || step.thought}</span>
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
