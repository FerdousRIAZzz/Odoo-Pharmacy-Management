# Odoo Pharmacy Management System

A custom **Odoo 19** ERP module built from scratch to run the core operations of a retail pharmacy — patient records, medicine catalog, batch/expiry tracking, and a full prescription workflow from creation to dispensing.

> Built as a learning + portfolio project to demonstrate practical Odoo ERP module development: custom models, inherited models, business workflows, security, automation, and reporting.

---

## ✨ Features

- **Patient Management** — extends Odoo's built-in Contacts (`res.partner`) instead of duplicating it, adding medical fields (blood group, allergies, DOB, emergency contact).
- **Medicine Catalog** — categorized medicines with reorder levels, dosage form, prescription-required flag.
- **Batch & Expiry Tracking** — every medicine can have multiple batches, each with its own expiry date and quantity. List views highlight expired (red) and near-expiry (orange) batches automatically.
- **Prescription Workflow** — `Draft → Verified → Dispensed` (or `Cancelled`), enforced in the backend, not just the UI.
- **FEFO Stock Deduction** — when a prescription is dispensed, stock is automatically deducted from the batch with the **soonest expiry date first**, exactly how a real pharmacy should manage inventory.
- **Automated Alerts** — two scheduled jobs (cron) run daily: one flags low-stock medicines, one flags batches expiring within 30 days.
- **Role-Based Security** — three access levels (Pharmacy Technician, Pharmacist, Pharmacy Manager) with a proper access-rights matrix, not "everyone sees everything."
- **PDF Report** — a printable prescription/dispensing document generated with QWeb.
- **Full audit trail** — prescriptions use Odoo's chatter (`mail.thread`) so every state change and note is logged automatically.

---

## 🧱 Tech Stack

| Layer          | Technology                       |
|----------------|-----------------------------------|
| ERP Framework  | Odoo 19 (Community)               |
| Backend        | Python 3, Odoo ORM                |
| Frontend/Views | Odoo XML views (form/list/kanban/search) |
| Database       | PostgreSQL                        |
| Reporting      | QWeb → PDF                        |

---

## 📂 Module Structure

```
pharmacy_management/
├── __init__.py
├── __manifest__.py                 # module metadata & load order
├── models/
│   ├── pharmacy_medicine_category.py
│   ├── pharmacy_medicine.py        # medicine + low-stock computation + cron methods
│   ├── pharmacy_medicine_batch.py  # batch/lot + expiry validation
│   ├── res_partner.py              # extends Contacts into Patients
│   ├── pharmacy_prescription.py    # workflow state machine
│   └── pharmacy_prescription_line.py  # FEFO stock deduction logic
├── views/                          # form/list/kanban/search views + menus
├── security/                       # groups + access rights (ir.model.access.csv)
├── data/                           # sequence + cron job definitions
└── report/                         # QWeb PDF report
```

---

## 🚀 Installation (local development)

1. **Prerequisites**: Odoo 19 running locally (or Odoo 18 — this module uses no 19-only APIs), PostgreSQL, Python 3.10+.

2. Clone this repo into your Odoo `addons` path:
   ```bash
   git clone https://github.com/your-username/odoo-pharmacy-management.git
   cp -r odoo-pharmacy-management/pharmacy_management /path/to/odoo/custom-addons/
   ```

3. Add that `custom-addons` folder to your Odoo config (`odoo.conf`):
   ```ini
   addons_path = /path/to/odoo/addons,/path/to/odoo/custom-addons
   ```

4. Restart the Odoo server, then in the UI:
   - Go to **Apps**
   - Click **Update Apps List**
   - Search for **"Pharmacy Management"** and click **Install**

5. Assign yourself a role: **Settings → Users → your user → set a Pharmacy group** (Technician / Pharmacist / Manager).

6. Open the new **Pharmacy** app from the main menu and start adding categories → medicines → batches → patients → prescriptions.

---

## 🖼️ Screenshots

_Add screenshots here after running the module locally — recruiters and interviewers respond well to visuals._

```
screenshots/
├── 01-medicine-list.png
├── 02-medicine-form.png
├── 03-prescription-workflow.png
├── 04-low-stock-alert.png
└── 05-prescription-report.png
```

---

## 🗣️ Talking Points for Interviews

This project was deliberately built to touch the Odoo concepts that come up most in real ERP work:

- **Model creation** (`pharmacy.medicine`, `pharmacy.prescription`, etc.) vs **model inheritance** (`_inherit` on `res.partner` to add Patient fields without duplicating Contacts).
- **Field types in practice**: `Many2one`, `One2many`, `Selection`, `related` fields, and `compute` + `store=True` fields that are reactive via `@api.depends`.
- **Business logic enforcement**: `@api.constrains` for data integrity (e.g. no negative batch quantities), custom methods for workflow transitions (`action_verify`, `action_dispense`), and `UserError` for user-facing validation.
- **A real inventory algorithm**: FEFO (First-Expiry-First-Out) stock deduction, not just a quantity counter.
- **Security model**: three-tier groups with `implied_ids` inheritance and a full `ir.model.access.csv` matrix.
- **Automation**: `ir.cron` scheduled jobs calling model methods with no user interaction.
- **Reporting**: QWeb templates rendered to PDF, wired up via `ir.actions.report`.
- **UI/UX details**: smart buttons, status bar workflow, kanban view, list decorations, search filters/group-bys, a ribbon widget for low stock.

---

## 🔮 Possible Extensions

- Integrate with Odoo's `Sales` / `Point of Sale` apps to actually invoice dispensed prescriptions.
- Integrate with the `Inventory` app (`stock.lot`) instead of the custom batch model, for multi-warehouse pharmacies.
- Barcode scanning for batch check-in.
- Multi-company support with record rules.
- A patient portal (via Odoo's `portal` module) so patients can view their prescription history online.

---

## License

LGPL-3 (same license as Odoo Community itself).
