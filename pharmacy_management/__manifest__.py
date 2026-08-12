# __manifest__.py
#
# Every Odoo module needs a manifest file. It's a plain Python dictionary
# that tells Odoo: what this module is called, what it depends on,
# which files to load (and in what order), and how it should appear
# in the Apps list.
{
    'name': 'Pharmacy Management',
    'version': '19.0.1.0.0',
    # Version format explained (Odoo convention):
    # 19.0        -> target Odoo version
    # 1.0.0       -> our own module version (major.minor.patch)
    'category': 'Industries/Healthcare',
    'summary': 'Manage patients, medicines, batches, expiry dates and prescriptions',
    'description': """
Pharmacy Management System
===========================
A custom Odoo ERP module built to run the core day-to-day operations
of a retail pharmacy:

* Patient records (built on top of Odoo's existing Contacts model)
* Medicine catalog with categories and reorder levels
* Batch / Lot tracking with expiry dates (FEFO dispensing logic)
* Prescriptions with a draft -> verified -> dispensed workflow
* Automatic stock deduction on dispensing (oldest-expiry-first)
* Scheduled jobs (cron) for low-stock and near-expiry alerts
* Role-based access: Pharmacy Technician, Pharmacist, Pharmacy Manager
* Printable prescription / dispensing report (PDF via QWeb)
""",
    'author': 'Your Name',
    'website': 'https://github.com/your-username/odoo-pharmacy-management',
    'license': 'LGPL-3',

    # 'depends' lists other Odoo modules that must be installed BEFORE
    # this one. We keep this list minimal on purpose so the module
    # installs cleanly on a fresh Odoo database:
    #   base -> core framework (res.partner, users, etc.)
    #   mail -> gives our models the chatter / activity / log-note features
    'depends': ['base', 'mail'],

    # 'data' lists every XML/CSV file that should be loaded when the
    # module is installed. ORDER MATTERS: security rules and sequences
    # must load before the views that use them.
    'data': [
        # Security first: access rights and groups must exist before
        # views try to reference them.
        'security/pharmacy_security.xml',
        'security/ir.model.access.csv',

        # Data: sequences and scheduled actions (cron jobs)
        'data/pharmacy_sequence.xml',
        'data/pharmacy_cron.xml',

        # Views: forms, lists, kanban, search, menus
        'views/pharmacy_medicine_category_views.xml',
        'views/pharmacy_medicine_views.xml',
        'views/pharmacy_medicine_batch_views.xml',
        'views/res_partner_views.xml',
        'views/pharmacy_prescription_views.xml',
        'views/pharmacy_menus.xml',

        # Reports last (they reference views/records above)
        'report/pharmacy_prescription_report.xml',
        'report/pharmacy_prescription_templates.xml',
    ],

    'installable': True,
    'application': True,   # Shows up as its own "App" tile, not just a technical module
    'auto_install': False,
}
