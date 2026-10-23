import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def render():
    # Import inside function to ensure sys.path is set first
    from chat import chat
    from memory import load_history, clear_history

    st.markdown("""
    <div style='margin-bottom: 1.5rem;'>
        <div class='badge'>Module 2 — AI Assistant</div>
        <div class='section-title' style='font-size:1.8rem;'>MARO</div>
        <div class='section-sub' style='font-size:0.95rem;'>
            Your expert assistant for Moroccan customs, Incoterms 2020, and port logistics.
            Ask in French or English.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "history" not in st.session_state:
        st.session_state.history = load_history()

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Clear conversation", use_container_width=True):
            st.session_state.history = clear_history()
            st.rerun()
    with col2:
        st.markdown(
            "<div style='text-align:right; color:#6b7a99; font-size:0.78rem; padding-top:8px;'>"
            + str(len(st.session_state.history)) + " messages saved</div>",
            unsafe_allow_html=True
        )

    st.markdown("<hr style='border-color:#1e2d45; margin:1rem 0;'>", unsafe_allow_html=True)

    if not st.session_state.history:
        st.markdown("""
        <div style='text-align:center; padding:3rem 0; color:#6b7a99;'>
            <div style='font-size:2.5rem; margin-bottom:1rem;'>⚓</div>
            <div style='font-family:Syne; font-size:1.1rem; font-weight:700;
                        color:#e8edf5; margin-bottom:0.5rem;'>
                Bonjour, je suis MARO
            </div>
            <div style='font-size:0.85rem;'>
                Ask me anything about Incoterms, Moroccan customs, or port logistics.<br>
                Posez-moi vos questions sur les Incoterms, la douane ou la logistique portuaire.
            </div>
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div style='display:flex; justify-content:flex-end; margin-bottom:1rem;'>
                <div style='background:linear-gradient(135deg,#0072ff,#00c6ff);
                            color:white; border-radius:18px 18px 4px 18px;
                            padding:0.8rem 1.2rem; max-width:70%;
                            font-size:0.88rem; line-height:1.6;'>
                    {msg["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='display:flex; justify-content:flex-start; margin-bottom:1rem;'>
                <div style='background:#0f1623; border:1px solid #1e2d45;
                            border-radius:18px 18px 18px 4px;
                            padding:0.8rem 1.2rem; max-width:75%;
                            font-size:0.88rem; line-height:1.8; color:#e8edf5;
                            white-space:pre-wrap;'>
                    <div style='font-family:Syne; font-size:0.68rem; font-weight:700;
                                color:#c9a84c; text-transform:uppercase;
                                letter-spacing:0.1em; margin-bottom:6px;'>
                        MARO
                    </div>
                    {msg["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Message",
            height=80,
            placeholder="Ask MARO... / Posez votre question...",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Send", use_container_width=True)

    if submitted and user_input.strip():
        with st.spinner("MARO is thinking..."):
            try:
                answer = chat(user_input.strip())
                st.session_state.history = load_history()
                st.rerun()
            except Exception as e:
                st.error("Error: " + str(e))