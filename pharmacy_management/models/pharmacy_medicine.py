# models/pharmacy_medicine.py
#
# This model represents a MEDICINE in the catalog (e.g. "Paracetamol 500mg").
# It does NOT track actual stock quantity itself — that job belongs to
# pharmacy.medicine.batch, because in a real pharmacy the same medicine
# can exist in several batches with different expiry dates. This model
# just aggregates that batch information.

from odoo import models, fields, api


class PharmacyMedicine(models.Model):
    _name = 'pharmacy.medicine'
    _description = 'Medicine'
    _order = 'name'

    # mail.thread gives every medicine record a "chatter" (message log)
    # for free. We use it here so the scheduled cron jobs below have
    # somewhere to post low-stock / near-expiry alerts that pharmacists
    # can see directly on the record.
    _inherit = ['mail.thread']

    name = fields.Char(string='Medicine Name', required=True)
    generic_name = fields.Char(string='Generic Name')
    manufacturer = fields.Char(string='Manufacturer')

    category_id = fields.Many2one(
        'pharmacy.medicine.category',
        string='Category',
    )

    # Selection fields store a fixed list of choices as a string in the
    # database — cheap, fast, and perfect for things like dosage form.
    dosage_form = fields.Selection(
        selection=[
            ('tablet', 'Tablet'),
            ('capsule', 'Capsule'),
            ('syrup', 'Syrup'),
            ('injection', 'Injection'),
            ('ointment', 'Ointment'),
            ('other', 'Other'),
        ],
        string='Dosage Form',
        default='tablet',
    )

    prescription_required = fields.Boolean(
        string='Prescription Required',
        default=True,
        help='If checked, this medicine can only be dispensed against a '
             'verified prescription.',
    )

    unit_price = fields.Float(string='Unit Price', required=True)

    reorder_level = fields.Integer(
        string='Reorder Level',
        default=10,
        help='When total quantity across all batches drops to or below '
             'this number, the medicine is flagged as low stock.',
    )

    # One2many: "give me every batch record that points its medicine_id
    # back at me". Notice there's no data stored here — Odoo builds this
    # list on the fly by querying pharmacy.medicine.batch.
    batch_ids = fields.One2many(
        'pharmacy.medicine.batch',
        'medicine_id',
        string='Batches',
    )

    # --- Computed fields -------------------------------------------------
    # compute='' + store=True means: calculate this value with the method
    # below, but also save the result in the database column so it can be
    # searched/sorted/grouped-by efficiently and shown in list views fast.
    total_quantity = fields.Integer(
        string='Total Quantity',
        compute='_compute_total_quantity',
        store=True,
    )

    is_low_stock = fields.Boolean(
        string='Low Stock',
        compute='_compute_total_quantity',
        store=True,
    )

    # @api.depends tells Odoo WHEN to re-run this compute method:
    # any time batch_ids.quantity changes, or reorder_level changes,
    # Odoo automatically recalculates total_quantity for the affected
    # medicine record(s). This is the core of Odoo's reactive ORM.
    @api.depends('batch_ids.quantity', 'reorder_level')
    def _compute_total_quantity(self):
        for medicine in self:
            total = sum(medicine.batch_ids.mapped('quantity'))
            medicine.total_quantity = total
            medicine.is_low_stock = total <= medicine.reorder_level

    def action_view_batches(self):
        """Smart-button action: opens the batch list filtered to this
        medicine. Smart buttons are the small stat-boxes you see at the
        top-right of a form view (e.g. '5 Batches')."""
        self.ensure_one()  # safety check: this action only makes sense for exactly one record
        return {
            'type': 'ir.actions.act_window',
            'name': 'Batches',
            'res_model': 'pharmacy.medicine.batch',
            'view_mode': 'list,form',
            'domain': [('medicine_id', '=', self.id)],
            'context': {'default_medicine_id': self.id},
        }

    # --- Scheduled job (called by a cron, see data/pharmacy_cron.xml) ---
    def _cron_check_low_stock(self):
        """Find every medicine currently at or below its reorder level
        and leave a chatter note so pharmacy staff see it when they open
        the record. In a production system this could also send an
        email or create a mail.activity for the Pharmacy Manager."""
        low_stock_medicines = self.search([('is_low_stock', '=', True)])
        for medicine in low_stock_medicines:
            medicine.message_post(
                body='⚠️ Low stock alert: only %d unit(s) left (reorder level: %d).'
                % (medicine.total_quantity, medicine.reorder_level)
            )

    def _cron_check_near_expiry_batches(self):
        """Find every batch expiring within the next 30 days and post a
        warning on its parent medicine record."""
        near_expiry_batches = self.env['pharmacy.medicine.batch'].search([])
        near_expiry_batches = near_expiry_batches.filtered('is_near_expiry')
        for batch in near_expiry_batches:
            batch.medicine_id.message_post(
                body='⏳ Batch %s (qty: %d) is expiring soon on %s.'
                % (batch.batch_number, batch.quantity, batch.expiry_date)
            )
