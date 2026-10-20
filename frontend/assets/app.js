/* Kaggle Solutions vs Datasets — frontend logic.
 *
 * The site is fully static: every page fetches data/dashboard.json, which
 * `python -m engine report` (and the daily GitHub Actions cycle) regenerates.
 * No build step, no framework — serve the frontend/ folder through any static
 * server; fetch() does not work from file://.
 */

"use strict";

const PAGE = document.body.dataset.page || "index";

/* ---------- primitives ------------------------------------------------------- */

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function fmt(value, digits = 5) {
  if (value === null || value === undefined || value === "") return "—";
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(digits) : "—";
}

function fmtPct(value) {
  const n = Number(value);
  return Number.isFinite(n) ? `${n.toFixed(1)}%` : "—";
}

/* Keep the raw ISO value in datetime= so timestamps stay machine-readable. */
function when(value) {
  if (!value) return "—";
  return `<time datetime="${esc(value)}">${esc(value)}</time>`;
}

function ageLabel(iso) {
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return "";
  const s = Math.max(0, (Date.now() - t) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

/* The cycle regenerates every 24h; older than that means a run was missed. */
function freshness(iso) {
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return null;
  const stale = Date.now() - t > 25 * 3600 * 1000;
  return { cls: stale ? "stale" : "fresh", text: ageLabel(iso) };
}

const CHIP_CLASS = { pass: "pass", fail: "fail", warn: "warn", "n/a": "na", na: "na" };

function chip(status) {
  const key = String(status ?? "").toLowerCase();
  return `<span class="chip ${CHIP_CLASS[key] || "info"}">${esc(status)}</span>`;
}

function gateChip(comp) {
  const verdict = gateVerdict(comp);
  if (verdict === "pass") return '<span class="chip pass">gate reached</span>';
  if (verdict === "fail") return '<span class="chip fail">gate not reached</span>';
  if (comp.target_score != null) return '<span class="chip na">gate pending</span>';
  return '<span class="chip na">no gate set</span>';
}

const STATUS_CLASS = {
  solved: "pass",
  in_progress: "warn",
  registered: "info",
  scaffolded: "info",
  dry_run: "warn",
  blocked: "fail",
  failed: "fail",
};

function statusChip(status) {
  const key = String(status ?? "").toLowerCase();
  return `<span class="chip ${STATUS_CLASS[key] || "na"}">${esc(status || "unknown")}</span>`;
}

/* Rules must sort R1..R13 — a plain localeCompare puts R10 before R2. */
function ruleRank(rule) {
  const n = Number.parseInt(String(rule ?? "").replace(/[^0-9]/g, ""), 10);
  return Number.isFinite(n) ? n : Number.MAX_SAFE_INTEGER;
}

function ruleOrder(checks) {
  return [...(checks || [])].sort((a, b) =>
    ruleRank(a.rule) - ruleRank(b.rule) ||
    String(a.rule ?? "").localeCompare(String(b.rule ?? "")));
}

function mount(id, html) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = html;
}

const SKELETON = `
  <div class="state skeleton" aria-hidden="true">
    <span class="sk-line w-75"></span>
    <span class="sk-line w-45"></span>
    <span class="sk-line w-60"></span>
  </div>`;

/* ---------- score-gate maths (R5) -------------------------------------------- */

/* Does the measured OOF score satisfy the gate? The measured numbers are the
 * authority (R4); the engine's `reached` flag is the fallback for runs where
 * cv/target are not both present. */
function gateVerdict(comp) {
  if (comp.cv_mean != null && comp.target_score != null) {
    const cv = Number(comp.cv_mean);
    const target = Number(comp.target_score);
    if (Number.isFinite(cv) && Number.isFinite(target)) {
      const higher = comp.higher_is_better !== false;
      return (higher ? cv >= target : cv <= target) ? "pass" : "fail";
    }
  }
  if (comp.reached === true) return "pass";
  if (comp.reached === false) return "fail";
  return null;
}

/* R5: a gap beyond 2x the CV std means the split is unrepresentative. */
function gapLooksLarge(comp) {
  if (comp.gap == null || comp.cv_std == null) return false;
  const gap = Number(comp.gap);
  const std = Number(comp.cv_std);
  return Number.isFinite(gap) && Number.isFinite(std) && Math.abs(gap) > 2 * std;
}

/* Attainment toward the target, in percent (100% = gate met). Clamped for the
 * meter, unclamped for the label so overshooting scores still read as >100%. */
function gateAttainment(comp) {
  if (comp.cv_mean == null || comp.target_score == null) return null;
  const cv = Number(comp.cv_mean);
  const target = Number(comp.target_score);
  if (!Number.isFinite(cv) || !Number.isFinite(target) || target === 0) return null;
  const higher = comp.higher_is_better !== false;
  const raw = (higher ? cv / target : target / cv) * 100;
  if (!Number.isFinite(raw)) return null;
  return { raw, clamped: Math.max(0, Math.min(100, raw)), verdict: gateVerdict(comp) };
}

/* ---------- shared header/footer ---------------------------------------------- */

/* Mark the current page before the fetch, so navigation still works when the
 * dashboard cannot be loaded. */
function markActiveNav() {
  document.querySelectorAll("nav.site a").forEach((a) => {
    if (a.dataset.nav === PAGE) {
      a.classList.add("active");
      a.setAttribute("aria-current", "page");
    }
  });
}

function hydrateChrome(data) {
  const gen = data.generated_at;
  const fresh = freshness(gen);
  mount("head-meta",
    `rulebook v${esc(data.rules_version ?? "—")}` +
    (gen ? ` · generated ${esc(gen)}` : "") +
    (fresh ? ` · <span class="freshness ${fresh.cls}" title="dashboard generated ${esc(gen)}">${esc(fresh.text)}</span>` : ""));
  mount("foot-generated",
    (gen
      ? `dashboard generated <time datetime="${esc(gen)}">${esc(gen)}</time> (${esc(ageLabel(gen))})`
      : "dashboard generation time unknown") +
    ` by <code>python -m engine report</code>`);
  const repo = data.repo_url || "#";
  document.querySelectorAll("[data-repo-link]").forEach((a) => {
    a.href = repo;
  });
}

/* ---------- component: repo tree ------------------------------------------------ */

/* The tree ships as plain <pre> text (readable without JS); this colours the
 * directory paths, file paths and "<-" notes without touching the markup. */
function decorateTree() {
  const pre = document.getElementById("repo-tree");
  if (!pre) return;
  const raw = pre.textContent.replace(/\s+$/, "");
  if (!raw) return;
  pre.innerHTML = raw.split("\n").map((line) => {
    const cut = line.indexOf("<-");
    const left = cut === -1 ? line : line.slice(0, cut);
    const note = cut === -1 ? "" : line.slice(cut);
    const isDir = /\/\s*$/.test(left);
    const leftHtml = isDir
      ? `<span class="t-dir">${esc(left)}</span>`
      : `<span class="t-path">${esc(left)}</span>`;
    return leftHtml + (note ? `<span class="t-note">${esc(note)}</span>` : "");
  }).join("\n") + "\n";
}

/* ---------- page: overview -------------------------------------------------------- */

function renderIndex(data) {
  const stats = data.stats || {};
  const engine = data.engine || {};
  decorateTree();

  const stageStats = stats.stages || {};
  const cards = [
    ["Competitions tracked", stats.competitions ?? 0, `${stats.tracked_on_disk ?? 0} folder(s) on disk`, ""],
    ["Gate reached", stats.gate_reached ?? 0, `${stats.gate_defined ?? 0} with a score gate defined`, (stats.gate_reached ?? 0) > 0 ? "pass" : ""],
    ["Runs recorded", stats.runs ?? 0, "scout / code / train attempts", (stats.runs ?? 0) > 0 ? "info" : ""],
    ["Solved", stats.solved ?? 0, "marked solved by the score gate", (stats.solved ?? 0) > 0 ? "pass" : ""],
    ["Data landed", stageStats.datasets ?? 0, "kaggle datasets extracted (checkpoint 1)", (stageStats.datasets ?? 0) > 0 ? "pass" : ""],
    ["Submissions", stageStats.submitted ?? 0, "logged by the engine (R9)", (stageStats.submitted ?? 0) > 0 ? "pass" : ""],
  ];
  mount("stats", cards.map(([label, value, sub, tone]) => `
    <div class="card">
      <div class="label">${esc(label)}</div>
      <div class="value${tone ? ` tone-${tone}` : ""}">${esc(value)}</div>
      <div class="sub">${esc(sub)}</div>
    </div>`).join(""));

  mount("engine-config", `
    <div class="kv">
      <span class="k">max coder attempts / cycle</span><span class="v">${esc(engine.max_attempts ?? "—")}</span>
      <span class="k">notebook timeout</span><span class="v">${engine.notebook_timeout != null ? esc(engine.notebook_timeout) + "s" : "—"}</span>
      <span class="k">coder model</span><span class="v">${esc(engine.opencode_model ?? "—")}</span>
      <span class="k">coder agent</span><span class="v">${esc(engine.opencode_agent ?? "—")}</span>
      <span class="k">kaggle auth ready</span><span class="v">${engine.kaggle_auth_ready ? chip("pass") + " ready" : chip("fail") + " missing credentials"}</span>
      <span class="k">submissions enabled</span><span class="v">${engine.submit_enabled ? chip("warn") + " enabled" : chip("na") + " disabled (R9)"}</span>
      <span class="k">vercel sync</span><span class="v">${engine.vercel_sync ? chip("info") + " configured" : chip("na") + " not configured"}</span>
    </div>`);

  mount("pipeline", (data.pipeline || []).map((stage) => `
    <li><span class="stage">${esc(stage.stage)}</span>
        <div class="desc">${esc(stage.description)}</div></li>`).join(""));

  const last = (stats.last_run || null);
  mount("last-run", last
    ? `<div class="kv">
         <span class="k">competition</span><span class="v">${esc(last.slug)}</span>
         <span class="k">phase</span><span class="v">${esc(last.phase)}</span>
         <span class="k">status</span><span class="v">${statusChip(last.status)}</span>
         <span class="k">finished</span><span class="v">${when(last.finished_at)}</span>
       </div>
       <div class="panel-foot"><a href="competitions.html#recent-runs">all recorded runs →</a></div>`
    : '<div class="state">No runs yet — start one with <code>python -m engine cycle</code>.</div>');
}

/* ---------- page: competitions ------------------------------------------------------ */

/* Seven checkpoint chips — 1 datasets · 2 statement · 3 coded · 4 trained ·
   5 scored · 6 gate · 7 submitted — driven by comp.stages from the engine's
   report feed. Absent stages (older feed) render nothing. */
function stageStrip(comp) {
  const s = comp.stages;
  if (!s) return "";
  const gateCls = s.gate === true ? "pass" : s.gate === false ? "fail" : "na";
  const gateWhy = s.gate === true
    ? "measured OOF score has reached the target gate (R7)"
    : s.gate === false
      ? "gate defined but not reached yet — the feedback loop keeps improving"
      : "no gate verdict yet — run a cycle to measure against the target";
  const items = [
    ["1 datasets", s.datasets ? "pass" : "na", "kaggle data extracted under datasets/"],
    ["2 statement", s.statement ? "pass" : "na", "PROBLEM_STATEMENT.md fetched from kaggle"],
    ["3 coded", s.coded ? "pass" : "na", "the engine coder has produced code for this competition"],
    ["4 trained", s.trained ? "pass" : "na", "train/metrics.json written by a full notebook run (R4)"],
    ["5 scored", s.scored ? "pass" : "na", "OOF score measured on held-out folds"],
    ["6 gate", gateCls, gateWhy],
    ["7 submitted", s.submitted ? "pass" : "na", "submission logged by the engine (R9)"],
  ];
  return `<div class="stages-row" role="group" aria-label="checkpoint progress">${items
    .map(([label, cls, why]) => `<span class="chip ${cls}" title="${esc(why)}">${esc(label)}</span>`)
    .join("")}</div>`;
}

function compCard(comp) {
  const checks = ruleOrder(comp.checks);
  const verdict = gateVerdict(comp);
  const oofClass = verdict === "pass" ? " v-pass" : verdict === "fail" ? " v-fail" : "";
  const gapLarge = gapLooksLarge(comp);
  const gapClass = gapLarge ? " v-warn" : "";
  const gapTitle = gapLarge
    ? ' title="gap beyond 2x CV std — diagnose the split before adding models (R5)"'
    : "";

  const passed = checks.filter((c) => c.status === "pass").length;
  const anyFail = checks.some((c) => c.status === "fail");
  const anyWarn = checks.some((c) => c.status === "warn");
  const summaryTone = anyFail ? "fail" : anyWarn ? "warn" : checks.length ? "pass" : "na";
  const summaryText = checks.length ? `${passed}/${checks.length} checks` : "no checks yet";

  const attain = gateAttainment(comp);
  const meterTone = attain ? (attain.verdict === "pass" ? "good" : attain.verdict === "fail" ? "bad" : "") : "";

  const links = [
    ["Kaggle", comp.url],
    ["readme.md", comp.readme_url],
    ["notebook", comp.notebook_url],
    ["problem statement", comp.problem_statement_url],
    ["brief", comp.brief_url],
  ].filter(([, href]) => href);

  return `
  <div class="comp">
    <div class="top">
      <h3>${esc(comp.title)}</h3>
      ${gateChip(comp)}
    </div>
    <div class="slugline">${esc(comp.slug)} · ${esc(comp.metric || "metric unknown")}
      ${comp.higher_is_better === false ? " · lower is better" : ""} · ${statusChip(comp.status)}${comp.last_attempt_at ? ` · last attempt ${when(comp.last_attempt_at)}` : ""}</div>
    <div class="scores">
      <div><div class="k">OOF ${esc(comp.metric || "")}</div><div class="v${oofClass}">${fmt(comp.cv_mean)}</div></div>
      <div><div class="k">± std</div><div class="v">${fmt(comp.cv_std)}</div></div>
      <div><div class="k">gate</div><div class="v">${comp.target_score == null ? "—" : fmt(comp.target_score)}</div></div>
      <div><div class="k">public LB</div><div class="v">${fmt(comp.lb_score)}</div></div>
      <div><div class="k">gap (LB−OOF)</div><div class="v${gapClass}"${gapTitle}>${fmt(comp.gap)}</div></div>
      <div><div class="k">attempts</div><div class="v">${esc(comp.attempts ?? 0)}</div></div>
    </div>
    ${attain ? `
    <div class="gate">
      <progress class="prog ${meterTone}" max="100" value="${attain.clamped.toFixed(1)}"
                aria-label="OOF score progress toward the score gate"></progress>
      <div class="gate-label">OOF ${fmt(comp.cv_mean)} vs gate ${fmt(comp.target_score)} — ${fmtPct(attain.raw)} of target</div>
    </div>` : ""}
    ${stageStrip(comp)}
    <div class="checks-row">
      <span class="chip ${summaryTone} summary" title="rules checked and passing for this competition">${esc(summaryText)}</span>
      ${checks.map((c) =>
        `<span class="chip ${CHIP_CLASS[c.status] || "info"}" title="${esc(c.detail)}">${esc(c.rule)} ${esc(c.status)}</span>`
      ).join("")}
    </div>
    ${(comp.notes || []).map((n) => `<div class="note">⚠ ${esc(n)}</div>`).join("")}
    <div class="links">${links.map(([label, href]) =>
      `<a href="${esc(href)}" target="_blank" rel="noopener">${esc(label)} <span aria-hidden="true">↗</span></a>`).join("")}</div>
  </div>`;
}

function runRow(r) {
  return `
        <tr>
          <td>${esc(r.slug)}</td>
          <td class="num">${esc(r.attempt)}</td>
          <td>${esc(r.phase)}</td>
          <td>${statusChip(r.status)}</td>
          <td class="num">${fmt(r.cv_mean)}</td>
          <td class="num">${fmt(r.lb_score)}</td>
          <td>${r.score_reached === true ? chip("pass") : r.score_reached === false ? chip("fail") : chip("n/a")}</td>
          <td class="num">${when(r.finished_at)}</td>
        </tr>`;
}

function runTable(runs) {
  return `
    <div class="scroll-x">
      <table class="data">
        <thead><tr><th scope="col">competition</th><th scope="col">attempt</th>
                   <th scope="col">phase</th><th scope="col">status</th>
                   <th scope="col" class="num">OOF</th><th scope="col" class="num">LB</th>
                   <th scope="col">gate</th><th scope="col">finished</th></tr></thead>
        <tbody id="runs-body">${runs.slice(0, 25).map(runRow).join("")}</tbody>
      </table>
    </div>`;
}

function renderCompetitions(data) {
  const comps = data.competitions || [];
  if (!comps.length) {
    mount("comps", '<div class="state">No competitions yet. Create one with <code>python -m engine init &lt;slug&gt;</code>, then run <code>python -m engine cycle &lt;slug&gt;</code>.</div>');
    return;
  }
  mount("comps", comps.map(compCard).join(""));

  const runs = comps
    .flatMap((c) => (c.history || []).map((h) => ({ ...h, slug: c.slug })))
    .sort((a, b) =>
      String(b.finished_at || "").localeCompare(String(a.finished_at || "")) ||
      (Number(b.attempt) || 0) - (Number(a.attempt) || 0));

  if (!runs.length) {
    mount("recent-runs", '<div class="state">No runs recorded yet.</div>');
    return;
  }

  const statuses = [...new Set(runs.map((r) => r.status).filter(Boolean))].sort();

  mount("recent-runs", `
    <div class="toolbar">
      <input id="runs-filter" type="search" placeholder="filter by competition, phase or status…"
             aria-label="Filter runs" autocomplete="off">
      <select id="runs-status" aria-label="Filter runs by status">
        <option value="">all statuses</option>
        ${statuses.map((s) => `<option value="${esc(s)}">${esc(s)}</option>`).join("")}
      </select>
      <span class="filter-count" id="runs-count"></span>
    </div>
    ${runTable(runs)}`);

  const input = document.getElementById("runs-filter");
  const select = document.getElementById("runs-status");
  const body = document.getElementById("runs-body");
  const count = document.getElementById("runs-count");
  if (!input || !select || !body || !count) return;

  const apply = () => {
    const q = input.value.trim().toLowerCase();
    const st = select.value;
    const filtered = runs.filter((r) =>
      (!st || String(r.status ?? "") === st) &&
      (!q || `${r.slug} ${r.phase} ${r.status} ${r.attempt}`.toLowerCase().includes(q)));
    body.innerHTML = filtered.length
      ? filtered.slice(0, 25).map(runRow).join("")
      : '<tr><td colspan="8" class="evidence">no runs match the current filter.</td></tr>';
    const shown = Math.min(25, filtered.length);
    count.textContent = filtered.length === runs.length
      ? `${runs.length} run${runs.length === 1 ? "" : "s"}`
      : `showing ${shown} of ${filtered.length} (${runs.length} total)`;
  };

  input.addEventListener("input", apply);
  select.addEventListener("change", apply);
  apply();
}

/* ---------- page: requirements matrix ------------------------------------------------ */

function renderRequirements(data) {
  const comps = data.competitions || [];
  const rules = data.requirements || [];
  if (!comps.length || !rules.length) {
    mount("matrix", '<div class="state">Nothing to show yet — run a cycle first.</div>');
    return;
  }

  const byRule = {};
  comps.forEach((c) => {
    (c.checks || []).forEach((check) => {
      byRule[check.rule] = byRule[check.rule] || {};
      byRule[check.rule][c.slug] = check;
    });
  });

  const totals = comps.map((c) => {
    const checks = c.checks || [];
    const pass = checks.filter((x) => x.status === "pass").length;
    return `<td class="num">${pass}/${checks.length}</td>`;
  }).join("");

  mount("matrix", `
    <table class="data">
      <thead><tr><th scope="col">rule</th><th scope="col">requirement</th>
        ${comps.map((c) => `<th scope="col">${esc(c.slug)}</th>`).join("")}</tr></thead>
      <tbody>${rules.map((r) => `
        <tr>
          <td class="mono">${esc(r.id)}</td>
          <td>${esc(r.title)}</td>
          ${comps.map((c) => {
            const check = byRule[r.id] && byRule[r.id][c.slug];
            return check
              ? `<td><a class="chip ${CHIP_CLASS[check.status] || "info"}" href="#ev-${esc(c.slug)}-${esc(check.rule)}" title="${esc(check.detail)}">${esc(check.status)}</a></td>`
              : `<td>${chip("n/a")}</td>`;
          }).join("")}
        </tr>`).join("")}</tbody>
      <tfoot><tr class="sum">
        <td class="mono">Σ</td><td>checks passing</td>${totals}
      </tr></tfoot>
    </table>`);

  mount("details", comps.map((c) => {
    const checks = ruleOrder(c.checks);
    const pass = checks.filter((x) => x.status === "pass").length;
    const fail = checks.filter((x) => x.status === "fail").length;
    const warn = checks.filter((x) => x.status === "warn").length;
    const pct = checks.length ? (pass / checks.length) * 100 : 0;
    const tone = fail ? "bad" : checks.length && pass === checks.length ? "good" : "";
    const checksChip = c.checks_passed === true ? chip("pass")
      : c.checks_passed === false ? chip("fail") : chip("na");

    return `
    <div class="panel">
      <div class="detail-head">
        <h3>${esc(c.title)} <span class="mono faint">${esc(c.slug)}</span> ${checksChip}</h3>
        <span class="gate-label">${pass}/${checks.length} passing${warn ? ` · ${warn} warn` : ""}${fail ? ` · ${fail} fail` : ""}</span>
      </div>
      <progress class="prog ${tone}" max="100" value="${pct.toFixed(1)}"
                aria-label="Share of requirement checks passing for ${esc(c.slug)}"></progress>
      <div class="scroll-x">
        <table class="data">
          <thead><tr><th scope="col">rule</th><th scope="col">requirement</th>
                     <th scope="col">status</th><th scope="col">evidence</th></tr></thead>
          <tbody>${checks.map((check) => `
            <tr id="ev-${esc(c.slug)}-${esc(check.rule)}">
              <td class="mono">${esc(check.rule)}</td>
              <td>${esc(check.title)}</td>
              <td>${chip(check.status)}</td>
              <td class="evidence">${esc(check.detail)}</td>
            </tr>`).join("") || '<tr><td colspan="4" class="evidence">no checks recorded</td></tr>'}</tbody>
        </table>
      </div>
    </div>`;
  }).join(""));
}

/* ---------- page: rulebook -------------------------------------------------------------- */

function renderRules(data) {
  const rules = data.requirements || [];

  mount("rules", rules.length ? `
    <nav class="rule-index" aria-label="Jump to rule">
      ${rules.map((r) => `<a class="chip info" href="#rule-${esc(r.id)}" title="${esc(r.title)}">${esc(r.id)}</a>`).join("")}
    </nav>
    ${rules.map((r) => `
    <article class="rule" id="rule-${esc(r.id)}">
      <div class="rule-head">
        <span class="rid">${esc(r.id)}</span><span class="rtitle">${esc(r.title)}</span>
        <button class="btn-copy" type="button" data-copy-rule aria-label="Copy rule ${esc(r.id)} text">copy</button>
      </div>
      <p>${esc(r.text)}</p>
    </article>`).join("")}`
    : '<div class="state">No rulebook loaded — regenerate <code>data/dashboard.json</code>.</div>');

  const engine = data.engine || {};
  mount("engine-rules", `
    <div class="kv">
      <span class="k">max attempts per cycle</span><span class="v">${esc(engine.max_attempts ?? "—")}</span>
      <span class="k">notebook timeout</span><span class="v">${engine.notebook_timeout != null ? esc(engine.notebook_timeout) + "s" : "—"}</span>
      <span class="k">submissions</span><span class="v">${engine.submit_enabled ? "enabled" : "disabled — ENGINE_SUBMIT_ENABLED=1 required (R9)"}</span>
      <span class="k">credentials</span><span class="v">env / ~/.kaggle/kaggle.json only — never in the database (R12)</span>
      <span class="k">sync</span><span class="v">${engine.vercel_sync ? "dashboard projection pushed to Vercel endpoint" : "no Vercel endpoint configured"}</span>
    </div>`);
}

/* ---------- component: copy rule text ---------------------------------------------------- */

function flashLabel(btn, text) {
  const old = btn.textContent;
  btn.textContent = text;
  btn.classList.add("ok");
  setTimeout(() => {
    btn.textContent = old;
    btn.classList.remove("ok");
  }, 1500);
}

function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text);
  }
  return new Promise((resolve, reject) => {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.className = "offscreen";
    ta.setAttribute("readonly", "");
    document.body.appendChild(ta);
    ta.select();
    let ok = false;
    try { ok = document.execCommand("copy"); } catch { ok = false; }
    ta.remove();
    ok ? resolve() : reject(new Error("copy failed"));
  });
}

