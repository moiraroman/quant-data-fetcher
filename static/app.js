/* ============================================================
   Quant Data Fetcher — Dashboard Logic
   ============================================================ */

const API_URL = '/api/data';
const REFRESH_URL = '/api/refresh';
const REFRESH_INTERVAL = 60;
const TICKERS = ['SPY', 'GDXU', 'SOXX'];

let countdownTimer = null;
let autoRefreshId = null;
let countdownVal = REFRESH_INTERVAL;
let currentScoreTicker = 'SPY';
let scoresData = null;
let lastFullData = null;

// =============================================================
// INIT
// =============================================================

document.addEventListener('DOMContentLoaded', () => {
  fetchData();
  startAutoRefresh();
});

// =============================================================
// TAB SWITCHING
// =============================================================

function switchTab(tabName) {
  document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
  document.querySelectorAll('.tab-nav-btn').forEach(b => b.classList.remove('active'));

  const target = document.getElementById('tab-' + tabName);
  const btn = document.querySelector('[data-tab="' + tabName + '"]');
  if (target) target.style.display = '';
  if (btn) btn.classList.add('active');

  // Generate markdown when switching to that tab
  if (tabName === 'markdown' && lastFullData) {
    renderMarkdown(lastFullData);
  }
}

// =============================================================
// LOADING STATE
// =============================================================

function showLoading() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.style.display = 'flex';
  const progress = document.getElementById('loading-progress');
  if (progress) progress.textContent = '';
}

function hideLoading() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.style.display = 'none';
}

function updateLoadingProgress(msg) {
  const progress = document.getElementById('loading-progress');
  if (progress) progress.textContent = msg;
}

// =============================================================
// FETCH
// =============================================================

async function fetchData() {
  showLoading();
  updateLoadingProgress('Connecting...');
  try {
    const resp = await fetch(API_URL);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    updateLoadingProgress('Parsing data...');
    const data = await resp.json();
    lastFullData = data;
    updateLoadingProgress('Rendering...');
    renderAll(data);
    setStatus('ok');
  } catch (err) {
    setStatus('error');
    showGlobalError(err.message);
  } finally {
    hideLoading();
  }
}

async function forceRefresh() {
  showLoading();
  updateLoadingProgress('Force refreshing all sources...');
  try {
    const resp = await fetch(REFRESH_URL);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    lastFullData = data;
    renderAll(data);
    setStatus('ok');
    resetCountdown();
  } catch (err) {
    setStatus('error');
    showGlobalError(err.message);
  } finally {
    hideLoading();
  }
}

// =============================================================
// COUNTDOWN / AUTO-REFRESH
// =============================================================

function startAutoRefresh() {
  autoRefreshId = setInterval(async () => {
    // Silent background refresh (no loading overlay for auto)
    try {
      const resp = await fetch(API_URL);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      lastFullData = data;
      // Only re-render dashboard if it's the active tab
      if (document.getElementById('tab-dashboard').style.display !== 'none') {
        renderAll(data);
      }
      setStatus('ok');
    } catch (err) {
      setStatus('error');
    }
  }, REFRESH_INTERVAL * 1000);
  countdownTimer = setInterval(tickCountdown, 1000);
}

function resetCountdown() {
  countdownVal = REFRESH_INTERVAL;
  updateCountdown();
}

function tickCountdown() {
  countdownVal--;
  if (countdownVal <= 0) countdownVal = REFRESH_INTERVAL;
  updateCountdown();
}

function updateCountdown() {
  const el = document.getElementById('countdown');
  if (el) el.textContent = countdownVal + 's';
}

// =============================================================
// STATUS
// =============================================================

function setStatus(state) {
  const dot = document.getElementById('status-dot');
  if (dot) dot.classList.toggle('error', state === 'error');
}

function showGlobalError(msg) {
  const ts = document.getElementById('fetch-ts');
  if (ts) ts.textContent = 'Error: ' + msg;
}

// =============================================================
// RENDER ALL
// =============================================================

function renderAll(data) {
  const meta = data.meta || {};
  const tsEl = document.getElementById('fetch-ts');
  if (tsEl) tsEl.textContent = meta.timestamp || '--';

  const badge = document.getElementById('cache-badge');
  if (badge) {
    if (meta.cache_hit) {
      badge.textContent = 'Cached';
      badge.className = 'cache-badge hit';
    } else {
      badge.textContent = 'Fresh';
      badge.className = 'cache-badge miss';
    }
  }

  renderTickers(data.tickers || {}, data.finviz || {}, data.scores || {});
  renderHistorical(data.historical_prices || {});
  renderTechnicals(data.finviz || {});
  renderMacro(data.macro || {}, data.fred || {});
  renderSentiment(data.sentiment || {}, data.aaii || {});
  renderDarkPool(data.dark_pool || {});
  renderCOT(data.cftc_cot || {});
  renderBreadth(data.market_breadth || {});
  renderSectors(data.sectors || {});
  renderScores(data.scores || {});
  renderErrors(data.meta ? data.meta.errors || [] : []);
  renderMarkdown(data);
}

