from __future__ import annotations

import html
import json

from agentic_knowledge_platform.demo_ui import load_demo_sample


def render_showcase_page(service_name: str) -> str:
    sample = load_demo_sample()
    safe_name = html.escape(service_name)
    sample_json = json.dumps(sample, ensure_ascii=False)
    return PRODUCT_SHOWCASE_TEMPLATE.replace("__SERVICE_NAME__", safe_name).replace("__SAMPLE_JSON__", sample_json)


SHOWCASE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>__SERVICE_NAME__ · Legal Assistant Demo</title>
    <style>
      :root { --bg:#f6f0e7; --paper:rgba(255,251,245,.88); --line:rgba(79,57,41,.14); --ink:#1c1714; --muted:#66584d; --brand:#8a341b; --ok:#1f7258; --warn:#91611f; --shadow:0 20px 42px rgba(83,60,43,.12); }
      * { box-sizing:border-box; }
      body { margin:0; color:var(--ink); background:
        radial-gradient(circle at top left, rgba(138,52,27,.1), transparent 28%),
        radial-gradient(circle at 90% 10%, rgba(31,114,88,.1), transparent 24%),
        linear-gradient(160deg, var(--bg), #efe8dd 45%, #f8f3eb 100%);
        font-family:"Microsoft YaHei","PingFang SC",sans-serif; }
      .shell { width:min(1320px, calc(100vw - 28px)); margin:0 auto; padding:24px 0 36px; }
      .hero, .panel, .metric { border:1px solid var(--line); background:var(--paper); box-shadow:var(--shadow); backdrop-filter:blur(8px); }
      .hero { position:relative; overflow:hidden; display:grid; grid-template-columns:1.5fr .9fr; gap:18px; border-radius:28px; padding:28px; margin-bottom:18px; }
      .hero::after { content:""; position:absolute; right:-72px; bottom:-108px; width:260px; height:260px; border-radius:999px; background:radial-gradient(circle, rgba(138,52,27,.16), transparent 68%); pointer-events:none; }
      .eyebrow { margin:0 0 10px; color:var(--brand); font-size:12px; font-weight:800; letter-spacing:.16em; text-transform:uppercase; }
      h1, h2, h3 { margin:0; font-family:"SimSun","Songti SC","Noto Serif SC",serif; }
      h1 { font-size:clamp(32px,4vw,50px); line-height:1.04; margin-bottom:14px; }
      .hero p:last-child { margin:0; color:var(--muted); line-height:1.8; max-width:62ch; }
      .metrics { display:grid; gap:12px; }
      .metric { border-radius:20px; padding:16px 18px; }
      .metric span { display:block; color:var(--muted); font-size:12px; margin-bottom:8px; }
      .metric strong { font-size:20px; line-height:1.25; }
      .caps { display:flex; flex-wrap:wrap; gap:10px; margin-top:18px; }
      .cap { padding:9px 13px; border-radius:999px; background:rgba(255,255,255,.82); border:1px solid rgba(79,57,41,.12); font-size:13px; font-weight:700; }
      .layout { display:grid; grid-template-columns:.98fr 1.02fr; gap:18px; }
      .panel { border-radius:24px; padding:22px; background:linear-gradient(180deg, rgba(255,251,245,.94), rgba(255,248,240,.86)); }
      .panel h2 { font-size:24px; margin-bottom:10px; }
      .note { margin:0 0 16px; color:var(--muted); line-height:1.75; }
      .grid3 { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }
      .card { padding:14px; border-radius:16px; border:1px solid rgba(79,57,41,.12); background:rgba(255,255,255,.8); }
      .card strong { display:block; margin-bottom:8px; color:var(--brand); }
      .card p { margin:0; color:var(--muted); line-height:1.7; font-size:14px; }
      .stack { display:grid; gap:14px; }
      .modes { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }
      .mode { border:1px solid rgba(79,57,41,.14); border-radius:16px; background:linear-gradient(180deg, rgba(255,255,255,.88), rgba(249,242,233,.72)); padding:14px; cursor:pointer; text-align:left; }
      .mode.active { border-color:rgba(138,52,27,.42); box-shadow:0 0 0 4px rgba(138,52,27,.08); background:linear-gradient(180deg, rgba(138,52,27,.08), rgba(255,255,255,.88)); }
      .mode strong { display:block; margin-bottom:7px; font-size:15px; }
      .mode span { color:var(--muted); font-size:13px; line-height:1.6; }
      label { display:grid; gap:8px; font-size:14px; font-weight:700; }
      input, textarea { width:100%; border:1px solid rgba(79,57,41,.16); border-radius:12px; background:rgba(255,255,255,.86); color:var(--ink); font:inherit; padding:13px 14px; outline:none; }
      textarea { min-height:150px; resize:vertical; line-height:1.75; }
      input:focus, textarea:focus { border-color:rgba(138,52,27,.38); box-shadow:0 0 0 4px rgba(138,52,27,.08); }
      .actions { display:flex; flex-wrap:wrap; gap:10px; }
      button { border:0; border-radius:999px; padding:12px 18px; font:inherit; font-weight:800; cursor:pointer; transition:transform .15s ease, opacity .15s ease; }
      button:hover { transform:translateY(-1px); }
      button:disabled { opacity:.68; transform:none; cursor:wait; }
      .primary { color:#fffaf6; background:linear-gradient(135deg, #8a341b, #ac4926); box-shadow:0 12px 20px rgba(138,52,27,.22); }
      .secondary { color:var(--ink); background:rgba(255,255,255,.92); border:1px solid rgba(79,57,41,.14); }
      .quiet { color:var(--brand); background:rgba(138,52,27,.08); }
      .status, .answer, .list { border-radius:16px; border:1px solid rgba(79,57,41,.12); background:rgba(255,255,255,.78); padding:16px; }
      .status { color:var(--muted); line-height:1.65; min-height:56px; }
      .status.ok { color:var(--ok); border-color:rgba(31,114,88,.22); background:rgba(31,114,88,.08); }
      .status.warn { color:var(--warn); border-color:rgba(145,97,31,.2); background:rgba(145,97,31,.08); }
      .summary { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }
      .answer { min-height:230px; white-space:pre-wrap; line-height:1.8; background:linear-gradient(180deg, rgba(255,255,255,.94), rgba(250,243,234,.78)); }
      .list ul, .list ol { margin:0; padding-left:18px; }
      .list li { margin-bottom:10px; line-height:1.75; }
      details { border-radius:16px; border:1px solid rgba(79,57,41,.1); background:rgba(255,255,255,.6); padding:14px 16px; }
      details summary { cursor:pointer; font-weight:800; color:var(--brand); }
      pre { margin:12px 0 0; max-height:220px; overflow:auto; font-size:12px; line-height:1.65; }
      @media (max-width:1100px) { .hero, .layout { grid-template-columns:1fr; } }
      @media (max-width:820px) { .grid3, .modes, .summary { grid-template-columns:1fr; } .panel, .hero { padding:18px; } }
    </style>
  </head>
  <body>
    <div class="shell">
      <section class="hero">
        <div>
          <p class="eyebrow">Legal Agent Demo</p>
          <h1>法律知识助手，回答要能追溯，结论要敢保守。</h1>
          <p>这个演示页把法律知识问答、严格引用、保守拒答和多 Agent 审核整合到一条真实可运行的后端链路里。普通访客只需要载入示例资料，输入问题，然后选择一种回答模式体验即可。</p>
          <div class="caps">
            <span class="cap">Grounded Answer</span>
            <span class="cap">Citation Trace</span>
            <span class="cap">Conservative Refusal</span>
            <span class="cap">Reviewer Agent</span>
            <span class="cap">Voice-ready Workflow</span>
          </div>
        </div>
        <div class="metrics">
          <div class="metric"><span>Service</span><strong id="service-name">__SERVICE_NAME__</strong></div>
          <div class="metric"><span>System Health</span><strong id="health-status">等待检查</strong></div>
          <div class="metric"><span>Knowledge Base</span><strong id="health-docs">0 documents / 0 vectors</strong></div>
          <div class="metric"><span>Inference Stack</span><strong id="health-backends">stub / hash / memory</strong></div>
        </div>
      </section>

      <section class="layout">
        <section class="panel">
          <h2>开始体验</h2>
          <p class="note">页面打开后会自动准备法律示例知识库，所以访客不需要关心文档入库、租户参数或任何后台配置。你只需要输入问题，并选择一种回答模式开始体验。</p>
          <div class="grid3" style="margin-bottom:16px;">
            <div class="card"><strong>引用回答</strong><p>聚焦 grounded RAG，适合先看 citation 和证据片段。</p></div>
            <div class="card"><strong>单 Agent</strong><p>在回答之外展示步骤追踪，并可串到语音讲解链路。</p></div>
            <div class="card"><strong>团队 Agent</strong><p>在生成回答后加入 reviewer，适合高风险问答场景。</p></div>
          </div>
          <div class="stack">
            <div class="status" id="doc-status">正在准备示例知识库...</div>
            <label>访客问题<textarea id="question-input" placeholder="例如：请比较抢劫与抢夺的区别，并说明为什么回答必须带引用。"></textarea></label>
            <div class="modes">
              <button type="button" class="mode active" data-mode="rag"><strong>引用回答</strong><span>最快体验 grounded answer 与 citation trace。</span></button>
              <button type="button" class="mode" data-mode="single"><strong>单 Agent</strong><span>展示回答步骤和语音链路准备结果。</span></button>
              <button type="button" class="mode" data-mode="team"><strong>团队 Agent</strong><span>额外加入 reviewer 审核结果。</span></button>
            </div>
            <div class="actions">
              <button class="primary" id="run-demo">生成回答</button>
              <button class="secondary" id="rebuild-demo">重新准备示例资料</button>
              <button class="quiet" id="prompt-rag">填入区分问题</button>
              <button class="quiet" id="prompt-agent">填入保守拒答问题</button>
              <button class="quiet" id="prompt-team">填入多 Agent 问题</button>
            </div>
            <details>
              <summary>为什么这里看起来像产品，而不是调试台？</summary>
              <div class="stack" style="margin-top:12px;">
                <div class="card">
                  <strong>前台只保留用户动作</strong>
                  <p>用户只需要提问、选模式、看答案、看引用和审核说明。文档入库、租户配置、运维细节这些后台动作已经收回到服务端处理。</p>
                </div>
              </div>
            </details>
          </div>
        </section>

        <section class="panel">
          <h2>回答结果</h2>
          <p class="note">这里优先展示给访客看的信息：答案正文、可信度、引用依据，以及 reviewer 或语音链路的附加说明。</p>
          <div class="summary">
            <div class="card"><strong id="mode-chip">引用回答</strong><p>当前模式</p></div>
            <div class="card"><strong id="grounded-chip">-</strong><p>Grounded</p></div>
            <div class="card"><strong id="confidence-chip">-</strong><p>Confidence</p></div>
          </div>
          <div class="status" id="query-status" style="margin-top:14px;">导入知识库后，输入问题并点击“生成回答”。</div>
          <div class="answer" id="answer-box" style="margin-top:14px;">回答生成后会显示在这里。</div>
          <div class="list" style="margin-top:14px;">
            <h3 style="margin-bottom:12px;">引用依据</h3>
            <ul id="citations-list"><li>这里会显示回答使用到的证据片段。</li></ul>
          </div>
          <div class="list" style="margin-top:14px;">
            <h3 style="margin-bottom:12px;">审核与执行说明</h3>
            <ul id="review-list"><li>如果使用 Team Agent，这里会出现 reviewer 的审核结论。</li></ul>
          </div>
          <details style="margin-top:14px;">
            <summary>展开查看系统细节</summary>
            <div class="list" style="margin-top:12px;">
              <h3 style="margin-bottom:12px;">Agent Steps</h3>
              <ol id="steps-list"><li>当前还没有步骤记录。</li></ol>
            </div>
          </details>
        </section>
      </section>
    </div>
    <script>
      const sample = __SAMPLE_JSON__;
      let currentMode = "rag";
      let seeded = false;
      const els = {
        docStatus: document.getElementById("doc-status"),
        questionInput: document.getElementById("question-input"),
        queryStatus: document.getElementById("query-status"),
        answerBox: document.getElementById("answer-box"),
        citationsList: document.getElementById("citations-list"),
        reviewList: document.getElementById("review-list"),
        stepsList: document.getElementById("steps-list"),
        serviceName: document.getElementById("service-name"),
        healthStatus: document.getElementById("health-status"),
        healthDocs: document.getElementById("health-docs"),
        healthBackends: document.getElementById("health-backends"),
        modeChip: document.getElementById("mode-chip"),
        groundedChip: document.getElementById("grounded-chip"),
        confidenceChip: document.getElementById("confidence-chip"),
      };
      function setStatus(target, message, tone="") {
        target.textContent = message;
        target.className = tone ? `status ${tone}` : "status";
      }
      async function fetchJson(url, options={}) {
        const response = await fetch(url, options);
        const isJson = (response.headers.get("content-type") || "").includes("application/json");
        const payload = isJson ? await response.json() : await response.text();
        if (!response.ok) {
          throw new Error(typeof payload === "string" ? payload : (payload.detail || JSON.stringify(payload, null, 2)));
        }
        return payload;
      }
      function fillSample(kind="rag") {
        els.questionInput.value = kind === "agent" ? sample.agent_question : kind === "team" ? sample.team_question : sample.rag_question;
      }
      function applyMode(mode) {
        currentMode = mode;
        document.querySelectorAll("[data-mode]").forEach((button) => {
          button.classList.toggle("active", button.dataset.mode === mode);
        });
        els.modeChip.textContent = mode === "single" ? "单 Agent" : mode === "team" ? "团队 Agent" : "引用回答";
      }
      function renderHealth(data) {
        els.serviceName.textContent = data.service || "__SERVICE_NAME__";
        els.healthStatus.textContent = data.status || "unknown";
        els.healthDocs.textContent = `${data.documents ?? 0} documents / ${data.vectors ?? 0} vectors`;
        els.healthBackends.textContent = `${data.model_provider || "-"} / ${data.embedding_provider || "-"} / ${data.vector_store_backend || "-"}`;
      }
      function renderResult(data) {
        els.answerBox.textContent = data.answer || "这次没有生成回答。";
        els.groundedChip.textContent = data.grounded ? "true" : "false";
        els.confidenceChip.textContent = data.confidence || "-";
        const citations = Array.isArray(data.citations) ? data.citations : [];
        els.citationsList.innerHTML = citations.length ? citations.map((item) => `<li><strong>${item.section || "未标注章节"}</strong><br />${item.snippet || ""}</li>`).join("") : "<li>当前没有引用片段。</li>";
        const notes = [];
        if (data.review_summary) notes.push(`<li><strong>Reviewer</strong><br />${data.review_summary}</li>`);
        if (data.voice_job) notes.push(`<li><strong>Voice Job</strong><br />job_id=${data.voice_job.job_id}<br />avatar=${data.voice_job.avatar_job_id || "-"}</li>`);
        if (data.question_type) notes.push(`<li><strong>Question Type</strong><br />${data.question_type}</li>`);
        els.reviewList.innerHTML = notes.length ? notes.join("") : "<li>当前模式没有额外审核或语音说明。</li>";
        const steps = Array.isArray(data.steps) ? data.steps : [];
        els.stepsList.innerHTML = steps.length ? steps.map((step) => `<li><strong>${step.agent}</strong> · ${step.action}<br />${step.observation || step.thought || "无详细记录"}</li>`).join("") : "<li>当前没有步骤追踪输出。</li>";
      }
      async function refreshHealth() { renderHealth(await fetchJson("/health")); }
      async function bootstrapDemo(force=false) {
        setStatus(els.docStatus, force ? "正在重新准备示例知识库..." : "正在准备示例知识库...", "");
        try {
          const suffix = force ? "?force=true" : "";
          const result = await fetchJson(`/demo/bootstrap${suffix}`, { method: "POST" });
          seeded = true;
          setStatus(
            els.docStatus,
            result.seeded ? `示例知识库已准备完成，chunk_count=${result.chunk_count}` : "示例知识库已就绪，可以直接提问。",
            "ok"
          );
          await refreshHealth();
        } catch (error) {
          setStatus(els.docStatus, `示例知识库准备失败：${error.message}`, "warn");
        }
      }
      async function runExperience() {
        if (!seeded) { setStatus(els.queryStatus, "请先等待示例知识库准备完成。", "warn"); return; }
        const question = els.questionInput.value.trim();
        if (!question) { setStatus(els.queryStatus, "请输入一个法律问题。", "warn"); return; }
        const tenantId = sample.tenant_id || "demo";
        const configs = {
          rag: { label: "引用回答", url: "/rag/query", payload: { question, tenant_id: tenantId, top_k: 4 } },
          single: { label: "单 Agent", url: "/agent/run", payload: { query: question, tenant_id: tenantId, speak_response: true } },
          team: { label: "团队 Agent", url: "/agent/team/run", payload: { query: question, tenant_id: tenantId } },
        };
        const config = configs[currentMode];
        setStatus(els.queryStatus, `${config.label} 正在生成回答...`, "");
        try {
          const result = await fetchJson(config.url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(config.payload) });
          renderResult(result);
          setStatus(els.queryStatus, `${config.label} 已完成：grounded=${result.grounded}，citations=${(result.citations || []).length}`, "ok");
          await refreshHealth();
        } catch (error) {
          setStatus(els.queryStatus, `${config.label} 失败：${error.message}`, "warn");
        }
      }
      document.getElementById("rebuild-demo").addEventListener("click", () => bootstrapDemo(true));
      document.getElementById("run-demo").addEventListener("click", runExperience);
      document.getElementById("prompt-rag").addEventListener("click", () => fillSample("rag"));
      document.getElementById("prompt-agent").addEventListener("click", () => fillSample("agent"));
      document.getElementById("prompt-team").addEventListener("click", () => fillSample("team"));
      document.querySelectorAll("[data-mode]").forEach((button) => button.addEventListener("click", () => applyMode(button.dataset.mode)));
      fillSample("rag");
      applyMode("rag");
      refreshHealth();
      bootstrapDemo(false);
    </script>
  </body>
</html>
"""


PRODUCT_SHOWCASE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>法律知识助手 | __SERVICE_NAME__</title>
    <style>
      :root {
        --bg: #f6f1e8;
        --paper: rgba(255, 252, 246, 0.92);
        --paper-strong: rgba(255, 255, 255, 0.96);
        --ink: #1f1916;
        --muted: #695c53;
        --line: rgba(84, 65, 48, 0.14);
        --brand: #23392f;
        --accent: #916949;
        --ok: #1f6a54;
        --warn: #99651b;
        --danger: #9d4534;
        --shadow: 0 24px 44px rgba(66, 49, 36, 0.12);
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        color: var(--ink);
        background:
          radial-gradient(circle at 0% 0%, rgba(145, 105, 73, 0.16), transparent 28%),
          radial-gradient(circle at 100% 10%, rgba(35, 57, 47, 0.12), transparent 24%),
          linear-gradient(180deg, #f8f4ed 0%, #f3ede4 44%, #f7f2ea 100%);
        font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
      }

      .shell {
        width: min(1240px, calc(100vw - 28px));
        margin: 0 auto;
        padding: 24px 0 40px;
      }

      .banner {
        margin-bottom: 18px;
        padding: 12px 16px;
        border-radius: 16px;
        border: 1px solid rgba(84, 65, 48, 0.12);
        background: rgba(255, 247, 233, 0.92);
        color: var(--warn);
        font-size: 14px;
        line-height: 1.7;
      }

      .banner.ready {
        border-color: rgba(31, 106, 84, 0.18);
        background: rgba(236, 248, 243, 0.94);
        color: var(--ok);
      }

      .banner.error {
        border-color: rgba(157, 69, 52, 0.18);
        background: rgba(255, 242, 239, 0.94);
        color: var(--danger);
      }

      .hero {
        display: grid;
        grid-template-columns: 1.2fr 0.8fr;
        gap: 18px;
        margin-bottom: 18px;
      }

      .hero-card,
      .panel,
      .result-card,
      .metric,
      .citation-card,
      .audit-card {
        border: 1px solid var(--line);
        background: var(--paper);
        box-shadow: var(--shadow);
        backdrop-filter: blur(10px);
      }

      .hero-card {
        position: relative;
        overflow: hidden;
        border-radius: 30px;
        padding: 32px;
      }

      .hero-card::after {
        content: "";
        position: absolute;
        right: -72px;
        bottom: -96px;
        width: 240px;
        height: 240px;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(145, 105, 73, 0.18), transparent 70%);
        pointer-events: none;
      }

      .eyebrow {
        margin: 0 0 12px;
        color: var(--accent);
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.18em;
        text-transform: uppercase;
      }

      h1,
      h2,
      h3 {
        margin: 0;
        font-family: "SimSun", "Songti SC", "Noto Serif SC", serif;
      }

      h1 {
        font-size: clamp(34px, 4vw, 52px);
        line-height: 1.08;
        letter-spacing: -0.02em;
        margin-bottom: 16px;
      }

      .hero-copy {
        margin: 0 0 22px;
        max-width: 34em;
        color: var(--muted);
        font-size: 16px;
        line-height: 1.9;
      }

      .tag-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .tag {
        padding: 9px 14px;
        border-radius: 999px;
        border: 1px solid rgba(84, 65, 48, 0.12);
        background: rgba(255, 255, 255, 0.86);
        color: var(--ink);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.04em;
      }

      .hero-side {
        display: grid;
        gap: 14px;
      }

      .metric {
        border-radius: 24px;
        padding: 18px 20px;
      }

      .metric span {
        display: block;
        margin-bottom: 8px;
        color: var(--muted);
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
      }

      .metric strong {
        display: block;
        font-size: 20px;
        line-height: 1.5;
      }

      .layout {
        display: grid;
        grid-template-columns: 0.94fr 1.06fr;
        gap: 18px;
      }

      .panel {
        border-radius: 28px;
        padding: 24px;
      }

      .panel h2 {
        font-size: 26px;
        margin-bottom: 10px;
      }

      .panel-note {
        margin: 0 0 18px;
        color: var(--muted);
        line-height: 1.85;
      }

      .mode-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
        margin-bottom: 18px;
      }

      .mode-button {
        padding: 16px;
        border-radius: 18px;
        border: 1px solid rgba(84, 65, 48, 0.12);
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(249, 243, 236, 0.8));
        color: inherit;
        text-align: left;
        cursor: pointer;
        transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
      }

      .mode-button:hover {
        transform: translateY(-1px);
      }

      .mode-button.active {
        border-color: rgba(35, 57, 47, 0.34);
        box-shadow: 0 0 0 4px rgba(35, 57, 47, 0.08);
        background: linear-gradient(180deg, rgba(35, 57, 47, 0.08), rgba(255, 255, 255, 0.92));
      }

      .mode-button strong {
        display: block;
        margin-bottom: 6px;
        font-size: 15px;
      }

      .mode-button span {
        color: var(--muted);
        font-size: 13px;
        line-height: 1.7;
      }

      .label {
        display: block;
        margin-bottom: 8px;
        font-size: 14px;
        font-weight: 700;
      }

      textarea {
        width: 100%;
        min-height: 170px;
        resize: vertical;
        padding: 16px 18px;
        border-radius: 18px;
        border: 1px solid rgba(84, 65, 48, 0.14);
        background: rgba(255, 255, 255, 0.86);
        color: var(--ink);
        font: inherit;
        line-height: 1.9;
        outline: none;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
      }

      textarea:focus {
        border-color: rgba(35, 57, 47, 0.28);
        box-shadow: 0 0 0 4px rgba(35, 57, 47, 0.08);
      }

      .action-row,
      .sample-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      .sample-row {
        margin-top: 14px;
      }

      button {
        border: 0;
        border-radius: 999px;
        font: inherit;
        font-weight: 700;
        cursor: pointer;
        transition: transform 0.15s ease, opacity 0.15s ease, background 0.15s ease;
      }

      button:hover {
        transform: translateY(-1px);
      }

      button:disabled {
        opacity: 0.65;
        transform: none;
        cursor: not-allowed;
      }

      .primary {
        padding: 13px 22px;
        color: #f9f4ee;
        background: linear-gradient(135deg, #21352a, #314d3e);
        box-shadow: 0 14px 22px rgba(35, 57, 47, 0.2);
      }

      .sample {
        padding: 10px 14px;
        border: 1px solid rgba(84, 65, 48, 0.12);
        background: rgba(255, 255, 255, 0.86);
        color: var(--muted);
      }

      .sample:hover {
        color: var(--ink);
      }

      .result-stack {
        display: grid;
        gap: 14px;
      }

      .result-card {
        border-radius: 24px;
        padding: 20px;
      }

      .chip-row {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
      }

      .metric-chip {
        border-radius: 18px;
        border: 1px solid rgba(84, 65, 48, 0.12);
        background: rgba(255, 255, 255, 0.86);
        padding: 14px;
      }

      .metric-chip span {
        display: block;
        margin-bottom: 8px;
        color: var(--muted);
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
      }

      .metric-chip strong {
        display: block;
        font-size: 16px;
        line-height: 1.5;
      }

      .metric-chip.ok strong {
        color: var(--ok);
      }

      .metric-chip.warn strong {
        color: var(--warn);
      }

      .result-status,
      .answer-box,
      .empty-box,
      .audit-card,
      details {
        border-radius: 18px;
        border: 1px solid rgba(84, 65, 48, 0.12);
      }

      .result-status {
        padding: 14px 16px;
        background: rgba(255, 255, 255, 0.82);
        color: var(--muted);
        line-height: 1.75;
      }

      .result-status.ok {
        background: rgba(236, 248, 243, 0.92);
        border-color: rgba(31, 106, 84, 0.18);
        color: var(--ok);
      }

      .result-status.warn {
        background: rgba(255, 246, 231, 0.92);
        border-color: rgba(153, 101, 27, 0.16);
        color: var(--warn);
      }

      .answer-box,
      .empty-box {
        padding: 22px;
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(249, 242, 233, 0.86));
        white-space: pre-wrap;
        line-height: 1.9;
      }

      .empty-box {
        color: var(--muted);
      }

      .section-title {
        margin: 0 0 12px;
        font-size: 18px;
      }

      .citation-grid,
      .audit-grid {
        display: grid;
        gap: 12px;
      }

      .citation-card,
      .audit-card {
        border-radius: 18px;
        padding: 16px;
        background: var(--paper-strong);
      }

      .citation-card strong,
      .audit-card strong {
        display: block;
        margin-bottom: 8px;
        font-size: 15px;
      }

      .citation-card p,
      .audit-card p {
        margin: 0;
        color: var(--muted);
        line-height: 1.75;
      }

      .citation-meta,
      .audit-meta {
        margin-top: 8px;
        color: var(--accent);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.04em;
      }

      details {
        background: rgba(255, 255, 255, 0.74);
        padding: 16px 18px;
      }

      details summary {
        cursor: pointer;
        color: var(--brand);
        font-weight: 800;
      }

      .steps-list {
        display: grid;
        gap: 10px;
        margin-top: 14px;
      }

      .step-item {
        border-radius: 14px;
        background: rgba(245, 240, 232, 0.9);
        padding: 14px;
      }

      .step-item strong {
        display: block;
        margin-bottom: 6px;
      }

      .step-item p {
        margin: 0;
        color: var(--muted);
        line-height: 1.75;
      }

      .footnote {
        margin-top: 18px;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.8;
      }

      @media (max-width: 980px) {
        .hero,
        .layout {
          grid-template-columns: 1fr;
        }
      }

      @media (max-width: 760px) {
        .shell {
          width: min(100vw - 20px, 1240px);
          padding: 16px 0 28px;
        }

        .hero-card,
        .panel,
        .result-card {
          padding: 18px;
        }

        .mode-grid,
        .chip-row {
          grid-template-columns: 1fr;
        }

        .sample-row {
          flex-direction: column;
        }
      }
    </style>
  </head>
  <body>
    <div class="shell">
      <div id="bootstrap-banner" class="banner">正在准备示例法律知识库，请稍候。</div>

      <section class="hero">
        <article class="hero-card">
          <p class="eyebrow">Legal Knowledge Assistant</p>
          <h1>带引用、能保守拒答、支持多 Agent 审核的法律知识助手。</h1>
          <p class="hero-copy">
            这个体验页只保留普通访客真正需要的能力。你只需要输入法律问题，然后选择一种回答模式，
            系统会自动准备示例知识库，并把引用依据、审核说明和回答结果一起展示出来。
          </p>
          <div class="tag-row">
            <span class="tag">Grounded Answer</span>
            <span class="tag">Citation Trace</span>
            <span class="tag">Conservative Refusal</span>
            <span class="tag">Reviewer Agent</span>
            <span class="tag">Voice-ready Workflow</span>
          </div>
        </article>

        <aside class="hero-side">
          <div class="metric">
            <span>产品定位</span>
            <strong>法律知识问答，不是普通聊天机器人。</strong>
          </div>
          <div class="metric">
            <span>风险控制重点</span>
            <strong>证据不足时不强答，优先给出保守、可追溯的结果。</strong>
          </div>
          <div class="metric">
            <span>适用场景</span>
            <strong>法条查询、概念比较、条文依据说明、多 Agent 复核。</strong>
          </div>
        </aside>
      </section>

      <section class="layout">
        <section class="panel">
          <h2>开始体验</h2>
          <p class="panel-note">
            页面加载后会自动准备法律样例资料，所以你可以直接提问。
            这里只保留体验所需的核心动作：选模式、提问题、看结果。
          </p>

          <div class="mode-grid">
            <button type="button" class="mode-button active" data-mode="rag">
              <strong>引用问答</strong>
              <span>优先展示 grounded answer 和 citation，适合先看法条依据。</span>
            </button>
            <button type="button" class="mode-button" data-mode="single">
              <strong>单 Agent 解析</strong>
              <span>展示检索与回答步骤，并串接语音讲解链路。</span>
            </button>
            <button type="button" class="mode-button" data-mode="team">
              <strong>Team Agent 审核</strong>
              <span>在回答之外增加 reviewer 复核，更适合高风险问答场景。</span>
            </button>
          </div>

          <label class="label" for="question-input">输入法律问题</label>
          <textarea
            id="question-input"
            placeholder="例如：请比较抢劫与抢夺的区别，并说明为什么这类回答必须附带引用。"
          ></textarea>

          <div class="sample-row">
            <button type="button" class="sample" id="sample-rag">抢劫与抢夺的区别</button>
            <button type="button" class="sample" id="sample-agent">证据不足时如何保守回答</button>
            <button type="button" class="sample" id="sample-team">多 Agent 如何做审核</button>
          </div>

          <div class="action-row" style="margin-top: 18px;">
            <button type="button" class="primary" id="run-button" disabled>生成回答</button>
          </div>

          <p class="footnote">
            当前体验由 __SERVICE_NAME__ 提供。页面会自动准备示例资料，
            所以你可以直接把注意力放在问题本身、回答质量和引用依据上。
          </p>
        </section>

        <section class="result-stack">
          <section class="result-card">
            <div class="chip-row">
              <div class="metric-chip">
                <span>Current Mode</span>
                <strong id="mode-chip">引用问答</strong>
              </div>
              <div class="metric-chip" id="grounded-chip-wrap">
                <span>Grounded</span>
                <strong id="grounded-chip">待生成</strong>
              </div>
              <div class="metric-chip" id="confidence-chip-wrap">
                <span>Confidence</span>
                <strong id="confidence-chip">待生成</strong>
              </div>
            </div>

            <div id="result-status" class="result-status" style="margin-top: 14px;">
              示例知识库准备完成后，你就可以直接提问。
            </div>

            <h3 class="section-title" style="margin-top: 18px;">综合解答</h3>
            <div id="answer-box" class="empty-box">
              回答生成后会显示在这里。系统会尽量带上引用证据，并在必要时给出更保守的结论。
            </div>
          </section>

          <section class="result-card">
            <h3 class="section-title">引用依据</h3>
            <div id="citations-box" class="citation-grid">
              <div class="citation-card">
                <strong>尚未生成引用</strong>
                <p>当回答完成后，这里会展示命中的法条片段、章节信息和证据摘要。</p>
              </div>
            </div>
          </section>

          <section class="result-card">
            <h3 class="section-title">审核与执行说明</h3>
            <div id="audit-box" class="audit-grid">
              <div class="audit-card">
                <strong>等待结果</strong>
                <p>如果使用 Team Agent，这里会出现 reviewer 的审核结论；如果使用单 Agent，这里会补充语音讲解链路状态。</p>
              </div>
            </div>
          </section>

          <details>
            <summary>查看底层执行链路</summary>
            <div id="steps-box" class="steps-list">
              <div class="step-item">
                <strong>暂无执行步骤</strong>
                <p>当单 Agent 或 Team Agent 返回结果后，这里会补充执行链明细。</p>
              </div>
            </div>
          </details>
        </section>
      </section>
    </div>

    <script>
      const sample = __SAMPLE_JSON__;
      let currentMode = "rag";
      let bootstrapped = false;
      let running = false;

      const modeLabelMap = {
        rag: "引用问答",
        single: "单 Agent 解析",
        team: "Team Agent 审核",
      };

      const elements = {
        banner: document.getElementById("bootstrap-banner"),
        input: document.getElementById("question-input"),
        runButton: document.getElementById("run-button"),
        resultStatus: document.getElementById("result-status"),
        answerBox: document.getElementById("answer-box"),
        citationsBox: document.getElementById("citations-box"),
        auditBox: document.getElementById("audit-box"),
        stepsBox: document.getElementById("steps-box"),
        modeChip: document.getElementById("mode-chip"),
        groundedChip: document.getElementById("grounded-chip"),
        groundedChipWrap: document.getElementById("grounded-chip-wrap"),
        confidenceChip: document.getElementById("confidence-chip"),
        confidenceChipWrap: document.getElementById("confidence-chip-wrap"),
      };

      function setBanner(message, tone) {
        elements.banner.textContent = message;
        elements.banner.className = tone ? `banner ${tone}` : "banner";
      }

      function setResultStatus(message, tone) {
        elements.resultStatus.textContent = message;
        elements.resultStatus.className = tone ? `result-status ${tone}` : "result-status";
      }

      function setRunEnabled(enabled) {
        elements.runButton.disabled = !enabled;
      }

      function updateRunButton() {
        if (running) {
          elements.runButton.textContent = "处理中...";
          setRunEnabled(false);
          return;
        }
        elements.runButton.textContent = "生成回答";
        setRunEnabled(bootstrapped && elements.input.value.trim().length > 0);
      }

      function escapeHtml(value) {
        return String(value)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#39;");
      }

      async function fetchJson(url, options = {}) {
        const response = await fetch(url, options);
        const isJson = (response.headers.get("content-type") || "").includes("application/json");
        const payload = isJson ? await response.json() : await response.text();
        if (!response.ok) {
          const detail = typeof payload === "string" ? payload : payload.detail || JSON.stringify(payload, null, 2);
          throw new Error(detail);
        }
        return payload;
      }

      function applyMode(mode) {
        currentMode = mode;
        document.querySelectorAll("[data-mode]").forEach((button) => {
          button.classList.toggle("active", button.dataset.mode === mode);
        });
        elements.modeChip.textContent = modeLabelMap[mode];
      }

      function fillSample(mode) {
        if (mode === "single") {
          elements.input.value = sample.agent_question || "证据不足时系统应该如何保守回答？";
        } else if (mode === "team") {
          elements.input.value = sample.team_question || "多 Agent 如何做审核？";
        } else {
          elements.input.value = sample.rag_question || "抢劫与抢夺的区别是什么？";
        }
        updateRunButton();
      }

      function renderCitations(citations) {
        if (!Array.isArray(citations) || citations.length === 0) {
          elements.citationsBox.innerHTML = `
            <div class="citation-card">
              <strong>本次没有返回引用</strong>
              <p>如果检索证据不足，系统会优先给出更保守的结果，而不是强行拼接引用。</p>
            </div>
          `;
          return;
        }
        elements.citationsBox.innerHTML = citations
          .map((item) => `
            <article class="citation-card">
              <strong>${escapeHtml(item.section || item.title || "未标注章节")}</strong>
              <p>${escapeHtml(item.snippet || "未返回引用片段。")}</p>
              <div class="citation-meta">${escapeHtml(item.title || "法律知识样本")}${item.score !== undefined ? ` · score=${escapeHtml(item.score)}` : ""}</div>
            </article>
          `)
          .join("");
      }

      function renderAudit(result) {
        const cards = [];
        if (result.review_summary) {
          cards.push(`
            <article class="audit-card">
              <strong>Reviewer Agent 审核结论</strong>
              <p>${escapeHtml(result.review_summary)}</p>
            </article>
          `);
        }
        if (result.voice_job) {
          cards.push(`
            <article class="audit-card">
              <strong>语音讲解链路</strong>
              <p>已生成语音任务，可继续衔接 TTS / A2F 播报。</p>
              <div class="audit-meta">job_id=${escapeHtml(result.voice_job.job_id || "-")} · avatar=${escapeHtml(result.voice_job.avatar_job_id || "-")}</div>
            </article>
          `);
        }
        if (result.question_type || result.refusal_triggered !== undefined) {
          cards.push(`
            <article class="audit-card">
              <strong>回答策略</strong>
              <p>question_type=${escapeHtml(result.question_type || "-")}；refusal_triggered=${escapeHtml(result.refusal_triggered ?? false)}</p>
            </article>
          `);
        }
        if (!cards.length) {
          cards.push(`
            <article class="audit-card">
              <strong>当前模式没有附加说明</strong>
              <p>如果切换到 Team Agent 或 Single Agent，这里会显示审核说明或语音链路状态。</p>
            </article>
          `);
        }
        elements.auditBox.innerHTML = cards.join("");
      }

      function renderSteps(steps) {
        if (!Array.isArray(steps) || steps.length === 0) {
          elements.stepsBox.innerHTML = `
            <div class="step-item">
              <strong>暂无执行步骤</strong>
              <p>当前模式没有返回步骤明细，或本次尚未运行 Agent。</p>
            </div>
          `;
          return;
        }
        elements.stepsBox.innerHTML = steps
          .map((step) => `
            <div class="step-item">
              <strong>${escapeHtml(step.agent || "agent")} · ${escapeHtml(step.action || "unknown")}</strong>
              <p>${escapeHtml(step.observation || step.thought || "没有补充说明。")}</p>
            </div>
          `)
          .join("");
      }

      function normalizeConfidence(value) {
        if (typeof value === "number") {
          return `${Math.round(value * 100)}%`;
        }
        if (!value) {
          return "未返回";
        }
        const map = {
          low: "低",
          medium: "中",
          high: "高",
        };
        return map[value] || String(value);
      }

      function renderResult(result) {
        elements.answerBox.className = "answer-box";
        elements.answerBox.textContent = result.answer || "本次没有生成回答。";
        elements.groundedChip.textContent = result.grounded ? "有依据" : "证据不足";
        elements.groundedChipWrap.className = result.grounded ? "metric-chip ok" : "metric-chip warn";
        elements.confidenceChip.textContent = normalizeConfidence(result.confidence);
        elements.confidenceChipWrap.className = "metric-chip";
        renderCitations(result.citations);
        renderAudit(result);
        renderSteps(result.steps);
      }

      async function bootstrap() {
        setBanner("正在准备示例法律知识库，请稍候。", "");
        try {
          await fetchJson("/showcase/bootstrap", { method: "POST" });
          bootstrapped = true;
          setBanner("示例知识库已就绪，现在可以直接提问。", "ready");
          setResultStatus("请选择一种模式并输入问题，然后点击“生成回答”。", "ok");
        } catch (error) {
          bootstrapped = false;
          setBanner(`示例知识库准备失败：${error.message}`, "error");
          setResultStatus("知识库尚未准备完成，请刷新页面后重试。", "warn");
        } finally {
          updateRunButton();
        }
      }

      async function runQuery() {
        const question = elements.input.value.trim();
        if (!bootstrapped || running || !question) {
          updateRunButton();
          return;
        }

        const tenantId = sample.tenant_id || "demo";
        const configs = {
          rag: {
            label: "引用问答",
            url: "/rag/query",
            payload: { question, tenant_id: tenantId, top_k: 4 },
          },
          single: {
            label: "单 Agent 解析",
            url: "/agent/run",
            payload: { query: question, tenant_id: tenantId, speak_response: true },
          },
          team: {
            label: "Team Agent 审核",
            url: "/agent/team/run",
            payload: { query: question, tenant_id: tenantId },
          },
        };

        const config = configs[currentMode];
        running = true;
        updateRunButton();
        setResultStatus(`${config.label} 正在生成结果，请稍候。`, "");

        try {
          const result = await fetchJson(config.url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(config.payload),
          });
          renderResult(result);
          setResultStatus(
            `${config.label} 已完成：grounded=${result.grounded}，citations=${(result.citations || []).length}`,
            "ok"
          );
        } catch (error) {
          setResultStatus(`${config.label} 失败：${error.message}`, "warn");
        } finally {
          running = false;
          updateRunButton();
        }
      }

      document.querySelectorAll("[data-mode]").forEach((button) => {
        button.addEventListener("click", () => applyMode(button.dataset.mode));
      });
      document.getElementById("sample-rag").addEventListener("click", () => fillSample("rag"));
      document.getElementById("sample-agent").addEventListener("click", () => fillSample("single"));
      document.getElementById("sample-team").addEventListener("click", () => fillSample("team"));
      document.getElementById("run-button").addEventListener("click", runQuery);
      elements.input.addEventListener("input", updateRunButton);

      applyMode("rag");
      fillSample("rag");
      bootstrap();
    </script>
  </body>
</html>
"""