document.addEventListener("click", (e) => {
  const btn = e.target && e.target.closest ? e.target.closest("[data-copy-rule]") : null;
  if (!btn) return;
  const text = btn.closest(".rule") ? btn.closest(".rule").querySelector("p").textContent.trim() : "";
  if (!text) return;
  copyText(text)
    .then(() => flashLabel(btn, "copied ✓"))
    .catch(() => flashLabel(btn, "copy failed"));
});

/* ---------- boot ---------------------------------------------------------------------------- */

function mountRoot(html) {
  const root = document.getElementById("root");
  if (root) { root.innerHTML = html; return; }
  document.querySelector("main.wrap")?.insertAdjacentHTML("afterbegin", html);
}

async function boot() {
  markActiveNav();
  mountRoot(SKELETON);

  let data;
  try {
    const resp = await fetch("data/dashboard.json", { cache: "no-store" });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const type = (resp.headers.get("content-type") || "").toLowerCase();
    if (type && !type.includes("json")) {
      throw new Error(`server replied ${type.split(";")[0]} instead of JSON`);
    }
    try {
      data = await resp.json();
    } catch {
      throw new Error("dashboard.json is not valid JSON — regenerate it with `python -m engine report`");
    }
  } catch (err) {
    mountRoot(`<div class="state error">
      Could not load <code>data/dashboard.json</code> (${esc(err.message)}).
      Generate it with <code>python -m engine report</code>, or serve the
      <code>frontend/</code> folder through a static server (fetch() does not
      work from <code>file://</code>).</div>`);
    return;
  }

  mountRoot("");
  try {
    hydrateChrome(data);
    ({ index: renderIndex, competitions: renderCompetitions,
       requirements: renderRequirements, rules: renderRules }[PAGE] || (() => {}))(data);
  } catch (err) {
    mountRoot(`<div class="state error">
      Loaded <code>data/dashboard.json</code>, but rendering failed (${esc(err.message)}).</div>`);
  }
}

document.addEventListener("DOMContentLoaded", boot);