// =============================================================
// TICKER CARDS
// =============================================================

function renderTickers(tickers, finviz, scores) {
  const grid = document.getElementById('ticker-grid');
  if (!grid) return;
  let html = '';
  for (const sym of TICKERS) {
    const q = tickers[sym] || {};
    const tech = finviz[sym] || {};
    const sc = (scores[sym] || {});
    const rsi = tech.rsi_14;
    const changeVal = q.change_pct || 0;

    let rsiClass = 'neutral', rsiLabel = '--';
    if (rsi != null) {
      rsiLabel = rsi.toFixed(1);
      rsiClass = rsi >= 70 ? 'overbought' : rsi <= 30 ? 'oversold' : 'neutral';
    }

    const signal = sc.signal || '--';
    const bullPct = sc.bullish_pct != null ? sc.bullish_pct : '--';
    const bearPct = sc.bearish_pct != null ? sc.bearish_pct : '--';

    html += '<div class="ticker-card">';
    if (rsi != null) html += `<span class="rsi-badge ${rsiClass}">RSI ${rsiLabel}</span>`;
    html += `<div class="sym">${escapeHtml(sym)}</div>`;
    html += `<div class="name">${escapeHtml(q.name || '')}</div>`;
    html += '<div class="price-row">';
    html += `<span class="price">$${fmtNum(q.price)}</span>`;
    html += `<span class="change ${changeVal >= 0 ? 'up' : 'down'}">${changeVal >= 0 ? '+' : ''}${fmtNum(changeVal)}%</span>`;
    html += '</div>';
    html += '<div class="meta-row">';
    html += `<span>Vol: ${fmtVol(q.volume)}</span>`;
    html += `<span>H: ${fmtNum(q.day_high)}</span>`;
    html += `<span>L: ${fmtNum(q.day_low)}</span>`;
    html += '</div>';
    if (sc.signal) {
      const bp = sc.bullish_pct || 0;
      const bop = sc.bearish_pct || 0;
      html += '<div class="card-score-bar">';
      html += `<div class="bar-bull" style="width:${bp}%"></div>`;
      html += `<div class="bar-bear" style="width:${bop}%"></div>`;
      html += '</div>';
      html += `<div class="card-score-text"><span class="score-signal ${signal}">${signal}</span> <span style="color:var(--accent-green)">Bull ${bullPct}%</span> / <span style="color:var(--accent-red)">Bear ${bearPct}%</span></div>`;
    }
    html += '</div>';
  }
  grid.innerHTML = html;
}

// =============================================================
// TECHNICALS TABLE
// =============================================================

function renderTechnicals(finviz) {
  const tbody = document.getElementById('tech-body');
  if (!tbody) return;
  const rows = [
    { label: 'RSI (14)', key: 'rsi_14', warnHi: 70, warnLo: 30, precision: 1 },
    { label: 'ATR (14)', key: 'atr_14', precision: 2 },
    { label: 'SMA 20%', key: 'sma20_pct', precision: 1, warnHi: 5, warnLo: -5 },
    { label: 'SMA 50%', key: 'sma50_pct', precision: 1, warnHi: 10, warnLo: -10 },
    { label: 'SMA 200%', key: 'sma200_pct', precision: 1, warnHi: 20, warnLo: -20 },
    { label: 'Week', key: 'perf_week', precision: 1 },
    { label: 'Month', key: 'perf_month', precision: 1 },
    { label: 'YTD', key: 'perf_ytd', precision: 1 },
    { label: '1 Year', key: 'perf_year', precision: 1 },
  ];

  let html = '';
  for (const r of rows) {
    html += `<tr><td>${escapeHtml(r.label)}</td>`;
    for (const sym of TICKERS) {
      const v = (finviz[sym] || {})[r.key];
      if (v == null) {
        html += '<td class="val-blue">--</td>';
      } else {
        let cls = 'val-blue';
        if (r.warnHi != null && v >= r.warnHi) cls = 'val-red';
        else if (r.warnLo != null && v <= r.warnLo) cls = 'val-green';
        html += `<td class="${cls}">${v.toFixed(r.precision)}</td>`;
      }
    }
    html += '</tr>';
  }
  tbody.innerHTML = html;
}

// =============================================================
// MACRO
// =============================================================

