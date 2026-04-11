"""
Seed script — inserts sample data into all four BU services via their REST APIs.

Usage:
    uv run python seed_data.py

All four BU services must be running before executing:
    docker compose up -d
        or
    uv run uvicorn api.main:app --port 8001  (in each BU service directory)
"""

import asyncio
import httpx

BU1 = "http://localhost:8001"
BU2 = "http://localhost:8002"
BU3 = "http://localhost:8003"
BU4 = "http://localhost:8004"


# ── Helpers ───────────────────────────────────────────────────────────────────

def print_section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def print_ok(label: str, record_id: str) -> None:
    print(f"  ✓  {label:<45} id={record_id}")


def print_err(label: str, status: int, body: str) -> None:
    print(f"  ✗  {label:<45} [{status}] {body}")


async def post(client: httpx.AsyncClient, url: str, payload: dict, label: str) -> dict | None:
    try:
        r = await client.post(url, json=payload, timeout=10.0)
        data = r.json()
        if r.status_code in (200, 201):
            print_ok(label, data.get("id", "—"))
            return data
        else:
            print_err(label, r.status_code, str(data))
            return None
    except Exception as e:
        print_err(label, 0, str(e))
        return None


# ── Health check ──────────────────────────────────────────────────────────────

async def check_services(client: httpx.AsyncClient) -> bool:
    print_section("Health Check")
    services = [
        ("BU1 — Onboarding",      f"{BU1}/health"),
        ("BU2 — Sales",           f"{BU2}/health"),
        ("BU3 — Billing",         f"{BU3}/health"),
        ("BU4 — Support",         f"{BU4}/health"),
    ]
    all_up = True
    for name, url in services:
        try:
            r = await client.get(url, timeout=3.0)
            up = r.status_code == 200
        except Exception:
            up = False
        icon = "✓" if up else "✗"
        print(f"  {icon}  {name}")
        if not up:
            all_up = False
    return all_up


# ── BU1 — Customer Onboarding ─────────────────────────────────────────────────

async def seed_bu1(client: httpx.AsyncClient) -> dict[str, str]:
    """
    Creates three customers. Returns a name → id mapping used by other BUs.
    BU1 CustomerCreateRequest fields: name, email, phone, address
    """
    print_section("BU1 — Customers")

    customers = [
        {
            "name": "Alice Johnson",
            "email": "alice.johnson@example.com",
            "phone": "555-0101",
            "address": "12 Oak Street, Springfield",
        },
        {
            "name": "Bob Martinez",
            "email": "bob.martinez@example.com",
            "phone": "555-0102",
            "address": "45 Pine Avenue, Shelbyville",
        },
        {
            "name": "Carol White",
            "email": "carol.white@example.com",
            "phone": "555-0103",
            "address": "78 Elm Road, Capital City",
        },
    ]

    ids: dict[str, str] = {}
    for c in customers:
        data = await post(client, f"{BU1}/customers", c, f"Customer: {c['name']}")
        if data and data.get("id"):
            ids[c["name"]] = data["id"]

    return ids


async def seed_bu1_kyc(client: httpx.AsyncClient, customer_ids: dict[str, str]) -> None:
    """
    Updates KYC status for Alice to VERIFIED so she has a complete profile.
    KYCUpdateRequest fields: kyc_status, kyc_notes
    """
    print_section("BU1 — KYC Updates")

    alice_id = customer_ids.get("Alice Johnson")
    if alice_id:
        r = await client.patch(
            f"{BU1}/customers/{alice_id}/kyc",
            json={"kyc_status": "verified", "kyc_notes": "All documents verified by agent-001"},
            timeout=10.0,
        )
        if r.status_code == 200:
            print_ok("KYC verified: Alice Johnson", alice_id)
        else:
            print_err("KYC update: Alice Johnson", r.status_code, r.text)


# ── BU2 — Sales & Maintenance ─────────────────────────────────────────────────

