import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="portiq.xyz",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
[data-testid="stSidebar"]{display:none!important}
[data-testid="collapsedControl"]{display:none!important}
[data-testid="stHeader"]{display:none!important}
[data-testid="stChatInput"]{display:none!important}
[data-testid="stBottom"]{display:none!important}
#MainMenu{display:none!important}
footer{display:none!important}
header{display:none!important}
.block-container{padding:0!important;max-width:100%!important}
section[data-testid="stMain"]>div{padding:0!important}
.stChatFloatingInputContainer{display:none!important}
</style>
""", unsafe_allow_html=True)

PAGES = [
    "Home",
    "Port Optimizer",
    "AI Logistics Assistant",
    "Global Disruption Radar",
    "PortWatch Live",
    "Données ANP",
    "Référentiel Douanier",
    "Document Intelligence",
]

if "page" not in st.session_state:
    st.session_state.page = "Home"

qp = st.query_params.get("page", None)
if qp and qp in PAGES:
    st.session_state.page = qp

page = st.session_state.page

def nav_button(label, target):
    active = "active" if page == target else ""
    url = f"?page={target.replace(' ', '+')}"
    return f'<a class="ml-link {active}" href="{url}" target="_self">{label}</a>'

NAV_HTML = f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
.ml-nav{{
    background:#ffffff;
    border-bottom:1px solid #E4E7EC;
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:0 32px;
    height:60px;
    box-shadow:0 1px 3px rgba(16,24,40,0.1);
    font-family:'Inter',sans-serif;
}}
.ml-brand{{display:flex;align-items:center;gap:12px;text-decoration:none}}
.ml-logo{{width:36px;height:36px;background:#0057B8;border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:14px;color:white;flex-shrink:0}}
.ml-brand-name{{font-weight:800;font-size:17px;color:#1D2939;letter-spacing:-.3px}}
.ml-brand-tag{{font-size:11px;color:#667085;margin-top:1px}}
.ml-links{{display:flex;gap:2px;align-items:center}}
.ml-link{{
    font-size:13px;color:#667085;font-weight:500;
    padding:6px 11px;border-radius:6px;cursor:pointer;
    text-decoration:none;
    transition:background .15s,color .15s;
    white-space:nowrap;
}}
.ml-link:hover{{background:#F0F2F5;color:#0057B8}}
.ml-link.active{{background:#EBF2FF;color:#0057B8;font-weight:600}}
.ml-right{{display:flex;align-items:center}}
</style>
<div class="ml-nav">
  <a class="ml-brand" href="?page=Home" target="_self">
    <div class="ml-logo">PQ</div>
    <div>
      <div class="ml-brand-name">portiq.xyz</div>
      <div class="ml-brand-tag">Planification et suivi portuaire</div>
    </div>
  </a>
  <div class="ml-links">
    {nav_button("Accueil", "Home")}
    {nav_button("Postes à quai", "Port Optimizer")}
    {nav_button("Veille maritime", "Global Disruption Radar")}
    {nav_button("Trafic", "PortWatch Live")}
    {nav_button("Données ANP", "Données ANP")}
    {nav_button("Référentiel Douanier", "Référentiel Douanier")}
    {nav_button("Documents", "Document Intelligence")}
  </div>
  <div class="ml-right"></div>
</div>
"""

st.markdown(NAV_HTML, unsafe_allow_html=True)

if page == "Home":
    from pages.home import render
    render()
elif page == "AI Logistics Assistant":
    from pages.assistant import render
    render()
elif page == "Port Optimizer":
    from pages.port_optimizer import render
    render()
elif page == "Global Disruption Radar":
    from pages.disruption_radar import render
    render()
elif page == "PortWatch Live":
    from pages.portwatch import show
    show()
elif page == "Données ANP":
    try:
        from pages.tmpa_insights import render
        render()
    except Exception as e:
        st.error(f"Error loading Données ANP: {e}")
elif page == "Référentiel Douanier":
    from pages.customs_simulator import render
    render()
elif page == "Document Intelligence":
    from pages.rag_assistant import render
    render()