function renderMacro(macro, fred) {
  const grid = document.getElementById('macro-grid');
  if (!grid) return;
  const items = [];

  for (const name of ['VIX', 'DXY', 'US10Y', 'GOLD']) {
    const q = macro[name] || {};
    items.push({
      label: name,
      value: q.price,
      change: q.change_pct,
      note: fred[name] ? `FRED T-1: ${fmtNum(fred[name].latest_value)}` : null,
    });
  }

  for (const sym of ['HYG', 'JNK']) {
    const q = macro[sym] || {};
    items.push({
      label: sym + ' (Credit)',
      value: q.price,
      change: q.change_pct,
    });
  }

  let html = '';
  for (const item of items) {
    html += '<div class="macro-card">';
    html += `<div class="macro-label">${escapeHtml(item.label)}</div>`;
    html += `<div class="macro-value">${item.value != null ? fmtNum(item.value) : '--'}</div>`;
    if (item.change != null) {
      const cls = item.change >= 0 ? 'val-green' : 'val-red';
      html += `<div class="macro-change ${cls}">${item.change >= 0 ? '+' : ''}${fmtNum(item.change)}%</div>`;
    }
    if (item.note) {
      html += `<div style="font-size:0.65rem;color:var(--text-muted);margin-top:2px">${escapeHtml(item.note)}</div>`;
    }
    html += '</div>';
  }
  grid.innerHTML = html;
}

// =============================================================
// SENTIMENT — only numbers
// =============================================================

function renderSentiment(sentiment, aaii) {
  const fg = sentiment;

  // CNN Fear & Greed — just the score number
  const fgEl = document.getElementById('sn-fg');
  if (fgEl) {
    if (fg && fg.score != null) {
      fgEl.textContent = fg.score + ' (' + (fg.rating || '?') + ')';
      fgEl.className = 'sn-val ' + getFearClass(fg.rating || '');
    } else {
      fgEl.textContent = '--';
      fgEl.className = 'sn-val';
    }
  }

  // AAII — just numbers
  if (aaii && aaii.bullish != null) {
    setSnVal('sn-aaii-bull', aaii.bullish.toFixed(1) + '%', 'bull');
    setSnVal('sn-aaii-neut', (aaii.neutral || 0).toFixed(1) + '%', '');
    setSnVal('sn-aaii-bear', (aaii.bearish || 0).toFixed(1) + '%', 'bear');
    const spread = aaii.bull_bear_spread;
    setSnVal('sn-aaii-spread', spread != null ? spread.toFixed(1) : '--', spread >= 0 ? 'bull' : 'bear');
    document.getElementById('aaii-date').textContent = aaii.date || '';
  } else {
    setSnVal('sn-aaii-bull', '--', '');
    setSnVal('sn-aaii-neut', '--', '');
    setSnVal('sn-aaii-bear', '--', '');
    setSnVal('sn-aaii-spread', '--', '');
    document.getElementById('aaii-date').textContent = 'No Data';
  }
}

function setSnVal(id, text, cls) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = text;
    el.className = 'sn-val ' + cls;
  }
}

function getFearClass(rating) {
  const r = (rating || '').toLowerCase();
  if (r.includes('extreme fear')) return 'extreme-fear';
  if (r.includes('fear')) return 'fear';
  if (r.includes('neutral')) return 'neutral';
  if (r.includes('extreme greed')) return 'extreme-greed';
  if (r.includes('greed')) return 'greed';
  return '';
}

// =============================================================
// DARK POOL
// =============================================================

function renderDarkPool(dp) {
  const grid = document.getElementById('dp-grid');
  if (!grid) return;
  let html = '';
  for (const sym of TICKERS) {
    const d = dp[sym] || {};
    if (!d.off_exchange_pct && d.off_exchange_pct !== 0) {
      html += `<div class="dp-card"><div class="dp-sym">${escapeHtml(sym)}</div><span style="color:var(--text-muted);font-size:0.8rem">No Data</span></div>`;
      continue;
    }
    const v = fmtVol(d.off_exchange_volume);
    html += '<div class="dp-card">';
    html += `<div class="dp-sym">${escapeHtml(sym)}</div>`;
    html += '<div class="dp-stats">';
    html += `<div class="dp-stat"><div class="val" style="color:var(--accent-red)">${d.off_exchange_pct}%</div><div class="lbl">Dark Pool</div></div>`;
    html += `<div class="dp-stat"><div class="val" style="color:var(--accent-blue)">${d.lit_pct}%</div><div class="lbl">Lit</div></div>`;
    html += `<div class="dp-stat"><div class="val">${v}</div><div class="lbl">DP Vol</div></div>`;
    html += `<div class="dp-stat"><div class="val">${d.avg_off_exchange_30d}%</div><div class="lbl">30d Avg DP</div></div>`;
    html += '</div>';
    html += `<span class="dp-signal ${d.signal || 'NEUTRAL'}">${d.signal || 'NEUTRAL'}</span>`;
    html += '</div>';
  }
  grid.innerHTML = html;
}

// =============================================================
// CFTC COT
// =============================================================

function renderCOT(cot) {
  const tbody = document.getElementById('cot-body');
  if (!tbody) return;
  const codes = ['138741', '209742'];
  let html = '';
  for (const code of codes) {
    const d = cot[code];
    if (!d) {
      html += `<tr><td>${code}</td><td colspan="5" class="loading-td">No Data</td></tr>`;
      continue;
    }
    html += '<tr>';
    html += `<td>${escapeHtml(d.comm_name || code)}</td>`;
    html += `<td>${escapeHtml(d.as_of_date || '?')}</td>`;
    html += `<td class="${(d.asset_manager || {}).net >= 0 ? 'val-green' : 'val-red'}">${fmtComma((d.asset_manager || {}).net)}</td>`;
    html += `<td class="${(d.leveraged_fund || {}).net >= 0 ? 'val-green' : 'val-red'}">${fmtComma((d.leveraged_fund || {}).net)}</td>`;
    html += `<td class="val-blue">${fmtComma((d.dealer || {}).net)}</td>`;
    html += `<td>${fmtComma(d.total_oi)}</td>`;
    html += '</tr>';
  }
  tbody.innerHTML = html;
}

