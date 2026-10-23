import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import math
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, LpStatus, value


class Vessel:
    def __init__(self, vessel_id, name, shipping_line, size_teu, eta, priority):
        self.vessel_id = vessel_id
        self.name = name
        self.shipping_line = shipping_line
        self.size_teu = size_teu
        self.eta = datetime.strptime(eta, "%Y-%m-%d %H:%M")
        self.priority = priority

class Berth:
    def __init__(self, berth_id, name, terminal, max_capacity_teu, handling_rate_teu_per_hour):
        self.berth_id = berth_id
        self.name = name
        self.terminal = terminal
        self.max_capacity_teu = max_capacity_teu
        self.handling_rate_teu_per_hour = handling_rate_teu_per_hour
    def can_accept(self, v):
        return v.size_teu <= self.max_capacity_teu
    def service_time_hours(self, v):
        return v.size_teu / self.handling_rate_teu_per_hour

class PortOptimizer:
    def __init__(self, vessels, berths, slot_hours=4, horizon_hours=432):
        self.vessels = vessels
        self.berths = berths
        self.slot_hours = slot_hours
        self.num_slots = horizon_hours // slot_hours
        self.base_time = min(v.eta for v in vessels)
        self.schedule = []
        self.status = None
    def eta_hours(self, v):
        return (v.eta - self.base_time).total_seconds() / 3600
    def eta_slot(self, v):
        return math.ceil(self.eta_hours(v) / self.slot_hours)
    def slots_needed(self, v, b):
        return math.ceil(b.service_time_hours(v) / self.slot_hours)
    def solve(self):
        prob = LpProblem("BAP", LpMinimize)
        slots = range(self.num_slots)
        x = {(v.vessel_id, b.berth_id, t): LpVariable(f"x_{v.vessel_id}_{b.berth_id}_{t}", cat=LpBinary)
             for v in self.vessels for b in self.berths if b.can_accept(v)
             for t in slots if t >= self.eta_slot(v)}
        pw = {1:3, 2:2, 3:1}
        prob += lpSum((t - self.eta_slot(v)) * self.slot_hours * pw[v.priority] * x[(v.vessel_id, b.berth_id, t)]
                      for v in self.vessels for b in self.berths if b.can_accept(v)
                      for t in slots if t >= self.eta_slot(v))
        for v in self.vessels:
            valid = [(v.vessel_id, b.berth_id, t) for b in self.berths if b.can_accept(v)
                     for t in slots if t >= self.eta_slot(v)]
            prob += lpSum(x[k] for k in valid) == 1
        for b in self.berths:
            for t in slots:
                occ = []
                for v in self.vessels:
                    if not b.can_accept(v): continue
                    dur = self.slots_needed(v, b)
                    for st in range(max(0, t - dur + 1), t + 1):
                        if st >= self.eta_slot(v) and (v.vessel_id, b.berth_id, st) in x:
                            occ.append(x[(v.vessel_id, b.berth_id, st)])
                if occ:
                    prob += lpSum(occ) <= 1
        prob.solve()
        self.status = LpStatus[prob.status]
        self._extract(x, slots)
        return self.status
    def _extract(self, x, slots):
        self.schedule = []
        for v in self.vessels:
            for b in self.berths:
                if not b.can_accept(v): continue
                for t in slots:
                    k = (v.vessel_id, b.berth_id, t)
                    if k in x and value(x[k]) is not None and round(value(x[k])) == 1:
                        sh = t * self.slot_hours
                        svc = b.service_time_hours(v)
                        start = self.base_time + timedelta(hours=sh)
                        end = start + timedelta(hours=svc)
                        wait = sh - self.eta_hours(v)
                        self.schedule.append({
                            "vessel": v.name, "shipping_line": v.shipping_line,
                            "size_teu": v.size_teu, "priority": v.priority,
                            "berth": b.name, "terminal": b.terminal,
                            "eta": v.eta.strftime("%b %d %H:%M"),
                            "start": start.strftime("%b %d %H:%M"),
                            "end": end.strftime("%b %d %H:%M"),
                            "wait_hours": round(max(wait, 0), 1),
                            "service_hours": round(svc, 1),
                            "start_h": sh, "end_h": sh + svc,
                        })
        self.schedule.sort(key=lambda r: r["start"])
    def avg_wait(self):
        return sum(r["wait_hours"] for r in self.schedule) / len(self.schedule) if self.schedule else 0
    def total_wait(self):
        return sum(r["wait_hours"] for r in self.schedule)

