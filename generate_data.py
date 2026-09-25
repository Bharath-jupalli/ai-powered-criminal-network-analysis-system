import csv
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# -----------------------------
# PEOPLE
# -----------------------------

people = []

names = [
    "Person A", "Person B", "Person C", "Person D", "Person E",
    "Person F", "Person G", "Person H", "Person I", "Person J",
    "Person K", "Person L", "Person M", "Person N", "Person O",
    "Person P", "Person Q", "Person R", "Person S", "Person T",
    "Person U", "Person V", "Person W", "Person X", "Person Y",
    "Person Z"
]

cities = [
    "Hyderabad",
    "Vijayawada",
    "Guntur",
    "Eluru",
    "Visakhapatnam"
]

for i, name in enumerate(names, start=1):
    people.append({
        "person_id": f"P{i:03}",
        "name": name,
        "city": random.choice(cities),
        "age": random.randint(21, 55)
    })

with open(DATA_DIR / "people.csv", "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["person_id", "name", "city", "age"]
    )
    writer.writeheader()
    writer.writerows(people)


# -----------------------------
# CALL RECORDS
# -----------------------------

calls = []

start_date = datetime(2026, 1, 1)

# Normal/random calls
for _ in range(180):
    caller = random.choice(people)["person_id"]
    receiver = random.choice(people)["person_id"]

    if caller == receiver:
        continue

    date = start_date + timedelta(
        days=random.randint(0, 90)
    )

    calls.append({
        "caller": caller,
        "receiver": receiver,
        "date": date.strftime("%Y-%m-%d"),
        "duration": random.randint(30, 900)
    })


# Strong hidden network
network_edges = [
    ("P001", "P002"),
    ("P001", "P003"),
    ("P001", "P004"),
    ("P002", "P005"),
    ("P003", "P006"),
    ("P004", "P007"),
    ("P005", "P008"),
    ("P006", "P009"),
    ("P007", "P010"),
    ("P008", "P011"),
    ("P009", "P012"),
    ("P010", "P013"),
    ("P003", "P014"),
    ("P004", "P015"),
    ("P001", "P016"),
    ("P016", "P017"),
    ("P017", "P018"),
]

for caller, receiver in network_edges:
    for _ in range(random.randint(2, 5)):
        date = start_date + timedelta(
            days=random.randint(0, 90)
        )

        calls.append({
            "caller": caller,
            "receiver": receiver,
            "date": date.strftime("%Y-%m-%d"),
            "duration": random.randint(60, 1200)
        })


with open(DATA_DIR / "calls.csv", "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "caller",
            "receiver",
            "date",
            "duration"
        ]
    )
    writer.writeheader()
    writer.writerows(calls)


# -----------------------------
# TRANSACTIONS
# -----------------------------

transactions = []

for _ in range(150):
    sender = random.choice(people)["person_id"]
    receiver = random.choice(people)["person_id"]

    if sender == receiver:
        continue

    date = start_date + timedelta(
        days=random.randint(0, 90)
    )

    transactions.append({
        "sender": sender,
        "receiver": receiver,
        "amount": random.randint(500, 20000),
        "date": date.strftime("%Y-%m-%d")
    })


# Deliberate transaction pattern
for receiver in ["P002", "P003", "P004", "P005"]:
    transactions.append({
        "sender": "P001",
        "receiver": receiver,
        "amount": 5000,
        "date": "2026-03-15"
    })


with open(DATA_DIR / "transactions.csv", "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "sender",
            "receiver",
            "amount",
            "date"
        ]
    )
    writer.writeheader()
    writer.writerows(transactions)


# -----------------------------
# VEHICLES
# -----------------------------

vehicles = []

for i in range(1, 16):
    vehicles.append({
        "vehicle_id": f"V{i:03}",
        "registration": f"AP-{i:02}-XX-{1000+i}",
        "owner": random.choice(people)["person_id"]
    })

# Shared vehicle pattern
vehicles.append({
    "vehicle_id": "V016",
    "registration": "AP-09-XX-9999",
    "owner": "P001"
})

with open(DATA_DIR / "vehicles.csv", "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "vehicle_id",
            "registration",
            "owner"
        ]
    )
    writer.writeheader()
    writer.writerows(vehicles)


# -----------------------------
# LOCATIONS
# -----------------------------

locations = [
    {
        "location_id": "L001",
        "name": "Central Railway Station",
        "city": "Vijayawada"
    },
    {
        "location_id": "L002",
        "name": "Market Area",
        "city": "Guntur"
    },
    {
        "location_id": "L003",
        "name": "Industrial Zone",
        "city": "Hyderabad"
    },
    {
        "location_id": "L004",
        "name": "Bus Terminal",
        "city": "Eluru"
    },
    {
        "location_id": "L005",
        "name": "Harbor Area",
        "city": "Visakhapatnam"
    }
]

with open(DATA_DIR / "locations.csv", "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "location_id",
            "name",
            "city"
        ]
    )
    writer.writeheader()
    writer.writerows(locations)


# -----------------------------
# CASES
# -----------------------------

cases = []

for i in range(1, 21):
    cases.append({
        "case_id": f"CASE-{i:03}",
        "title": f"Investigation Case {i:03}",
        "location": random.choice(locations)["location_id"],
        "lead_person": random.choice(people)["person_id"],
        "date": (
            start_date +
            timedelta(days=random.randint(0, 90))
        ).strftime("%Y-%m-%d")
    })

with open(DATA_DIR / "cases.csv", "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "case_id",
            "title",
            "location",
            "lead_person",
            "date"
        ]
    )
    writer.writeheader()
    writer.writerows(cases)


print()
print("======================================")
print(" SYNTHETIC INVESTIGATION DATA CREATED")
print("======================================")
print()
print("Files created:")
print("  people.csv")
print("  calls.csv")
print("  transactions.csv")
print("  vehicles.csv")
print("  locations.csv")
print("  cases.csv")
print()