// =============================================================
// BREADTH
// =============================================================

function renderBreadth(breadth) {
  const sig = document.getElementById('breadth-signal');
  if (!sig) return;
  sig.textContent = breadth ? (breadth.signal || 'NEUTRAL') : 'NEUTRAL';
  sig.className = 'breadth-signal ' + ((breadth && breadth.signal) || 'NEUTRAL');

  const detail = document.getElementById('breadth-detail');
  if (!detail) return;
  let html = '';
  if (breadth && breadth.advance_ratio != null) {
    html += `<div class="broad-stat"><span class="lbl">Advance Ratio: </span><span class="val">${breadth.advance_ratio.toFixed(3)}</span></div>`;
  }
  const ad = breadth ? breadth.nyse_advance_decline : null;
  if (ad) {
    html += `<div class="broad-stat"><span class="lbl">Adv/Dec: </span><span class="val">${ad.advances}/${ad.declines}</span></div>`;
  }
  const idx = breadth ? breadth.nyse_index : null;
  if (idx && idx.price) {
    html += `<div class="broad-stat"><span class="lbl">NYSE Index: </span><span class="val">${fmtNum(idx.price)} (${fmtNum(idx.change_pct)}%)</span></div>`;
  }
  detail.innerHTML = html || 'No Data';
}

// =============================================================
// SECTORS — full width
// =============================================================

function renderSectors(sectors) {
  const list = document.getElementById('sector-list');
  if (!list) return;
  const entries = [];
  for (const [sym, s] of Object.entries(sectors || {})) {
    if (s && s.price) entries.push({ sym, ...s });
  }
  entries.sort((a, b) => (b.change_pct || 0) - (a.change_pct || 0));

  if (!entries.length) {
    list.innerHTML = '<span class="loading-td">No Data</span>';
    return;
  }

  const maxAbs = Math.max(...entries.map(e => Math.abs(e.change_pct || 0)), 1);
  let html = '';
  for (const e of entries) {
    const pct = e.change_pct || 0;
    const barW = Math.abs(pct) / maxAbs * 100;
    const up = pct >= 0;
    html += '<div class="sector-row">';
    html += `<span class="sector-sym">${escapeHtml(e.sym)}</span>`;
    html += `<span class="sector-name">${escapeHtml(e.name || '')}</span>`;
    html += `<div class="sector-bar"><div class="sector-bar-fill ${up ? 'up' : 'down'}" style="width:${barW}%"></div></div>`;
    html += `<span class="sector-pct" style="color:${up ? 'var(--accent-green)' : 'var(--accent-red)'}">${up ? '+' : ''}${pct.toFixed(2)}%</span>`;
    html += '</div>';
  }
  list.innerHTML = html;
}

// =============================================================
// SCORES — full width
// =============================================================

function renderScores(scores) {
  scoresData = scores;
  renderScoreCards(scores);
  renderScoreBreakdown(currentScoreTicker, scores);
}

function renderScoreCards(scores) {
  const grid = document.getElementById('score-grid');
  if (!grid) return;
  let html = '';
  for (const sym of TICKERS) {
    const sc = scores[sym] || {};
    if (!sc.signal) {
      html += `<div class="score-card"><div class="score-sym">${escapeHtml(sym)}</div><span class="no-data">No Score Data</span></div>`;
      continue;
    }
    const sigClass = (sc.signal || '').toLowerCase().replace(/_/g, '-');
    const bp = sc.bullish_pct || 0;
    const bop = sc.bearish_pct || 0;
    html += '<div class="score-card">';
    html += `<div class="score-sym">${escapeHtml(sym)}</div>`;
    html += `<div class="score-signal-big ${sigClass}">${sc.signal}</div>`;
    html += '<div class="score-bar-wrap">';
    html += `<div class="score-bar-bull" style="width:${bp}%"></div>`;
    html += `<div class="score-bar-bear" style="width:${bop}%"></div>`;
    html += '</div>';
    html += '<div class="score-pcts">';
    html += `<span class="bull-pct">Bull ${bp}%</span>`;
    html += `<span class="bear-pct">Bear ${bop}%</span>`;
    html += '</div>';
    html += `<div class="score-ws">Weighted Score: ${sc.weighted_score != null ? (sc.weighted_score >= 0 ? '+' : '') + sc.weighted_score.toFixed(1) : '--'}</div>`;
    html += '</div>';
  }
  grid.innerHTML = html;
}