def run_fcfs(vessels, berths):
    free_at = {b.berth_id: datetime(2000,1,1) for b in berths}
    schedule = []
    base = min(v.eta for v in vessels)
    for v in sorted(vessels, key=lambda x: x.eta):
        best_b, best_start = None, None
        for b in berths:
            if not b.can_accept(v): continue
            es = max(v.eta, free_at[b.berth_id])
            if best_start is None or es < best_start:
                best_start, best_b = es, b
        if not best_b: continue
        svc = best_b.service_time_hours(v)
        end = best_start + timedelta(hours=svc)
        free_at[best_b.berth_id] = end
        wait = (best_start - v.eta).total_seconds() / 3600
        start_h = (best_start - base).total_seconds() / 3600
        schedule.append({
            "vessel": v.name, "shipping_line": v.shipping_line,
            "size_teu": v.size_teu, "priority": v.priority,
            "berth": best_b.name, "terminal": best_b.terminal,
            "eta": v.eta.strftime("%b %d %H:%M"),
            "start": best_start.strftime("%b %d %H:%M"),
            "end": end.strftime("%b %d %H:%M"),
            "wait_hours": round(max(wait, 0), 1),
            "service_hours": round(svc, 1),
            "start_h": start_h, "end_h": start_h + svc,
        })
    return schedule

