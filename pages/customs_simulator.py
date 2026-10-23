import streamlit as st
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


@st.cache_resource(show_spinner=False)
def load_rag():
    try:
        from rag import ask as rag_ask
        return rag_ask, None
    except Exception as e:
        return None, str(e)

GOODS_TYPES = [
    "Conteneurs / Marchandises générales",
    "Véhicules automobiles",
    "Produits alimentaires et agroalimentaires",
    "Matières premières (phosphate, minerais)",
    "Produits chimiques et engrais",
    "Hydrocarbures et produits pétroliers",
    "Équipements industriels et machines",
    "Textiles et vêtements",
    "Produits pharmaceutiques",
    "Électronique et informatique",
]

ORIGINS = [
    "Chine / Asie de l'Est",
    "Europe (France, Espagne, Allemagne...)",
    "États-Unis / Amérique du Nord",
    "Turquie / Moyen-Orient",
    "Afrique subsaharienne",
    "Inde / Asie du Sud",
    "Amérique du Sud (Brésil, Argentine...)",
    "Maroc (export national)",
]

DESTINATIONS = [
    "Marché marocain (import définitif)",
    "Réexportation vers un pays tiers (transbordement)",
    "Zone Franche de Tanger (TFZ)",
    "Zone Franche Industrielle (Melloussa, Kénitra...)",
    "Entrepôt sous douane (stockage temporaire)",
    "Admission temporaire (usage puis réexport)",
]

INCOTERMS = [
    "EXW — Ex Works",
    "FCA — Free Carrier",
    "FOB — Free On Board",
    "CFR — Cost and Freight",
    "CIF — Cost, Insurance and Freight",
    "DAP — Delivered At Place",
    "DDP — Delivered Duty Paid",
    "CPT — Carriage Paid To",
    "CIP — Carriage and Insurance Paid To",
    "DPU — Delivered at Place Unloaded",
]

REGIME_MAP = {
    "Marché marocain (import définitif)": {
        "regime": "Mise à la Consommation (MAC)",
        "code": "Article 114 — Code des Douanes Maroc 2026",
        "color": "#0057B8",
        "description": "Les marchandises entrent définitivement sur le territoire marocain. Les droits de douane et la TVA à l'importation sont exigibles immédiatement.",
        "docs": [
            "Déclaration Unique de Marchandises (DUM) — obligatoire",
            "Connaissement / Bill of Lading (B/L)",
            "Facture commerciale (en français ou arabe)",
            "Liste de colisage (Packing List)",
            "Certificat d'origine",
            "Certificat d'assurance",
            "Bon à délivrer (BAD) de l'armateur",
        ],
        "duties": "Droits de douane variables selon la nomenclature douanière (NDP) + TVA 20% + TIC si applicable",
    },
    "Réexportation vers un pays tiers (transbordement)": {
        "regime": "Transit Douanier / Transbordement",
        "code": "Article 152 — Code des Douanes Maroc 2026",
        "color": "#00875A",
        "description": "Les marchandises traversent le territoire douanier marocain sans y être mises en consommation. Tanger Med est le principal hub de transbordement en Afrique.",
        "docs": [
            "Déclaration de Transit (T1)",
            "Manifeste de transbordement",
            "Connaissement de transit (Through B/L)",
            "Garantie douanière ou caution bancaire",
            "Autorisation ADII (Administration des Douanes)",
        ],
        "duties": "Aucun droit de douane ni TVA — régime suspensif. Garantie obligatoire couvrant les droits potentiels.",
    },
    "Zone Franche de Tanger (TFZ)": {
        "regime": "Zone Franche d'Exportation (ZFE)",
        "code": "Loi 19-94 relative aux zones franches d'exportation",
        "color": "#7E22CE",
        "description": "Les marchandises entrent dans la Zone Franche de Tanger (Tanger Free Zone). Exonération totale des droits de douane et avantages fiscaux spéciaux.",
        "docs": [
            "Déclaration d'entrée en zone franche",
            "Connaissement / B/L",
            "Facture commerciale",
            "Autorisation d'établissement en ZFE (TMSA)",
            "Certificat d'origine si réexportation",
        ],
        "duties": "Exonération totale des droits de douane. IS réduit (jusqu'à 0% les 5 premières années). TVA non applicable sur les opérations intra-zone.",
    },
    "Zone Franche Industrielle (Melloussa, Kénitra...)": {
        "regime": "Zone Franche Industrielle d'Exportation (ZFIE)",
        "code": "Loi 19-94 + Décret d'application — Code des Investissements",
        "color": "#C2410C",
        "description": "Régime applicable aux usines Renault (Melloussa) et Stellantis (Kénitra). Les intrants industriels bénéficient d'une suspension des droits de douane.",
        "docs": [
            "Déclaration d'importation industrielle",
            "Connaissement / B/L",
            "Facture proforma et commerciale",
            "Certificat de conformité technique",
            "Autorisation AMDIE (Agence Marocaine de Développement des Investissements)",
            "Engagement de réexportation du produit fini",
        ],
        "duties": "Suspension des droits de douane sur les intrants. Exonération IS 5 ans puis 8.75%. TVA récupérable sur les achats locaux.",
    },
    "Entrepôt sous douane (stockage temporaire)": {
        "regime": "Entrepôt de Douane",
        "code": "Articles 130-145 — Code des Douanes Maroc 2026",
        "color": "#D97706",
        "description": "Les marchandises sont stockées sous contrôle douanier sans paiement immédiat des droits. Durée maximale de stockage : 3 ans renouvelable.",
        "docs": [
            "Déclaration de mise en entrepôt (DME)",
            "Connaissement / B/L",
            "Facture commerciale",
            "Inventaire des marchandises",
            "Caution bancaire ou garantie douanière",
            "Autorisation d'exploiter l'entrepôt (ADII)",
        ],
        "duties": "Droits suspendus pendant la durée de stockage. Payables à la sortie selon le régime définitif choisi (mise à la consommation ou réexportation).",
    },
    "Admission temporaire (usage puis réexport)": {
        "regime": "Admission Temporaire (AT)",
        "code": "Articles 156-175 — Code des Douanes Maroc 2026",
        "color": "#0E7490",
        "description": "Permet l'importation temporaire de marchandises destinées à être réexportées après usage ou transformation. Utilisé pour les foires, expositions, matériels de travaux.",
        "docs": [
            "Déclaration d'Admission Temporaire (DAT)",
            "Carnet ATA (si applicable — Convention internationale)",
            "Connaissement / B/L",
            "Engagement de réexportation dans le délai accordé",
            "Garantie douanière couvrant les droits potentiels",
            "Justificatif de l'usage temporaire (contrat, invitation...)",
        ],
        "duties": "Suspension totale des droits et taxes pendant la durée autorisée (généralement 6 mois à 2 ans). Pénalités en cas de non-réexportation dans les délais.",
    },
}

