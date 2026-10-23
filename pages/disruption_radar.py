import streamlit as st
import streamlit.components.v1 as components
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "port_optimizer"))

def render():
    st.markdown("""
    <style>
    [data-testid="stHeader"]{display:none!important}
    footer{display:none!important}
    .block-container{padding:0!important;max-width:100%!important}
    section[data-testid="stMain"]>div{padding:0!important}
    iframe{border:none!important;display:block!important}
    </style>
    """, unsafe_allow_html=True)

    # ── Auto-refresh state ────────────────────────────────────────────────────
    REFRESH_INTERVAL = 1800  # 30 minutes in seconds

    if "radar_last_fetch" not in st.session_state:
        st.session_state.radar_last_fetch = 0
        st.session_state.radar_data = None

    now = time.time()
    age_seconds = now - st.session_state.radar_last_fetch
    force = age_seconds >= REFRESH_INTERVAL or st.session_state.radar_data is None

    with st.spinner("Chargement des événements maritimes..."):
        try:
            from scraper import run_scraper
            data = run_scraper(force_refresh=True)
            st.session_state.radar_data = data
            st.session_state.radar_last_fetch = now
        except Exception as e:
            if st.session_state.radar_data:
                data = st.session_state.radar_data
            else:
                st.error(f"Erreur pipeline: {e}")
                return

    alerts = data.get("alerts", [])
    vessel_impacts = data.get("vessel_impacts", [])
    recalibrations = data.get("recalibrations", [])
    summary = data.get("summary", {})
    scraped_at = data.get("scraped_at", "Unknown")

    # ── Age label for "Dernière mise à jour" ──────────────────────────────────
    ts = data.get("timestamp", now)
    age_min = int((now - ts) / 60)
    if age_min < 2:
        age_label = "il y a moins de 2 minutes"
    elif age_min < 60:
        age_label = f"il y a {age_min} minutes"
    else:
        age_label = f"il y a {age_min // 60}h {age_min % 60}min"

    alerts_json       = json.dumps(alerts)
    vessels_json      = json.dumps(vessel_impacts)
    summary_json      = json.dumps(summary)
    recalib_json      = json.dumps(recalibrations)

    HTML = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --blue:#0057B8;--blue-light:#EBF2FF;
  --green:#00875A;--green-light:#E3F5EE;
  --red:#C0392B;--red-light:#FDECEA;
  --orange:#D97706;--orange-light:#FEF3C7;
  --yellow:#F59E0B;--yellow-light:#FFFBEB;
  --purple:#6B21A8;--purple-light:#F3E8FF;
  --gray-50:#F8F9FA;--gray-100:#F0F2F5;--gray-200:#E4E7EC;
  --gray-400:#98A2B3;--gray-500:#667085;--gray-600:#475467;
  --gray-700:#344054;--gray-800:#1D2939;--gray-900:#101828;
  --white:#FFFFFF;
  --shadow-sm:0 1px 3px rgba(16,24,40,0.1);
  --shadow-md:0 4px 12px rgba(16,24,40,0.1);
  --font:'Inter',sans-serif;
}}
html,body{{background:var(--gray-100);font-family:var(--font);font-size:13px;color:var(--gray-800);min-height:100vh}}