function switchScoreTicker(ticker) {
  currentScoreTicker = ticker;
  document.querySelectorAll('#score-ticker-tabs .tab-btn').forEach(b => b.classList.remove('active'));
  if (event && event.target) event.target.classList.add('active');
  // Also activate the correct button if event is missing
  if (!event || !event.target) {
    const btns = document.querySelectorAll('#score-ticker-tabs .tab-btn');
    btns.forEach(b => { if (b.textContent === ticker) b.classList.add('active'); });
  }
  renderScoreBreakdown(ticker, scoresData);
}

function renderScoreBreakdown(ticker, scores) {
  const tbody = document.getElementById('score-body');
  if (!tbody || !scores) return;
  const sc = scores[ticker] || {};
  const indicators = sc.indicators || [];
  if (!indicators.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="loading-td">No Score Data</td></tr>';
    return;
  }
  let html = '';
  for (const ind of indicators) {
    const cls = ind.score >= 10 ? 'val-green' : ind.score <= -10 ? 'val-red' : 'val-blue';
    html += '<tr>';
    html += `<td>${escapeHtml(ind.name)}</td>`;
    html += `<td>${ind.value != null ? (typeof ind.value === 'number' ? ind.value.toFixed(2) : escapeHtml(String(ind.value))) : '--'}</td>`;
    html += `<td class="${cls}">${ind.score != null ? (ind.score >= 0 ? '+' : '') + ind.score : '--'}</td>`;
    html += `<td style="color:var(--accent-red)">${ind.bear_pct}%</td>`;
    html += `<td style="color:var(--accent-green)">${ind.bull_pct}%</td>`;
    html += `<td style="font-size:0.8rem;color:var(--text-muted);max-width:260px">${escapeHtml(ind.detail || '')}</td>`;
    html += '</tr>';
  }
  tbody.innerHTML = html;
}

// =============================================================
// MARKDOWN GENERATION
// =============================================================