INCOTERM_DETAILS = {
    "EXW — Ex Works": {
        "risk_transfer": "À l'usine/entrepôt du vendeur",
        "who_pays_freight": "Acheteur paie tout",
        "who_pays_customs": "Acheteur gère export ET import",
        "best_for": "Acheteur expérimenté qui contrôle toute la chaîne",
        "port_relevance": "Peu utilisé pour le maritime — l'acheteur doit tout organiser depuis l'usine du vendeur",
    },
    "FCA — Free Carrier": {
        "risk_transfer": "Remise au transporteur désigné par l'acheteur",
        "who_pays_freight": "Acheteur paie le fret principal",
        "who_pays_customs": "Vendeur gère export / Acheteur gère import",
        "best_for": "Transport multimodal, conteneurs",
        "port_relevance": "Recommandé pour Tanger Med — le vendeur livre le conteneur au terminal, l'acheteur prend en charge depuis là",
    },
    "FOB — Free On Board": {
        "risk_transfer": "À bord du navire au port d'expédition",
        "who_pays_freight": "Acheteur paie le fret maritime",
        "who_pays_customs": "Vendeur gère export / Acheteur gère import",
        "best_for": "Vrac, marchandises en vrac liquide",
        "port_relevance": "Très utilisé au Maroc pour les exportations de phosphate et céréales. Risque passe au Maroc à l'embarquement.",
    },
    "CFR — Cost and Freight": {
        "risk_transfer": "À bord du navire au port d'expédition",
        "who_pays_freight": "Vendeur paie le fret jusqu'au port de destination",
        "who_pays_customs": "Vendeur gère export / Acheteur gère import",
        "best_for": "Import marocain de vrac",
        "port_relevance": "Courant pour les importations marocaines. Le risque reste sur l'acheteur dès l'embarquement malgré que le vendeur paie le fret.",
    },
    "CIF — Cost, Insurance and Freight": {
        "risk_transfer": "À bord du navire au port d'expédition",
        "who_pays_freight": "Vendeur paie fret + assurance minimum",
        "who_pays_customs": "Vendeur gère export / Acheteur gère import",
        "best_for": "Import standard — le plus utilisé au Maroc",
        "port_relevance": "L'Incoterm le plus fréquent dans les importations marocaines. La valeur CIF sert de base de calcul des droits de douane à l'ADII.",
    },
    "DAP — Delivered At Place": {
        "risk_transfer": "Au lieu de destination convenu (non déchargé)",
        "who_pays_freight": "Vendeur paie tout jusqu'à destination",
        "who_pays_customs": "Vendeur gère export / Acheteur gère import et droits",
        "best_for": "E-commerce, livraisons directes",
        "port_relevance": "Utilisé pour les livraisons directes en entreprise. L'acheteur marocain gère le dédouanement à l'arrivée.",
    },
    "DDP — Delivered Duty Paid": {
        "risk_transfer": "Au lieu de destination convenu (non déchargé)",
        "who_pays_freight": "Vendeur paie TOUT — fret, assurance, droits de douane",
        "who_pays_customs": "Vendeur gère TOUT — export ET import ET droits",
        "best_for": "Acheteur qui veut zéro responsabilité logistique",
        "port_relevance": "Maximum de responsabilité pour le vendeur. Le vendeur étranger doit connaître la réglementation douanière marocaine. Rare mais existe dans certains contrats grands comptes.",
    },
    "CPT — Carriage Paid To": {
        "risk_transfer": "Remise au premier transporteur",
        "who_pays_freight": "Vendeur paie le transport jusqu'à destination",
        "who_pays_customs": "Vendeur gère export / Acheteur gère import",
        "best_for": "Transport multimodal",
        "port_relevance": "Similaire à CIP mais sans assurance obligatoire. Le risque passe très tôt à l'acheteur.",
    },
    "CIP — Carriage and Insurance Paid To": {
        "risk_transfer": "Remise au premier transporteur",
        "who_pays_freight": "Vendeur paie transport + assurance étendue",
        "who_pays_customs": "Vendeur gère export / Acheteur gère import",
        "best_for": "Marchandises de haute valeur, transport multimodal",
        "port_relevance": "Incoterms 2020 a augmenté le niveau d'assurance obligatoire pour CIP. Recommandé pour les équipements industriels importés au Maroc.",
    },
    "DPU — Delivered at Place Unloaded": {
        "risk_transfer": "Au lieu de destination — après déchargement",
        "who_pays_freight": "Vendeur paie tout incluant le déchargement",
        "who_pays_customs": "Vendeur gère export / Acheteur gère import",
        "best_for": "Livraisons avec déchargement inclus",
        "port_relevance": "Nouveau dans Incoterms 2020 (remplace DAT). Le vendeur assume le risque jusqu'au déchargement complet à destination.",
    },
}


