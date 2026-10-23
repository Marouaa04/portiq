import streamlit as st
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

SUGGESTED = [
    "Quels documents sont requis pour l'importation au Maroc ?",
    "Quelle est la différence entre FOB et CIF ?",
    "Comment fonctionne le dédouanement au Maroc ?",
    "Quels sont les régimes douaniers disponibles à Tanger Med ?",
    "Expliquez l'Incoterm DDP et ses obligations pour l'acheteur",
    "Quel est le rôle du connaissement (Bill of Lading) ?",
]

KB_DOCS = [
    {"icon": "📘", "name": "Incoterms 2020",             "detail": "Guide Pratique ICC — Publication No. 723E",   "chunks": "~640 chunks"},
    {"icon": "⚖️", "name": "Code des Douanes Maroc 2026", "detail": "ADII — Texte officiel complet",              "chunks": "~890 chunks"},
    {"icon": "🏗️", "name": "ANP Rapport Trafic 2025",    "detail": "Tableau de bord portuaire Décembre 2025",     "chunks": "~312 chunks"},
    {"icon": "🔗", "name": "Circuit Anglais",              "detail": "Procédures logistiques internationales",     "chunks": "~120 chunks"},
]


@st.cache_resource(show_spinner=False)
def load_rag():
    try:
        from rag import ask as rag_ask
        return rag_ask, None
    except Exception as e:
        return None, str(e)


