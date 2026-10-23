import sqlite3
import random
from datetime import datetime, timedelta

def create_database():
    conn = sqlite3.connect("port_optimizer.db")
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS vessels")
    cursor.execute("DROP TABLE IF EXISTS berths")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS berths (
            berth_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            terminal TEXT NOT NULL,
            max_capacity_teu INTEGER NOT NULL,
            handling_rate_teu_per_hour INTEGER NOT NULL,
            water_depth_m REAL NOT NULL,
            num_cranes INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vessels (
            vessel_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            shipping_line TEXT NOT NULL,
            size_teu INTEGER NOT NULL,
            eta TEXT NOT NULL,
            priority INTEGER NOT NULL,
            origin_port TEXT NOT NULL,
            origin_country TEXT NOT NULL,
            route TEXT NOT NULL,
            draft_m REAL NOT NULL,
            vessel_type TEXT NOT NULL
        )
    """)

    berths_data = [
        (1, "Berth A1", "TC1", 18000, 120, 16.0, 4),
        (2, "Berth A2", "TC1", 16000, 110, 15.5, 3),
        (3, "Berth B1", "TC2", 20000, 130, 17.0, 5),
        (4, "Berth B2", "TC2", 14000,  95, 16.0, 3),
        (5, "Berth C1", "TC3", 12000,  90, 14.0, 3),
        (6, "Berth C2", "TC3",  9000,  75, 13.5, 2),
        (7, "Berth D1", "TC4", 10000,  80, 13.0, 2),
        (8, "Berth D2", "TC4",  8000,  70, 12.5, 2),
    ]

    cursor.executemany(
        "INSERT INTO berths VALUES (?, ?, ?, ?, ?, ?, ?)",
        berths_data
    )

    DRAFT_BY_SIZE = {
        14000: (15.0, "MOTHER"),
        12000: (14.5, "MOTHER"),
        10000: (14.0, "MOTHER"),
         8000: (13.5, "FEEDER"),
         6000: (12.5, "FEEDER"),
         4000: (11.5, "FEEDER"),
    }

    vessels_info = [
        ("Atlas",               "Shanghai",    "China",       "Asia-Suez"),
        ("Tanger Express",      "Rotterdam",   "Netherlands", "Europe-Gibraltar"),
        ("Casablanca Star",     "Singapore",   "Singapore",   "Asia-Suez"),
        ("Sahara Wind",         "Antwerp",     "Belgium",     "Europe-Gibraltar"),
        ("Mediterranean Pearl", "Busan",       "South Korea", "Asia-Suez"),
        ("Strait Voyager",      "Valencia",    "Spain",       "Europe-Gibraltar"),
        ("Phoenix",             "Ningbo",      "China",       "Asia-Suez"),
        ("Horizon",             "Hamburg",     "Germany",     "Europe-Gibraltar"),
        ("Maghreb Trader",      "Port Said",   "Egypt",       "Med-Direct"),
        ("Atlantic Bridge",     "New York",    "USA",         "Atlantic"),
        ("Gibraltar Pass",      "Algeciras",   "Spain",       "Europe-Gibraltar"),
        ("Rabat Glory",         "Guangzhou",   "China",       "Asia-Suez"),
        ("Fes Pioneer",         "Felixstowe",  "UK",          "Europe-Gibraltar"),
        ("Agadir Spirit",       "Tokyo",       "Japan",       "Asia-Suez"),
        ("Oujda Light",         "Le Havre",    "France",      "Europe-Gibraltar"),
        ("Tetouan Star",        "Tianjin",     "China",       "Asia-Suez"),
        ("Nador Wave",          "Marseille",   "France",      "Med-Direct"),
        ("Dakhla Sun",          "Hong Kong",   "China",       "Asia-Suez"),
        ("Laayoune Trail",      "Santos",      "Brazil",      "Atlantic"),
        ("Kenitra Hope",        "Shenzhen",    "China",       "Asia-Suez"),
        ("Meknes Quest",        "Barcelona",   "Spain",       "Europe-Gibraltar"),
        ("Safi Current",        "Colombo",     "Sri Lanka",   "Asia-Suez"),
        ("Essaouira Breeze",    "Genoa",       "Italy",       "Med-Direct"),
        ("Marrakech",           "Qingdao",     "China",       "Asia-Suez"),
        ("Tarfaya Wind",        "Houston",     "USA",         "Atlantic"),
    ]

    shipping_lines = [
        "Maersk", "MSC", "CMA CGM",
        "COSCO", "Hapag-Lloyd", "Evergreen"
    ]

    # Fixed vessel sizes to guarantee good mix of MOTHER and FEEDER
    fixed_sizes = [
        14000, 8000, 6000, 6000, 4000, 4000,
        12000, 8000, 12000, 6000, 6000, 10000,
        4000, 6000, 8000, 8000, 8000, 6000,
        10000, 10000, 8000, 6000, 8000, 8000, 8000
    ]

    random.seed(42)
    base_date = datetime(2026, 6, 22, 6, 0)
    vessels_data = []

    for i, (name, origin_port, origin_country, route) in enumerate(vessels_info):
        vessel_id = i + 1
        line = random.choice(shipping_lines)
        size = fixed_sizes[i]
        eta_offset = random.randint(0, 48)
        eta = (base_date + timedelta(hours=eta_offset)).strftime("%Y-%m-%d %H:%M")
        draft_m, vessel_type = DRAFT_BY_SIZE[size]
        if vessel_type == "MOTHER":
            priority = 1
        else:
            priority = random.choice([2, 2, 3])

        vessels_data.append((
            vessel_id, name, line, size, eta, priority,
            origin_port, origin_country, route,
            draft_m, vessel_type
        ))

    cursor.executemany(
        "INSERT INTO vessels VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        vessels_data
    )

    conn.commit()
    conn.close()

    print("Database created successfully!")
    print(f"  {len(berths_data)} berths inserted")
    print(f"  {len(vessels_data)} vessels inserted")
    print("")
    print(f"  {'Name':<12} {'Terminal':<6} {'Depth':>8} {'Cranes':>8} {'Max TEU':>10}")
    print("  " + "-"*50)
    for b in berths_data:
        print(f"  {b[1]:<12} {b[2]:<6} {b[5]:>7.1f}m {b[6]:>7} cranes {b[3]:>8,} TEU")
    print("")
    print(f"  {'Name':<25} {'Type':<8} {'Size':>8} {'Draft':>8} {'Priority':>10}")
    print("  " + "-"*65)
    for v in vessels_data:
        print(f"  {v[1]:<25} {v[10]:<8} {v[3]:>6,} TEU {v[9]:>6.1f}m  Priority {v[5]}")

create_database()