async def seed_bu2(client: httpx.AsyncClient, customer_ids: dict[str, str]) -> dict[str, str]:
    """
    Creates contracts and field visits linked to BU1 customers.
    ContractCreateRequest fields: customer_id, contract_type, start_date, end_date, value, description
    VisitCreateRequest fields: customer_id, contract_id, scheduled_at, assigned_to, notes
    contract_type values: service | maintenance | warranty
    """
    print_section("BU2 — Contracts")

    alice_id = customer_ids.get("Alice Johnson")
    bob_id = customer_ids.get("Bob Martinez")
    carol_id = customer_ids.get("Carol White")

    contracts_payload = [
        {
            "customer_id": alice_id,
            "contract_type": "maintenance",
            "start_date": "2025-01-01T00:00:00Z",
            "end_date": "2026-01-01T00:00:00Z",
            "value": 1200.00,
            "description": "Annual maintenance contract for X200 pump unit",
        },
        {
            "customer_id": bob_id,
            "contract_type": "service",
            "start_date": "2025-03-01T00:00:00Z",
            "end_date": "2026-03-01T00:00:00Z",
            "value": 800.00,
            "description": "Quarterly service contract for HVAC system",
        },
        {
            "customer_id": carol_id,
            "contract_type": "warranty",
            "start_date": "2025-02-01T00:00:00Z",
            "end_date": "2027-02-01T00:00:00Z",
            "value": 500.00,
            "description": "Two-year warranty contract for industrial compressor",
        },
    ]

    contract_ids: dict[str, str] = {}
    for c in contracts_payload:
        data = await post(client, f"{BU2}/contracts", c, f"Contract ({c['contract_type']}) → {c['customer_id'][:8]}...")
        if data and data.get("id"):
            contract_ids[c["customer_id"]] = data["id"]

    print_section("BU2 — Visits")

    visits_payload = [
        {
            "customer_id": alice_id,
            "contract_id": contract_ids.get(alice_id),
            "scheduled_at": "2025-06-15T09:00:00Z",
            "assigned_to": "engineer-001",
            "notes": "Routine inspection of X200 pump — check pressure valve and seals",
        },
        {
            "customer_id": alice_id,
            "contract_id": contract_ids.get(alice_id),
            "scheduled_at": "2025-09-10T10:00:00Z",
            "assigned_to": "engineer-001",
            "notes": "Follow-up visit after pressure fault report — replace worn seal on X200",
        },
        {
            "customer_id": bob_id,
            "contract_id": contract_ids.get(bob_id),
            "scheduled_at": "2025-07-20T10:00:00Z",
            "assigned_to": "engineer-002",
            "notes": "Quarterly HVAC service visit — lubricate fan bearings and check filters",
        },
        {
            "customer_id": carol_id,
            "contract_id": contract_ids.get(carol_id),
            "scheduled_at": "2025-08-05T14:00:00Z",
            "assigned_to": "engineer-003",
            "notes": "Annual compressor inspection under warranty",
        },
    ]

    for v in visits_payload:
        await post(client, f"{BU2}/visits", v, f"Visit → {v['customer_id'][:8]}... on {v['scheduled_at'][:10]}")

    return contract_ids


# ── BU3 — Billing & Subscription ─────────────────────────────────────────────

async def seed_bu3(client: httpx.AsyncClient, customer_ids: dict[str, str]) -> list[str]:
    """
    Creates subscriptions and invoices for all three customers.
    SubscriptionCreateRequest fields: customer_id, plan, start_date, renewal_date, monthly_fee
    InvoiceCreateRequest fields: customer_id, amount, due_date, description
    plan values: basic | standard | premium
    """
    print_section("BU3 — Subscriptions")

    alice_id = customer_ids.get("Alice Johnson")
    bob_id = customer_ids.get("Bob Martinez")
    carol_id = customer_ids.get("Carol White")

    subscriptions = [
        {
            "customer_id": alice_id,
            "plan": "premium",
            "start_date": "2025-01-01T00:00:00Z",
            "renewal_date": "2026-01-01T00:00:00Z",
            "monthly_fee": 99.99,
        },
        {
            "customer_id": bob_id,
            "plan": "basic",
            "start_date": "2025-03-01T00:00:00Z",
            "renewal_date": "2026-03-01T00:00:00Z",
            "monthly_fee": 49.99,
        },
        {
            "customer_id": carol_id,
            "plan": "standard",
            "start_date": "2025-02-01T00:00:00Z",
            "renewal_date": "2026-02-01T00:00:00Z",
            "monthly_fee": 69.99,
        },
    ]

    for s in subscriptions:
        await post(client, f"{BU3}/subscriptions", s, f"Subscription ({s['plan']}) → {s['customer_id'][:8]}...")

    print_section("BU3 — Invoices")

    invoices = [
        {
            "customer_id": alice_id,
            "amount": 99.99,
            "due_date": "2025-02-01T00:00:00Z",
            "description": "Monthly premium plan — January 2025",
        },
        {
            "customer_id": alice_id,
            "amount": 99.99,
            "due_date": "2025-03-01T00:00:00Z",
            "description": "Monthly premium plan — February 2025",
        },
        {
            "customer_id": alice_id,
            "amount": 99.99,
            "due_date": "2025-04-01T00:00:00Z",
            "description": "Monthly premium plan — March 2025",
        },
        {
            "customer_id": bob_id,
            "amount": 49.99,
            "due_date": "2025-04-01T00:00:00Z",
            "description": "Monthly basic plan — March 2025",
        },
        {
            "customer_id": carol_id,
            "amount": 69.99,
            "due_date": "2025-03-01T00:00:00Z",
            "description": "Monthly standard plan — February 2025",
        },
    ]

    invoice_ids = []
    for inv in invoices:
        data = await post(client, f"{BU3}/invoices", inv, f"Invoice ({inv['description'][:35]}...)")
        if data and data.get("id"):
            invoice_ids.append(data["id"])

    return invoice_ids


