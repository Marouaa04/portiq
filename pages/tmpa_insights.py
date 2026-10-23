import streamlit as st
import os

def render():
    st.markdown("""
    <style>
    [data-testid="stHeader"]{display:none!important}
    footer{display:none!important}
    .block-container{padding:0!important;max-width:100%!important}
    section[data-testid="stMain"]>div{padding:0!important}
    </style>
    """, unsafe_allow_html=True)

    # ── TOP HEADER ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:#0057B8;padding:24px 32px 20px 32px;">
      <div style="display:flex;align-items:center;justify-content:space-between;">
        <div>
          <div style="font-size:10px;font-weight:700;color:#93C5FD;letter-spacing:.12em;text-transform:uppercase;margin-bottom:6px;">
            Tableau de Bord National
          </div>
          <div style="font-size:22px;font-weight:700;color:#FFFFFF;margin-bottom:4px;">
            Données ANP — 2025
          </div>
          <div style="font-size:13px;color:#BFDBFE;">
            Agence Nationale des Ports · Données officielles · Comparaison 2024 vs 2025
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:10px;">
          <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:8px 14px;text-align:center;">
            <div style="font-size:10px;color:#BFDBFE;font-weight:600;letter-spacing:.08em;text-transform:uppercase;">Outil</div>
            <div style="font-size:13px;color:#FFFFFF;font-weight:700;margin-top:2px;">Microsoft Power BI</div>
          </div>
          <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:8px 14px;text-align:center;">
            <div style="font-size:10px;color:#BFDBFE;font-weight:600;letter-spacing:.08em;text-transform:uppercase;">Source</div>
            <div style="font-size:13px;color:#FFFFFF;font-weight:700;margin-top:2px;">ANP Officiel</div>
          </div>
          <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:8px 14px;text-align:center;">
            <div style="font-size:10px;color:#BFDBFE;font-weight:600;letter-spacing:.08em;text-transform:uppercase;">Ports couverts</div>
            <div style="font-size:13px;color:#FFFFFF;font-weight:700;margin-top:2px;">10 ports</div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI CARDS ───────────────────────────────────────────────────────────
    st.markdown("<div style='padding:20px 32px 0 32px;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:10px;font-weight:700;color:#98A2B3;letter-spacing:.1em;text-transform:uppercase;
                margin-bottom:14px;display:flex;align-items:center;gap:8px;">
      Indicateurs Clés 2025
      <div style="flex:1;height:1px;background:#E4E7EC;"></div>
      <span style="font-size:10px;color:#98A2B3;font-weight:400;">vs 2024</span>
    </div>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4, k5, k6 = st.columns(6)

    def kpi_card(col, label, value2025, variation, unit=""):
        color = "#00875A" if variation > 0 else "#C0392B"
        arrow = "▲" if variation > 0 else "▼"
        with col:
            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid #E4E7EC;border-radius:8px;padding:16px 14px;
                        box-shadow:0 1px 3px rgba(16,24,40,0.08);position:relative;overflow:hidden;">
              <div style="position:absolute;top:0;left:0;width:3px;height:100%;background:{color};"></div>
              <div style="font-size:9px;font-weight:600;color:#667085;letter-spacing:.05em;
                          text-transform:uppercase;margin-bottom:6px;">{label}</div>
              <div style="font-size:20px;font-weight:700;color:#1D2939;line-height:1;margin-bottom:4px;">
                {value2025}{unit}
              </div>
              <div style="font-size:11px;font-weight:600;color:{color};">
                {arrow} {abs(variation)}%
              </div>
            </div>
            """, unsafe_allow_html=True)

    kpi_card(k1, "Trafic Global", "102.4 MT", 2.5)
    kpi_card(k2, "Conteneurs EVP", "1.66M", 6.9)
    kpi_card(k3, "Passagers", "2.40M", 4.9)
    kpi_card(k4, "Croisières PAX", "383K", 41.7)
    kpi_card(k5, "Camions TIR", "27,508", 8.6)
    kpi_card(k6, "Cabotage", "4.2 MT", 39.5)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── POWER BI BADGE ──────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin:18px 32px 0 32px;background:#F0F7FF;border:1px solid #BFDBFE;
                border-radius:8px;padding:12px 16px;display:flex;align-items:center;gap:12px;">
      <div style="background:#0057B8;border-radius:6px;padding:6px 10px;
                  font-size:11px;font-weight:700;color:white;flex-shrink:0;">
        Power BI
      </div>
      <div style="font-size:12px;color:#1D4ED8;line-height:1.5;">
        <strong>Dashboards construits avec Microsoft Power BI Desktop</strong> à partir des données officielles ANP 2025.
        Modèle de données multi-tables · 4 pages de visualisation · Comparaison temporelle 2021–2025.
        <span style="color:#64748B;"> Rapport interactif complet disponible sur demande.</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── TABS ────────────────────────────────────────────────────────────────
    st.markdown("<div style='padding:20px 32px 0 32px;'>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Vue Générale",
        "🚢 Trafic par Port",
        "📦 Conteneurs & Marchandises",
        "🛳️ Passagers & Croisières"
    ])

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(base_dir, "assets")

    def show_dashboard(tab, filename, title, description, insights):
        with tab:
            st.markdown(f"""
            <div style="margin-bottom:14px;">
              <div style="font-size:15px;font-weight:600;color:#1D2939;margin-bottom:4px;">{title}</div>
              <div style="font-size:12px;color:#667085;">{description}</div>
            </div>
            """, unsafe_allow_html=True)

            img_path = os.path.join(assets_dir, filename)
            if os.path.exists(img_path):
                st.image(img_path, use_container_width=True)
            else:
                st.warning(f"Image not found: place '{filename}' in the assets/ folder")

            st.markdown("""
            <div style="margin-top:14px;font-size:10px;font-weight:700;color:#98A2B3;
                        letter-spacing:.1em;text-transform:uppercase;margin-bottom:10px;">
              Analyse
            </div>
            """, unsafe_allow_html=True)

            cols = st.columns(len(insights))
            for col, (label, value, note) in zip(cols, insights):
                with col:
                    st.markdown(f"""
                    <div style="background:#F8F9FA;border:1px solid #E4E7EC;border-radius:8px;
                                padding:14px;text-align:center;">
                      <div style="font-size:9px;font-weight:600;color:#667085;
                                  text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">{label}</div>
                      <div style="font-size:18px;font-weight:700;color:#0057B8;">{value}</div>
                      <div style="font-size:10px;color:#98A2B3;margin-top:3px;">{note}</div>
                    </div>
                    """, unsafe_allow_html=True)

    show_dashboard(
        tab1,
        "anp_vue_generale.jpg",
        "Vue Générale — Tableau de Bord ANP 2025",
        "Comparaison du trafic portuaire national 2024 vs 2025 · 10 ports couverts · 8 indicateurs clés",
        [
            ("Trafic Global", "102.4 MT", "+2.5% vs 2024"),
            ("Port Leader", "Jorf Lasfar", "~40M MT en 2025"),
            ("2ème Port", "Casablanca", "~32M MT en 2025"),
            ("Croissance TIR", "+8.6%", "27,508 camions"),
        ]
    )

    show_dashboard(
        tab2,
        "anp_trafic_port.jpg",
        "Trafic par Port — Analyse Détaillée 2021–2025",
        "Évolution du trafic total par port sur 5 ans · Tendance nationale 2021–2025",
        [
            ("Tendance 2021–2025", "↗ +12%", "Croissance globale"),
            ("Pic 2022", "88 MT", "Creux post-COVID"),
            ("Record 2025", "102.4 MT", "Nouveau sommet"),
            ("TCAC 2021–25", "+2.8%/an", "Taux de croissance"),
        ]
    )

    show_dashboard(
        tab3,
        "anp_conteneurs.jpg",
        "Conteneurs et Marchandises — ANP 2025",
        "EVP par port · Marchandises par produit · Import/Export détaillé",
        [
            ("EVP National", "1.66M", "+6.9% vs 2024"),
            ("Leader EVP", "Casablanca", "~1.45M EVP"),
            ("Export", "32.6 MT", "+0.6% vs 2024"),
            ("Import", "65.6 MT", "+1.6% vs 2024"),
        ]
    )

    show_dashboard(
        tab4,
        "anp_passagers.jpg",
        "Passagers et Croisières — ANP 2025",
        "Trafic passagers par port · Croisières internationales · Tanger en tête",
        [
            ("Passagers", "2.40M", "+4.9% vs 2024"),
            ("Leader", "Tanger", "~2.4M passagers"),
            ("Croisières", "383K PAX", "+41.7% vs 2024"),
            ("2ème Croisières", "Casablanca", "Forte croissance"),
        ]
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── FOOTER ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin:24px 32px 16px 32px;padding:14px 18px;background:#F8F9FA;
                border:1px solid #E4E7EC;border-radius:8px;
                display:flex;align-items:center;justify-content:space-between;">
      <div style="font-size:11px;color:#667085;">
        <strong style="color:#1D2939;">Source des données :</strong>
        Agence Nationale des Ports (ANP) — Rapport Annuel 2025 · Données officielles du Royaume du Maroc
      </div>
      <div style="font-size:11px;color:#667085;">
        <strong style="color:#1D2939;">Outil BI :</strong> Microsoft Power BI Desktop ·
        <strong style="color:#1D2939;">Intégration :</strong> portiq.xyz
      </div>
    </div>
    """, unsafe_allow_html=True)