def render():
    st.markdown("""
    <style>
    [data-testid="stHeader"]{display:none!important}
    footer{display:none!important}
    .block-container{padding:2rem 2rem 2rem 2rem!important;max-width:1100px!important}
    </style>
    """, unsafe_allow_html=True)

    rag_ask, load_error = load_rag()
    rag_ok = rag_ask is not None

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='margin-bottom:8px'>
      <div style='font-size:11px;font-weight:700;color:#0057B8;letter-spacing:.12em;
                  text-transform:uppercase;margin-bottom:6px'>
        Documents de référence
      </div>
      <div style='font-size:22px;font-weight:800;color:#101828;letter-spacing:-.3px;
                  margin-bottom:8px'>
        Système de Consultation Documentaire Intelligent
      </div>
      <div style='font-size:13px;color:#667085;line-height:1.6;max-width:680px'>
        Interrogez la base de connaissances réglementaires en langage naturel.
        Les réponses sont ancrées exclusivement dans les documents officiels indexés.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # RAG status pill
    if rag_ok:
        st.markdown("<span style='background:#E3F5EE;color:#00875A;font-size:11px;font-weight:600;padding:4px 10px;border-radius:20px'>● RAG : Connecté</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"<span style='background:#FDECEA;color:#C0392B;font-size:11px;font-weight:600;padding:4px 10px;border-radius:20px'>● RAG : Non disponible — {load_error}</span>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── KB Source Cards ───────────────────────────────────────────────────────
    cols = st.columns(4)
    for i, doc in enumerate(KB_DOCS):
        with cols[i]:
            st.markdown(f"""
            <div style='background:white;border:1px solid #E4E7EC;border-radius:8px;
                        padding:16px;box-shadow:0 1px 3px rgba(16,24,40,0.1);
                        border-top:3px solid #0057B8;'>
              <div style='font-size:20px;margin-bottom:8px'>{doc['icon']}</div>
              <div style='font-size:12px;font-weight:700;color:#1D2939;margin-bottom:3px'>{doc['name']}</div>
              <div style='font-size:11px;color:#667085;margin-bottom:8px;line-height:1.4'>{doc['detail']}</div>
              <span style='font-size:10px;font-weight:600;padding:2px 7px;border-radius:10px;
                           background:#EBF2FF;color:#0057B8'>{doc['chunks']}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Stats Row ─────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div style='background:white;border:1px solid #E4E7EC;border-radius:8px;padding:16px 18px;
                    box-shadow:0 1px 3px rgba(16,24,40,0.1);display:flex;align-items:center;gap:14px'>
          <div style='width:40px;height:40px;border-radius:8px;background:#EBF2FF;
                      display:flex;align-items:center;justify-content:center;font-size:18px'>🧠</div>
          <div>
            <div style='font-size:22px;font-weight:800;color:#0057B8;letter-spacing:-.3px'>1 962</div>
            <div style='font-size:11px;color:#667085;margin-top:2px'>Chunks vectorisés — ChromaDB</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style='background:white;border:1px solid #E4E7EC;border-radius:8px;padding:16px 18px;
                    box-shadow:0 1px 3px rgba(16,24,40,0.1);display:flex;align-items:center;gap:14px'>
          <div style='width:40px;height:40px;border-radius:8px;background:#E3F5EE;
                      display:flex;align-items:center;justify-content:center;font-size:18px'>🔍</div>
          <div>
            <div style='font-size:22px;font-weight:800;color:#00875A;letter-spacing:-.3px'>Top-4</div>
            <div style='font-size:11px;color:#667085;margin-top:2px'>Passages récupérés — similarité cosinus</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div style='background:white;border:1px solid #E4E7EC;border-radius:8px;padding:16px 18px;
                    box-shadow:0 1px 3px rgba(16,24,40,0.1);display:flex;align-items:center;gap:14px'>
          <div style='width:40px;height:40px;border-radius:8px;background:#EBF2FF;
                      display:flex;align-items:center;justify-content:center;font-size:18px'>⚡</div>
          <div>
            <div style='font-size:22px;font-weight:800;color:#0057B8;letter-spacing:-.3px'>Groq</div>
            <div style='font-size:11px;color:#667085;margin-top:2px'>Génération — openai/gpt-oss-20b</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Query Panel ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style='background:white;border:1px solid #E4E7EC;border-radius:8px;
                padding:18px 20px 4px 20px;box-shadow:0 1px 3px rgba(16,24,40,0.1);
                margin-bottom:16px'>
      <div style='font-size:13px;font-weight:700;color:#1D2939;margin-bottom:4px'>
        Interrogation de la Base Documentaire
      </div>
      <div style='font-size:11px;color:#98A2B3;margin-bottom:16px'>
        Posez une question en français ou en anglais
      </div>
      <div style='font-size:10px;font-weight:700;color:#98A2B3;letter-spacing:.1em;
                  text-transform:uppercase;margin-bottom:10px'>
        Requêtes fréquentes
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Suggested question buttons
    clicked_q = None
    cols = st.columns(3)
    for i, q in enumerate(SUGGESTED):
        with cols[i % 3]:
            if st.button(q, key=f"sq_{i}", use_container_width=True):
                clicked_q = q

    st.markdown("<br>", unsafe_allow_html=True)

    # If a suggested question was clicked, store it and rerun
    if clicked_q:
        st.session_state["rag_prefill"] = clicked_q
        st.rerun()

    # Get prefill value if set
    prefill = st.session_state.pop("rag_prefill", None)
    if prefill:
        st.session_state["rag_question_input"] = prefill

    if "rag_question_input" not in st.session_state:
        st.session_state["rag_question_input"] = ""

    question = st.text_area(
        "Votre requête",
        height=100,
        placeholder="Ex: Quels documents sont requis pour une importation sous régime de mise à la consommation au Maroc ?",
        label_visibility="collapsed",
        key="rag_question_input"
    )

    col1, col2 = st.columns([4, 1])
    with col2:
        search = st.button("🔍 Interroger", use_container_width=True, type="primary")

    # ── Result ────────────────────────────────────────────────────────────────
    if search and question.strip():
        if not rag_ok:
            st.error(f"RAG non disponible : {load_error}")
        else:
            with st.spinner("Extraction des passages pertinents..."):
                try:
                    result = rag_ask(question.strip())
                    answer = result.get("answer", "")
                    sources = result.get("sources", [])

                    st.markdown("""
                    <div style='background:#EBF2FF;border-left:4px solid #0057B8;border-radius:6px;
                                padding:14px 18px;margin-bottom:12px;margin-top:16px'>
                      <div style='font-size:10px;font-weight:700;color:#0057B8;letter-spacing:.1em;
                                  text-transform:uppercase;margin-bottom:8px'>
                        Réponse — documents officiels
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(answer)

                    if sources:
                        st.markdown("<br>**Sources documentaires utilisées :**", unsafe_allow_html=True)
                        for s in sources:
                            st.markdown(f"📄 `{s}`")

                except Exception as e:
                    st.error(f"Erreur RAG : {e}")

    elif search and not question.strip():
        st.warning("Veuillez saisir une question.")

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center;padding:20px;font-size:11px;color:#98A2B3;
                border-top:1px solid #E4E7EC;margin-top:32px'>
      portiq.xyz — Consultation documentaire — ChromaDB + all-MiniLM-L6-v2 + Groq —
      Incoterms 2020 · Code Douanes Maroc 2026 · ANP 2025
    </div>
    """, unsafe_allow_html=True)