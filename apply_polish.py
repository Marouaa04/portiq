"""
apply_polish.py - one-shot, reversible clean-up of the portiq.xyz front end.

Put this file in the marologix folder (next to app.py) and run:
    python apply_polish.py

What it does
  1. Backs up every file it touches to backup_before_polish/ (only the first time).
  2. Forces a LIGHT theme on every page (.streamlit/config.toml), so the pages stop
     switching between dark and light depending on the computer's settings.
  3. Plain, consistent wording: French navigation, no 'Intelligence' buzzwords,
     no masters / university / professor mentions on the home page.
  4. Removes the weak AI-assistant page from the menu and the home page.
  5. Labels scenario numbers as scenario numbers.
  6. Re-checks that every edited file still compiles. If one does not, EVERYTHING is
     restored automatically.

To undo by hand: copy the files from backup_before_polish/ back to where they were.
"""
import os
import py_compile
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKUP = os.path.join(ROOT, "backup_before_polish")
FILES = [
    "app.py",
    os.path.join("pages", "home.py"),
    os.path.join("pages", "customs_simulator.py"),
    os.path.join("pages", "rag_assistant.py"),
    os.path.join("pages", "disruption_radar.py"),
    os.path.join("pages", "portwatch.py"),
    os.path.join("pages", "tmpa_insights.py"),
]
report = []


def path(rel):
    return os.path.join(ROOT, rel)


def read(rel):
    with open(path(rel), encoding="utf-8") as f:
        return f.read()


def write(rel, text):
    with open(path(rel), "w", encoding="utf-8") as f:
        f.write(text)


def note(ok, rel, label):
    report.append((ok, rel, label))


def rep(rel, old, new, label, count=1):
    s = read(rel)
    if old in s:
        write(rel, s.replace(old, new, count))
        note(True, rel, label)
    else:
        note(False, rel, label + "  (text not found - already changed?)")


def rx(rel, pattern, repl, label, flags=re.S):
    s = read(rel)
    new, n = re.subn(pattern, lambda m: repl if isinstance(repl, str) else repl(m), s, count=1, flags=flags)
    if n:
        write(rel, new)
        note(True, rel, label)
    else:
        note(False, rel, label + "  (pattern not found - already changed?)")


# ------------------------------------------------------------------ 0. backup
missing = [f for f in FILES if not os.path.exists(path(f))]
if missing:
    print("Run this from the marologix folder. Missing:", missing)
    sys.exit(1)
