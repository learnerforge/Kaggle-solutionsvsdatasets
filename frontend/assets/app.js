/* Kaggle Solutions vs Datasets — frontend logic.
 *
 * The site is fully static: every page fetches data/dashboard.json, which
 * `python -m engine report` (and the daily GitHub Actions cycle) regenerates.
 * No build step, no framework — serve the frontend/ folder through any static
 * server; fetch() does not work from file://.
 */

"use strict";

const PAGE = document.body.dataset.page || "index";

/* ---------- helpers -------------------------------------------------------- */

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

/* Keep the raw ISO value in datetime= so timestamps stay machine-readable. */
function when(value) {
  if (!value) return "—";
  return `<time datetime="${esc(value)}">${esc(value)}</time>`;
}

const CHIP_CLASS = { pass: "pass", fail: "fail", warn: "warn", "n/a": "na", na: "na" };

function chip(status) {
  const key = String(status ?? "").toLowerCase();
  return `<span class="chip ${CHIP_CLASS[key] || "info"}">${esc(status)}</span>`;
}

function gateChip(comp) {
  if (comp.reached === true) return '<span class="chip pass">gate reached</span>';
  if (comp.reached === false) return '<span class="chip fail">gate not reached</span>';
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

/* Does the measured OOF score satisfy the gate? (R5) */
function gateVerdict(comp) {
  if (comp.reached === true) return "pass";
  if (comp.reached === false) return "fail";
  if (comp.cv_mean == null || comp.target_score == null) return null;
  const cv = Number(comp.cv_mean);
  const target = Number(comp.target_score);
  if (!Number.isFinite(cv) || !Number.isFinite(target)) return null;
  const higher = comp.higher_is_better !== false;
  return (higher ? cv >= target : cv <= target) ? "pass" : "fail";
}

/* R5: a gap beyond 2x the CV std means the split is unrepresentative. */
function gapLooksLarge(comp) {
  if (comp.gap == null || comp.cv_std == null) return false;
  const gap = Number(comp.gap);
  const std = Number(comp.cv_std);
  return Number.isFinite(gap) && Number.isFinite(std) && Math.abs(gap) > 2 * std;
}

/* ---------- shared header/footer ------------------------------------------- */

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
  mount("head-meta",
    `rulebook v${esc(data.rules_version ?? "—")} · generated ${esc(data.generated_at ?? "—")}`);
  mount("foot-generated",
    `dashboard generated ${esc(data.generated_at ?? "—")} by <code>python -m engine report</code>`);
  const repo = data.repo_url || "#";
  document.querySelectorAll("[data-repo-link]").forEach((a) => {
    a.href = repo;
  });
}

/* ---------- pages ----------------------------------------------------------- */