def build_rag_query(goods, origin, destination, incoterm):
    incoterm_code = incoterm.split("—")[0].strip()
    dest_clean = destination.split("(")[0].strip()
    return f"""Pour une importation de {goods} en provenance de {origin} vers {dest_clean} au Maroc avec l'Incoterm {incoterm_code}:
1. Quel régime douanier s'applique selon le Code des Douanes Maroc 2026?
2. Quels sont les documents obligatoires requis?
3. Quelles sont les obligations de l'acheteur et du vendeur selon cet Incoterm?
4. Y a-t-il des restrictions ou réglementations spéciales pour ce type de marchandise?"""


def render():
    st.markdown("""
    <style>
    [data-testid="stHeader"]{display:none!important}
    footer{display:none!important}
    .block-container{padding:0!important;max-width:100%!important}
    section[data-testid="stMain"]>div{padding:0!important}
    </style>
    """, unsafe_allow_html=True)

    # ── HEADER ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0057B8,#003d82);padding:24px 32px 20px 32px;">
      <div style="font-size:10px;font-weight:700;color:#93C5FD;letter-spacing:.12em;
                  text-transform:uppercase;margin-bottom:6px;">
        Outil Opérationnel · Douane & Commerce International
      </div>
      <div style="font-size:22px;font-weight:700;color:#FFFFFF;margin-bottom:4px;">
        Référentiel Douanier — Tanger Med
      </div>
      <div style="font-size:13px;color:#BFDBFE;">
        Identifiez votre régime douanier, vos documents requis et vos obligations Incoterm
        · Basé sur le Code des Douanes Maroc 2026 et les Incoterms 2020
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── SOURCE BADGE ────────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin:16px 32px 0 32px;background:#F0F7FF;border:1px solid #BFDBFE;
                border-radius:8px;padding:10px 16px;display:flex;align-items:center;gap:12px;">
      <div style="background:#0057B8;border-radius:4px;padding:4px 8px;
                  font-size:10px;font-weight:700;color:white;flex-shrink:0;">
        Sources officielles
      </div>
      <div style="font-size:12px;color:#1D4ED8;">
        Code des Douanes et Impôts Indirects — Maroc 2026 &nbsp;·&nbsp;
        Incoterms 2020 — ICC Guide Pratique &nbsp;·&nbsp;
        ADII — Administration des Douanes et Impôts Indirects
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='padding:20px 32px 0 32px;'>", unsafe_allow_html=True)

    # ── FORM ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="font-size:10px;font-weight:700;color:#98A2B3;letter-spacing:.1em;
                text-transform:uppercase;margin-bottom:14px;display:flex;
                align-items:center;gap:8px;">
      Paramètres de l'opération douanière
      <div style="flex:1;height:1px;background:#E4E7EC;"></div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        goods = st.selectbox(
            "Type de marchandise",
            GOODS_TYPES,
            help="Sélectionnez la catégorie de marchandise"
        )
        origin = st.selectbox(
            "Pays / région d'origine",
            ORIGINS,
            help="Origine des marchandises"
        )

    with col2:
        destination = st.selectbox(
            "Destination douanière",
            DESTINATIONS,
            help="Quel est le régime de destination?"
        )
        incoterm = st.selectbox(
            "Incoterm applicable",
            INCOTERMS,
            index=4,
            help="L'Incoterm définit le partage des risques et coûts"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    simulate = st.button(
        "Consulter la procédure douanière",
        use_container_width=True,
        type="primary"
    )

    if simulate:
        # ── RESULTS ─────────────────────────────────────────────────────────
        regime_info = REGIME_MAP.get(destination, REGIME_MAP["Marché marocain (import définitif)"])
        incoterm_info = INCOTERM_DETAILS.get(incoterm, {})
        incoterm_code = incoterm.split("—")[0].strip()

        st.markdown("""
        <div style="font-size:10px;font-weight:700;color:#98A2B3;letter-spacing:.1em;
                    text-transform:uppercase;margin:20px 0 14px 0;display:flex;
                    align-items:center;gap:8px;">
          Résultats de la simulation
          <div style="flex:1;height:1px;background:#E4E7EC;"></div>
        </div>
        """, unsafe_allow_html=True)

        # Regime card
        color = regime_info["color"]
        st.markdown(f"""
        <div style="background:#FFFFFF;border:1px solid #E4E7EC;border-radius:8px;
                    padding:20px;margin-bottom:14px;box-shadow:0 1px 3px rgba(16,24,40,0.08);
                    border-left:4px solid {color};">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
            <div style="background:{color};color:white;border-radius:6px;padding:6px 12px;
                        font-size:11px;font-weight:700;text-transform:uppercase;
                        letter-spacing:.06em;flex-shrink:0;">
              Régime douanier
            </div>
            <div style="font-size:16px;font-weight:700;color:#1D2939;">
              {regime_info["regime"]}
            </div>
          </div>
          <div style="font-size:12px;color:#667085;margin-bottom:8px;line-height:1.6;">
            {regime_info["description"]}
          </div>
          <div style="font-size:11px;color:{color};font-weight:600;">
            📖 Référence légale: {regime_info["code"]}
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Two columns — docs and duties
        c1, c2 = st.columns([3, 2])

        with c1:
            docs_html = "".join([
                f"""<div style="display:flex;align-items:flex-start;gap:8px;
                    padding:8px 0;border-bottom:1px solid #F0F2F5;">
                  <div style="color:{color};font-size:14px;flex-shrink:0;margin-top:1px;">✓</div>
                  <div style="font-size:12px;color:#344054;">{doc}</div>
                </div>"""
                for doc in regime_info["docs"]
            ])
            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid #E4E7EC;border-radius:8px;
                        padding:16px 18px;box-shadow:0 1px 3px rgba(16,24,40,0.08);">
              <div style="font-size:10px;font-weight:700;color:#667085;letter-spacing:.08em;
                          text-transform:uppercase;margin-bottom:12px;">
                Documents requis
              </div>
              {docs_html}
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid #E4E7EC;border-radius:8px;
                        padding:16px 18px;box-shadow:0 1px 3px rgba(16,24,40,0.08);
                        margin-bottom:14px;">
              <div style="font-size:10px;font-weight:700;color:#667085;letter-spacing:.08em;
                          text-transform:uppercase;margin-bottom:12px;">
                Droits & Taxes
              </div>
              <div style="font-size:12px;color:#344054;line-height:1.7;">
                {regime_info["duties"]}
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Incoterm card
            if incoterm_info:
                st.markdown(f"""
                <div style="background:#FFFFFF;border:1px solid #E4E7EC;border-radius:8px;
                            padding:16px 18px;box-shadow:0 1px 3px rgba(16,24,40,0.08);">
                  <div style="font-size:10px;font-weight:700;color:#667085;letter-spacing:.08em;
                              text-transform:uppercase;margin-bottom:12px;">
                    Incoterm {incoterm_code}
                  </div>
                  <div style="margin-bottom:8px;">
                    <div style="font-size:10px;color:#98A2B3;text-transform:uppercase;
                                letter-spacing:.06em;margin-bottom:2px;">Transfert de risque</div>
                    <div style="font-size:12px;color:#344054;font-weight:500;">
                      {incoterm_info.get("risk_transfer","")}
                    </div>
                  </div>
                  <div style="margin-bottom:8px;">
                    <div style="font-size:10px;color:#98A2B3;text-transform:uppercase;
                                letter-spacing:.06em;margin-bottom:2px;">Fret</div>
                    <div style="font-size:12px;color:#344054;font-weight:500;">
                      {incoterm_info.get("who_pays_freight","")}
                    </div>
                  </div>
                  <div style="margin-bottom:8px;">
                    <div style="font-size:10px;color:#98A2B3;text-transform:uppercase;
                                letter-spacing:.06em;margin-bottom:2px;">Douane</div>
                    <div style="font-size:12px;color:#344054;font-weight:500;">
                      {incoterm_info.get("who_pays_customs","")}
                    </div>
                  </div>
                  <div style="background:#F0F7FF;border-radius:6px;padding:8px 10px;
                              margin-top:10px;">
                    <div style="font-size:11px;color:#0057B8;font-weight:600;">
                      🚢 Pertinence portuaire
                    </div>
                    <div style="font-size:11px;color:#344054;margin-top:4px;line-height:1.5;">
                      {incoterm_info.get("port_relevance","")}
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        # ── RAG QUERY ───────────────────────────────────────────────────────
        st.markdown("""
        <div style="font-size:10px;font-weight:700;color:#98A2B3;letter-spacing:.1em;
                    text-transform:uppercase;margin:20px 0 14px 0;display:flex;
                    align-items:center;gap:8px;">
          Analyse IA — Base documentaire officielle
          <div style="flex:1;height:1px;background:#E4E7EC;"></div>
        </div>
        """, unsafe_allow_html=True)

        query = build_rag_query(goods, origin, destination, incoterm)
        rag_ask, load_error = load_rag()

        with st.spinner("Consultation du Code des Douanes et des Incoterms 2020..."):
            if not rag_ask:
                st.warning(f"RAG non disponible : {load_error}")
            else:
                try:
                    result = rag_ask(query)
                    answer  = result.get("answer", "")
                    sources = result.get("sources", [])

                    st.markdown(f"""
                    <div style="background:#FFFFFF;border:1px solid #E4E7EC;border-radius:8px;
                                padding:20px;box-shadow:0 1px 3px rgba(16,24,40,0.08);">
                      <div style="font-size:10px;font-weight:700;color:#0057B8;
                                  letter-spacing:.08em;text-transform:uppercase;margin-bottom:12px;">
                        Analyse RAG — Documents officiels
                      </div>
                      <div style="font-size:13px;color:#344054;line-height:1.8;white-space:pre-wrap;">
                        {answer}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if sources:
                        sources_html = "".join([
                            f"""<div style="padding:5px 10px;margin:4px 0;
                                background:#F0F7FF;border-left:3px solid #0057B8;
                                border-radius:3px;font-size:11px;color:#344054;">{s}</div>"""
                            for s in sources
                        ])
                        st.markdown(f"""
                        <div style="margin-top:12px;">
                          <div style="font-size:10px;font-weight:700;color:#667085;
                                      text-transform:uppercase;letter-spacing:.08em;
                                      margin-bottom:8px;">Sources utilisées</div>
                          {sources_html}
                        </div>
                        """, unsafe_allow_html=True)

                except Exception as e:
                    st.warning(f"Erreur RAG : {e}")

    # ── FOOTER ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin:24px 0 16px 0;padding:14px 18px;background:#F8F9FA;
                border:1px solid #E4E7EC;border-radius:8px;
                display:flex;align-items:center;justify-content:space-between;">
      <div style="font-size:11px;color:#667085;">
        <strong style="color:#1D2939;">Sources légales:</strong>
        Code des Douanes et Impôts Indirects — Maroc 2026 (ADII) ·
        Incoterms® 2020 — ICC Publication No. 723E ·
        Règles ADII sur les régimes économiques en douane
      </div>
      <div style="font-size:11px;color:#667085;">
        <strong style="color:#1D2939;">Avertissement:</strong>
        Référentiel à titre indicatif — Consulter un transitaire agréé pour validation
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)