if not os.path.exists(BACKUP):
    for f in FILES:
        dst = os.path.join(BACKUP, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(path(f), dst)
    print("Backup saved in backup_before_polish/")
else:
    print("Backup already exists - keeping the original one.")

# ------------------------------------------------------------------ 1. light theme everywhere
cfg_dir = path(".streamlit")
cfg = os.path.join(cfg_dir, "config.toml")
THEME = '''
[theme]
base = "light"
primaryColor = "#0057B8"
backgroundColor = "#F0F2F5"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#1D2939"
font = "sans serif"
'''
os.makedirs(cfg_dir, exist_ok=True)
existing = open(cfg, encoding="utf-8").read() if os.path.exists(cfg) else ""
if "[theme]" in existing:
    note(False, ".streamlit/config.toml", "light theme  (a [theme] section already exists - check it says base = \"light\")")
else:
    with open(cfg, "a", encoding="utf-8") as f:
        f.write(THEME)
    note(True, ".streamlit/config.toml", "light theme on every page")

# ------------------------------------------------------------------ 2. navigation (app.py)
A = "app.py"
rep(A, '    {nav_button("AI Assistant", "AI Logistics Assistant")}\n', "", "remove AI Assistant from the menu")
rep(A, 'nav_button("Home", "Home")', 'nav_button("Accueil", "Home")', "menu: Accueil")
rep(A, 'nav_button("Port Optimizer", "Port Optimizer")', 'nav_button("Postes à quai", "Port Optimizer")', "menu: Postes à quai")
rep(A, 'nav_button("Disruption Radar", "Global Disruption Radar")', 'nav_button("Veille maritime", "Global Disruption Radar")', "menu: Veille maritime")
rep(A, 'nav_button("PortWatch Live", "PortWatch Live")', 'nav_button("Trafic", "PortWatch Live")', "menu: Trafic")
rep(A, "Port Intelligence Platform", "Planification et suivi portuaire", "brand tagline")

# ------------------------------------------------------------------ 3. home page
H = os.path.join("pages", "home.py")
rep(H, '<div class="hero-eyebrow">Tanger Med Port Intelligence</div>', '<div class="hero-eyebrow">Port de Tanger Med</div>', "hero eyebrow")
rep(H, "Tour de Contrôle<br><span>Portuaire Intelligente</span><br>pour Tanger Med",
    "Postes à quai<br><span>et suivi du trafic</span><br>à Tanger Med", "hero title")
rx(H, r'<div class="hero-subtitle">.*?</div>',
   '<div class="hero-subtitle">Un outil d\'aide à la décision pour affecter les navires aux postes à quai, '
   'suivre les escales et consulter les textes douaniers et les Incoterms.</div>', "hero subtitle")
rep(H, '<div class="hstat-label">Navires Suivis</div>', '<div class="hstat-label">Navires (scénario)</div>', "hero label 1")
rep(H, '<div class="hstat-label">Réduction Attente</div>', '<div class="hstat-label">Réduction de l\'attente</div>', "hero label 2")
rep(H, '<div class="hstat-label">Surestaries Évitées</div>', '<div class="hstat-label">Surestaries évitées (hypothèse)</div>', "hero label 3")
rep(H, '<div class="section-eyebrow">Métriques Temps Réel</div>', '<div class="section-eyebrow">Indicateurs</div>', "section eyebrow")
rep(H, "Ce que portiq.xyz fait en ce moment", "Indicateurs clés", "section title")
rep(H, "Chiffres calculés en direct par la plateforme — pas des données statiques",
    "Scénario synthétique de 25 navires sur 8 postes ; escales issues d'IMF PortWatch", "section subtitle")
rx(H, r'(<div class="lc-label">Navires Planifiés</div>\s*<div class="lc-num">[^<]*</div>\s*<div class="lc-sub">[^<]*</div>\s*<div class="live-badge"><div class="live-badge-dot"></div>)LIVE',
   lambda m: m.group(1) + "SCÉNARIO", "badge: Navires = SCÉNARIO")
rep(H, '<div class="live-badge-dot"></div>CALCULÉ', '<div class="live-badge-dot"></div>SCÉNARIO', "badge: Calculé = SCÉNARIO")
rep(H, "Chunks RAG Indexés", "Passages indexés", "card label")
rep(H, "Modules Plateforme", "Outils", "modules eyebrow")
rep(H, "Quatre Couches d'Intelligence", "Quatre outils", "modules title")
rep(H, "Chaque module adresse une dimension différente de l'intelligence logistique portuaire",
    "Planification, trafic, douane et documentation pour les opérations du port", "modules subtitle")
rep(H, "Amélioration prouvée de", "Amélioration mesurée sur le scénario synthétique :", "no 'prouvée'")
rep(H, "Intelligence PortWatch Live", "Suivi du trafic — PortWatch", "module name")
rep(H, "Intelligence Documentaire RAG", "Consultation documentaire", "module name")
rep(H, "1 962 Chunks", "1 962 passages", "module tag")
rep(H, "Données terminaux réelles intégrées dans le modèle d'allocation des postes",
    "Paramètres retenus dans le modèle d'allocation des postes (hypothèses de modélisation)", "terminals subtitle")

NEW_CARD = '''    <div class="module-card green" onclick="navTo('Référentiel Douanier')">
      <div class="module-icon green">02</div>
      <div class="module-name">Référentiel Douanier</div>
      <div class="module-desc">Régimes douaniers, documents requis et Incoterms 2020 pour une opération d'import ou d'export via Tanger Med, avec renvoi aux textes officiels.</div>
      <div class="module-tags"><span class="mtag green">Incoterms 2020</span><span class="mtag green">Code des Douanes</span></div>
      <div class="module-status ms-live"><div class="msdot"></div>Actif</div>
    </div>
'''
rx(H, r'[ \t]*<div class="module-card green" onclick="navTo\(\'AI Logistics Assistant\'\)">.*?\n[ \t]{4}</div>\n',
   NEW_CARD, "replace assistant card with customs card")
rep(H, '<div class="module-icon">⚓</div>', '<div class="module-icon">01</div>', "icon 01")
rep(H, '<div class="module-icon purple">📡</div>', '<div class="module-icon purple">03</div>', "icon 03")
rep(H, '<div class="module-icon orange">📄</div>', '<div class="module-icon orange">04</div>', "icon 04")
rep(H, '<div class="pc-icon">⚓</div>', '<div class="pc-icon">▸</div>', "plain icon")
rep(H, '<div class="pc-icon green">🌐</div>', '<div class="pc-icon green">▸</div>', "plain icon")

NEW_ABOUT = '''<!-- À PROPOS -->
<div class="apropos">
  <div class="apropos-grid">
    <div class="apropos-left">
      <div class="apropos-eyebrow">À propos</div>
      <div class="apropos-title">Un outil d'aide à la décision pour la <span>planification portuaire</span></div>
      <div class="apropos-body">
        portiq.xyz est un prototype qui regroupe quatre outils autour du port de Tanger Med : l'affectation des navires aux postes à quai, la veille sur les perturbations maritimes, le suivi des escales à partir des données IMF PortWatch, et la consultation des textes douaniers et des Incoterms.
      </div>
      <div class="apropos-body">
        L'optimiseur propose un planning ; le planificateur reste décisionnaire. Les navires du scénario sont synthétiques, et le coût de surestarie de 10 000 $/h est une hypothèse.
      </div>
      <div class="apropos-badges">
        <span class="apropos-badge green">Prototype — données synthétiques</span>
      </div>
    </div>
    <div class="apropos-right">
      <div class="apropos-finding">
        <div class="af-label">Résultat du scénario synthétique</div>
        <div class="af-stat">{improvement}%</div>
        <div class="af-desc">de réduction de l'attente totale par rapport à « premier arrivé, premier servi » sur 25 navires synthétiques — {hours_saved} h économisées. Coût de surestarie : hypothèse de 10 000 $/h.</div>
        <div class="af-source">Calculé par le solveur CBC · Scénario de démonstration</div>
      </div>
    </div>
  </div>
</div>

'''
rx(H, r'<!-- TECH STACK -->.*?(?=<div class="footer">)', NEW_ABOUT, "tech stack + about replaced by a plain 'À propos'")
rep(H, "portiq.xyz — Port Intelligence Platform", "portiq.xyz — Tanger Med", "footer brand")
rep(H, "Tanger Med TC1 / TC2 / TC3 / TC4 — CBC MILP — Groq — ChromaDB — IMF PortWatch",
    "Terminaux TC1 à TC4 · Sources : IMF PortWatch, ANP, textes officiels", "footer line")
rx(H, r"Python 3\.14 — Streamlit — PuLP 2\.x<br>\s*Logistique Portuaire · IA · Optimisation",
   "Prototype de démonstration<br>Scénario synthétique", "footer right")

# ------------------------------------------------------------------ 4. other pages: plain titles
C = os.path.join("pages", "customs_simulator.py")
rep(C, "Simulateur Douanier — Tanger Med", "Référentiel Douanier — Tanger Med", "customs title")
rep(C, "🔍 Simuler la procédure douanière", "Consulter la procédure douanière", "customs button")
R = os.path.join("pages", "rag_assistant.py")
rep(R, "Module 4 — Document Intelligence", "Documents de référence", "documents eyebrow")
rep(R, "Réponse — Intelligence Documentaire RAG", "Réponse — documents officiels", "documents answer label")
rep(R, "portiq.xyz — Intelligence Documentaire RAG", "portiq.xyz — Consultation documentaire", "documents footer")
D = os.path.join("pages", "disruption_radar.py")
rep(D, "Système de Veille Maritime — Maritime Event Intelligence", "Veille maritime — perturbations et retards", "radar title")
rep(D, "Tableau de Bord — Intelligence Temps Réel", "Tableau de bord", "radar section")
rep(D, "Pipeline d'ingestion de signaux maritimes en cours...", "Chargement des événements maritimes...", "radar spinner")
rep(os.path.join("pages", "portwatch.py"), "PortWatch Live Intelligence", "Suivi du trafic — IMF PortWatch", "portwatch title")
T = os.path.join("pages", "tmpa_insights.py")
rep(T, "ANP Port Intelligence — 2025", "Données ANP — 2025", "ANP title")
rep(T, "MaroLogix Port Intelligence Platform", "portiq.xyz", "ANP footer")

# ------------------------------------------------------------------ 5. verify, roll back if anything broke
broken = []
for f in FILES:
    try:
        py_compile.compile(path(f), doraise=True)
    except py_compile.PyCompileError as e:
        broken.append((f, str(e)))
if broken:
    for f in FILES:
        shutil.copy2(os.path.join(BACKUP, f), path(f))
    print("\nA file would not compile, so EVERYTHING was restored from the backup:")
    for f, e in broken:
        print(" -", f, e[:300])
    sys.exit(2)

print("\n" + "=" * 60)
ok = [r for r in report if r[0]]
bad = [r for r in report if not r[0]]
print(f"Applied {len(ok)} of {len(report)} changes. All edited files still compile.")
for _, rel, label in bad:
    print(f"  NOT APPLIED  {rel}: {label}")
print("\nNow run:  python -m streamlit run app.py   and click through every page.")