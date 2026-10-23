import sqlite3
import math
from datetime import datetime, timedelta
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, LpStatus, value


class Vessel:
    def __init__(self, vessel_id, name, shipping_line, size_teu, eta, priority,
                 origin_port, origin_country, route, draft_m, vessel_type):
        self.vessel_id = vessel_id
        self.name = name
        self.shipping_line = shipping_line
        self.size_teu = size_teu
        self.eta = datetime.strptime(eta, "%Y-%m-%d %H:%M")
        self.priority = priority
        self.origin_port = origin_port
        self.origin_country = origin_country
        self.route = route
        self.draft_m = draft_m
        self.vessel_type = vessel_type

    def __repr__(self):
        return f"Vessel({self.name}, {self.size_teu} TEU, {self.vessel_type}, draft {self.draft_m}m)"


class Berth:
    def __init__(self, berth_id, name, terminal, max_capacity_teu,
                 handling_rate_teu_per_hour, water_depth_m, num_cranes):
        self.berth_id = berth_id
        self.name = name
        self.terminal = terminal
        self.max_capacity_teu = max_capacity_teu
        self.handling_rate_teu_per_hour = handling_rate_teu_per_hour
        self.water_depth_m = water_depth_m
        self.num_cranes = num_cranes

    def can_accept(self, vessel):
        if vessel.size_teu > self.max_capacity_teu:
            return False
        if vessel.draft_m > self.water_depth_m:
            return False
        return True

    def service_time_hours(self, vessel):
        crane_bonus = (self.num_cranes - 2) * 15
        effective_rate = self.handling_rate_teu_per_hour + crane_bonus
        return vessel.size_teu / effective_rate

    def __repr__(self):
        return f"Berth({self.name}, {self.terminal}, depth {self.water_depth_m}m, {self.num_cranes} cranes)"


class PortOptimizer:
    def __init__(self, vessels, berths, slot_hours=4, horizon_hours=432):
        self.vessels = vessels
        self.berths = berths
        self.slot_hours = slot_hours
        self.horizon_hours = horizon_hours
        self.num_slots = horizon_hours // slot_hours
        self.base_time = min(v.eta for v in vessels)
        self.schedule = []
        self.status = None
        self.rejected_vessels = []

    def eta_hours(self, vessel):
        return (vessel.eta - self.base_time).total_seconds() / 3600

    def eta_slot(self, vessel):
        return math.ceil(self.eta_hours(vessel) / self.slot_hours)

    def slots_needed(self, vessel, berth):
        return math.ceil(berth.service_time_hours(vessel) / self.slot_hours)

    def solve(self):
        prob = LpProblem("Berth_Allocation_Problem", LpMinimize)
        slots = range(self.num_slots)

        eligible = {}
        for v in self.vessels:
            valid_berths = [b for b in self.berths if b.can_accept(v)]
            if not valid_berths:
                self.rejected_vessels.append(v)
                continue
            eligible[v.vessel_id] = valid_berths

        eligible_vessels = [v for v in self.vessels if v.vessel_id in eligible]

        x = {
            (v.vessel_id, b.berth_id, t): LpVariable(
                f"x_{v.vessel_id}_{b.berth_id}_{t}", cat=LpBinary
            )
            for v in eligible_vessels
            for b in eligible[v.vessel_id]
            for t in slots
            if t >= self.eta_slot(v)
        }

        priority_weight = {1: 3, 2: 2, 3: 1}

        prob += lpSum(
            (t - self.eta_slot(v)) * self.slot_hours * priority_weight[v.priority]
            * x[(v.vessel_id, b.berth_id, t)]
            for v in eligible_vessels
            for b in eligible[v.vessel_id]
            for t in slots
            if t >= self.eta_slot(v)
        )

        for v in eligible_vessels:
            valid_keys = [
                (v.vessel_id, b.berth_id, t)
                for b in eligible[v.vessel_id]
                for t in slots
                if t >= self.eta_slot(v)
            ]
            prob += lpSum(x[k] for k in valid_keys) == 1

        for b in self.berths:
            for t in slots:
                occupying = []
                for v in eligible_vessels:
                    if b not in eligible.get(v.vessel_id, []):
                        continue
                    dur = self.slots_needed(v, b)
                    for start_t in range(max(0, t - dur + 1), t + 1):
                        if start_t >= self.eta_slot(v) and (v.vessel_id, b.berth_id, start_t) in x:
                            occupying.append(x[(v.vessel_id, b.berth_id, start_t)])
                if occupying:
                    prob += lpSum(occupying) <= 1

        prob.solve()
        self.status = LpStatus[prob.status]
        self._extract(x, slots, eligible_vessels, eligible)
        return self.status

    def _extract(self, x, slots, eligible_vessels, eligible):
        self.schedule = []
        for v in eligible_vessels:
            for b in eligible[v.vessel_id]:
                for t in slots:
                    k = (v.vessel_id, b.berth_id, t)
                    if k in x and value(x[k]) is not None and round(value(x[k])) == 1:
                        sh = t * self.slot_hours
                        svc = b.service_time_hours(v)
                        start = self.base_time + timedelta(hours=sh)
                        end = start + timedelta(hours=svc)
                        wait = sh - self.eta_hours(v)
                        self.schedule.append({
                            "vessel": v.name,
                            "shipping_line": v.shipping_line,
                            "size_teu": v.size_teu,
                            "priority": v.priority,
                            "vessel_type": v.vessel_type,
                            "draft_m": v.draft_m,
                            "origin_port": v.origin_port,
                            "route": v.route,
                            "berth": b.name,
                            "terminal": b.terminal,
                            "water_depth_m": b.water_depth_m,
                            "num_cranes": b.num_cranes,
                            "eta": v.eta,
                            "start": start,
                            "end": end,
                            "wait_hours": round(max(wait, 0), 1),
                            "service_hours": round(svc, 1),
                        })
        self.schedule.sort(key=lambda r: r["start"])

    def total_wait(self):
        return sum(r["wait_hours"] for r in self.schedule)

    def avg_wait(self):
        return self.total_wait() / len(self.schedule) if self.schedule else 0

    def priority_weighted_wait(self):
        pw = {1: 3, 2: 2, 3: 1}
        return sum(r["wait_hours"] * pw[r["priority"]] for r in self.schedule)

    def mother_vessel_avg_wait(self):
        mv = [r for r in self.schedule if r["vessel_type"] == "MOTHER"]
        return sum(r["wait_hours"] for r in mv) / len(mv) if mv else 0

    def feeder_vessel_avg_wait(self):
        fv = [r for r in self.schedule if r["vessel_type"] == "FEEDER"]
        return sum(r["wait_hours"] for r in fv) / len(fv) if fv else 0

    def berth_occupancy_rate(self):
        occupancy = {}
        for b in self.berths:
            used = sum(r["service_hours"] for r in self.schedule if r["berth"] == b.name)
            occupancy[b.name] = round((used / self.horizon_hours) * 100, 1)
        return occupancy


