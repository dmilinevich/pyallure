from __future__ import annotations

from pathlib import Path

from pyrep.generator import write_report_data


def generate_static_report(results_dir: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_report_data(results_dir, out_dir)
    assets = out_dir / "assets"
    assets.mkdir(exist_ok=True)
    (out_dir / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    (assets / "app.js").write_text(APP_JS, encoding="utf-8")
    (assets / "styles.css").write_text(STYLES_CSS, encoding="utf-8")


INDEX_HTML = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>pyrep report</title>
  <link rel=\"stylesheet\" href=\"assets/styles.css\" />
</head>
<body>
  <header><h1>pyrep report</h1></header>
  <main>
    <section id=\"summary\"></section>
    <section id=\"filters\"></section>
    <section id=\"trend\"></section>
    <section id=\"content\"></section>
  </main>
  <script src=\"assets/app.js\"></script>
</body>
</html>"""

APP_JS = """const state = { run:null, tests:[], selected:null, filters:{status:'all', suite:'all', q:''} };

async function loadData(){
  state.run = await fetch('report-data/run.json').then(r=>r.json());
  state.tests = await fetch('report-data/tests.json').then(r=>r.json());
  render();
}
function esc(v){return String(v||'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');}
function fmt(sec){return `${sec.toFixed(2)}s`;}
function renderSummary(){
  const s = state.run.summary;
  document.getElementById('summary').innerHTML = `<div class='cards'>
  <div>Passed <b>${s.passed}</b></div><div>Failed <b>${s.failed}</b></div>
  <div>Skipped <b>${s.skipped}</b></div><div>Duration <b>${fmt(state.run.duration)}</b></div></div>`;
}
function renderFilters(){
  const suites = [...new Set(state.tests.map(t=>t.suite))].sort();
  document.getElementById('filters').innerHTML = `<label>Status <select id='status'><option>all</option><option>passed</option><option>failed</option><option>skipped</option></select></label>
  <label>Suite <select id='suite'><option>all</option>${suites.map(s=>`<option>${esc(s)}</option>`).join('')}</select></label>
  <input id='q' placeholder='search test/tag'/>`;
  ['status','suite','q'].forEach(id=>document.getElementById(id).oninput=(e)=>{state.filters[id]=e.target.value; renderContent();});
}
function visibleTests(){
  return state.tests.filter(t=>(state.filters.status==='all'||t.status===state.filters.status)
    && (state.filters.suite==='all'||t.suite===state.filters.suite)
    && (!state.filters.q || t.name.includes(state.filters.q) || (t.tags||[]).join(',').includes(state.filters.q)));
}
function stepHtml(step){
  const kids=(step.steps||[]).map(stepHtml).join('');
  return `<li><span>${esc(step.name)}</span> <em>${fmt((step.stop-step.start)||0)}</em>${kids?`<ul>${kids}</ul>`:''}</li>`;
}
function renderDetail(t){
  const at = (t.attachments||[]).map(a=>`<li><a href='report-data/attachments/${encodeURIComponent(a.path)}' target='_blank'>${esc(a.name)}</a> (${esc(a.mime)})</li>`).join('');
  return `<article><h3>${esc(t.name)}</h3><p>${esc(t.suite)} · ${esc(t.status)} · ${fmt(t.duration)}</p>
  ${t.error?`<pre>${esc(t.error)}</pre>`:''}
  <h4>Steps</h4><ul>${(t.steps||[]).map(stepHtml).join('')}</ul>
  <h4>Attachments</h4><ul>${at}</ul></article>`;
}
function renderContent(){
  const tests = visibleTests();
  const left = `<div class='tree'>${tests.map(t=>`<div class='test ${t.status}' data-id='${t.id}'>${esc(t.suite)} / ${esc(t.name)}</div>`).join('')}</div>`;
  const selected = state.selected && tests.find(t=>t.id===state.selected) || tests[0];
  state.selected = selected? selected.id : null;
  document.getElementById('content').innerHTML = `<div class='split'>${left}<div id='detail'>${selected?renderDetail(selected):'<p>No tests</p>'}</div></div>`;
  document.querySelectorAll('.test').forEach(el=>el.onclick=()=>{state.selected=el.dataset.id; renderContent();});
}
async function renderTrend(){
  const host = document.getElementById('trend');
  try {
    const history = await fetch('history/index.json').then(r=>r.json());
    const max = Math.max(...history.map(h=>h.pass_rate), 100);
    const bars = history.map(h=>`<rect x='${h.i*24+10}' y='${100-(h.pass_rate/max*100)}' width='18' height='${h.pass_rate/max*100}'/>`).join('');
    host.innerHTML = `<h3>Trend</h3><svg viewBox='0 0 ${history.length*24+20} 110' class='trend'>${bars}</svg>`;
  } catch(_e) {
    host.innerHTML = '<h3>Trend</h3><p>No history yet.</p>';
  }
}
function render(){renderSummary(); renderFilters(); renderTrend(); renderContent();}
loadData();
"""

STYLES_CSS = """body{font-family:Arial,sans-serif;margin:0;background:#f7f8fa;color:#222}header{background:#20252c;color:#fff;padding:8px 16px}
main{padding:16px}.cards{display:grid;grid-template-columns:repeat(4,minmax(80px,1fr));gap:8px}.cards>div{background:#fff;padding:12px;border-radius:6px}
#filters{display:flex;gap:12px;align-items:center;margin:16px 0}.split{display:grid;grid-template-columns:36% 1fr;gap:12px}.tree{background:#fff;border-radius:6px;padding:8px;max-height:70vh;overflow:auto}
.test{padding:6px;border-bottom:1px solid #eee;cursor:pointer}.test.failed{border-left:4px solid #c62828}.test.passed{border-left:4px solid #2e7d32}.test.skipped{border-left:4px solid #ef6c00}
#detail{background:#fff;border-radius:6px;padding:12px}pre{white-space:pre-wrap;background:#111;color:#f5f5f5;padding:8px;border-radius:4px}.trend rect{fill:#4e79a7}
"""