function renderMarkdown(data) {
  const output = document.getElementById('markdown-output');
  if (!output || !data) return;

  const meta = data.meta || {};
  const lines = [];

  lines.push('# Quant Data Fetcher — Raw Data Export');
  lines.push('');
  lines.push('> Generated: ' + (meta.timestamp || '?'));
  lines.push('> Fetch time: ' + (meta.fetch_seconds != null ? meta.fetch_seconds + 's' : '?'));
  lines.push('> Data sources: ' + ((meta.data_sources || []).join(', ') || '?'));
  lines.push('');

  // ── Ticker Quotes ──
  lines.push('## Main Tickers');
  lines.push('');
  lines.push('| Symbol | Price | Change | Change% | Day High | Day Low | Volume | Avg Vol | 52W High | 52W Low |');
  lines.push('|--------|-------|--------|---------|----------|---------|--------|---------|----------|----------|');
  const tickers = data.tickers || {};
  for (const sym of TICKERS) {
    const q = tickers[sym] || {};
    lines.push(`| ${sym} | ${fmtMd(q.price)} | ${fmtMd(q.change)} | ${fmtMdPct(q.change_pct)} | ${fmtMd(q.day_high)} | ${fmtMd(q.day_low)} | ${fmtMdVol(q.volume)} | ${fmtMdVol(q.avg_volume)} | ${fmtMd(q.week52_high)} | ${fmtMd(q.week52_low)} |`);
  }
  lines.push('');

  // ── Technical Indicators ──
  lines.push('## Technical Indicators (Finviz)');
  lines.push('');
  const finviz = data.finviz || {};
  const techRows = [
    ['RSI (14)', 'rsi_14'],
    ['ATR (14)', 'atr_14'],
    ['SMA 20%', 'sma20_pct'],
    ['SMA 50%', 'sma50_pct'],
    ['SMA 200%', 'sma200_pct'],
    ['Perf Week', 'perf_week'],
    ['Perf Month', 'perf_month'],
    ['Perf YTD', 'perf_ytd'],
    ['Perf Year', 'perf_year'],
  ];
  lines.push('| Indicator | ' + TICKERS.join(' | ') + ' |');
  lines.push('|-----------|' + TICKERS.map(() => '------').join('|') + '|');
  for (const [label, key] of techRows) {
    const vals = TICKERS.map(s => fmtMd(((finviz[s] || {})[key])));
    lines.push(`| ${label} | ${vals.join(' | ')} |`);
  }
  lines.push('');

  // ── Macro ──
  lines.push('## Macro Indicators');
  lines.push('');
  const macro = data.macro || {};
  lines.push('| Symbol | Price | Change% |');
  lines.push('|--------|-------|---------|');
  for (const name of ['VIX', 'DXY', 'US10Y', 'GOLD', 'HYG', 'JNK']) {
    const m = macro[name] || {};
    lines.push(`| ${name} | ${fmtMd(m.price)} | ${fmtMdPct(m.change_pct)} |`);
  }
  lines.push('');

  // ── FRED ──
  const fred = data.fred || {};
  if (Object.keys(fred).length) {
    lines.push('## FRED Economic Data');
    lines.push('');
    lines.push('| Series | Latest Value | Date |');
    lines.push('|--------|-------------|------|');
    for (const [key, f] of Object.entries(fred)) {
      lines.push(`| ${key} | ${fmtMd(f.latest_value)} | ${f.latest_date || '?'} |`);
    }
    lines.push('');
  }

  // ── Sentiment ──
  lines.push('## Market Sentiment');
  lines.push('');
  const sentiment = data.sentiment || {};
  if (sentiment.score != null) {
    lines.push(`- **CNN Fear & Greed**: ${sentiment.score} (${sentiment.rating || '?'})`);
  }
  const aaii = data.aaii || {};
  if (aaii.bullish != null) {
    lines.push(`- **AAII Bullish**: ${aaii.bullish.toFixed(1)}%`);
    lines.push(`- **AAII Neutral**: ${(aaii.neutral || 0).toFixed(1)}%`);
    lines.push(`- **AAII Bearish**: ${(aaii.bearish || 0).toFixed(1)}%`);
    lines.push(`- **Bull-Bear Spread**: ${(aaii.bull_bear_spread != null ? aaii.bull_bear_spread.toFixed(1) : '?')}`);
    lines.push(`- **Date**: ${aaii.date || '?'}`);
  }
  lines.push('');

  // ── Dark Pool ──
  lines.push('## Dark Pool / Off-Exchange Volume');
  lines.push('');
  const dp = data.dark_pool || {};
  for (const sym of TICKERS) {
    const d = dp[sym] || {};
    if (d.off_exchange_pct != null) {
      lines.push(`- **${sym}**: Off-Exchange ${d.off_exchange_pct}% / Lit ${d.lit_pct}% / 30d Avg ${d.avg_off_exchange_30d}% → ${d.signal || 'NEUTRAL'}`);
    }
  }
  lines.push('');

  // ── CFTC COT ──
  const cot = data.cftc_cot || {};
  if (Object.keys(cot).length) {
    lines.push('## CFTC COT — Institutional Positioning');
    lines.push('');
    lines.push('| Commodity | Date | Asset Mgr Net | Lev Fund Net | Dealer Net | Total OI |');
    lines.push('|-----------|------|---------------|--------------|------------|----------|');
    for (const [code, c] of Object.entries(cot)) {
      lines.push(`| ${c.comm_name || code} | ${c.as_of_date || '?'} | ${fmtMdComma((c.asset_manager || {}).net)} | ${fmtMdComma((c.leveraged_fund || {}).net)} | ${fmtMdComma((c.dealer || {}).net)} | ${fmtMdComma(c.total_oi)} |`);
    }
    lines.push('');
  }

  // ── Market Breadth ──
  const breadth = data.market_breadth || {};
  if (breadth.signal) {
    lines.push('## Market Breadth');
    lines.push('');
    lines.push(`- **Signal**: ${breadth.signal}`);
    if (breadth.advance_ratio != null) lines.push(`- **Advance Ratio**: ${breadth.advance_ratio.toFixed(3)}`);
    const ad = breadth.nyse_advance_decline;
    if (ad) lines.push(`- **NYSE Adv/Dec**: ${ad.advances}/${ad.declines}`);
    lines.push('');
  }

  // ── Sectors ──
  const sectors = data.sectors || {};
  if (Object.keys(sectors).length) {
    lines.push('## Sector Performance');
    lines.push('');
    lines.push('| Symbol | Name | Price | Change% |');
    lines.push('|--------|------|-------|---------|');
    for (const [sym, s] of Object.entries(sectors)) {
      if (s && s.price) lines.push(`| ${sym} | ${s.name || ''} | ${fmtMd(s.price)} | ${fmtMdPct(s.change_pct)} |`);
    }
    lines.push('');
  }

  // ── Historical 30-Day OHLC ──
  const hist = data.historical_prices || {};
  const hasHist = Object.values(hist).some(v => Array.isArray(v) && v.length > 0);
  if (hasHist) {
    lines.push('## Historical 30-Day OHLC');
    lines.push('');
    for (const sym of TICKERS) {
      const bars = hist[sym] || [];
      if (!bars.length) continue;
      lines.push(`### ${sym}`);
      const first = bars[0];
      const last = bars[bars.length - 1];
      if (first && last && first.close != null && last.close != null) {
        const pct = ((last.close - first.close) / first.close * 100);
        lines.push(`- Range: ${Math.min(...bars.map(b => b.low || Infinity)).toFixed(2)} – ${Math.max(...bars.map(b => b.high || 0)).toFixed(2)}`);
        lines.push(`- ${first.date} → ${last.date}: ${first.close.toFixed(2)} → ${last.close.toFixed(2)} (${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%)`);
      }
      lines.push('');
      lines.push('| Date | Open | High | Low | Close | Volume |');
      lines.push('|------|------|------|-----|-------|--------|');
      for (const bar of bars) {
        lines.push(`| ${bar.date} | ${fmtMd(bar.open)} | ${fmtMd(bar.high)} | ${fmtMd(bar.low)} | ${fmtMd(bar.close)} | ${fmtMdVol(bar.volume)} |`);
      }
      lines.push('');
    }
  }

  // ── Scores ──
  const scores = data.scores || {};
  const scoreTickers = ['SPY', 'GDXU', 'SOXX', 'MARKET'];
  const hasScores = scoreTickers.some(s => scores[s] && scores[s].signal);
  if (hasScores) {
    lines.push('## AI Score Assessment');
    lines.push('');
    for (const sym of scoreTickers) {
      const sc = scores[sym] || {};
      if (!sc.signal) continue;
      lines.push(`### ${sym}`);
      lines.push(`- **Signal**: ${sc.signal}`);
      lines.push(`- **Weighted Score**: ${sc.weighted_score != null ? sc.weighted_score.toFixed(1) : '?'}`);
      lines.push(`- **Bullish**: ${sc.bullish_pct || 0}% / **Bearish**: ${sc.bearish_pct || 0}%`);
      lines.push('');
      lines.push('| Indicator | Value | Score | Bear% | Bull% | Detail |');
      lines.push('|-----------|-------|-------|-------|-------|--------|');
      for (const ind of (sc.indicators || [])) {
        const v = ind.value != null ? (typeof ind.value === 'number' ? ind.value.toFixed(2) : String(ind.value)) : '--';
        lines.push(`| ${ind.name} | ${v} | ${ind.score} | ${ind.bear_pct}% | ${ind.bull_pct}% | ${ind.detail || ''} |`);
      }
      lines.push('');
    }
  }

  // ── Errors ──
  if (meta.errors && meta.errors.length) {
    lines.push('## Errors');
    lines.push('');
    for (const e of meta.errors) lines.push(`- ${e}`);
    lines.push('');
  }

  output.textContent = lines.join('\n');
}

