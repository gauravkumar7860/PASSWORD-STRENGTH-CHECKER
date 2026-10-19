const $ = id => document.getElementById(id);
const COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#0d9488'];
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let timer, ctl, mode = 'random';

const toast = m => { const t = $('toast'); t.textContent = m; t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 2200); };
const post = (url, body, signal) => fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body), signal});
const payload = () => ({
  password: $('pw').value,
  personal: [$('pName').value, $('pYear').value, $('pEmail').value].filter(Boolean),
  previous: $('pPrev').value
});

$('themeBtn').onclick = () => {
  const t = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = t;
  try { localStorage.setItem('theme', t); } catch (e) {}
};
$('toggle').onclick = () => {
  const show = $('pw').type === 'password';
  $('pw').type = show ? 'text' : 'password';
  $('toggle').textContent = show ? 'Hide' : 'Show';
};

function reset() {
  $('score').textContent = 0; $('entropy').textContent = 0;
  $('label').textContent = 'Waiting for input'; $('label').style.color = '';
  $('arc').style.strokeDasharray = '0 327'; $('bar').style.width = '0';
  $('crack').innerHTML = ['Online, rate-limited', 'Online, no limit', 'Offline, slow hash', 'Offline, fast hash']
    .map(k => `<div><small>${k}</small><b>-</b></div>`).join('');
  $('checks').innerHTML = ''; $('sugWrap').hidden = true; $('pdfBtn').disabled = true;
}

function render(d) {
  if (d.error) return;
  const c = COLORS[d.level];
  $('score').textContent = d.percent; $('entropy').textContent = d.entropy;
  $('label').textContent = d.label; $('label').style.color = c;
  $('arc').style.strokeDasharray = `${d.percent * 3.27} 327`; $('arc').style.stroke = c;
  $('bar').style.width = d.percent + '%'; $('bar').style.background = c;
  $('crack').innerHTML = d.crack.map(x => `<div><small>${esc(x[0])}</small><b>${esc(x[1])}</b></div>`).join('');
  $('checks').innerHTML = d.checks.map(x => `<li class="${x.ok ? 'ok' : 'bad'}"><i>${x.ok ? '&#10003;' : '&#10005;'}</i>${esc(x.text)}</li>`).join('');
  $('sugs').innerHTML = d.suggestions.map(s => `<li>${esc(s)}</li>`).join('');
  $('sugWrap').hidden = !d.suggestions.length;
  $('pdfBtn').disabled = false;
}

async function analyze() {
  if (!$('pw').value) return reset();
  if (ctl) ctl.abort();
  ctl = new AbortController();
  try {
    const r = await post('/api/check', payload(), ctl.signal);
    render(await r.json());
  } catch (e) { if (e.name !== 'AbortError') toast('Could not reach the server. Try again.'); }
}
const schedule = () => { clearTimeout(timer); timer = setTimeout(analyze, 300); };
['pw', 'pName', 'pYear', 'pEmail', 'pPrev'].forEach(id => $(id).addEventListener('input', schedule));

document.querySelectorAll('.tab').forEach(t => t.onclick = () => {
  mode = t.dataset.mode;
  document.querySelectorAll('.tab').forEach(x => x.classList.toggle('active', x === t));
  $('optRandom').hidden = mode !== 'random'; $('optPhrase').hidden = mode !== 'phrase';
});
$('len').oninput = () => $('lenOut').textContent = $('len').value;
$('words').oninput = () => $('wOut').textContent = $('words').value;

$('genBtn').onclick = async () => {
  const o = {mode, length: +$('len').value, upper: $('upper').checked, lower: $('lower').checked,
    digits: $('digits').checked, symbols: $('symbols').checked, noamb: $('noamb').checked,
    words: +$('words').value, number: $('pnum').checked, sep: $('sep').value};
  try {
    const d = await (await post('/api/generate', o)).json();
    if (d.error) return toast(d.error);
    $('out').textContent = d.password; $('out').classList.add('has');
    $('copyBtn').disabled = false;
    $('pw').value = d.password; analyze();
  } catch (e) { toast('Could not generate a password. Try again.'); }
};

$('copyBtn').onclick = async () => {
  try { await navigator.clipboard.writeText($('out').textContent); toast('Password copied'); }
  catch (e) { toast('Copy failed. Select the text and copy it manually.'); }
};

$('pdfBtn').onclick = async () => {
  try {
    const r = await post('/api/report', payload());
    if (!r.ok) return toast('Could not create the report.');
    const url = URL.createObjectURL(await r.blob());
    const a = Object.assign(document.createElement('a'), {href: url, download: 'passguard-report.pdf'});
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
    toast('Report downloaded');
  } catch (e) { toast('Could not create the report.'); }
};

reset();
