from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEGAL_SAMPLE_PATH = ROOT / "examples" / "legal" / "legal_assistant_handbook.md"

DEFAULT_SAMPLE = {
    "title": "刑事法律知识助手示例手册",
    "source": "examples/legal/legal_assistant_handbook.md",
    "modality": "markdown",
    "tenant_id": "demo",
    "content": "",
    "rag_question": "请比较抢劫与抢夺的区别，并说明系统为什么要强制带引用回答。",
    "agent_question": "如果证据不足，法律助手应该如何给出保守回答？顺便说明语音讲解链路怎么接入。",
    "team_question": "请从多 Agent 视角解释这个平台如何完成检索、审核和讲解。",
}


def load_demo_sample() -> dict[str, str]:
    sample = dict(DEFAULT_SAMPLE)
    if LEGAL_SAMPLE_PATH.exists():
        sample["content"] = LEGAL_SAMPLE_PATH.read_text(encoding="utf-8")
    return sample


def render_demo_page(service_name: str) -> str:
    sample = load_demo_sample()
    sample_json = json.dumps(sample, ensure_ascii=False)
    safe_service_name = html.escape(service_name)
    return HTML_TEMPLATE.replace("__SERVICE_NAME__", safe_service_name).replace("__SAMPLE_JSON__", sample_json)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>__SERVICE_NAME__ · Local Demo</title>
    <style>
      :root {
        --bg: #f4efe6;
        --bg-accent: #e6dcc9;
        --panel: rgba(255, 251, 244, 0.88);
        --panel-strong: rgba(255, 248, 238, 0.96);
        --ink: #1f1915;
        --muted: #6b5b51;
        --line: rgba(83, 60, 43, 0.18);
        --brand: #7a2c16;
        --brand-soft: rgba(122, 44, 22, 0.1);
        --ok: #1b6f53;
        --warn: #8d5b12;
        --shadow: 0 18px 40px rgba(70, 49, 36, 0.12);
        --radius-lg: 24px;
        --radius-md: 18px;
        --radius-sm: 12px;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(122, 44, 22, 0.08), transparent 30%),
          radial-gradient(circle at top right, rgba(27, 111, 83, 0.1), transparent 24%),
          linear-gradient(160deg, var(--bg) 0%, #efe7da 38%, #f8f4ed 100%);
        font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
      }

      .shell {
        width: min(1480px, calc(100vw - 32px));
        margin: 0 auto;
        padding: 28px 0 40px;
      }

      .hero {
        display: grid;
        grid-template-columns: 1.6fr 1fr;
        gap: 20px;
        margin-bottom: 20px;
      }

      .hero-copy,
      .hero-meta,
      .card {
        border: 1px solid var(--line);
        border-radius: var(--radius-lg);
        background: var(--panel);
        backdrop-filter: blur(8px);
        box-shadow: var(--shadow);
      }

      .hero-copy {
        padding: 28px;
        position: relative;
        overflow: hidden;
      }

      .hero-copy::after {
        content: "";
        position: absolute;
        inset: auto -10% -35% auto;
        width: 220px;
        height: 220px;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(122, 44, 22, 0.18), transparent 70%);
      }

      .eyebrow {
        margin: 0 0 10px;
        color: var(--brand);
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
      }

      h1,
      h2,
      h3 {
        margin: 0;
        font-family: "SimSun", "Songti SC", "Noto Serif SC", serif;
      }

      h1 {
        font-size: clamp(28px, 4vw, 42px);
        line-height: 1.1;
        margin-bottom: 14px;
      }

      .hero-copy p:last-child {
        margin: 0;
        max-width: 60ch;
        color: var(--muted);
        line-height: 1.75;
      }

      .hero-meta {
        padding: 22px;
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
        align-content: start;
      }

      .meta-tile {
        padding: 16px 18px;
        border-radius: var(--radius-md);
        background: var(--panel-strong);
        border: 1px solid rgba(83, 60, 43, 0.12);
      }

      .meta-label {
        display: block;
        margin-bottom: 10px;
        color: var(--muted);
        font-size: 13px;
      }

      .meta-value {
        font-size: 16px;
        font-weight: 700;
        line-height: 1.35;
        word-break: break-word;
      }

      .layout {
        display: grid;
        grid-template-columns: 1.08fr 0.92fr 1fr;
        gap: 20px;
      }

      .card {
        padding: 22px;
      }

      .card h2 {
        font-size: 22px;
        margin-bottom: 8px;
      }

      .section-note {
        margin: 0 0 18px;
        color: var(--muted);
        line-height: 1.6;
      }

      .stack {
        display: grid;
        gap: 14px;
      }

      label {
        display: grid;
        gap: 8px;
        font-size: 14px;
        font-weight: 600;
      }

      input,
      textarea,
      select {
        width: 100%;
        border: 1px solid rgba(83, 60, 43, 0.16);
        border-radius: var(--radius-sm);
        background: rgba(255, 255, 255, 0.76);
        color: var(--ink);
        font: inherit;
        padding: 12px 14px;
        outline: none;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
      }

      input:focus,
      textarea:focus,
      select:focus {
        border-color: rgba(122, 44, 22, 0.4);
        box-shadow: 0 0 0 4px rgba(122, 44, 22, 0.08);
      }

      textarea {
        resize: vertical;
        min-height: 120px;
        line-height: 1.65;
      }

      .doc-editor {
        min-height: 360px;
      }

      .button-row,
      .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      button {
        border: 0;
        border-radius: 999px;
        padding: 11px 16px;
        font: inherit;
        font-weight: 700;
        cursor: pointer;
        transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
      }

      button:hover {
        transform: translateY(-1px);
      }

      button:disabled {
        cursor: wait;
        opacity: 0.66;
        transform: none;
      }

      .primary {
        color: #fffaf5;
        background: linear-gradient(135deg, #7a2c16, #9b4523);
        box-shadow: 0 10px 18px rgba(122, 44, 22, 0.22);
      }

      .secondary {
        color: var(--ink);
        background: rgba(255, 255, 255, 0.88);
        border: 1px solid rgba(83, 60, 43, 0.14);
      }

      .ghost {
        color: var(--brand);
        background: var(--brand-soft);
      }

      .status {
        min-height: 54px;
        padding: 14px 16px;
        border-radius: var(--radius-md);
        background: rgba(255, 255, 255, 0.64);
        color: var(--muted);
        border: 1px dashed rgba(83, 60, 43, 0.18);
        line-height: 1.55;
      }

      .status.ok {
        color: var(--ok);
        border-style: solid;
        border-color: rgba(27, 111, 83, 0.22);
        background: rgba(27, 111, 83, 0.08);
      }

      .status.warn {
        color: var(--warn);
        border-style: solid;
        border-color: rgba(141, 91, 18, 0.22);
        background: rgba(141, 91, 18, 0.08);
      }

      .chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid rgba(83, 60, 43, 0.12);
        font-size: 13px;
        font-weight: 700;
      }

      .chip strong {
        color: var(--brand);
      }

      .quick-prompts {
        display: grid;
        gap: 8px;
      }

      .quick-prompts button {
        text-align: left;
        border-radius: var(--radius-sm);
      }

      .output {
        display: grid;
        gap: 18px;
      }

      .answer-box,
      .json-box,
      .list-box {
        border-radius: var(--radius-md);
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid rgba(83, 60, 43, 0.12);
        padding: 16px;
      }

      .answer-box {
        min-height: 180px;
        white-space: pre-wrap;
        line-height: 1.75;
      }

      .json-box {
        margin: 0;
        overflow: auto;
        max-height: 320px;
        font-size: 12px;
        line-height: 1.65;
      }

      ul,
      ol {
        margin: 0;
        padding-left: 18px;
      }

      li {
        margin-bottom: 10px;
        line-height: 1.65;
      }

      .ops-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }

      .ops-tile {
        padding: 14px 16px;
        border-radius: var(--radius-md);
        background: var(--panel-strong);
        border: 1px solid rgba(83, 60, 43, 0.1);
      }

      .ops-tile span {
        display: block;
        margin-bottom: 8px;
        font-size: 13px;
        color: var(--muted);
      }

      .ops-tile strong {
        font-size: 24px;
      }

      details summary {
        cursor: pointer;
        font-weight: 700;
        color: var(--brand);
      }

      .footer-note {
        margin-top: 18px;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.7;
      }

      @media (max-width: 1200px) {
        .layout,
        .hero {
          grid-template-columns: 1fr;
        }
      }

      @media (max-width: 720px) {
        .shell {
          width: min(100vw - 20px, 1480px);
          padding-top: 18px;
        }

        .card,
        .hero-copy,
        .hero-meta {
          padding: 18px;
        }

        .hero-meta,
        .ops-grid {
          grid-template-columns: 1fr;
        }
      }
    </style>
  </head>
  <body>
    <div class="shell">
      <section class="hero">
        <div class="hero-copy">
          <p class="eyebrow">Local Demo Panel</p>
          <h1>法律知识问答 Agent 平台</h1>
          <p>
            这个页面把本地调试最常用的几步收在一起：装载法律示例文档、跑 grounded RAG、
            切换单 Agent / 团队 Agent、查看 citations、review 结果、recent runs 和 ops 快照。
          </p>
        </div>
        <div class="hero-meta">
          <div class="meta-tile">
            <span class="meta-label">Service</span>
            <div class="meta-value" id="service-name">__SERVICE_NAME__</div>
          </div>
          <div class="meta-tile">
            <span class="meta-label">Health</span>
            <div class="meta-value" id="health-status">等待检查</div>
          </div>
          <div class="meta-tile">
            <span class="meta-label">Knowledge Base</span>
            <div class="meta-value" id="health-docs">0 documents / 0 vectors</div>
          </div>
          <div class="meta-tile">
            <span class="meta-label">Runtime Backends</span>
            <div class="meta-value" id="health-backends">stub / hash / memory</div>
          </div>
        </div>
      </section>

      <section class="layout">
        <section class="card">
          <h2>文档准备</h2>
          <p class="section-note">先把法律样例装进本地知识库，再开始问答。这个页面默认使用本仓库里的法律示例手册。</p>
          <div class="stack">
            <div class="button-row">
              <button class="secondary" id="load-sample">载入法律样例</button>
              <button class="ghost" id="clear-doc">清空文档区</button>
              <button class="primary" id="ingest-doc">写入知识库</button>
            </div>
            <label>
              API Key（可选）
              <input id="api-key" placeholder="本地默认留空；启用鉴权后再填" />
            </label>
            <label>
              Tenant ID
              <input id="tenant-id" value="demo" />
            </label>
            <label>
              文档标题
              <input id="doc-title" />
            </label>
            <label>
              来源标识
              <input id="doc-source" />
            </label>
            <label>
              文档内容
              <textarea class="doc-editor" id="doc-content"></textarea>
            </label>
            <div class="status" id="doc-status">还没有入库。建议先点“载入法律样例”，再执行“写入知识库”。</div>
          </div>
        </section>

        <section class="card">
          <h2>问答与 Agent</h2>
          <p class="section-note">同一份知识库可以直接测 RAG，也可以切到 single agent 或 team agent，看 grounded、review 和语音链路表现。</p>
          <div class="stack">
            <div class="chip-row">
              <span class="chip">Mode <strong id="mode-chip">待选择</strong></span>
              <span class="chip">Grounded <strong id="grounded-chip">-</strong></span>
              <span class="chip">Confidence <strong id="confidence-chip">-</strong></span>
            </div>
            <label>
              问题
              <textarea id="question-input" rows="8"></textarea>
            </label>
            <label>
              RAG Top-K
              <select id="top-k">
                <option value="3">3</option>
                <option value="4" selected>4</option>
                <option value="5">5</option>
              </select>
            </label>
            <label>
              <input type="checkbox" id="speak-response" />
              单 Agent 时同时触发语音讲解链路
            </label>
            <div class="button-row">
              <button class="secondary" id="run-rag">运行 RAG</button>
              <button class="primary" id="run-agent">运行 Single Agent</button>
              <button class="ghost" id="run-team">运行 Team Agent</button>
            </div>
            <div class="quick-prompts">
              <button class="secondary" data-prompt="rag">填入法律区分问题</button>
              <button class="secondary" data-prompt="agent">填入保守拒答问题</button>
              <button class="secondary" data-prompt="team">填入多 Agent 审核问题</button>
            </div>
            <div class="status" id="query-status">选择一个问题后开始运行。每次运行都会刷新 recent runs 和 ops 概览。</div>
          </div>
        </section>

        <section class="card">
          <h2>结果看板</h2>
          <p class="section-note">这里集中看 answer、citations、步骤追踪、review 结论和原始返回。</p>
          <div class="output">
            <div class="answer-box" id="answer-box">运行结果会显示在这里。</div>
            <div class="list-box">
              <h3>Reviewer / Voice</h3>
              <ul id="review-list">
                <li>Team Agent 的审核结论和 Single Agent 的语音任务会显示在这里。</li>
              </ul>
            </div>
            <div class="list-box">
              <h3>Citations</h3>
              <ul id="citations-list">
                <li>还没有 citations。</li>
              </ul>
            </div>
            <div class="list-box">
              <h3>Agent Steps</h3>
              <ol id="steps-list">
                <li>还没有执行记录。</li>
              </ol>
            </div>
            <details>
              <summary>查看原始 JSON</summary>
              <pre class="json-box" id="raw-json">{}</pre>
            </details>
          </div>
        </section>
      </section>

      <section class="layout" style="margin-top: 20px; grid-template-columns: 1.15fr 0.85fr 1fr;">
        <section class="card">
          <h2>Recent Runs</h2>
          <p class="section-note">每次执行后，这里会展示最近的工作流记录，方便你确认 single / team 模式和 grounding 表现。</p>
          <div class="button-row" style="margin-bottom: 14px;">
            <button class="secondary" id="refresh-runs">刷新 runs</button>
          </div>
          <div class="list-box">
            <ul id="runs-list">
              <li>还没有运行记录。</li>
            </ul>
          </div>
        </section>

        <section class="card">
          <h2>Ops Overview</h2>
          <p class="section-note">这个区块对应 /ops/overview，可以快速看 HTTP 请求量、pipeline 次数和最近请求。</p>
          <div class="button-row" style="margin-bottom: 14px;">
            <button class="secondary" id="refresh-ops">刷新 ops</button>
          </div>
          <div class="ops-grid">
            <div class="ops-tile">
              <span>HTTP Requests</span>
              <strong id="ops-http">0</strong>
            </div>
            <div class="ops-tile">
              <span>Pipeline Runs</span>
              <strong id="ops-pipeline">0</strong>
            </div>
            <div class="ops-tile">
              <span>Uptime (s)</span>
              <strong id="ops-uptime">0</strong>
            </div>
            <div class="ops-tile">
              <span>Recent Request</span>
              <strong id="ops-recent">-</strong>
            </div>
          </div>
          <details style="margin-top: 16px;">
            <summary>查看 ops JSON</summary>
            <pre class="json-box" id="ops-json">{}</pre>
          </details>
        </section>

        <section class="card">
          <h2>本地调试建议</h2>
          <p class="section-note">这页是给你本地测试用的，不依赖外部前端框架，也不会改动线上部署方式。</p>
          <div class="list-box">
            <ul>
              <li>先点“载入法律样例”，再“写入知识库”，确认 chunk_count 正常返回。</li>
              <li>RAG 模式重点看 grounded、citations 和 confidence。</li>
              <li>Single Agent 模式重点看 steps 和 voice_job。</li>
              <li>Team Agent 模式重点看 reviewer summary 和 recent runs。</li>
              <li>如果启用了 API 鉴权，只要在左侧填上 API Key，这个页面也能继续调用。</li>
            </ul>
          </div>
          <p class="footer-note">
            你可以把这个页面当成后端调试台，而不是正式产品前端。等你本地满意后，我们再决定要不要把它整理成公开版本。
          </p>
        </section>
      </section>
    </div>

    <script>
      const legalSample = __SAMPLE_JSON__;

      const els = {
        apiKey: document.getElementById("api-key"),
        tenantId: document.getElementById("tenant-id"),
        docTitle: document.getElementById("doc-title"),
        docSource: document.getElementById("doc-source"),
        docContent: document.getElementById("doc-content"),
        docStatus: document.getElementById("doc-status"),
        questionInput: document.getElementById("question-input"),
        speakResponse: document.getElementById("speak-response"),
        topK: document.getElementById("top-k"),
        queryStatus: document.getElementById("query-status"),
        answerBox: document.getElementById("answer-box"),
        citationsList: document.getElementById("citations-list"),
        stepsList: document.getElementById("steps-list"),
        reviewList: document.getElementById("review-list"),
        rawJson: document.getElementById("raw-json"),
        runsList: document.getElementById("runs-list"),
        opsJson: document.getElementById("ops-json"),
        healthStatus: document.getElementById("health-status"),
        healthDocs: document.getElementById("health-docs"),
        healthBackends: document.getElementById("health-backends"),
        serviceName: document.getElementById("service-name"),
        modeChip: document.getElementById("mode-chip"),
        groundedChip: document.getElementById("grounded-chip"),
        confidenceChip: document.getElementById("confidence-chip"),
        opsHttp: document.getElementById("ops-http"),
        opsPipeline: document.getElementById("ops-pipeline"),
        opsUptime: document.getElementById("ops-uptime"),
        opsRecent: document.getElementById("ops-recent"),
      };

      function apiHeaders() {
        const headers = { "Content-Type": "application/json" };
        const apiKey = els.apiKey.value.trim();
        if (apiKey) {
          headers["X-API-Key"] = apiKey;
        }
        return headers;
      }

      function setStatus(target, message, tone = "") {
        target.textContent = message;
        target.className = tone ? `status ${tone}` : "status";
      }

      async function fetchJson(url, options = {}) {
        const response = await fetch(url, options);
        const contentType = response.headers.get("content-type") || "";
        const payload = contentType.includes("application/json")
          ? await response.json()
          : await response.text();
        if (!response.ok) {
          const detail =
            typeof payload === "string"
              ? payload
              : payload.detail || JSON.stringify(payload, null, 2);
          throw new Error(detail || `Request failed: ${response.status}`);
        }
        return payload;
      }

      function applySample(kind = "rag") {
        els.docTitle.value = legalSample.title;
        els.docSource.value = legalSample.source;
        els.docContent.value = legalSample.content;
        els.tenantId.value = legalSample.tenant_id;
        if (kind === "agent") {
          els.questionInput.value = legalSample.agent_question;
        } else if (kind === "team") {
          els.questionInput.value = legalSample.team_question;
        } else {
          els.questionInput.value = legalSample.rag_question;
        }
      }

      function renderHealth(data) {
        els.serviceName.textContent = data.service || "__SERVICE_NAME__";
        els.healthStatus.textContent = data.status || "unknown";
        els.healthDocs.textContent = `${data.documents ?? 0} documents / ${data.vectors ?? 0} vectors`;
        els.healthBackends.textContent = `${data.model_provider || "-"} / ${data.embedding_provider || "-"} / ${data.vector_store_backend || "-"}`;
      }

      function renderResult(data, modeLabel) {
        els.answerBox.textContent = data.answer || "这次没有返回 answer。";
        els.modeChip.textContent = modeLabel;
        els.groundedChip.textContent = data.grounded ? "true" : "false";
        els.confidenceChip.textContent = data.confidence || "-";
        els.rawJson.textContent = JSON.stringify(data, null, 2);

        const citations = Array.isArray(data.citations) ? data.citations : [];
        els.citationsList.innerHTML = citations.length
          ? citations
              .map(
                (item) =>
                  `<li><strong>${item.section || "未标注章节"}</strong><br />score=${item.score ?? "-"}<br />${item.snippet || ""}</li>`
              )
              .join("")
          : "<li>这次没有 citations。</li>";

        const steps = Array.isArray(data.steps) ? data.steps : [];
        els.stepsList.innerHTML = steps.length
          ? steps
              .map(
                (step) =>
                  `<li><strong>${step.agent}</strong> · ${step.action}<br />${step.observation || step.thought || "无详细记录"}</li>`
              )
              .join("")
          : "<li>当前模式没有 steps 输出。</li>";

        const reviewItems = [];
        if (data.review_summary) {
          reviewItems.push(`<li><strong>Reviewer</strong><br />${data.review_summary}</li>`);
        }
        if (data.voice_job) {
          reviewItems.push(
            `<li><strong>Voice Job</strong><br />job_id=${data.voice_job.job_id}<br />avatar=${data.voice_job.avatar_job_id || "-"}</li>`
          );
        }
        if (!reviewItems.length) {
          reviewItems.push("<li>当前结果没有 reviewer summary 或 voice job。</li>");
        }
        els.reviewList.innerHTML = reviewItems.join("");
      }

      function renderRuns(items) {
        els.runsList.innerHTML = Array.isArray(items) && items.length
          ? items
              .map(
                (run) =>
                  `<li><strong>${run.workflow}</strong> · ${run.agent_mode} · grounded=${run.grounded}<br />${run.query}<br />citations=${run.citation_count} · ${run.created_at}</li>`
              )
              .join("")
          : "<li>还没有运行记录。</li>";
      }

      function renderOps(data) {
        els.opsJson.textContent = JSON.stringify(data, null, 2);
        els.opsHttp.textContent = String(data.http?.total_requests ?? 0);
        els.opsPipeline.textContent = String(data.pipelines?.total_runs ?? 0);
        els.opsUptime.textContent = String(data.uptime_seconds ?? 0);
        const recent = Array.isArray(data.http?.recent_requests) && data.http.recent_requests.length
          ? data.http.recent_requests[0]
          : null;
        els.opsRecent.textContent = recent ? `${recent.method} ${recent.path}` : "-";
      }

      async function refreshHealth() {
        const data = await fetchJson("/health");
        renderHealth(data);
      }

      async function ingestDocument() {
        const payload = {
          title: els.docTitle.value.trim(),
          content: els.docContent.value,
          source: els.docSource.value.trim() || legalSample.source,
          modality: "markdown",
          tenant_id: els.tenantId.value.trim() || "demo",
        };
        if (!payload.title || !payload.content.trim()) {
          setStatus(els.docStatus, "标题和文档内容不能为空。", "warn");
          return;
        }
        setStatus(els.docStatus, "正在写入知识库...", "");
        try {
          const result = await fetchJson("/documents/ingest", {
            method: "POST",
            headers: apiHeaders(),
            body: JSON.stringify(payload),
          });
          setStatus(
            els.docStatus,
            `入库成功：document_id=${result.document.document_id}，chunk_count=${result.chunk_count}`,
            "ok"
          );
          await refreshHealth();
        } catch (error) {
          setStatus(els.docStatus, `入库失败：${error.message}`, "warn");
        }
      }

      async function runWorkflow(mode) {
        const tenantId = els.tenantId.value.trim() || "demo";
        const question = els.questionInput.value.trim();
        if (!question) {
          setStatus(els.queryStatus, "请先输入问题。", "warn");
          return;
        }
        const config = {
          rag: {
            label: "RAG",
            url: "/rag/query",
            payload: {
              question,
              top_k: Number(els.topK.value || "4"),
              tenant_id: tenantId,
            },
          },
          single: {
            label: "Single Agent",
            url: "/agent/run",
            payload: {
              query: question,
              tenant_id: tenantId,
              speak_response: els.speakResponse.checked,
            },
          },
          team: {
            label: "Team Agent",
            url: "/agent/team/run",
            payload: {
              query: question,
              tenant_id: tenantId,
            },
          },
        }[mode];

        setStatus(els.queryStatus, `${config.label} 正在运行...`, "");
        try {
          const result = await fetchJson(config.url, {
            method: "POST",
            headers: apiHeaders(),
            body: JSON.stringify(config.payload),
          });
          renderResult(result, config.label);
          setStatus(
            els.queryStatus,
            `${config.label} 运行完成：grounded=${result.grounded}，citations=${(result.citations || []).length}`,
            "ok"
          );
          await Promise.all([refreshRuns(), refreshOps(), refreshHealth()]);
        } catch (error) {
          setStatus(els.queryStatus, `${config.label} 运行失败：${error.message}`, "warn");
        }
      }

      async function refreshRuns() {
        try {
          const tenantId = els.tenantId.value.trim() || "demo";
          const runs = await fetchJson(`/runs?tenant_id=${encodeURIComponent(tenantId)}`);
          renderRuns(runs);
        } catch (error) {
          els.runsList.innerHTML = `<li>读取 runs 失败：${error.message}</li>`;
        }
      }

      async function refreshOps() {
        try {
          const data = await fetchJson("/ops/overview", {
            headers: apiHeaders(),
          });
          renderOps(data);
        } catch (error) {
          els.opsJson.textContent = `读取 ops 失败：${error.message}`;
        }
      }

      document.getElementById("load-sample").addEventListener("click", () => {
        applySample("rag");
        setStatus(els.docStatus, "法律样例已经载入，可以直接入库。", "ok");
      });

      document.getElementById("clear-doc").addEventListener("click", () => {
        els.docTitle.value = "";
        els.docSource.value = legalSample.source;
        els.docContent.value = "";
        setStatus(els.docStatus, "文档区已清空。", "");
      });

      document.getElementById("ingest-doc").addEventListener("click", ingestDocument);
      document.getElementById("run-rag").addEventListener("click", () => runWorkflow("rag"));
      document.getElementById("run-agent").addEventListener("click", () => runWorkflow("single"));
      document.getElementById("run-team").addEventListener("click", () => runWorkflow("team"));
      document.getElementById("refresh-runs").addEventListener("click", refreshRuns);
      document.getElementById("refresh-ops").addEventListener("click", refreshOps);

      document.querySelectorAll("[data-prompt]").forEach((button) => {
        button.addEventListener("click", () => applySample(button.dataset.prompt));
      });

      applySample("rag");
      refreshHealth();
      refreshRuns();
      refreshOps();
    </script>
  </body>
</html>
"""