def load_data(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT berth_id, name, terminal, max_capacity_teu,
               handling_rate_teu_per_hour, water_depth_m, num_cranes
        FROM berths
    """)
    berths = [Berth(*row) for row in cursor.fetchall()]
    cursor.execute("""
        SELECT vessel_id, name, shipping_line, size_teu, eta, priority,
               origin_port, origin_country, route, draft_m, vessel_type
        FROM vessels
    """)
    vessels = [Vessel(*row) for row in cursor.fetchall()]
    conn.close()
    return vessels, berths


if __name__ == "__main__":
    vessels, berths = load_data("port_optimizer.db")
    print(f"Loaded {len(vessels)} vessels and {len(berths)} berths")

    optimizer = PortOptimizer(vessels, berths)
    status = optimizer.solve()

    if optimizer.rejected_vessels:
        print(f"WARNING: {len(optimizer.rejected_vessels)} vessels rejected (draft constraint):")
        for v in optimizer.rejected_vessels:
            print(f"  {v.name} draft {v.draft_m}m")

    print(f"Solver status: {status}")
    print(f"Average wait time:              {optimizer.avg_wait():.1f} hours")
    print(f"Total wait time:                {optimizer.total_wait():.1f} hours")
    print(f"Priority-weighted wait:         {optimizer.priority_weighted_wait():.1f}")
    print(f"MOTHER vessel avg wait:         {optimizer.mother_vessel_avg_wait():.1f} hours")
    print(f"FEEDER vessel avg wait:         {optimizer.feeder_vessel_avg_wait():.1f} hours")

    print("\nBerth Occupancy Rates:")
    for berth, rate in optimizer.berth_occupancy_rate().items():
        print(f"  {berth}: {rate}%")

    print(f"\nOptimized Schedule ({len(optimizer.schedule)} vessels):")
    print(f"{'Vessel':<25} {'Type':<8} {'Berth':<10} {'Draft':>6} {'Depth':>6} {'Cranes':>7} {'Wait':>6}")
    print("-" * 80)
    for r in optimizer.schedule:
        print(
            f"{r['vessel']:<25} {r['vessel_type']:<8} {r['berth']:<10} "
            f"{r['draft_m']:>5.1f}m {r['water_depth_m']:>5.1f}m "
            f"{r['num_cranes']:>5} cr  {r['wait_hours']}h"
        )