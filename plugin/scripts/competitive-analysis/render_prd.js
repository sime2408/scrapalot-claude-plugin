/*
 * render_prd.js — unified visual review surface for a competitive-analysis PRD.
 *
 * Renders competitive_analysis_<slug>.md into ONE self-contained, scannable HTML
 * review page (markdown + rendered mermaid diagrams + inline wireframe PNGs,
 * GitHub-dark docs theme) plus segmented screenshots. This is our local
 * equivalent of the BuilderIO visual-plan / Agent-Native Plan review surface —
 * no external app, content stays private. See visual_plan_discipline.md §5.
 *
 * Usage: node render_prd.js <slug>        e.g.  node render_prd.js hermes_agent
 * Outputs (in prd-competitive/):
 *   prd_<slug>_review.html   — portable single file (wireframes base64-inlined)
 *   prd_<slug>_NN.png        — ~2600px segments for quick visual verification
 */
const { chromium } = require('/opt/scrapalot/scrapalot-ui/node_modules/playwright');
const fs = require('fs');
const path = require('path');

const PRD_DIR = '/opt/scrapalot/scrapalot-chat/docs/prd-competitive';

const slug = process.argv[2];
if (!slug) { console.error('usage: node render_prd.js <slug>  (e.g. hermes_agent)'); process.exit(1); }
const mdPath = path.join(PRD_DIR, `competitive_analysis_${slug}.md`);
if (!fs.existsSync(mdPath)) { console.error('not found:', mdPath); process.exit(1); }

// Inline wireframe images as base64 data URIs so the HTML is portable (scp the one file).
let MD = fs.readFileSync(mdPath, 'utf-8');
MD = MD.replace(/!\[([^\]]*)\]\((wireframes\/[^)]+\.png)\)/g, (m, alt, rel) => {
  const img = path.join(PRD_DIR, rel);
  if (!fs.existsSync(img)) return m;
  const b64 = fs.readFileSync(img).toString('base64');
  return `![${alt}](data:image/png;base64,${b64})`;
});

const html = `<!DOCTYPE html><html><head><meta charset="utf-8">
<link href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.1/github-markdown-dark.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<style>
  body{background:#0d1117;margin:0;}
  .markdown-body{max-width:920px;margin:0 auto;padding:48px 56px;font-family:Inter,system-ui,sans-serif;font-size:15px;}
  .markdown-body img{border:1px solid #30363d;border-radius:6px;}
  .markdown-body table{display:table;width:100%;}
  .mermaid{background:#0f1620;border:1px solid #30363d;border-radius:8px;padding:18px;margin:16px 0;text-align:center;overflow:auto;}
  .mermaid svg{max-width:100%;height:auto;}
  .markdown-body h2{border-bottom:1px solid #30363d;padding-bottom:.3em;margin-top:36px;}
  .markdown-body blockquote{border-left:3px solid #3b82f6;}
</style></head>
<body><article class="markdown-body" id="content"></article>
<script>
  marked.setOptions({ gfm:true });
  document.getElementById('content').innerHTML = marked.parse(MD_PLACEHOLDER);
  document.querySelectorAll('code.language-mermaid').forEach(function(code){
    var div = document.createElement('div'); div.className='mermaid';
    div.textContent = code.textContent;
    (code.closest('pre') || code).replaceWith(div);
  });
  mermaid.initialize({ startOnLoad:false, theme:'dark', securityLevel:'loose', themeVariables:{ fontSize:'13px' }, flowchart:{ htmlLabels:true, useMaxWidth:true } });
  mermaid.run({ querySelector:'.mermaid' }).then(function(){ window.__done=true; }).catch(function(e){ window.__err=String(e); window.__done=true; });
</script></body></html>`.replace('MD_PLACEHOLDER', JSON.stringify(MD));

const reviewPath = path.join(PRD_DIR, `prd_${slug}_review.html`);
fs.writeFileSync(reviewPath, html);

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport:{ width:1040, height:1200 }, deviceScaleFactor:2 });
  await page.goto('file://' + reviewPath, { waitUntil:'networkidle' });
  await page.waitForFunction(() => window.__done === true, { timeout:45000 }).catch(()=>{});
  await page.waitForTimeout(1000);
  const blocks = await page.evaluate(()=>document.querySelectorAll('.mermaid').length);
  const svgs = await page.evaluate(()=>document.querySelectorAll('.mermaid svg').length);
  console.log(`mermaid: ${svgs}/${blocks} rendered`);
  const box = await (await page.$('body')).boundingBox();
  const total = Math.ceil(box.height); const SEG = 2600, n = Math.ceil(total / SEG);
  for (let i=0; i<n; i++){
    await page.setViewportSize({ width:1040, height:Math.min(SEG, total - i*SEG) });
    await page.evaluate(y => window.scrollTo(0, y), i*SEG);
    await page.waitForTimeout(200);
    await page.screenshot({ path: path.join(PRD_DIR, `prd_${slug}_${String(i+1).padStart(2,'0')}.png`), type:'png' });
  }
  console.log(`review: ${reviewPath}`);
  console.log(`segments: ${n} (prd_${slug}_NN.png), total height ${total}px`);
  await browser.close();
})().catch(e=>{ console.error(e); process.exit(1); });