/* TOPBAR */
.topbar{{background:var(--white);border-bottom:1px solid var(--gray-200);display:flex;align-items:center;justify-content:space-between;padding:0 28px;height:52px;box-shadow:var(--shadow-sm)}}
.tb-left{{display:flex;align-items:center;gap:8px}}
.tb-logo{{width:28px;height:28px;background:var(--blue);border-radius:5px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:12px;color:white}}
.tb-name{{font-weight:700;font-size:15px;color:var(--gray-900)}}
.tb-sep{{color:var(--gray-300);margin:0 4px}}
.tb-page{{font-size:13px;color:var(--gray-500);font-weight:500}}
.tb-right{{display:flex;align-items:center;gap:14px}}
.live-pill{{display:flex;align-items:center;gap:5px;background:#FDECEA;border-radius:20px;padding:4px 10px;font-size:11px;font-weight:600;color:var(--red)}}
.ldot{{width:5px;height:5px;border-radius:50%;background:var(--red);animation:pulse 1s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}
.tb-time{{font-size:11px;color:var(--gray-400)}}
.last-update{{font-size:11px;color:var(--gray-400);display:flex;align-items:center;gap:4px}}
.last-update::before{{content:'🕐';font-size:10px}}

/* URGENT ALERT BAR */
.alert-bar{{background:#FFF8E1;border-bottom:2px solid #FFE082;padding:0 28px;display:flex;align-items:center;gap:14px;height:40px;overflow:hidden}}
.alert-bar-label{{font-size:10px;font-weight:700;color:#E65100;letter-spacing:.1em;text-transform:uppercase;flex-shrink:0;background:#FFE082;padding:3px 8px;border-radius:4px;white-space:nowrap}}
.ticker-track{{overflow:hidden;flex:1;height:20px;position:relative}}
.ticker-inner{{display:flex;gap:48px;white-space:nowrap;animation:scroll 30s linear infinite;align-items:center}}
@keyframes scroll{{0%{{transform:translateX(0)}}100%{{transform:translateX(-50%)}}}}
.tick-item{{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--gray-700);flex-shrink:0;font-weight:500}}
.tick-dot{{width:7px;height:7px;border-radius:50%;flex-shrink:0}}
.dot-red{{background:var(--red)}}.dot-orange{{background:var(--orange)}}.dot-green{{background:var(--green)}}

/* PAGE */
.page{{padding:20px 28px}}
.sec-label{{font-size:10px;font-weight:700;color:var(--gray-400);letter-spacing:.1em;text-transform:uppercase;margin-bottom:12px;display:flex;align-items:center;gap:8px}}
.sec-label::after{{content:'';flex:1;height:1px;background:var(--gray-200)}}

/* KPI ROW */
.kpi-row{{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin-bottom:20px}}
.kpi{{background:var(--white);border:1px solid var(--gray-200);border-radius:8px;padding:16px 18px;box-shadow:var(--shadow-sm);position:relative;overflow:hidden}}
.kpi::after{{content:'';position:absolute;top:0;left:0;width:3px;height:100%;background:var(--blue)}}
.kpi.red::after{{background:var(--red)}}.kpi.orange::after{{background:var(--orange)}}.kpi.green::after{{background:var(--green)}}.kpi.purple::after{{background:var(--purple)}}
.kl{{font-size:10px;font-weight:600;color:var(--gray-500);letter-spacing:.05em;text-transform:uppercase;margin-bottom:5px}}
.kv{{font-size:28px;font-weight:700;color:var(--gray-900);line-height:1;letter-spacing:-.5px}}
.kv.red{{color:var(--red)}}.kv.orange{{color:var(--orange)}}.kv.green{{color:var(--green)}}.kv.blue{{color:var(--blue)}}.kv.purple{{color:var(--purple)}}
.ks{{font-size:11px;color:var(--gray-400);margin-top:3px}}

/* ALERT CARDS */
.alerts-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:20px}}
.alert-card{{background:var(--white);border:1px solid var(--gray-200);border-radius:8px;padding:18px;box-shadow:var(--shadow-sm);position:relative;overflow:hidden}}
.alert-card.HIGH{{border-left:4px solid var(--red);background:linear-gradient(to right,#FDECEA,var(--white))}}
.alert-card.MEDIUM{{border-left:4px solid var(--orange);background:linear-gradient(to right,#FEF3C7,var(--white))}}
.alert-card.LOW{{border-left:4px solid var(--green);background:linear-gradient(to right,#E3F5EE,var(--white))}}
.alert-top{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px}}
.alert-badges{{display:flex;gap:5px;align-items:center;flex-wrap:wrap}}
.alert-sev{{display:inline-flex;align-items:center;gap:5px;font-size:10px;font-weight:700;letter-spacing:.08em;padding:3px 8px;border-radius:12px}}
.sev-HIGH{{background:#FDECEA;color:var(--red)}}.sev-MEDIUM{{background:#FEF3C7;color:var(--orange)}}.sev-LOW{{background:#E3F5EE;color:var(--green)}}
.conf-badge{{font-size:10px;font-weight:700;padding:3px 8px;border-radius:12px;background:var(--purple-light);color:var(--purple)}}
.fin-badge{{font-size:10px;font-weight:600;padding:2px 7px;border-radius:10px}}
.fin-HIGH{{background:#FDECEA;color:var(--red)}}.fin-MEDIUM{{background:#FEF3C7;color:var(--orange)}}.fin-LOW{{background:#E3F5EE;color:var(--green)}}
.alert-title{{font-size:14px;font-weight:700;color:var(--gray-900);margin-bottom:6px;line-height:1.3}}
.alert-location{{font-size:11px;color:var(--gray-500);margin-bottom:6px;display:flex;align-items:center;gap:4px}}
/* NLP entity fields row */
.nlp-row{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px}}
.nlp-chip{{display:inline-flex;align-items:center;gap:3px;font-size:10px;font-weight:500;padding:2px 7px;border-radius:8px;background:var(--gray-100);color:var(--gray-600)}}
.nlp-chip .nlp-key{{font-weight:700;color:var(--gray-500);margin-right:2px}}
.cause-congestion{{background:#EFF6FF;color:#1D4ED8}}
.cause-weather{{background:#F0FDF4;color:#166534}}
.cause-strike{{background:#FFF7ED;color:#C2410C}}
.cause-geopolitical{{background:#FDF4FF;color:#7E22CE}}
.cause-infrastructure{{background:#F0F9FF;color:#0369A1}}
.cause-accident{{background:#FEF2F2;color:#991B1B}}
.cause-unknown{{background:var(--gray-100);color:var(--gray-500)}}
.alert-summary{{font-size:12px;color:var(--gray-600);line-height:1.5;margin-bottom:12px}}
.alert-footer{{display:flex;justify-content:space-between;align-items:center;padding-top:10px;border-top:1px solid var(--gray-100)}}
.alert-delay{{font-size:13px;font-weight:700}}
.delay-HIGH{{color:var(--red)}}.delay-MEDIUM{{color:var(--orange)}}.delay-LOW{{color:var(--green)}}
.alert-routes{{display:flex;gap:4px;flex-wrap:wrap}}
.route-tag{{font-size:9px;font-weight:600;padding:2px 6px;border-radius:10px;background:var(--blue-light);color:var(--blue)}}

/* GATE RECALIBRATION PANEL */
.recalib-section{{margin-bottom:20px}}
.recalib-panel{{background:var(--white);border:2px solid #FFE082;border-left:5px solid var(--orange);border-radius:8px;padding:18px;box-shadow:var(--shadow-md);margin-bottom:12px}}
.recalib-header{{display:flex;align-items:center;gap:10px;margin-bottom:14px}}
.recalib-icon{{font-size:18px}}
.recalib-title{{font-size:14px;font-weight:800;color:var(--gray-900)}}
.recalib-subtitle{{font-size:11px;color:var(--gray-500);margin-top:1px}}
.recalib-grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:14px}}
.recalib-field{{background:var(--gray-50);border:1px solid var(--gray-200);border-radius:6px;padding:10px 12px}}
.rf-label{{font-size:9px;font-weight:700;color:var(--gray-400);letter-spacing:.08em;text-transform:uppercase;margin-bottom:3px}}
.rf-value{{font-size:12px;font-weight:600;color:var(--gray-800)}}
.rf-value.highlight{{color:var(--orange);font-size:14px}}
.recalib-carriers{{margin-bottom:14px}}
.rc-label{{font-size:10px;font-weight:700;color:var(--gray-500);letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px}}
.carrier-row{{display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid var(--gray-100);font-size:12px;color:var(--gray-700)}}
.carrier-row:last-child{{border-bottom:none}}
.carrier-icon{{width:20px;height:20px;border-radius:4px;background:var(--orange-light);display:flex;align-items:center;justify-content:center;font-size:11px;flex-shrink:0}}
.recalib-status{{display:inline-flex;align-items:center;gap:6px;background:#FFF8E1;border:1px solid #FFE082;border-radius:20px;padding:5px 14px;font-size:11px;font-weight:700;color:#B45309}}
.status-dot{{width:7px;height:7px;border-radius:50%;background:var(--orange);animation:pulse 1s infinite}}

/* VESSEL TABLE */
.tcard{{background:var(--white);border:1px solid var(--gray-200);border-radius:8px;box-shadow:var(--shadow-sm);overflow:hidden;margin-bottom:20px}}
.thead-row{{padding:14px 18px;border-bottom:1px solid var(--gray-200);display:flex;align-items:center;justify-content:space-between}}
.ttitle{{font-size:13px;font-weight:600;color:var(--gray-800)}}
.tcount{{font-size:11px;color:var(--gray-400);background:var(--gray-100);padding:3px 8px;border-radius:12px}}
table{{width:100%;border-collapse:collapse}}
th{{padding:9px 14px;text-align:left;font-size:10px;font-weight:600;color:var(--gray-500);letter-spacing:.05em;text-transform:uppercase;background:var(--gray-50);border-bottom:1px solid var(--gray-200);white-space:nowrap}}
td{{padding:10px 14px;border-bottom:1px solid var(--gray-100);font-size:12px;color:var(--gray-700);vertical-align:middle}}
tbody tr:last-child td{{border-bottom:none}}
tbody tr:hover td{{background:var(--blue-light)}}
tbody tr.has-recalib td{{background:#FFFBEB}}
tbody tr.has-recalib:hover td{{background:#FEF3C7}}
.vname{{font-weight:600;color:var(--gray-800)}}
.vline{{font-size:10px;color:var(--gray-400);margin-top:1px}}
.badge{{display:inline-flex;align-items:center;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:600}}
.bon-time{{background:#E3F5EE;color:var(--green)}}
.bdelayed{{background:#FDECEA;color:var(--red)}}
.brecalib{{background:#FEF3C7;color:var(--orange);margin-left:4px}}
.route-badge{{background:var(--blue-light);color:var(--blue);font-size:10px;font-weight:600;padding:2px 7px;border-radius:10px}}
.priority-high{{color:var(--red);font-weight:600}}
.priority-med{{color:var(--orange);font-weight:600}}
.priority-low{{color:var(--gray-400)}}
.delay-cell{{font-weight:700}}
.d-red{{color:var(--red)}}.d-orange{{color:var(--orange)}}.d-green{{color:var(--green)}}
.impacts-cell{{font-size:11px;color:var(--gray-500);max-width:180px}}
.vtype{{font-size:10px;color:var(--gray-400);margin-top:1px}}

/* ROUTE SUMMARY */
.route-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}}
.route-card{{background:var(--white);border:1px solid var(--gray-200);border-radius:8px;padding:18px;box-shadow:var(--shadow-sm)}}
.route-name{{font-size:13px;font-weight:700;color:var(--gray-800);margin-bottom:4px}}
.route-desc{{font-size:11px;color:var(--gray-500);margin-bottom:12px}}
.route-stat{{display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid var(--gray-100);font-size:12px}}
.route-stat:last-child{{border-bottom:none}}
.rs-key{{color:var(--gray-500)}}
.rs-val{{font-weight:600;color:var(--gray-800)}}

/* FOOTER */
.footer{{text-align:center;padding:14px;font-size:11px;color:var(--gray-400);border-top:1px solid var(--gray-200);background:var(--white)}}
</style>
</head>
<body>

<!-- TOPBAR -->
<div class="topbar">
  <div class="tb-left">
    <div class="tb-logo">PQ</div>
    <span class="tb-name">portiq.xyz</span>
    <span class="tb-sep">/</span>
    <span class="tb-page">Veille maritime — perturbations et retards</span>
  </div>
  <div class="tb-right">
    <div class="live-pill"><div class="ldot"></div>LIVE DATA</div>
    <div class="last-update">Dernière mise à jour : {age_label}</div>
    <div class="tb-time" id="clk">--:--:-- UTC</div>
  </div>
</div>

<!-- URGENT ALERT BAR -->
<div class="alert-bar" id="alertBar">
  <div class="alert-bar-label">⚡ Signaux Urgents</div>
  <div class="ticker-track"><div class="ticker-inner" id="ticker"></div></div>
</div>

<!-- PAGE -->
<div class="page">

  <!-- KPI ROW -->
  <div class="sec-label">Tableau de bord</div>
  <div class="kpi-row" id="kpiRow"></div>

  <!-- ALERT CARDS — Événements Portuaires Classifiés -->
  <div class="sec-label">Événements Portuaires Classifiés</div>
  <div class="alerts-grid" id="alertsGrid"></div>

  <!-- GATE RECALIBRATION PANELS -->
  <div id="recalibSection" style="display:none">
    <div class="sec-label">⚡ Recalibration Proposée — Scénario de Démonstration</div>
    <div class="recalib-section" id="recalibPanels"></div>
  </div>

  <!-- ROUTE SUMMARY -->
  <div class="sec-label">Analyse d'Impact par Corridor Maritime</div>
  <div class="route-grid" id="routeGrid"></div>

  <!-- VESSEL TABLE -->
  <div class="sec-label">Évaluation d'Impact — Niveau Navire</div>
  <div class="tcard">
    <div class="thead-row">
      <div class="ttitle">25 Navires Synthétiques — Impact Simulé</div>
      <div class="tcount" id="delayedCount">-- navires impactés</div>
    </div>
    <table>
      <thead><tr>
        <th>Navire</th>
        <th>Origine</th>
        <th>Corridor</th>
        <th>ETA Initial</th>
        <th>Nouvel ETA</th>
        <th>Retard</th>
        <th>Priorité</th>
        <th>Statut</th>
        <th>Événement Déclencheur</th>
      </tr></thead>
      <tbody id="vesselTable"></tbody>
    </table>
  </div>

  <div class="footer">
    portiq.xyz — Système de Veille Maritime — Pipeline d'ingestion Google News RSS — Analyse NLP via Groq llama-3.1-8b-instant —
    Alertes basées sur titres de presse · Délais et scores de confiance = estimations du modèle NLP · Recalibrations = scénarios simulés
  </div>
</div>

<script>
const ALERTS = {alerts_json};
const VESSELS = {vessels_json};
const SUMMARY = {summary_json};
const RECALIBS = {recalib_json};

const SEV_COLOR = {{HIGH:'dot-red', MEDIUM:'dot-orange', LOW:'dot-green'}};
const CAUSE_LABELS = {{
  congestion:'Congestion',geopolitical:'Géopolitique',weather:'Météo',
  strike:'Grève',infrastructure:'Infrastructure',accident:'Accident',unknown:'Inconnu'
}};
const ROUTE_LABELS = {{
  'Asia-Suez':'Asia via Canal de Suez',
  'Europe-Gibraltar':'Europe via Gibraltar',
  'Med-Direct':'Méditerranée Directe',
  'Atlantic':'Trans-Atlantique'
}};

// Clock
function tick(){{const t=new Date().toUTCString().slice(17,25)+' UTC';document.getElementById('clk').textContent=t;}}
setInterval(tick,1000);tick();

// Ticker
function buildTicker(){{
  const tk=document.getElementById('ticker');
  const urgent=ALERTS.filter(a=>a.severity==='HIGH'||a.severity==='MEDIUM');
  if(urgent.length===0){{
    tk.innerHTML='<div class="tick-item"><div class="tick-dot dot-green"></div>Aucune alerte critique — tous les corridors nominaux</div>';
    return;
  }}
  const items=[...urgent,...urgent];
  tk.innerHTML=items.map(a=>`
    <div class="tick-item">
      <div class="tick-dot ${{SEV_COLOR[a.severity]}}"></div>
      [${{a.severity}}] ${{a.title}} — +${{a.delay_hours}}h — ${{a.location}}
      ${{a.confidence?'— Confiance: '+Math.round(a.confidence*100)+'%':''}}
    </div>
  `).join('');
}}

// KPI Row — now 6 cards including recalibrations
function buildKPIs(){{
  const row=document.getElementById('kpiRow');
  const high=SUMMARY.high_severity||0;
  const med=SUMMARY.medium_severity||0;
  const low=SUMMARY.low_severity||0;
  const delayed=SUMMARY.vessels_delayed||0;
  const ontime=SUMMARY.vessels_on_time||0;
  const recal=SUMMARY.recalibrations_triggered||0;
  row.innerHTML=`
    <div class="kpi red"><div class="kl">Sévérité Haute</div><div class="kv red">${{high}}</div><div class="ks">Action immédiate requise</div></div>
    <div class="kpi orange"><div class="kl">Sévérité Moyenne</div><div class="kv orange">${{med}}</div><div class="ks">Surveillance rapprochée</div></div>
    <div class="kpi"><div class="kl">Sévérité Basse</div><div class="kv blue">${{low}}</div><div class="ks">Information</div></div>
    <div class="kpi red"><div class="kl">Navires Retardés</div><div class="kv red">${{delayed}}</div><div class="ks">Ajustements ETA nécessaires</div></div>
    <div class="kpi green"><div class="kl">Navires À Temps</div><div class="kv green">${{ontime}}</div><div class="ks">Aucun impact</div></div>
    <div class="kpi purple"><div class="kl">Recalibrations</div><div class="kv purple">${{recal}}</div><div class="ks">Créneaux camions à décaler</div></div>
  `;
}}

// Alert Cards — with confidence badge + NLP entity chips
function buildAlerts(){{
  const grid=document.getElementById('alertsGrid');
  if(ALERTS.length===0){{
    grid.innerHTML='<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--gray-400)">Aucun événement portuaire détecté.</div>';
    return;
  }}
  grid.innerHTML=ALERTS.map(a=>{{
    const routes=a.affected_routes||[];
    const confPct=a.confidence?Math.round(a.confidence*100):null;
    const causeKey=a.cause||'unknown';
    const causeLabel=CAUSE_LABELS[causeKey]||causeKey;
    const portAff=a.port_affected||a.location||'Global';
    return `
    <div class="alert-card ${{a.severity}}">
      <div class="alert-top">
        <div class="alert-badges">
          <span class="alert-sev sev-${{a.severity}}">${{a.severity}}</span>
          ${{confPct?`<span class="conf-badge">Confiance estimée ${{confPct}}%</span>`:''}}
        </div>
        <span class="fin-badge fin-${{a.financial_impact||'MEDIUM'}}">Impact: ${{a.financial_impact||'MEDIUM'}}</span>
      </div>
      <div class="alert-title">${{a.title}}</div>
      <div class="alert-location">📍 ${{a.location||'Global'}}</div>
      <div class="nlp-row">
        <span class="nlp-chip cause-${{causeKey}}"><span class="nlp-key">Cause</span>${{causeLabel}}</span>
        <span class="nlp-chip"><span class="nlp-key">Port</span>${{portAff}}</span>
      </div>
      <div class="alert-summary">${{a.summary||a.headline}}</div>
      <div class="alert-footer">
        <div class="alert-delay delay-${{a.severity}}">+${{a.delay_hours}}h retard estimé (NLP)</div>
        <div class="alert-routes">${{routes.map(r=>`<span class="route-tag">${{r}}</span>`).join('')}}</div>
      </div>
    </div>`;
  }}).join('');
}}

// Gate Recalibration Panels
function buildRecalib(){{
  const section=document.getElementById('recalibSection');
  const container=document.getElementById('recalibPanels');
  if(!RECALIBS||RECALIBS.length===0){{section.style.display='none';return;}}
  section.style.display='block';
  container.innerHTML=RECALIBS.map(r=>{{
    const carriers=(r.carriers||[]).map((c,i)=>`
      <div class="carrier-row">
        <div class="carrier-icon">🚛</div>
        <span>${{c}}</span>
        <span style="margin-left:auto;font-size:10px;color:var(--orange);font-weight:600">NOTIFICATION EN ATTENTE</span>
      </div>
    `).join('');
    return `
    <div class="recalib-panel">
      <div class="recalib-header">
        <div class="recalib-icon">⚡</div>
        <div>
          <div class="recalib-title">RECALIBRATION PROPOSÉE — ${{r.vessel_name}}</div>
          <div class="recalib-subtitle">Déclenché par: ${{r.alert_title}} · ${{r.vessel_type}}</div>
        </div>
      </div>
      <div class="recalib-grid">
        <div class="recalib-field">
          <div class="rf-label">Retard Détecté</div>
          <div class="rf-value highlight">+${{r.delay_hours}}h</div>
        </div>
        <div class="recalib-field">
          <div class="rf-label">ETA Original</div>
          <div class="rf-value">${{r.original_eta}}</div>
        </div>
        <div class="recalib-field">
          <div class="rf-label">Nouvel ETA Estimé</div>
          <div class="rf-value" style="color:var(--red)">${{r.new_eta}}</div>
        </div>
        <div class="recalib-field" style="grid-column:1/-1">
          <div class="rf-label">Nouvelle Fenêtre de Livraison Proposée</div>
          <div class="rf-value highlight">${{r.window_open}} — ${{r.window_close}}</div>
        </div>
      </div>
      <div class="recalib-carriers">
        <div class="rc-label">Transporteurs Affectés (${{(r.carriers||[]).length}})</div>
        ${{carriers}}
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div class="recalib-status"><div class="status-dot"></div>${{r.status}}</div>
        <span style="font-size:10px;color:var(--gray-400)">Validation opérateur requise avant notification automatique</span>
      </div>
      <div style="margin-top:10px;padding:6px 10px;background:#F0F2F5;border-radius:5px;font-size:10px;color:#667085;text-align:center">
        ⚠ Scénario de démonstration — recalibration simulée · Les créneaux et transporteurs sont synthétiques
      </div>
    </div>`;
  }}).join('');
}}

// Route Grid
function buildRoutes(){{
  const grid=document.getElementById('routeGrid');
  const routes=['Asia-Suez','Europe-Gibraltar','Med-Direct','Atlantic'];
  grid.innerHTML=routes.map(route=>{{
    const vessels=VESSELS.filter(v=>v.route===route);
    const delayed=vessels.filter(v=>v.status==='DELAYED');
    const maxDelay=delayed.length>0?Math.max(...delayed.map(v=>v.total_delay_hours)):0;
    const alerts=ALERTS.filter(a=>(a.affected_routes||[]).includes(route));
    return `
    <div class="route-card">
      <div class="route-name">${{route}}</div>
      <div class="route-desc">${{ROUTE_LABELS[route]||route}}</div>
      <div class="route-stat"><span class="rs-key">Navires</span><span class="rs-val">${{vessels.length}}</span></div>
      <div class="route-stat"><span class="rs-key">Retardés</span><span class="rs-val" style="color:${{delayed.length>0?'var(--red)':'var(--green)'}}">${{delayed.length}}</span></div>
      <div class="route-stat"><span class="rs-key">Retard Max</span><span class="rs-val" style="color:${{maxDelay>0?'var(--red)':'var(--green)'}}">${{maxDelay>0?'+'+maxDelay+'h':'Aucun'}}</span></div>
      <div class="route-stat"><span class="rs-key">Alertes Actives</span><span class="rs-val">${{alerts.length}}</span></div>
    </div>`;
  }}).join('');
}}

// Vessel Table — with vessel_type, recalibration badge
function buildVesselTable(){{
  const tb=document.getElementById('vesselTable');
  const delayed=VESSELS.filter(v=>v.status==='DELAYED').length;
  document.getElementById('delayedCount').textContent=delayed+' navires impactés';

  tb.innerHTML=VESSELS.map(v=>{{
    const pc=v.priority===1?'priority-high':v.priority===2?'priority-med':'priority-low';
    const pl=v.priority===1?'HAUTE':v.priority===2?'MED':'BASSE';
    const dc=v.total_delay_hours>=24?'d-red':v.total_delay_hours>0?'d-orange':'d-green';
    const causes=(v.impacted_by||[]).map(i=>i.alert_title).join(', ')||'—';
    const hasRecalib=!!v.recalibration;
    return `
    <tr class="${{hasRecalib?'has-recalib':''}}">
      <td>
        <div class="vname">${{v.name}}</div>
        <div class="vline">${{v.shipping_line}}</div>
        <div class="vtype">${{v.vessel_type||''}}</div>
      </td>
      <td style="color:var(--gray-600)">${{v.origin_port}}, ${{v.origin_country}}</td>
      <td><span class="route-badge">${{v.route}}</span></td>
      <td style="color:var(--gray-500)">${{v.eta}}</td>
      <td style="font-weight:${{v.status==='DELAYED'?'600':'400'}};color:${{v.status==='DELAYED'?'var(--red)':'var(--gray-700)'}}">${{v.new_eta}}</td>
      <td class="delay-cell ${{dc}}">${{v.total_delay_hours>0?'+'+v.total_delay_hours+'h':'Aucun'}}</td>
      <td class="${{pc}}">${{pl}}</td>
      <td>
        <span class="badge ${{v.status==='DELAYED'?'bdelayed':'bon-time'}}">${{v.status==='DELAYED'?'RETARDÉ':'À TEMPS'}}</span>
        ${{hasRecalib?'<span class="badge brecalib">⚡ RECAL</span>':''}}
      </td>
      <td class="impacts-cell">${{causes}}</td>
    </tr>`;
  }}).join('');
}}

window.addEventListener('load',()=>{{
  buildTicker();
  buildKPIs();
  buildAlerts();
  buildRecalib();
  buildRoutes();
  buildVesselTable();
}});
</script>
</body></html>"""

    components.html(HTML, height=2800, scrolling=True)