function copyMarkdown() {
  const output = document.getElementById('markdown-output');
  if (!output || output.textContent === 'Loading data...') return;
  navigator.clipboard.writeText(output.textContent).then(() => {
    const btn = document.getElementById('btn-copy-md');
    if (btn) {
      const orig = btn.textContent;
      btn.textContent = 'Copied!';
      btn.classList.add('copied');
      setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 2000);
    }
  }).catch(() => {
    // Fallback
    const ta = document.createElement('textarea');
    ta.value = output.textContent;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    const btn = document.getElementById('btn-copy-md');
    if (btn) {
      btn.textContent = 'Copied!';
      setTimeout(() => { btn.textContent = 'Copy Markdown'; }, 2000);
    }
  });
}

// =============================================================
// HISTORICAL 30-DAY OHLC CHART
// =============================================================

function renderHistorical(historical) {
  const grid = document.getElementById('historical-grid');
  if (!grid) return;

  let html = '';
  for (const sym of TICKERS) {
    const bars = historical[sym] || [];
    html += '<div class="hist-card">';
    html += `<div class="hist-sym">${escapeHtml(sym)}</div>`;
    if (!bars.length) {
      html += '<div class="hist-no-data">No Data</div>';
    } else {
      const uid = 'hist-canvas-' + sym.replace(/[^a-zA-Z0-9]/g, '_');
      html += `<canvas class="hist-canvas" id="${uid}" width="460" height="200"></canvas>`;
      html += `<div class="hist-stats"><span class="hist-stat" id="${uid}-stats"></span></div>`;
    }
    html += '</div>';
  }
  grid.innerHTML = html;

  // Draw canvases after DOM update
  for (const sym of TICKERS) {
    const bars = historical[sym] || [];
    if (!bars.length) continue;
    const uid = 'hist-canvas-' + sym.replace(/[^a-zA-Z0-9]/g, '_');
    drawOHLCChart(uid, bars);
  }
}