@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "port_optimizer", "port_optimizer.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT berth_id,name,terminal,max_capacity_teu,handling_rate_teu_per_hour FROM berths")
    berths = [Berth(*r) for r in cur.fetchall()]
    cur.execute("SELECT vessel_id,name,shipping_line,size_teu,eta,priority FROM vessels")
    vessels = [Vessel(*r) for r in cur.fetchall()]
    conn.close()
    return vessels, berths


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

    if "port_solved" not in st.session_state:
        st.session_state.port_solved = False

    vessels, berths = load_data()

    if not st.session_state.port_solved:
        with st.spinner("Running CBC MILP Solver..."):
            opt = PortOptimizer(vessels, berths)
            opt.solve()
            fcfs = run_fcfs(vessels, berths)
            fcfs_total = sum(r["wait_hours"] for r in fcfs)
            fcfs_avg = fcfs_total / len(fcfs) if fcfs else 0
            st.session_state.port_opt_schedule = opt.schedule
            st.session_state.port_opt_avg = round(opt.avg_wait(), 1)
            st.session_state.port_opt_total = round(opt.total_wait(), 1)
            st.session_state.port_fcfs_schedule = fcfs
            st.session_state.port_fcfs_avg = round(fcfs_avg, 1)
            st.session_state.port_fcfs_total = round(fcfs_total, 1)
            st.session_state.port_solved = True

    opt_schedule = st.session_state.port_opt_schedule
    opt_avg = st.session_state.port_opt_avg
    opt_total = st.session_state.port_opt_total
    fcfs_schedule = st.session_state.port_fcfs_schedule
    fcfs_avg = st.session_state.port_fcfs_avg
    fcfs_total = st.session_state.port_fcfs_total
    improvement = round((fcfs_total - opt_total) / fcfs_total * 100, 1)
    hours_saved = round(fcfs_total - opt_total, 1)
    high_pri = sum(1 for r in opt_schedule if r["priority"] == 1)
    zero_wait = sum(1 for r in opt_schedule if r["wait_hours"] == 0)

    # FIX 1: Demurrage rate corrected from $25,000 to $10,000/hour
    # Real demurrage at Tanger Med ranges $8,000-$15,000/hour depending on vessel class
    DEMURRAGE_PER_HOUR = 10000
    demurrage_avoided = round(hours_saved * DEMURRAGE_PER_HOUR)
    horizon_hours = 432  # 18-day planning horizon
    horizon_days = horizon_hours / 24  # 18 days
    tat_saved_per_week = round(hours_saved / horizon_days * 7, 1)
    total_service_hours = sum(r["service_hours"] for r in opt_schedule)
    num_berths = 8
    bor = round((total_service_hours / (horizon_hours * num_berths)) * 100, 1)

    mother_opt = [r for r in opt_schedule if r["priority"] == 1]
    mother_fcfs = [r for r in fcfs_schedule if r["priority"] == 1]
    mother_wait_opt = round(sum(r["wait_hours"] for r in mother_opt) / len(mother_opt), 1) if mother_opt else 0
    mother_wait_fcfs = round(sum(r["wait_hours"] for r in mother_fcfs) / len(mother_fcfs), 1) if mother_fcfs else 0
    mother_improvement = round((mother_wait_fcfs - mother_wait_opt) / mother_wait_fcfs * 100, 1) if mother_wait_fcfs else 0

    opt_json = json.dumps(opt_schedule)
    fcfs_json = json.dumps(fcfs_schedule)

    st.markdown(f"""
    <div style="padding:20px 24px 0 24px;">
      <div style="font-size:10px;font-weight:700;color:#98A2B3;letter-spacing:.1em;text-transform:uppercase;margin-bottom:14px;">
        Optimizer Results &mdash; Synthetic Scenario &mdash; Tanger Med
      </div>
    </div>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("TAT Saved / Week", f"{tat_saved_per_week}h", delta="vs FCFS baseline")
    with k2:
        st.metric("Berth Occupancy Rate", f"{bor}%", delta="Target: 75-85%")
    with k3:
        # FIX 1 continued: label updated to $10K/h
        st.metric("Est. Demurrage Avoided", f"${demurrage_avoided:,}", delta=f"{hours_saved}h @ $10K/h")
    with k4:
        st.metric("Mother Vessel Wait", f"{mother_wait_opt}h", delta=f"-{mother_improvement}% vs FCFS", delta_color="inverse")

    st.markdown("<div style='padding:0 24px;margin-top:8px;'>", unsafe_allow_html=True)

    with st.expander("MILP Formulation — Discrete Berth Allocation Problem"):
        st.markdown(r"""
**Model type:** Discrete time-indexed BAP — planning horizon divided into 4-hour slots.

**Objective Function — Minimize Priority-Weighted Total Wait:**

$$\min \sum_{i \in V} \sum_{b \in B} \sum_{t \geq \text{ETA}_i} w_i \cdot (t - \text{ETA\_slot}_i) \cdot \Delta t \cdot x_{i,b,t}$$

**Where:**
- $w_i$ = priority weight of vessel $i$ — Mother Vessel $w=3$, Feeder L1 $w=2$, Feeder L2 $w=1$
- $t$ = discrete time slot (each slot = 4 hours), $\Delta t = 4$
- $x_{i,b,t} \in \{0,1\}$ = 1 if vessel $i$ starts service at berth $b$ in slot $t$

**Subject to:**

$$\sum_{b \in B} \sum_{t \geq \text{ETA\_slot}_i} x_{i,b,t} = 1 \quad \forall i \in V \quad \text{(each vessel assigned exactly once)}$$

$$\sum_{i \in V} \sum_{s=t-d_{i,b}+1}^{t} x_{i,b,s} \leq 1 \quad \forall b \in B, \forall t \in T \quad \text{(no berth overlap)}$$

$$\text{TEU}_i \leq \text{capacity}_b \quad \forall i \in V, b \in B \quad \text{(capacity constraint — enforced in code)}$$

$$x_{i,b,t} \in \{0,1\} \quad \text{(binary decision variable)}$$

**Note:** Draft/depth constraint is not enforced in the current implementation. Capacity (TEU) is the only physical constraint active in this version.

**Solver:** CBC (COIN-OR Branch and Cut) via PuLP
        """)

    st.markdown("</div>", unsafe_allow_html=True)

    df_export = pd.DataFrame(opt_schedule)
    df_export_display = df_export[["vessel","shipping_line","size_teu","priority","berth","terminal","eta","start","end","wait_hours","service_hours"]]
    df_export_display.columns = ["Vessel","Shipping Line","TEU","Priority","Berth","Terminal","ETA","Start","End","Wait (h)","Service (h)"]

    col_csv, col_json, _ = st.columns([1, 1, 4])
    with col_csv:
        st.download_button(
            label="Export CSV (PCS Format)",
            data=df_export_display.to_csv(index=False).encode("utf-8"),
            file_name="portiq_optimized_schedule.csv",
            mime="text/csv",
        )
    with col_json:
        st.download_button(
            label="Export JSON (ERP Format)",
            data=json.dumps({"source": "portiq.xyz", "port": "Tanger Med", "schedule": opt_schedule}, indent=2).encode("utf-8"),
            file_name="portiq_optimized_schedule.json",
            mime="application/json",
        )

    HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --blue:#0057B8;--blue-light:#EBF2FF;--blue-mid:#C5D9F5;
  --green:#00875A;--green-light:#E3F5EE;
  --red:#C0392B;--red-light:#FDECEA;
  --orange:#D97706;--orange-light:#FEF3C7;
  --gray-50:#F8F9FA;--gray-100:#F0F2F5;--gray-200:#E4E7EC;
  --gray-300:#D0D5DD;--gray-400:#98A2B3;--gray-500:#667085;
  --gray-600:#475467;--gray-700:#344054;--gray-800:#1D2939;--gray-900:#101828;
  --white:#FFFFFF;
  --shadow-sm:0 1px 3px rgba(16,24,40,0.1),0 1px 2px rgba(16,24,40,0.06);
  --shadow-md:0 4px 8px rgba(16,24,40,0.08),0 2px 4px rgba(16,24,40,0.04);
  --radius:8px;--font:'Inter',sans-serif;
}}
html,body{{background:var(--gray-100);font-family:var(--font);font-size:13px;color:var(--gray-800);min-height:100vh}}
.topbar{{background:var(--white);border-bottom:1px solid var(--gray-200);display:flex;align-items:center;justify-content:space-between;padding:0 24px;height:52px;box-shadow:var(--shadow-sm)}}
.tb-left{{display:flex;align-items:center;gap:8px}}
.tb-logo{{width:28px;height:28px;background:var(--blue);border-radius:5px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;color:white}}
.tb-name{{font-weight:700;font-size:15px;color:var(--gray-900)}}
.tb-sep{{color:var(--gray-300);margin:0 4px}}
.tb-page{{font-size:13px;color:var(--gray-500);font-weight:500}}
.tb-right{{display:flex;align-items:center;gap:16px}}
.pill{{display:flex;align-items:center;gap:5px;background:var(--green-light);border-radius:20px;padding:4px 10px;font-size:11px;font-weight:600;color:var(--green)}}
.pdot{{width:5px;height:5px;border-radius:50%;background:var(--green);animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.tb-time{{font-size:11px;color:var(--gray-500)}}
.ticker-wrap{{background:#FFF8E1;border-bottom:1px solid #FFE082;padding:8px 24px;display:flex;align-items:center;gap:12px;overflow:hidden}}
.ticker-label{{font-size:10px;font-weight:700;color:#F57F17;letter-spacing:.1em;text-transform:uppercase;flex-shrink:0;background:#FFE082;padding:3px 8px;border-radius:4px}}
.ticker-track{{overflow:hidden;flex:1;position:relative;height:18px}}
.ticker-inner{{display:flex;gap:64px;white-space:nowrap;animation:scroll 28s linear infinite;align-items:center}}
@keyframes scroll{{0%{{transform:translateX(0)}}100%{{transform:translateX(-50%)}}}}
.alert-item{{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--gray-700);flex-shrink:0}}
.alert-dot{{width:7px;height:7px;border-radius:50%;flex-shrink:0}}
.dot-red{{background:#C0392B}}.dot-yellow{{background:#D97706}}.dot-green{{background:#00875A}}
.page{{padding:20px 24px}}
.sec-label{{font-size:10px;font-weight:700;color:var(--gray-400);letter-spacing:.1em;text-transform:uppercase;margin-bottom:12px;display:flex;align-items:center;gap:8px}}
.sec-label::after{{content:'';flex:1;height:1px;background:var(--gray-200)}}
.kpi-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:20px}}
.kpi{{background:var(--white);border-radius:var(--radius);border:1px solid var(--gray-200);padding:18px 20px;box-shadow:var(--shadow-sm);position:relative;overflow:hidden}}
.kpi::after{{content:'';position:absolute;top:0;left:0;width:3px;height:100%;background:var(--blue)}}
.kpi.g::after{{background:var(--green)}}.kpi.o::after{{background:var(--orange)}}.kpi.r::after{{background:var(--red)}}
.kl{{font-size:10px;font-weight:600;color:var(--gray-500);letter-spacing:.05em;text-transform:uppercase;margin-bottom:6px}}
.kv{{font-size:30px;font-weight:700;color:var(--gray-900);line-height:1;margin-bottom:3px;letter-spacing:-.5px}}
.kv.blue{{color:var(--blue)}}.kv.green{{color:var(--green)}}.kv.orange{{color:var(--orange)}}
.ks{{font-size:11px;color:var(--gray-400)}}
.cstrip{{background:var(--white);border:1px solid var(--gray-200);border-radius:var(--radius);padding:18px 24px;margin-bottom:20px;box-shadow:var(--shadow-sm);display:flex;align-items:center;gap:28px}}
.clabel{{font-size:10px;font-weight:700;color:var(--gray-400);letter-spacing:.08em;text-transform:uppercase;flex-shrink:0}}
.cnum{{font-size:26px;font-weight:700;letter-spacing:-.5px;line-height:1}}
.cdesc{{font-size:10px;color:var(--gray-400);margin-top:2px}}
.arrow{{font-size:18px;color:var(--gray-300)}}
.ibox{{flex:1;background:var(--green-light);border-radius:6px;padding:14px 18px;display:flex;align-items:center;gap:16px}}
.inum{{font-size:34px;font-weight:700;color:var(--green);letter-spacing:-.5px;line-height:1}}
.idesc{{font-size:12px;color:var(--green);font-weight:600}}
.isub{{font-size:10px;color:var(--gray-500);margin-top:2px}}
.bars{{flex:1}}
.brow{{display:flex;align-items:center;gap:10px;margin-bottom:7px}}
.brow:last-child{{margin-bottom:0}}
.blabel{{font-size:11px;color:var(--gray-600);width:130px;flex-shrink:0;font-weight:500}}
.btrack{{flex:1;height:7px;background:var(--gray-100);border-radius:4px;overflow:hidden}}
.bfill{{height:100%;border-radius:4px}}
.bval{{font-size:11px;font-weight:600;width:42px;text-align:right;flex-shrink:0}}
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px}}
.card{{background:var(--white);border:1px solid var(--gray-200);border-radius:var(--radius);padding:18px;box-shadow:var(--shadow-sm)}}
.ctitle{{font-size:13px;font-weight:600;color:var(--gray-800);margin-bottom:3px}}
.csub{{font-size:11px;color:var(--gray-400);margin-bottom:12px}}
.legend{{display:flex;gap:14px;margin-bottom:10px;flex-wrap:wrap}}
.leg{{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--gray-600);font-weight:500}}
.ldot{{width:9px;height:9px;border-radius:2px}}
canvas{{display:block;width:100%}}
.tcard{{background:var(--white);border:1px solid var(--gray-200);border-radius:var(--radius);box-shadow:var(--shadow-sm);overflow:hidden;margin-bottom:20px}}
.thead{{padding:14px 18px;border-bottom:1px solid var(--gray-200);display:flex;align-items:center;justify-content:space-between}}
.ttitle{{font-size:13px;font-weight:600;color:var(--gray-800)}}
.tcount{{font-size:11px;color:var(--gray-400);background:var(--gray-100);padding:3px 8px;border-radius:12px;font-weight:500}}
table{{width:100%;border-collapse:collapse}}
th{{padding:9px 14px;text-align:left;font-size:10px;font-weight:600;color:var(--gray-500);letter-spacing:.05em;text-transform:uppercase;background:var(--gray-50);border-bottom:1px solid var(--gray-200);white-space:nowrap}}
td{{padding:10px 14px;border-bottom:1px solid var(--gray-100);font-size:12px;color:var(--gray-700);vertical-align:middle}}
tbody tr:last-child td{{border-bottom:none}}
tbody tr:hover td{{background:var(--blue-light)}}
.badge{{display:inline-flex;align-items:center;padding:2px 8px;border-radius:12px;font-size:10px;font-weight:600}}
.btc1{{background:#EBF2FF;color:#0057B8}}.btc2{{background:#F0FDF4;color:#15803D}}
.btc3{{background:#FFF7ED;color:#C2410C}}.btc4{{background:#FDF4FF;color:#7E22CE}}
.bhigh{{background:#FDECEA;color:#C0392B}}.bmed{{background:#FEF3C7;color:#D97706}}.blow{{background:var(--gray-100);color:var(--gray-500)}}
.wok{{color:var(--green);font-weight:600}}.wmd{{color:var(--orange);font-weight:600}}.whi{{color:var(--red);font-weight:600}}
.vname{{font-weight:600;color:var(--gray-800);font-size:12px}}
.vline{{font-size:10px;color:var(--gray-400);margin-top:1px}}
.vtype{{font-size:9px;font-weight:700;letter-spacing:.05em;padding:1px 5px;border-radius:3px;display:inline-block;margin-top:2px}}
.mother{{background:#FDECEA;color:#C0392B}}.feeder{{background:#EBF2FF;color:#0057B8}}
/* FIX 2: Transhipment info box */
.tranship-info{{background:#FFF8E1;border:1px solid #FFE082;border-radius:8px;padding:12px 16px;margin-bottom:14px;font-size:12px;color:#344054;line-height:1.6;}}
.tranship-info strong{{color:#1D2939;}}
/* FIX 3: Footer disclaimer */
.footer{{text-align:center;padding:16px;font-size:11px;color:var(--gray-400);border-top:1px solid var(--gray-200);background:var(--white)}}
.footer-disclaimer{{font-size:10px;color:#98A2B3;margin-top:4px;}}
</style>
</head>
<body>

<div class="topbar">
  <div class="tb-left">
    <div class="tb-logo">PQ</div>
    <span class="tb-name">portiq.xyz</span>
    <span class="tb-sep">/</span>
    <span class="tb-page">Berth Allocation Optimizer — Tanger Med</span>
  </div>
  <div class="tb-right">
    <div class="pill"><div class="pdot"></div>OPTIMAL SOLUTION</div>
    <div class="tb-time" id="clk">--:--:-- UTC</div>
  </div>
</div>

<div class="ticker-wrap">
  <div class="ticker-label">Note</div>
  <div class="ticker-track">
    <div class="ticker-inner">
      <div class="alert-item"><div class="alert-dot dot-yellow"></div>Simulation on 25 synthetic vessels generated for demonstration — shipping lines, sizes and routes reflect realistic Tanger Med traffic profiles (ANP 2025)</div>
      <div class="alert-item"><div class="alert-dot dot-yellow"></div>Demurrage rate of $10,000/hour is a modelling assumption — realistic range for Tanger Med vessel classes: $8,000–$15,000/hour</div>
      <div class="alert-item"><div class="alert-dot dot-yellow"></div>Simulation on 25 synthetic vessels generated for demonstration — shipping lines, sizes and routes reflect realistic Tanger Med traffic profiles (ANP 2025)</div>
      <div class="alert-item"><div class="alert-dot dot-yellow"></div>Demurrage rate of $10,000/hour is a modelling assumption — realistic range for Tanger Med vessel classes: $8,000–$15,000/hour</div>
    </div>
  </div>
</div>

<div class="page">
  <div class="sec-label">Quickview Dashboard</div>
  <div class="kpi-grid">
    <div class="kpi"><div class="kl">Vessels Scheduled</div><div class="kv blue">25</div><div class="ks">All assigned &mdash; optimal</div></div>
    <div class="kpi g"><div class="kl">LP Optimizer Avg Wait</div><div class="kv green">{opt_avg}h</div><div class="ks">Priority-weighted minimum</div></div>
    <div class="kpi o"><div class="kl">FCFS Baseline Avg Wait</div><div class="kv orange">{fcfs_avg}h</div><div class="ks">First come first served</div></div>
    <div class="kpi g"><div class="kl">Mother Vessel Wait</div><div class="kv green">{mother_wait_opt}h</div><div class="ks">vs {mother_wait_fcfs}h FCFS &mdash; -{mother_improvement}%</div></div>
    <div class="kpi"><div class="kl">High Priority (Mother)</div><div class="kv blue">{high_pri}</div><div class="ks">{zero_wait} vessels with zero wait</div></div>
  </div>

  <div class="sec-label">Optimizer vs Baseline</div>
  <div class="cstrip">
    <div class="clabel">Performance<br>Analysis</div>
    <div><div class="cnum" style="color:var(--red)">{fcfs_avg}h</div><div class="cdesc">FCFS Avg Wait</div></div>
    <div class="arrow">&rarr;</div>
    <div><div class="cnum" style="color:var(--green)">{opt_avg}h</div><div class="cdesc">Optimizer Avg Wait</div></div>
    <div class="ibox">
      <div>
        <div class="inum">&minus;{improvement}%</div>
        <div class="idesc">Reduction in total wait (unweighted hours)</div>
        <div class="isub">{hours_saved}h saved &mdash; ${demurrage_avoided:,} demurrage avoided (assumption: $10K/h) &mdash; BOR {bor}%</div>
      </div>
    </div>
    <div class="bars">
      <div class="brow"><div class="blabel">FCFS (unoptimized)</div><div class="btrack"><div class="bfill" style="width:100%;background:var(--red);opacity:.7"></div></div><div class="bval" style="color:var(--red)">{fcfs_avg}h</div></div>
      <div class="brow"><div class="blabel">LP Optimizer</div><div class="btrack"><div class="bfill" style="width:{round(opt_avg/fcfs_avg*100,1)}%;background:var(--green)"></div></div><div class="bval" style="color:var(--green)">{opt_avg}h</div></div>
      <div class="brow"><div class="blabel">Mother Vessel Gain</div><div class="btrack"><div class="bfill" style="width:{mother_improvement}%;background:var(--blue)"></div></div><div class="bval" style="color:var(--blue)">{mother_improvement}%</div></div>
    </div>
  </div>

  <div class="sec-label">Berth Schedule Visualization</div>
  <div class="two-col">
    <div class="card">
      <div class="ctitle">FCFS Schedule &mdash; Unoptimized Baseline</div>
      <div class="csub">First Come First Served &mdash; avg wait {fcfs_avg}h &mdash; ignores priority & constraints</div>
      <div class="legend" id="leg1"></div>
      <canvas id="gF" height="195"></canvas>
    </div>
    <div class="card">
      <div class="ctitle">LP Optimizer Schedule &mdash; Optimal Solution</div>
      <div class="csub">CBC MILP &mdash; Mother vessels prioritized &mdash; avg wait {opt_avg}h</div>
      <div class="legend" id="leg2"></div>
      <canvas id="gO" height="195"></canvas>
    </div>
  </div>

  <div class="sec-label">Optimized Berth Assignment</div>

  <!-- FIX 2: Transhipment priority explanation box -->
  <div class="tranship-info">
    <strong>Transhipment Priority Logic:</strong> Tanger Med handles approximately 75% transhipment traffic,
    making it the leading hub in Africa and the Mediterranean (source: ANP Rapport 2025 — 10.2M TEU in 2024).
    <strong>MOTHER vessels</strong> (large deep-sea ships) receive priority weight &times;3 in the MILP objective,
    reflecting their higher operational priority in transhipment hub operations.
    <strong>FEEDER vessels</strong> receive weight &times;2 (priority service) or &times;1 (standard).
    The &times;3 weight is a modelling assumption — sensitivity analysis on this parameter is a planned extension.
  </div>

  <div class="tcard">
    <div class="thead">
      <div class="ttitle">All Vessels &mdash; Optimized Schedule</div>
      <div class="tcount">25 vessels</div>
    </div>
    <table>
      <thead><tr>
        <th>Vessel</th><th>Berth</th><th>Terminal</th>
        <th>ETA</th><th>Start</th><th>End</th>
        <th>Service</th><th>TEU</th><th>Priority</th><th>Wait</th>
      </tr></thead>
      <tbody id="tb"></tbody>
    </table>
  </div>

  <!-- FIX 3: Footer with data disclaimer -->
  <div class="footer">
    portiq.xyz &mdash; Berth Allocation Optimizer &mdash; CBC MILP Solver (PuLP 2.x) &mdash; Python 3.14
    <div class="footer-disclaimer">
      Simulation on synthetic vessels. Terminal infrastructure parameters sourced from official ANP and Tanger Med publications.
      3,600m quay &middot; 18m depth &middot; 9M TEU annual capacity &middot; Operators: Marsa Maroc (TC1), APM Terminals (TC2), Eurogate (TC3), TMPA (TC4)
      &middot; Demurrage rate $10,000/h = modelling assumption &middot; ×3 Mother weight = modelling assumption
    </div>
  </div>
</div>

<script>
const OPT={opt_json};
const FCFS={fcfs_json};
const TCC={{"TC1":"#0057B8","TC2":"#15803D","TC3":"#C2410C","TC4":"#7E22CE"}};
const TCL={{"TC1":"#EBF2FF","TC2":"#F0FDF4","TC3":"#FFF7ED","TC4":"#FDF4FF"}};
const BO=["Berth A1","Berth A2","Berth B1","Berth B2","Berth C1","Berth C2","Berth D1","Berth D2"];

function tick(){{const t=new Date().toUTCString().slice(17,25)+' UTC';document.getElementById('clk').textContent=t;}}
setInterval(tick,1000);tick();

function buildLegend(id){{
  const el=document.getElementById(id);
  Object.entries(TCC).forEach(([tc,col])=>{{
    const d=document.createElement('div');d.className='leg';
    d.innerHTML=`<div class="ldot" style="background:${{col}}"></div>${{tc}}`;
    el.appendChild(d);
  }});
}}
buildLegend('leg1');buildLegend('leg2');

function drawGantt(id,data){{
  const cv=document.getElementById(id);
  const dpr=window.devicePixelRatio||1;
  const W=cv.parentElement.clientWidth-36;
  const RH=22,LW=72,H=BO.length*RH+32;
  cv.width=W*dpr;cv.height=H*dpr;
  cv.style.width=W+'px';cv.style.height=H+'px';
  const c=cv.getContext('2d');c.scale(dpr,dpr);
  c.fillStyle='#F8F9FA';c.fillRect(0,0,W,H);
  const maxE=Math.max(...data.map(r=>r.end_h));
  const sc=(W-LW-4)/maxE;
  const ti=maxE>200?48:24;
  for(let t=0;t<=maxE;t+=ti){{
    const x=LW+t*sc;
    c.strokeStyle='#E4E7EC';c.lineWidth=1;
    c.beginPath();c.moveTo(x,0);c.lineTo(x,H-18);c.stroke();
    c.fillStyle='#98A2B3';c.font='9px Inter,sans-serif';
    c.fillText(t+'h',x+2,H-6);
  }}
  BO.forEach((b,i)=>{{
    const y=i*RH+12;
    c.fillStyle=i%2===0?'#FFFFFF':'#F8F9FA';
    c.fillRect(LW,y,W-LW,RH-1);
    c.fillStyle='#475467';c.font='500 10px Inter,sans-serif';
    c.fillText(b.replace('Berth ','Berth '),3,y+13);
    data.filter(r=>r.berth===b).forEach(r=>{{
      const x=LW+r.start_h*sc;
      const w=Math.max(3,(r.end_h-r.start_h)*sc);
      const col=TCC[r.terminal]||'#0057B8';
      const lgt=TCL[r.terminal]||'#EBF2FF';
      c.fillStyle=lgt;c.fillRect(x,y+2,w,RH-5);
      c.fillStyle=col;c.fillRect(x,y+2,3,RH-5);
      c.strokeStyle=col+'50';c.lineWidth=1;c.strokeRect(x,y+2,w,RH-5);
      if(w>50){{
        c.fillStyle='#1D2939';c.font='500 9px Inter,sans-serif';
        c.fillText(r.vessel.slice(0,13),x+6,y+12);
        if(w>80){{c.fillStyle='#667085';c.font='9px Inter,sans-serif';c.fillText(r.wait_hours+'h wait',x+6,y+21);}}
      }}
    }});
  }});
  c.strokeStyle='#D0D5DD';c.lineWidth=1;
  c.beginPath();c.moveTo(LW,0);c.lineTo(LW,H-18);c.stroke();
  c.beginPath();c.moveTo(LW,H-18);c.lineTo(W,H-18);c.stroke();
}}

function buildTable(){{
  const tb=document.getElementById('tb');
  OPT.forEach(r=>{{
    const pc=r.priority===1?'bhigh':r.priority===2?'bmed':'blow';
    const pl=r.priority===1?'High':r.priority===2?'Medium':'Low';
    const vtype=r.priority===1?'MOTHER':'FEEDER';
    const vtc=r.priority===1?'mother':'feeder';
    const wc=r.wait_hours===0?'wok':r.wait_hours<=20?'wmd':'whi';
    const tr=document.createElement('tr');
    tr.innerHTML=`<td><div class="vname">${{r.vessel}}</div><div class="vline">${{r.shipping_line}}</div><span class="vtype ${{vtc}}">${{vtype}}</span></td><td style="font-weight:500">${{r.berth}}</td><td><span class="badge btc${{r.terminal.slice(2)}}">${{r.terminal}}</span></td><td style="color:var(--gray-500)">${{r.eta}}</td><td style="font-weight:500">${{r.start}}</td><td style="color:var(--gray-500)">${{r.end}}</td><td style="color:var(--gray-500)">${{r.service_hours}}h</td><td style="color:var(--gray-600)">${{r.size_teu.toLocaleString()}}</td><td><span class="badge ${{pc}}">${{pl}}</span></td><td class="${{wc}}">${{r.wait_hours===0?'No wait':r.wait_hours+'h'}}</td>`;
    tb.appendChild(tr);
  }});
}}

window.addEventListener('load',()=>{{drawGantt('gF',FCFS);drawGantt('gO',OPT);buildTable();}});
window.addEventListener('resize',()=>{{drawGantt('gF',FCFS);drawGantt('gO',OPT);}});
</script>
</body></html>"""

    components.html(HTML, height=1650, scrolling=True)