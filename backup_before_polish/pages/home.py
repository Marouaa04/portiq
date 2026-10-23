import streamlit as st
import streamlit.components.v1 as components
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'port_optimizer'))


def get_platform_stats():
    try:
        from portwatch_connector import run_portwatch
        data = run_portwatch(force_refresh=False)
        avg_calls = data.get("summary", {}).get("avg_daily_calls", 12.7)
        latest_date = data.get("summary", {}).get("latest_date", "N/A")
    except Exception:
        avg_calls = 12.7
        latest_date = "N/A"
    return avg_calls, latest_date


@st.cache_data(show_spinner=False)
def solve_scenario():
    """Run optimizer once, cache the result — both home and optimizer pages use same numbers."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from pages.port_optimizer import load_data, PortOptimizer, run_fcfs
    vessels, berths = load_data()
    opt = PortOptimizer(vessels, berths)
    opt.solve()
    fcfs = run_fcfs(vessels, berths)
    ft = sum(r["wait_hours"] for r in fcfs)
    return dict(
        opt_schedule=opt.schedule,
        opt_avg=round(opt.avg_wait(), 1),
        opt_total=round(opt.total_wait(), 1),
        fcfs_schedule=fcfs,
        fcfs_avg=round(ft / len(fcfs), 1) if fcfs else 0,
        fcfs_total=round(ft, 1),
    )


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

    avg_calls, latest_date = get_platform_stats()

    # ── Solve once and store in session state ─────────────────────────────────
    if not st.session_state.get("port_solved", False):
        try:
            r = solve_scenario()
            st.session_state.port_opt_schedule  = r["opt_schedule"]
            st.session_state.port_opt_avg       = r["opt_avg"]
            st.session_state.port_opt_total     = r["opt_total"]
            st.session_state.port_fcfs_schedule = r["fcfs_schedule"]
            st.session_state.port_fcfs_avg      = r["fcfs_avg"]
            st.session_state.port_fcfs_total    = r["fcfs_total"]
            st.session_state.port_solved        = True
        except Exception as e:
            st.warning(f"Optimiseur indisponible : {e} — chiffres non disponibles.")

    opt_avg    = st.session_state.get("port_opt_avg", 0)
    fcfs_avg   = st.session_state.get("port_fcfs_avg", 0)
    opt_total  = st.session_state.get("port_opt_total", 0)
    fcfs_total = st.session_state.get("port_fcfs_total", 0)
    hours_saved  = round(fcfs_total - opt_total, 1)
    improvement  = round((fcfs_total - opt_total) / fcfs_total * 100, 1) if fcfs_total else 0.0
    demurrage    = round(hours_saved * 10000)
 
    HTML = f"""<!DOCTYPE html>