function renderIndex(data) {
  const stats = data.stats || {};
  const engine = data.engine || {};
  const cards = [
    ["Competitions tracked", stats.competitions ?? 0, `${stats.tracked_on_disk ?? 0} folder(s) on disk`],
    ["Gate reached", stats.gate_reached ?? 0, `${stats.gate_defined ?? 0} with a score gate defined`],
    ["Runs recorded", stats.runs ?? 0, "scout / code / train attempts"],
    ["Solved", stats.solved ?? 0, "marked solved by the score gate"],
  ];
  mount("stats", cards.map(([label, value, sub]) => `
    <div class="card">
      <div class="label">${esc(label)}</div>
      <div class="value">${esc(value)}</div>
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
       </div>`
    : '<div class="state">No runs yet — start one with <code>python -m engine cycle</code>.</div>');
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
      ${comp.higher_is_better === false ? " · lower is better" : ""} · ${statusChip(comp.status)}</div>
    <div class="scores">
      <div><div class="k">OOF ${esc(comp.metric || "")}</div><div class="v${oofClass}">${fmt(comp.cv_mean)}</div></div>
      <div><div class="k">± std</div><div class="v">${fmt(comp.cv_std)}</div></div>
      <div><div class="k">gate</div><div class="v">${comp.target_score == null ? "—" : fmt(comp.target_score)}</div></div>
      <div><div class="k">public LB</div><div class="v">${fmt(comp.lb_score)}</div></div>
      <div><div class="k">gap (LB−OOF)</div><div class="v${gapClass}"${gapTitle}>${fmt(comp.gap)}</div></div>
      <div><div class="k">attempts</div><div class="v">${esc(comp.attempts ?? 0)}</div></div>
    </div>
    <div class="checks-row">${checks.map((c) =>
      `<span class="chip ${CHIP_CLASS[c.status] || "info"}" title="${esc(c.detail)}">${esc(c.rule)} ${esc(c.status)}</span>`
    ).join("") || '<span class="chip na">no checks yet</span>'}</div>
    ${(comp.notes || []).map((n) => `<div class="note">⚠ ${esc(n)}</div>`).join("")}
    <div class="links">${links.map(([label, href]) =>
      `<a href="${esc(href)}" target="_blank" rel="noopener">${esc(label)}</a>`).join("")}</div>
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

  mount("recent-runs", runs.length ? `
    <table class="data">
      <thead><tr><th scope="col">competition</th><th scope="col">attempt</th>
                 <th scope="col">phase</th><th scope="col">status</th>
                 <th scope="col" class="num">OOF</th><th scope="col" class="num">LB</th>
                 <th scope="col">gate</th><th scope="col">finished</th></tr></thead>
      <tbody>${runs.slice(0, 25).map((r) => `
        <tr>
          <td>${esc(r.slug)}</td>
          <td class="num">${esc(r.attempt)}</td>
          <td>${esc(r.phase)}</td>
          <td>${statusChip(r.status)}</td>
          <td class="num">${fmt(r.cv_mean)}</td>
          <td class="num">${fmt(r.lb_score)}</td>
          <td>${r.score_reached === true ? chip("pass") : r.score_reached === false ? chip("fail") : chip("n/a")}</td>
          <td class="num">${when(r.finished_at)}</td>
        </tr>`).join("")}</tbody>
    </table>` : '<div class="state">No runs recorded yet.</div>');
}

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
            return `<td>${check ? chip(check.status) : chip("n/a")}</td>`;
          }).join("")}
        </tr>`).join("")}</tbody>
    </table>`);

  mount("details", comps.map((c) => `
    <div class="panel">
      <h3>${esc(c.title)} <span class="mono faint">${esc(c.slug)}</span>
        ${c.checks_passed === true ? chip("pass") : c.checks_passed === false ? chip("fail") : chip("na")}</h3>
      <div class="scroll-x">
        <table class="data">
          <thead><tr><th scope="col">rule</th><th scope="col">requirement</th>
                     <th scope="col">status</th><th scope="col">evidence</th></tr></thead>
          <tbody>${ruleOrder(c.checks).map((check) => `
            <tr>
              <td class="mono">${esc(check.rule)}</td>
              <td>${esc(check.title)}</td>
              <td>${chip(check.status)}</td>
              <td class="evidence">${esc(check.detail)}</td>
            </tr>`).join("") || '<tr><td colspan="4" class="evidence">no checks recorded</td></tr>'}</tbody>
        </table>
      </div>
    </div>`).join(""));
}

function renderRules(data) {
  mount("rules", (data.requirements || []).map((r) => `
    <div class="rule">
      <span class="rid">${esc(r.id)}</span><span class="rtitle">${esc(r.title)}</span>
      <p>${esc(r.text)}</p>
    </div>`).join(""));

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

/* ---------- boot -------------------------------------------------------------- */

function mountRoot(html) {
  const root = document.getElementById("root");
  if (root) { root.innerHTML = html; return; }
  document.querySelector("main.wrap")?.insertAdjacentHTML("afterbegin", html);
}

async function boot() {
  markActiveNav();
  mountRoot('<div class="state">Loading <code>data/dashboard.json</code>…</div>');

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
