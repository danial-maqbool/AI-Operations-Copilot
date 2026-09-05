# Acme Industrial Supplies — Demo Dataset & Walkthrough Guide

OpsPilot includes a built-in enterprise demo scenario featuring **Acme Industrial Supplies**, a mid-sized B2B distributor of industrial safety equipment, tools, and warehouse machinery.

The demo environment seeds over **4,000+ realistic relational records** and **4 policy documents** with deliberately planted operational bottlenecks, overdue accounts, low stock emergencies, carrier delays, and SLA risks.

---

## 1. Demo Architecture & Tables

When seeded via the UI banner or the `POST /api/demo/seed` endpoint, OpsPilot loads 10 interconnected tables into `data/warehouse.db`:

```
                    ┌─────────────┐
                    │  CUSTOMERS  │
                    └──────┬──────┘
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
       ┌───────────┐ ┌───────────┐ ┌──────────────┐
       │  ORDERS   │ │ INVOICES  │ │SUPPORT_TICKET│
       └─────┬─────┘ └───────────┘ └──────────────┘
             │             ▲
             ▼             │
      ┌─────────────┐      │
      │ ORDER_ITEMS │──────┘
      └──────┬──────┘
             ▼
       ┌───────────┐       ┌───────────┐
       │ PRODUCTS  │◄──────┤ INVENTORY │
       └───────────┘       └───────────┘
             ▲
             │             ┌───────────┐
       ┌───────────┐       │ EMPLOYEES │
       │ SHIPMENTS │       └─────┬─────┘
       └───────────┘             ▼
                           ┌───────────┐
                           │   TASKS   │
                           └───────────┘
```

| Table | Records | Operational Purpose |
| :--- | :--- | :--- |
| `customers` | 250 | Enterprise accounts with credit limits, tiers, and assigned reps |
| `products` | 500 | SKUs across 8 categories with costs, prices, and safety thresholds |
| `inventory` | 1,200 | Stock levels across 4 distribution hubs (Chicago, Dallas, Reno, Atlanta) |
| `orders` | 1,200 | Customer orders with order dates, statuses, and delivery dates |
| `order_items` | 3,500 | Individual line items with unit quantities and discount rates |
| `invoices` | 1,100 | Accounts receivable ledger with payment terms, due dates, and paid flags |
| `shipments` | 950 | Carrier tracking records with transit times, carriers, and delivery status |
| `support_tickets`| 350 | Customer complaints and requests with priority, status, and SLA deadlines |
| `employees` | 45 | Operations, logistics, support, and finance team roster |
| `tasks` | 180 | Departmental action items, priority tags, and completion statuses |

---

## 2. Planted Operational Scenarios (Ground Truth)

The dataset contains deliberately planted operational issues designed to test and showcase OpsPilot's intelligence engines:

### 1. Carrier Bottleneck & Delayed Shipments
- **Problem:** Carrier **"Apex Freight"** has severe delays in the Midwest region.
- **Data Footprint:** 34 orders marked `in_transit` are delayed past their promised delivery dates by 4 to 11 days.
- **Copilot Query:** *"Which orders are delayed past their promised delivery date?"*

### 2. Overdue Receivables & Credit Hold Violations
- **Problem:** Multiple accounts exceed their credit limits and have invoices overdue by >45 days.
- **Data Footprint:** Acme has $48,650 in unpaid invoices past due date. Account `CUST-104` (Titan Manufacturing) has $18,400 overdue while continuing to place new orders.
- **Policy Link:** `docs/policies/credit_policy.md` §3.2 stipulates that accounts past 45 days overdue must be placed on immediate credit hold.
- **Copilot Query:** *"Which accounts violate our credit hold policy and have overdue invoices?"*

### 3. Inventory Stockouts & Reorder Violations
- **Problem:** Chicago Distribution Center is running out of high-velocity safety gear.
- **Data Footprint:** 12 SKUs have `quantity_on_hand < minimum_reorder_level` with pending orders waiting for fulfillment.
- **Copilot Query:** *"Which products are below minimum safety stock across our warehouses?"*

### 4. Support SLA Risk Breaches
- **Problem:** Critical customer tickets are nearing their SLA resolution cutoffs.
- **Data Footprint:** 8 High/Critical priority tickets are within 2 hours of SLA breach, and 3 tickets have already breached SLA.
- **Copilot Query:** *"Which support tickets are close to breaching SLA?"*

---

## 3. Knowledge Base Documents (RAG)

OpsPilot automatically embeds and indexes 4 standard operating procedure documents:

1. **Credit & Accounts Receivable Policy (`credit_policy.md`):** Net-30 payment terms, 1.5% monthly late fees, automated dunning schedule, and mandatory credit hold triggers (§3.2: >$10,000 or >45 days overdue).
2. **Customer Support Service Level Agreement (`sla_standards.md`):** Tier 1 (1 hour first response, 4 hours resolution), Tier 2 (2 hours first response, 8 hours resolution), and Tier 3 resolution commitments.
3. **Logistics & Carrier Partner SOP (`logistics_sop.md`):** Carrier on-time performance target (98%), packaging specifications, delayed shipment escalation protocol, and $50/day late delivery penalty clauses (§7.4).
4. **Inventory Management & Procurement Guidelines (`procurement_manual.md`):** Economic Order Quantity (EOQ) formula, safety stock buffer formulas, weekly cycle count policies, and emergency expedited freight protocols.

---

## 4. Guided Walkthrough Tour

Follow these 5 steps to experience the complete OpsPilot workflow:

### Step 1: Trigger the Morning Operations Review
1. Launch OpsPilot via `python run.py`.
2. Open `http://localhost:8000` in your browser.
3. Click the **"Morning Operations Review"** button in the header bar.
4. Review the automated synthesis of overnight anomalies, urgent SLA breaches, and high-priority recommendations.

### Step 2: Inquire with the Operations Copilot
1. Navigate to the **Copilot** tab in the sidebar.
2. Ask: *"What is our total overdue accounts receivable, and which customers violate our credit policy?"*
3. Observe:
   - The Copilot generates and runs a safe SQL query against `invoices` and `customers`.
   - The Copilot queries the RAG vector store for `credit_policy.md` and cites Section 3.2.
   - The Copilot synthesizes the grounded answer, displays the SQL evidence table, and suggests creating dunning actions.

### Step 3: Inspect Exceptions & Rules
1. Navigate to the **Exceptions** tab.
2. Filter by **Severity: High** to inspect the planted overdue invoices and delayed carrier shipments.
3. View the calculated Priority Score and the root cause breakdown.

### Step 4: Approve Actions in the Action Center
1. Navigate to the **Action Center**.
2. Locate the proposed action: *"Send Dunning Notice & Apply Credit Hold to Titan Manufacturing"*.
3. Click **"Verify Payload / Dry Run"** to inspect the parameters.
4. Click **"Approve"** to authorize execution.
5. Watch the state transition to `SUCCEEDED` and observe the live log entry.

### Step 5: Export Executive Operations Report
1. Navigate to the **Reports** tab.
2. Select **"Generate Comprehensive Executive Report"** (OpenPyXL multi-tab Excel).
3. Download the generated `.xlsx` workbook and inspect the formatted KPI summary, exceptions list, inventory health, and audit trail tabs.