<html lang="fr" id="root">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#FFFFFF;--bg2:#F8F9FA;--surface:#FFFFFF;
  --border:#E4E7EC;--border2:#D0D5DD;
  --blue:#0057B8;--blue-light:#EBF2FF;--blue-dark:#003D82;
  --green:#00875A;--green-light:#E3F5EE;
  --gray-400:#98A2B3;--gray-500:#667085;--gray-600:#475467;
  --gray-700:#344054;--gray-800:#1D2939;--gray-900:#101828;
  --text:#1D2939;--text2:#667085;
  --shadow-sm:0 1px 3px rgba(16,24,40,0.1);
  --shadow-md:0 4px 12px rgba(16,24,40,0.1);
  --font:'Inter',sans-serif;
}}
html,body{{background:var(--bg);font-family:var(--font);color:var(--text);min-height:100vh}}
.topbar{{background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;padding:0 40px;height:60px;position:sticky;top:0;z-index:100;box-shadow:var(--shadow-sm)}}
.brand{{display:flex;align-items:center;gap:12px}}
.brand-logo{{width:36px;height:36px;background:var(--blue);border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:14px;color:white}}
.brand-name{{font-weight:800;font-size:18px;color:var(--text);letter-spacing:-.3px}}
.brand-tagline{{font-size:11px;color:var(--text2);margin-top:1px}}
.hero{{background:linear-gradient(135deg,#003D82 0%,#0057B8 40%,#0072E5 70%,#00875A 100%);padding:72px 40px 80px;position:relative;overflow:hidden}}
.hero::before{{content:'';position:absolute;top:-100px;right:-100px;width:500px;height:500px;background:radial-gradient(circle,rgba(255,255,255,0.08) 0%,transparent 70%)}}
.hero::after{{content:'';position:absolute;bottom:-80px;left:200px;width:400px;height:400px;background:radial-gradient(circle,rgba(0,135,90,0.2) 0%,transparent 70%)}}
.hero-inner{{max-width:700px;position:relative;z-index:2}}
.hero-eyebrow{{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.25);border-radius:20px;padding:5px 14px;font-size:11px;font-weight:600;color:rgba(255,255,255,0.9);letter-spacing:.06em;text-transform:uppercase;margin-bottom:20px}}
.hero-title{{font-size:clamp(32px,4vw,54px);font-weight:800;color:white;line-height:1.08;letter-spacing:-.5px;margin-bottom:16px}}
.hero-title span{{color:#7DD9C0}}
.hero-subtitle{{font-size:16px;color:rgba(255,255,255,0.75);line-height:1.65;margin-bottom:32px;max-width:560px}}
.hero-actions{{display:flex;gap:12px;flex-wrap:wrap}}
.btn-primary{{background:white;color:var(--blue);border:none;padding:12px 24px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.15)}}
.btn-primary:hover{{background:#f0f4ff}}
.btn-secondary{{background:rgba(255,255,255,0.12);color:white;border:1px solid rgba(255,255,255,0.3);padding:12px 24px;border-radius:8px;font-weight:600;font-size:13px;cursor:pointer}}
.btn-secondary:hover{{background:rgba(255,255,255,0.2)}}
.hero-stats{{display:flex;margin-top:48px;background:rgba(255,255,255,0.1);border-radius:12px;border:1px solid rgba(255,255,255,0.15);overflow:hidden;backdrop-filter:blur(10px)}}
.hstat{{flex:1;padding:20px 24px;border-right:1px solid rgba(255,255,255,0.12);text-align:center}}
.hstat:last-child{{border-right:none}}
.hstat-num{{font-size:28px;font-weight:800;color:white;letter-spacing:-.5px;line-height:1}}
.hstat-label{{font-size:10px;color:rgba(255,255,255,0.6);text-transform:uppercase;letter-spacing:.08em;margin-top:4px;font-weight:500}}
.section{{padding:56px 40px;background:var(--bg)}}
.section.alt{{background:var(--bg2)}}
.section-center{{text-align:center;margin-bottom:40px}}
.section-eyebrow{{font-size:11px;font-weight:700;color:var(--blue);letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px}}
.section-title{{font-size:28px;font-weight:800;color:var(--text);letter-spacing:-.3px;margin-bottom:10px}}
.section-sub{{font-size:14px;color:var(--text2);line-height:1.6;max-width:520px;margin:0 auto}}
.live-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:32px}}
.live-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:24px;box-shadow:var(--shadow-sm);text-align:center;position:relative;overflow:hidden}}
.live-card::after{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--blue)}}
.live-card.green::after{{background:var(--green)}}
.live-card.orange::after{{background:#D97706}}
.live-card.purple::after{{background:#7E22CE}}
.lc-num{{font-size:36px;font-weight:800;color:var(--blue);letter-spacing:-.5px;line-height:1;margin-bottom:4px}}
.lc-num.green{{color:var(--green)}}
.lc-num.orange{{color:#D97706}}
.lc-num.purple{{color:#7E22CE}}
.lc-label{{font-size:11px;font-weight:600;color:var(--text2);text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px}}
.lc-sub{{font-size:10px;color:var(--gray-400)}}
.live-badge{{display:inline-flex;align-items:center;gap:4px;background:var(--green-light);color:var(--green);font-size:9px;font-weight:700;padding:2px 7px;border-radius:10px;margin-top:6px;letter-spacing:.05em}}
.live-badge-dot{{width:4px;height:4px;border-radius:50%;background:var(--green);animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.platform-row{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}}
.platform-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px 24px;box-shadow:var(--shadow-sm);display:flex;align-items:center;gap:16px}}
.pc-icon{{width:48px;height:48px;border-radius:10px;background:var(--blue-light);display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0}}
.pc-icon.green{{background:var(--green-light)}}
.pc-title{{font-size:13px;font-weight:700;color:var(--text);margin-bottom:3px}}
.pc-val{{font-size:20px;font-weight:800;color:var(--blue);letter-spacing:-.3px}}
.pc-val.green{{color:var(--green)}}
.pc-sub{{font-size:11px;color:var(--text2);margin-top:2px}}
.modules-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:20px}}
.module-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:28px;box-shadow:var(--shadow-sm);position:relative;overflow:hidden;cursor:pointer;transition:box-shadow .2s,border-color .2s}}
.module-card:hover{{box-shadow:var(--shadow-md);border-color:var(--blue)}}
.module-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--blue)}}
.module-card.green::before{{background:var(--green)}}
.module-card.purple::before{{background:#7E22CE}}
.module-card.orange::before{{background:#C2410C}}
.module-icon{{width:44px;height:44px;border-radius:10px;background:var(--blue-light);display:flex;align-items:center;justify-content:center;font-size:20px;margin-bottom:16px}}
.module-icon.green{{background:var(--green-light)}}
.module-icon.purple{{background:rgba(126,34,206,0.1)}}
.module-icon.orange{{background:rgba(194,65,12,0.1)}}
.module-name{{font-size:15px;font-weight:700;color:var(--text);margin-bottom:6px}}
.module-desc{{font-size:13px;color:var(--text2);line-height:1.6;margin-bottom:16px}}
.module-tags{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px}}
.mtag{{font-size:10px;font-weight:600;padding:3px 8px;border-radius:12px;background:var(--blue-light);color:var(--blue)}}
.mtag.green{{background:var(--green-light);color:var(--green)}}
.mtag.purple{{background:rgba(126,34,206,0.1);color:#7E22CE}}
.mtag.orange{{background:rgba(194,65,12,0.1);color:#C2410C}}
.module-status{{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:600}}
.msdot{{width:6px;height:6px;border-radius:50%}}
.ms-live{{color:var(--green)}}.ms-live .msdot{{background:var(--green);animation:pulse 2s infinite}}
.ms-ready{{color:var(--blue)}}.ms-ready .msdot{{background:var(--blue)}}
.tm-grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
.tm-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:24px;box-shadow:var(--shadow-sm)}}
.tm-title{{font-size:14px;font-weight:700;color:var(--text);margin-bottom:12px}}
.tm-fact{{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border);font-size:12px}}
.tm-fact:last-child{{border-bottom:none}}
.tm-key{{color:var(--text2);font-weight:500}}
.tm-val{{color:var(--text);font-weight:600}}
.tech-grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}}
.tech-item{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:18px 12px;text-align:center;box-shadow:var(--shadow-sm)}}
.tech-icon{{font-size:24px;margin-bottom:8px;display:block}}
.tech-name{{font-size:11px;font-weight:700;color:var(--text);margin-bottom:2px}}
.tech-role{{font-size:10px;color:var(--text2)}}
 
/* ── À PROPOS SECTION ─────────────────────────────────────────────────────── */
.apropos{{background:var(--bg);padding:56px 40px}}
.apropos-grid{{display:grid;grid-template-columns:1fr 1fr;gap:40px;align-items:start;max-width:1100px;margin:0 auto}}
.apropos-left{{}}
.apropos-eyebrow{{font-size:11px;font-weight:700;color:var(--blue);letter-spacing:.12em;text-transform:uppercase;margin-bottom:12px}}
.apropos-title{{font-size:26px;font-weight:800;color:var(--text);letter-spacing:-.3px;margin-bottom:16px;line-height:1.2}}
.apropos-title span{{color:var(--blue)}}
.apropos-body{{font-size:14px;color:var(--text2);line-height:1.75;margin-bottom:20px}}
.apropos-quote{{border-left:3px solid var(--blue);padding:14px 20px;background:var(--blue-light);border-radius:0 8px 8px 0;margin-bottom:24px}}
.apropos-quote-text{{font-size:13px;color:var(--gray-700);line-height:1.65;font-style:italic;margin-bottom:6px}}
.apropos-quote-source{{font-size:11px;font-weight:600;color:var(--blue)}}
.apropos-badges{{display:flex;gap:10px;flex-wrap:wrap}}
.apropos-badge{{display:inline-flex;align-items:center;gap:6px;background:var(--blue-light);border:1px solid var(--border);color:var(--blue);padding:6px 14px;border-radius:20px;font-size:11px;font-weight:600}}
.apropos-badge.green{{background:var(--green-light);color:var(--green)}}
.apropos-right{{display:flex;flex-direction:column;gap:16px}}
.apropos-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:22px;box-shadow:var(--shadow-sm);position:relative;overflow:hidden}}
.apropos-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--blue)}}
.apropos-card.green::before{{background:var(--green)}}
.apropos-card.purple::before{{background:#7E22CE}}
.ac-label{{font-size:10px;font-weight:700;color:var(--gray-400);letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px}}
.ac-name{{font-size:15px;font-weight:700;color:var(--text);margin-bottom:4px}}
.ac-detail{{font-size:12px;color:var(--text2);line-height:1.5}}
.ac-tag{{display:inline-block;margin-top:8px;font-size:10px;font-weight:600;padding:2px 8px;border-radius:10px;background:var(--blue-light);color:var(--blue)}}
.ac-tag.green{{background:var(--green-light);color:var(--green)}}
.ac-tag.purple{{background:rgba(126,34,206,0.1);color:#7E22CE}}
.apropos-finding{{background:linear-gradient(135deg,#003D82,#0057B8);border-radius:12px;padding:22px;color:white}}
.af-label{{font-size:10px;font-weight:700;color:rgba(255,255,255,0.6);letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px}}
.af-stat{{font-size:32px;font-weight:800;color:white;letter-spacing:-.5px;line-height:1;margin-bottom:4px}}
.af-desc{{font-size:12px;color:rgba(255,255,255,0.7);line-height:1.5}}
.af-source{{font-size:10px;color:rgba(255,255,255,0.45);margin-top:8px}}
 
/* ── ABOUT STRIP (bottom) ─────────────────────────────────────────────────── */
.about-strip{{background:linear-gradient(135deg,#003D82,#0057B8);padding:48px 40px;display:flex;align-items:center;gap:40px}}
.about-text{{flex:1}}
.about-title{{font-size:22px;font-weight:800;color:white;margin-bottom:8px}}
.about-desc{{font-size:14px;color:rgba(255,255,255,0.75);line-height:1.65}}
.about-badges{{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap}}
.abadge{{background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);color:white;padding:5px 12px;border-radius:20px;font-size:11px;font-weight:600}}
.about-right{{flex-shrink:0;text-align:center}}
.about-uni{{font-size:12px;color:rgba(255,255,255,0.6);margin-bottom:4px;font-weight:500}}
.about-uni-name{{font-size:15px;font-weight:700;color:white}}
.about-program{{font-size:11px;color:rgba(255,255,255,0.6);margin-top:4px}}
.footer{{background:#101828;padding:28px 40px;display:flex;align-items:center;justify-content:space-between}}
.footer-brand{{font-weight:700;font-size:14px;color:white}}
.footer-sub{{font-size:11px;color:#667085;margin-top:2px}}
.footer-right{{font-size:11px;color:#667085;text-align:right}}
</style>
</head>
<body>
 
<!-- HERO -->
<div class="hero">
  <div class="hero-inner">
    <div class="hero-eyebrow">Tanger Med Port Intelligence</div>
    <div class="hero-title">Tour de Contrôle<br><span>Portuaire Intelligente</span><br>pour Tanger Med</div>
    <div class="hero-subtitle">Plateforme d'intelligence logistique combinant optimisation par programmation linéaire (MILP), analyse NLP multilingue en temps réel et données AIS satellites IMF PortWatch — conçue pour l'avenir des opérations portuaires marocaines.</div>
    <div class="hero-actions">
      <button class="btn-primary" onclick="navTo('Port Optimizer')">Ouvrir l'Optimiseur</button>
      <button class="btn-secondary" onclick="navTo('PortWatch Live')">PortWatch Live</button>
    </div>
    <div class="hero-stats">
      <div class="hstat"><div class="hstat-num">25</div><div class="hstat-label">Navires Suivis</div></div>
      <div class="hstat"><div class="hstat-num">8</div><div class="hstat-label">Postes Gérés</div></div>
      <div class="hstat"><div class="hstat-num">{improvement}%</div><div class="hstat-label">Réduction Attente</div></div>
      <div class="hstat"><div class="hstat-num">${demurrage:,}</div><div class="hstat-label">Surestaries Évitées</div></div>
      <div class="hstat"><div class="hstat-num">{avg_calls}</div><div class="hstat-label">Escales/Jour Live</div></div>
    </div>
  </div>
</div>
 
<!-- LIVE METRICS -->
<div class="section">
  <div class="section-center">
    <div class="section-eyebrow">Métriques Temps Réel</div>
    <div class="section-title">Ce que portiq.xyz fait en ce moment</div>
    <div class="section-sub">Chiffres calculés sur un scénario synthétique de 25 navires — solveur CBC</div>
  </div>
  <div class="live-grid">
    <div class="live-card">
      <div class="lc-label">Navires Planifiés</div>
      <div class="lc-num">25</div>
      <div class="lc-sub">Sur 8 postes, 4 terminaux</div>
      <div class="live-badge"><div class="live-badge-dot"></div>LIVE</div>
    </div>
    <div class="live-card green">
      <div class="lc-label">Surestaries Évitées</div>
      <div class="lc-num green">${demurrage:,}</div>
      <div class="lc-sub">{hours_saved}h économisées · hypothèse $10K/h</div>
      <div class="live-badge"><div class="live-badge-dot"></div>CALCULÉ</div>
    </div>
    <div class="live-card orange">
      <div class="lc-label">Escales/Jour Live</div>
      <div class="lc-num orange">{avg_calls}</div>
      <div class="lc-sub">IMF PortWatch — {latest_date}</div>
      <div class="live-badge"><div class="live-badge-dot"></div>LIVE</div>
    </div>
    <div class="live-card purple">
      <div class="lc-label">Chunks RAG Indexés</div>
      <div class="lc-num purple">1 962</div>
      <div class="lc-sub">Incoterms, Code Douanes, ANP</div>
      <div class="live-badge"><div class="live-badge-dot"></div>INDEXÉ</div>
    </div>
  </div>
  <div class="platform-row">
    <div class="platform-card">
      <div class="pc-icon">⚓</div>
      <div>
        <div class="pc-title">Réduction Temps d'Attente</div>
        <div class="pc-val">{improvement}% d'amélioration</div>
        <div class="pc-sub">vs baseline FCFS — {opt_avg}h moy. vs {fcfs_avg}h</div>
      </div>
    </div>
    <div class="platform-card">
      <div class="pc-icon green">🌐</div>
      <div>
        <div class="pc-title">Perturbations Surveillées</div>
        <div class="pc-val green">Flux Actif</div>
        <div class="pc-sub">Google News RSS — Analyse Groq NLP — 4 corridors</div>
      </div>
    </div>
  </div>
</div>
 
<!-- MODULES -->
<div class="section alt">
  <div class="section-center">
    <div class="section-eyebrow">Modules Plateforme</div>
    <div class="section-title">Quatre Couches d'Intelligence</div>
    <div class="section-sub">Chaque module adresse une dimension différente de l'intelligence logistique portuaire</div>
  </div>
  <div class="modules-grid">
    <div class="module-card" onclick="navTo('Port Optimizer')">
      <div class="module-icon">⚓</div>
      <div class="module-name">Optimiseur d'Allocation des Postes</div>
      <div class="module-desc">Solveur CBC MILP (PuLP) qui assigne 25 navires à 8 postes sur TC1-TC4, minimisant le temps d'attente pondéré par priorité. Les navires MOTHER ont une priorité ×3. Amélioration mesurée de {improvement}% vs baseline FCFS sur scénario synthétique.</div>
      <div class="module-tags"><span class="mtag">Python</span><span class="mtag">PuLP MILP</span><span class="mtag">SQLite</span><span class="mtag">Gantt</span></div>
      <div class="module-status ms-live"><div class="msdot"></div>Actif</div>
    </div>
    <div class="module-card green" onclick="navTo('AI Logistics Assistant')">
      <div class="module-icon green">🤖</div>
      <div class="module-name">Assistant IA Logistique MARO</div>
      <div class="module-desc">IA conversationnelle propulsée par Groq avec mémoire JSON, spécialisée dans la logistique portuaire marocaine, les Incoterms 2020, les réglementations douanières et les opérations de Tanger Med.</div>
      <div class="module-tags"><span class="mtag green">Groq API</span><span class="mtag green">Mémoire JSON</span><span class="mtag green">NLP</span></div>
      <div class="module-status ms-live"><div class="msdot"></div>Actif</div>
    </div>
    <div class="module-card purple" onclick="navTo('PortWatch Live')">
      <div class="module-icon purple">📡</div>
      <div class="module-name">Intelligence PortWatch Live</div>
      <div class="module-desc">Flux AIS satellite IMF PortWatch affichant les escales journalières réelles et le tonnage import/export de Tanger Med. Moyenne de {avg_calls} escales/jour sur 30 jours. Dernière mise à jour : {latest_date}.</div>
      <div class="module-tags"><span class="mtag purple">IMF PortWatch</span><span class="mtag purple">AIS Satellite</span><span class="mtag purple">Données Live</span></div>
      <div class="module-status ms-live"><div class="msdot"></div>Actif</div>
    </div>
    <div class="module-card orange" onclick="navTo('Document Intelligence')">
      <div class="module-icon orange">📄</div>
      <div class="module-name">Intelligence Documentaire RAG</div>
      <div class="module-desc">Base vectorielle ChromaDB avec 1 962 chunks issus de PDFs ANP réels, du guide Incoterms 2020 et du Code des Douanes Maroc 2026. Recherche sémantique via sentence-transformers + Groq.</div>
      <div class="module-tags"><span class="mtag orange">ChromaDB</span><span class="mtag orange">RAG</span><span class="mtag orange">1 962 Chunks</span></div>
      <div class="module-status ms-live"><div class="msdot"></div>Actif</div>
    </div>
  </div>
</div>
 
<!-- TERMINAL STRUCTURE -->
<div class="section">
  <div class="section-center">
    <div class="section-eyebrow">Contexte Portuaire</div>
    <div class="section-title">Structure des Terminaux de Tanger Med</div>
    <div class="section-sub">Données terminaux réelles intégrées dans le modèle d'allocation des postes</div>
  </div>
  <div class="tm-grid">
    <div class="tm-card">
      <div class="tm-title">TC1 — Terminal à Conteneurs 1</div>
      <div class="tm-fact"><span class="tm-key">Postes</span><span class="tm-val">A1, A2</span></div>
      <div class="tm-fact"><span class="tm-key">Capacité Max</span><span class="tm-val">18 000 / 16 000 TEU</span></div>
      <div class="tm-fact"><span class="tm-key">Cadence</span><span class="tm-val">120 / 110 TEU/h</span></div>
      <div class="tm-fact"><span class="tm-key">Opérateur</span><span class="tm-val">Marsa Maroc</span></div>
    </div>
    <div class="tm-card">
      <div class="tm-title">TC2 — Terminal à Conteneurs 2</div>
      <div class="tm-fact"><span class="tm-key">Postes</span><span class="tm-val">B1, B2</span></div>
      <div class="tm-fact"><span class="tm-key">Capacité Max</span><span class="tm-val">20 000 / 14 000 TEU</span></div>
      <div class="tm-fact"><span class="tm-key">Cadence</span><span class="tm-val">130 / 95 TEU/h</span></div>
      <div class="tm-fact"><span class="tm-key">Opérateur</span><span class="tm-val">APM Terminals</span></div>
    </div>
    <div class="tm-card">
      <div class="tm-title">TC3 — Terminal à Conteneurs 3</div>
      <div class="tm-fact"><span class="tm-key">Postes</span><span class="tm-val">C1, C2</span></div>
      <div class="tm-fact"><span class="tm-key">Capacité Max</span><span class="tm-val">12 000 / 9 000 TEU</span></div>
      <div class="tm-fact"><span class="tm-key">Cadence</span><span class="tm-val">90 / 75 TEU/h</span></div>
      <div class="tm-fact"><span class="tm-key">Opérateur</span><span class="tm-val">Eurogate</span></div>
    </div>
    <div class="tm-card">
      <div class="tm-title">TC4 — Terminal à Conteneurs 4</div>
      <div class="tm-fact"><span class="tm-key">Postes</span><span class="tm-val">D1, D2</span></div>
      <div class="tm-fact"><span class="tm-key">Capacité Max</span><span class="tm-val">10 000 / 8 000 TEU</span></div>
      <div class="tm-fact"><span class="tm-key">Cadence</span><span class="tm-val">80 / 70 TEU/h</span></div>
      <div class="tm-fact"><span class="tm-key">Opérateur</span><span class="tm-val">TMPA</span></div>
    </div>
  </div>
</div>
 
<!-- TECH STACK -->
<div class="section alt">
  <div class="section-center">
    <div class="section-eyebrow">Stack Technologique</div>
    <div class="section-title">Construit avec</div>
  </div>
  <div class="tech-grid">
    <div class="tech-item"><span class="tech-icon">🐍</span><div class="tech-name">Python 3.14</div><div class="tech-role">Langage principal</div></div>
    <div class="tech-item"><span class="tech-icon">🎯</span><div class="tech-name">PuLP / CBC</div><div class="tech-role">Optimiseur MILP</div></div>
    <div class="tech-item"><span class="tech-icon">🚀</span><div class="tech-name">Groq API</div><div class="tech-role">Inférence LLM</div></div>
    <div class="tech-item"><span class="tech-icon">🗄️</span><div class="tech-name">SQLite</div><div class="tech-role">Base opérationnelle</div></div>
    <div class="tech-item"><span class="tech-icon">🧠</span><div class="tech-name">ChromaDB</div><div class="tech-role">Stockage vectoriel</div></div>
    <div class="tech-item"><span class="tech-icon">📡</span><div class="tech-name">IMF PortWatch</div><div class="tech-role">Données AIS Live</div></div>
  </div>
</div>
 
<!-- À PROPOS -->
<div class="apropos">
  <div class="apropos-grid">
    <div class="apropos-left">
      <div class="apropos-eyebrow">À Propos du Projet</div>
      <div class="apropos-title">Un prototype d'intelligence logistique pour la <span>supply chain portuaire marocaine</span></div>
      <div class="apropos-body">
        portiq.xyz est une plateforme full-stack développée comme projet de portfolio en logistique portuaire et intelligence artificielle. Elle explore l'application de l'optimisation par programmation linéaire, de l'analyse NLP et de la recherche documentaire sémantique aux opérations du port de Tanger Med.
      </div>
      <div class="apropos-quote">
        <div class="apropos-quote-text">
          La recherche académique récente sur la supply chain portuaire marocaine identifie l'automatisation des processus comme facteur clé de la performance opérationnelle — portiq.xyz explore cette direction à travers trois modules d'automatisation.
        </div>
        <div class="apropos-quote-source">Inspiré de la littérature sur la transformation digitale des ports marocains — IJAFAME 2024</div>
      </div>
      <div class="apropos-body">
        L'optimiseur MILP automatise l'allocation des postes à quai. Le radar de perturbations automatise la veille maritime. Le système RAG automatise la consultation documentaire réglementaire.
      </div>
      <div class="apropos-badges">
        <span class="apropos-badge">🎓 FSJES Tanger — Licence Gestion</span>
        <span class="apropos-badge green">🔬 Prototype — Données Synthétiques</span>
      </div>
    </div>
    <div class="apropos-right">
      <div class="apropos-card">
        <div class="ac-label">Domaine 1</div>
        <div class="ac-name">Logistique Portuaire & Transport International</div>
        <div class="ac-detail">Optimisation d'allocation des postes · Gestion des perturbations maritimes · Incoterms 2020 · Régimes douaniers marocains</div>
        <div class="ac-tag">Logistique · Ports · Transport</div>
      </div>
      <div class="apropos-card green">
        <div class="ac-label">Domaine 2</div>
        <div class="ac-name">Intelligence Artificielle & Économie Numérique</div>
        <div class="ac-detail">Pipeline NLP Groq · RAG ChromaDB · Extraction d'entités structurées · Recherche sémantique multilingue</div>
        <div class="ac-tag green">Intelligence Artificielle · Data · NLP</div>
      </div>
      <div class="apropos-finding">
        <div class="af-label">Résultat Clé — Optimiseur MILP (scénario synthétique)</div>
        <div class="af-stat">${demurrage:,}</div>
        <div class="af-desc">de surestaries évitées sur 25 navires synthétiques — {hours_saved}h économisées. Taux de surestarie : hypothèse $10 000/h. Amélioration de {improvement}% vs baseline FCFS.</div>
        <div class="af-source">Calculé par le solveur CBC · Scénario de démonstration sur données synthétiques</div>
      </div>
    </div>
  </div>
</div>
 
<!-- ABOUT STRIP -->
<div class="about-strip">
  <div class="about-text">
    <div class="about-title">Prototype Full-Stack — Logistique Portuaire & IA</div>
    <div class="about-desc">portiq.xyz combine optimisation opérationnelle (MILP), analyse NLP en temps réel et intelligence documentaire RAG dans une plateforme intégrée focalisée sur les opérations du port de Tanger Med.</div>
    <div class="about-badges">
      <span class="abadge">Logistique Portuaire & Transport International</span>
      <span class="abadge">IA & Économie Numérique</span>
      <span class="abadge">Management Logistique & Stratégie</span>
    </div>
  </div>
  <div class="about-right">
    <div class="about-uni">Tanger Med · Maroc</div>
    <div class="about-uni-name">portiq.xyz</div>
    <div class="about-program">Python · Streamlit · PuLP · Groq · ChromaDB</div>
  </div>
</div>
 
<div class="footer">
  <div>
    <div class="footer-brand">portiq.xyz — Port Intelligence Platform</div>
    <div class="footer-sub">Tanger Med TC1 / TC2 / TC3 / TC4 — CBC MILP — Groq — ChromaDB — IMF PortWatch</div>
  </div>
  <div class="footer-right">
    Python 3.14 — Streamlit — PuLP 2.x<br>
    Logistique Portuaire · IA · Optimisation
  </div>
</div>
 
<script>
function navTo(page) {{
  try {{
    const ta = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
    const btn = window.parent.document.querySelector('[data-testid="stChatInputSubmitButton"]');
    if (ta && btn) {{
      const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
      nativeSetter.call(ta, page);
      ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
      setTimeout(() => btn.click(), 100);
    }}
  }} catch(e) {{ console.log('nav error:', e); }}
}}
</script>
</body>
</html>"""
 
    components.html(HTML, height=3200, scrolling=True)