function drawOHLCChart(canvasId, bars) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width;
  const H = canvas.height;

  // Margins
  const margin = { top: 14, right: 16, bottom: 28, left: 46 };
  const plotW = W - margin.left - margin.right;
  const plotH = H - margin.top - margin.bottom;

  // Compute price range
  let minP = Infinity, maxP = -Infinity;
  for (const bar of bars) {
    if (bar.high != null && bar.high > maxP) maxP = bar.high;
    if (bar.low != null && bar.low < minP) minP = bar.low;
  }
  if (!isFinite(minP)) return;

  const pad = (maxP - minP) * 0.06 || 1;
  minP -= pad;
  maxP += pad;
  const priceToY = (p) => margin.top + plotH * (1 - (p - minP) / (maxP - minP));

  ctx.clearRect(0, 0, W, H);

  // Grid lines + price labels
  ctx.strokeStyle = '#1e2d47';
  ctx.lineWidth = 0.5;
  for (let i = 0; i <= 4; i++) {
    const y = margin.top + (plotH / 4) * i;
    ctx.beginPath();
    ctx.moveTo(margin.left, y);
    ctx.lineTo(W - margin.right, y);
    ctx.stroke();
    const val = maxP - (maxP - minP) * (i / 4);
    ctx.fillStyle = '#64748b';
    ctx.font = '9px "Segoe UI", monospace';
    ctx.textAlign = 'right';
    ctx.fillText(val.toFixed(1), margin.left - 6, y + 3);
  }

  const barGap = plotW / bars.length;
  const barW = Math.max(barGap * 0.6, 1.5);

  for (let i = 0; i < bars.length; i++) {
    const bar = bars[i];
    if (bar.high == null || bar.low == null) continue;

    const x = margin.left + barGap * i + barGap / 2;
    const highY = priceToY(bar.high);
    const lowY = priceToY(bar.low);
    const closeY = bar.close != null ? priceToY(bar.close) : null;
    const openY = bar.open != null ? priceToY(bar.open) : null;

    const isUp = bar.close != null && bar.open != null && bar.close >= bar.open;
    const color = isUp ? '#00d4aa' : '#ff4757';

    // High-low line
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(x, highY);
    ctx.lineTo(x, lowY);
    ctx.stroke();

    // Open tick left
    if (openY != null) {
      ctx.beginPath();
      ctx.moveTo(x - barW / 2, openY);
      ctx.lineTo(x, openY);
      ctx.stroke();
    }

    // Close tick right
    if (closeY != null) {
      ctx.beginPath();
      ctx.moveTo(x, closeY);
      ctx.lineTo(x + barW / 2, closeY);
      ctx.stroke();
    }

    // Date label every 5 days
    if (i % 5 === 0 || i === bars.length - 1) {
      ctx.fillStyle = '#64748b';
      ctx.font = '8px "Segoe UI", monospace';
      ctx.textAlign = 'center';
      ctx.fillText(bar.date.slice(5), x, margin.top + plotH + 14);
    }
  }

  // Summary: first → last close
  const first = bars[0];
  const last = bars[bars.length - 1];
  if (first && last && first.close != null && last.close != null) {
    const pct = ((last.close - first.close) / first.close * 100);
    const label = `${last.close.toFixed(2)} (${pct >= 0 ? '+' : ''}${pct.toFixed(1)}% / 30d)`;
    ctx.fillStyle = pct >= 0 ? '#00d4aa' : '#ff4757';
    ctx.font = 'bold 10px "Segoe UI", monospace';
    ctx.textAlign = 'right';
    ctx.fillText(label, W - margin.right, margin.top - 2);
  }

  // Update stats text
  const statsEl = document.getElementById(canvasId + '-stats');
  if (statsEl && first && last) {
    const hi = Math.max(...bars.map(b => b.high || 0));
    const lo = Math.min(...bars.filter(b => b.low).map(b => b.low));
    statsEl.textContent = `Range: ${lo.toFixed(1)} – ${hi.toFixed(1)}  |  Prev Close: ${first.close?.toFixed(1)} → Last: ${last.close?.toFixed(1)}`;
  }
}

// =============================================================
// ERRORS
// =============================================================

function renderErrors(errors) {
  const section = document.getElementById('section-errors');
  if (!section) return;
  const log = document.getElementById('error-log');
  const count = document.getElementById('err-count');

  if (!errors || errors.length === 0) {
    section.style.display = 'none';
    return;
  }

  section.style.display = '';
  count.textContent = '(' + errors.length + ')';
  log.innerHTML = errors.map(e => `<div class="err-line">${escapeHtml(String(e))}</div>`).join('');
}

function toggleErrors() {
  const log = document.getElementById('error-log');
  if (log) log.style.display = log.style.display === 'none' ? '' : 'none';
}

// =============================================================
// HELPERS
// =============================================================

function fmtNum(v) {
  if (v == null) return '--';
  if (typeof v === 'string') return v;
  return v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtVol(v) {
  if (v == null || v === 0) return '--';
  const n = Number(v);
  if (n >= 1e9) return (n / 1e9).toFixed(2) + 'B';
  if (n >= 1e6) return (n / 1e6).toFixed(2) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
  return n.toLocaleString();
}

function fmtComma(v) {
  if (v == null) return '--';
  return Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 });
}

function escapeHtml(str) {
  if (str == null) return '';
  const div = document.createElement('div');
  div.textContent = String(str);
  return div.innerHTML;
}

// Markdown-safe formatters (avoid locale commas)
function fmtMd(v) {
  if (v == null) return '--';
  return typeof v === 'number' ? v.toFixed(2) : String(v);
}

function fmtMdPct(v) {
  if (v == null) return '--';
  return (v >= 0 ? '+' : '') + Number(v).toFixed(2) + '%';
}

function fmtMdVol(v) {
  if (v == null || v === 0) return '--';
  const n = Number(v);
  if (n >= 1e9) return (n / 1e9).toFixed(2) + 'B';
  if (n >= 1e6) return (n / 1e6).toFixed(2) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
  return String(Math.round(n));
}

function fmtMdComma(v) {
  if (v == null) return '--';
  return String(Math.round(Number(v)));
}