# ── BU4 — Support & Fulfillment ───────────────────────────────────────────────

async def seed_bu4(client: httpx.AsyncClient, customer_ids: dict[str, str]) -> None:
    """
    Creates support tickets for all three customers.
    TicketCreateRequest fields: customer_id, category, priority, subject, description, assigned_to
    category values: technical | billing | onboarding | maintenance | other
    priority values: low | medium | high | critical
    """
    print_section("BU4 — Support Tickets")

    alice_id = customer_ids.get("Alice Johnson")
    bob_id = customer_ids.get("Bob Martinez")
    carol_id = customer_ids.get("Carol White")

    tickets = [
        {
            "customer_id": alice_id,
            "category": "technical",
            "priority": "high",
            "subject": "Pressure fault on X200 pump unit",
            "description": (
                "Customer reports intermittent pressure fault alarm on X200 pump. "
                "Fault code PF-042. Unit shuts down after 10 minutes of operation. "
                "Issue started after last maintenance visit."
            ),
            "assigned_to": "engineer-001",
        },
        {
            "customer_id": alice_id,
            "category": "billing",
            "priority": "low",
            "subject": "Query on February invoice amount",
            "description": (
                "Customer says the February invoice of $99.99 does not match "
                "the agreed plan rate discussed during onboarding. Requesting clarification."
            ),
            "assigned_to": "agent-001",
        },
        {
            "customer_id": bob_id,
            "category": "maintenance",
            "priority": "medium",
            "subject": "HVAC unit making unusual noise after last service",
            "description": (
                "Rattling noise from HVAC unit started after the last quarterly service visit. "
                "Noise gets louder at high fan speed. Customer suspects loose component."
            ),
            "assigned_to": "engineer-002",
        },
        {
            "customer_id": bob_id,
            "category": "technical",
            "priority": "critical",
            "subject": "HVAC complete failure — no cooling",
            "description": (
                "HVAC unit stopped working entirely. No cooling output. "
                "Error code E-501 on display panel. Customer site is a server room — urgent."
            ),
            "assigned_to": "engineer-002",
        },
        {
            "customer_id": carol_id,
            "category": "other",
            "priority": "low",
            "subject": "Request for X200 pump service manual PDF",
            "description": (
                "Customer requesting a PDF copy of the X200 pump service manual "
                "for their internal maintenance team reference."
            ),
            "assigned_to": "agent-002",
        },
        {
            "customer_id": carol_id,
            "category": "onboarding",
            "priority": "medium",
            "subject": "KYC documents not received confirmation",
            "description": (
                "Customer submitted KYC documents 5 days ago but has not received "
                "a confirmation email. Requesting status update."
            ),
            "assigned_to": "agent-001",
        },
    ]

    for t in tickets:
        await post(client, f"{BU4}/tickets", t, f"Ticket ({t['priority']}/{t['category']}): {t['subject'][:35]}...")


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    print("\n" + "═" * 50)
    print("  RiteCare — Database Seed Script")
    print("═" * 50)

    async with httpx.AsyncClient() as client:

        # 1. Verify all services are up
        all_up = await check_services(client)
        if not all_up:
            print("\n  ✗ One or more services are down.")
            print("  Start services first:\n")
            print("    docker compose up -d")
            print("      or")
            print("    uv run uvicorn api.main:app --port 800X\n")
            return

        # 2. BU1 — create customers first (other BUs need the IDs)
        customer_ids = await seed_bu1(client)

        if not customer_ids:
            print("\n  ✗ No customers created. Aborting.")
            return

        await seed_bu1_kyc(client, customer_ids)

        # 3. BU2 — contracts and visits
        await seed_bu2(client, customer_ids)

        # 4. BU3 — subscriptions and invoices
        await seed_bu3(client, customer_ids)

        # 5. BU4 — support tickets
        await seed_bu4(client, customer_ids)

    print("\n" + "═" * 50)
    print("  Seed complete.")
    print("═" * 50)
    print("\n  Customer IDs created:")
    for name, cid in customer_ids.items():
        print(f"    {name:<20} {cid}")
    print("\n  Use these IDs in test queries.\n")


if __name__ == "__main__":
    asyncio.run(main())
