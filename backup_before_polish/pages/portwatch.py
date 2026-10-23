import streamlit as st
import sys
import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'port_optimizer'))
from portwatch_connector import run_portwatch


def show():
    st.markdown("""
    <style>
    .pw-header {
        background: linear-gradient(135deg, #0a2540 0%, #1a3a5c 100%);
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    .pw-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
    }
    .pw-subtitle {
        font-size: 0.95rem;
        color: #a0b4c8;
        margin-top: 0.4rem;
    }
    .pw-badge {
        display: inline-block;
        background: #00c853;
        color: #fff;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 10px;
        border-radius: 20px;
        margin-left: 10px;
        vertical-align: middle;
        letter-spacing: 0.05em;
    }
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e8edf2;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .kpi-value {
        font-size: 1.9rem;
        font-weight: 700;
        color: #0a2540;
    }
    .kpi-label {
        font-size: 0.78rem;
        color: #6b7c93;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 0.3rem;
    }
    .kpi-sub {
        font-size: 0.82rem;
        color: #00c853;
        font-weight: 600;
        margin-top: 0.2rem;
    }
    .section-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0a2540;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e8edf2;
    }
    .source-bar {
        background: #f0f4f8;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-size: 0.78rem;
        color: #6b7c93;
        margin-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="pw-header">
        <div class="pw-title">PortWatch Live Intelligence <span class="pw-badge">LIVE</span></div>
        <div class="pw-subtitle">Tanger Med Port &mdash; IMF PortWatch AIS Satellite Feed &mdash; Updated Daily</div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Loading live PortWatch data..."):
        col_refresh, _ = st.columns([1, 5])
        with col_refresh:
            force = st.button("Refresh Data")
        data = run_portwatch(force_refresh=force)

    if data.get("error") or not data.get("records"):
        st.error("Could not retrieve PortWatch data. Check your internet connection and try refreshing.")
        return

    records = data["records"]
    summary = data["summary"]
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{summary.get('avg_daily_calls', 0)}</div>
            <div class="kpi-label">Avg Daily Calls (30d)</div>
            <div class="kpi-sub">vessel calls / day</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{summary.get('latest_calls', 0)}</div>
            <div class="kpi-label">Latest Day Calls</div>
            <div class="kpi-sub">{summary.get('latest_date', '')}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        imp = summary.get('total_import_tons', 0)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{imp/1_000_000:.1f}M</div>
            <div class="kpi-label">Total Import (30d)</div>
            <div class="kpi-sub">tonnes</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        exp = summary.get('total_export_tons', 0)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{exp/1_000_000:.1f}M</div>
            <div class="kpi-label">Total Export (30d)</div>
            <div class="kpi-sub">tonnes</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Daily Vessel Calls</div>', unsafe_allow_html=True)

    fig_calls = go.Figure()
    fig_calls.add_trace(go.Bar(
        x=df["date"], y=df["calls"],
        name="Total Calls",
        marker_color="#0a2540",
        opacity=0.85,
    ))
    fig_calls.add_trace(go.Bar(
        x=df["date"], y=df["calls_container"],
        name="Container",
        marker_color="#2196f3",
        opacity=0.85,
    ))
    fig_calls.add_trace(go.Scatter(
        x=df["date"],
        y=[summary.get("avg_daily_calls", 0)] * len(df),
        name="30d Average",
        mode="lines",
        line=dict(color="#00c853", width=2, dash="dash"),
    ))
    fig_calls.update_layout(
        barmode="overlay",
        height=320,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=1.12),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        yaxis=dict(gridcolor="#f0f4f8", title="Vessel Calls"),
        xaxis=dict(gridcolor="#f0f4f8"),
    )
    st.plotly_chart(fig_calls, use_container_width=True)

    st.markdown('<div class="section-title">Import vs Export Tonnage (Daily)</div>', unsafe_allow_html=True)

    fig_trade = make_subplots(specs=[[{"secondary_y": False}]])
    fig_trade.add_trace(go.Scatter(
        x=df["date"], y=df["import_tons"],
        name="Import (t)",
        fill="tozeroy",
        line=dict(color="#2196f3", width=2),
        fillcolor="rgba(33,150,243,0.12)",
    ))
    fig_trade.add_trace(go.Scatter(
        x=df["date"], y=df["export_tons"],
        name="Export (t)",
        fill="tozeroy",
        line=dict(color="#ff6b35", width=2),
        fillcolor="rgba(255,107,53,0.12)",
    ))
    fig_trade.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=1.12),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        yaxis=dict(gridcolor="#f0f4f8", title="Tonnes"),
        xaxis=dict(gridcolor="#f0f4f8"),
    )
    st.plotly_chart(fig_trade, use_container_width=True)

    st.markdown('<div class="section-title">Raw Data Table</div>', unsafe_allow_html=True)

    display_df = df[["date", "calls", "calls_container", "import_tons", "export_tons"]].copy()
    display_df.columns = ["Date", "Total Calls", "Container Calls", "Import (t)", "Export (t)"]
    display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
    display_df = display_df.sort_values("Date", ascending=False).reset_index(drop=True)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown(f"""
    <div class="source-bar">
        Data source: IMF PortWatch &mdash; AIS satellite tracking (UN Global Platform) &mdash;
        Port ID: port1265 &mdash; Last fetched: {data.get('fetched_at', 'N/A')}
    </div>
    """, unsafe_allow_html=True)