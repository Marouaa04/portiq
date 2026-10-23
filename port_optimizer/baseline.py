import sqlite3
from datetime import datetime, timedelta


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
        FROM vessels ORDER BY eta ASC
    """)
    vessels = [Vessel(*row) for row in cursor.fetchall()]
    conn.close()
    return vessels, berths


def run_fcfs(vessels, berths):
    berth_free_at = {b.berth_id: datetime(2000, 1, 1) for b in berths}
    schedule = []

    for v in vessels:
        best_berth = None
        best_start = None

        for b in berths:
            if not b.can_accept(v):
                continue
            earliest_start = max(v.eta, berth_free_at[b.berth_id])
            if best_start is None or earliest_start < best_start:
                best_start = earliest_start
                best_berth = b

        if best_berth is None:
            print(f"WARNING: No valid berth for {v.name} (draft {v.draft_m}m)")
            continue

        service_h = best_berth.service_time_hours(v)
        end_time = best_start + timedelta(hours=service_h)
        berth_free_at[best_berth.berth_id] = end_time
        wait_h = (best_start - v.eta).total_seconds() / 3600

        schedule.append({
            "vessel": v.name,
            "shipping_line": v.shipping_line,
            "size_teu": v.size_teu,
            "priority": v.priority,
            "vessel_type": v.vessel_type,
            "draft_m": v.draft_m,
            "berth": best_berth.name,
            "terminal": best_berth.terminal,
            "water_depth_m": best_berth.water_depth_m,
            "num_cranes": best_berth.num_cranes,
            "eta": v.eta,
            "start": best_start,
            "end": end_time,
            "wait_hours": round(max(wait_h, 0), 1),
            "service_hours": round(service_h, 1),
        })

    return schedule


if __name__ == "__main__":
    vessels, berths = load_data("port_optimizer.db")
    print(f"Loaded {len(vessels)} vessels and {len(berths)} berths")

    schedule = run_fcfs(vessels, berths)

    total_wait = sum(r["wait_hours"] for r in schedule)
    avg_wait = total_wait / len(schedule) if schedule else 0
    pw = {1: 3, 2: 2, 3: 1}
    pw_wait = sum(r["wait_hours"] * pw[r["priority"]] for r in schedule)
    mothers = [r for r in schedule if r["vessel_type"] == "MOTHER"]
    feeders = [r for r in schedule if r["vessel_type"] == "FEEDER"]
    mother_avg = sum(r["wait_hours"] for r in mothers) / len(mothers) if mothers else 0
    feeder_avg = sum(r["wait_hours"] for r in feeders) / len(feeders) if feeders else 0

    print(f"Average wait time:              {avg_wait:.1f} hours")
    print(f"Total wait time:                {total_wait:.1f} hours")
    print(f"Priority-weighted wait:         {pw_wait:.1f}")
    print(f"MOTHER vessel avg wait:         {mother_avg:.1f} hours")
    print(f"FEEDER vessel avg wait:         {feeder_avg:.1f} hours")

    print(f"\nFCFS Schedule ({len(schedule)} vessels):")
    print(f"{'Vessel':<25} {'Type':<8} {'Berth':<10} {'Draft':>6} {'Depth':>6} {'Wait':>6}")
    print("-" * 70)
    for r in schedule:
        print(
            f"{r['vessel']:<25} {r['vessel_type']:<8} {r['berth']:<10} "
            f"{r['draft_m']:>5.1f}m {r['water_depth_m']:>5.1f}m "
            f"{r['wait_hours']}h"
        )