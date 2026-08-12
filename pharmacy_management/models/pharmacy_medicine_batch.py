# models/pharmacy_medicine_batch.py
#
# A BATCH (also called a "lot") is a specific delivery of a medicine that
# shares one expiry date, e.g. "500 tablets of Paracetamol, Batch #PC2201,
# expiring 2027-03-01". This is where real quantity is stored.

from datetime import date, timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PharmacyMedicineBatch(models.Model):
    _name = 'pharmacy.medicine.batch'
    _description = 'Medicine Batch'
    # Ordering by expiry_date ascending means the OLDEST-expiring batch
    # always appears first — handy on its own, and also the exact order
    # our FEFO dispensing logic (in pharmacy_prescription.py) relies on.
    _order = 'expiry_date asc'

    medicine_id = fields.Many2one(
        'pharmacy.medicine',
        string='Medicine',
        required=True,
        ondelete='cascade',   # delete the batch automatically if the medicine is deleted
    )
    batch_number = fields.Char(string='Batch / Lot Number', required=True)
    expiry_date = fields.Date(string='Expiry Date', required=True)
    quantity = fields.Integer(string='Quantity', required=True, default=0)

    # Computed, non-stored (store=False is the default) fields used purely
    # for display badges in the UI — cheap to calculate on the fly, no
    # need to clutter the database with them.
    is_expired = fields.Boolean(string='Expired', compute='_compute_expiry_flags')
    is_near_expiry = fields.Boolean(string='Near Expiry', compute='_compute_expiry_flags')

    @api.depends('expiry_date')
    def _compute_expiry_flags(self):
        today = date.today()
        for batch in self:
            if not batch.expiry_date:
                batch.is_expired = False
                batch.is_near_expiry = False
                continue
            batch.is_expired = batch.expiry_date < today
            # "Near expiry" = expires within the next 30 days but hasn't expired yet
            batch.is_near_expiry = today <= batch.expiry_date <= (today + timedelta(days=30))

    # --- Validation --------------------------------------------------
    # @api.constrains runs automatically every time listed fields change
    # (on create AND on write), and raises a ValidationError to block the
    # save if the condition fails. This is server-side data integrity —
    # it can't be bypassed by the UI, the API, or an import.
    @api.constrains('quantity')
    def _check_quantity_not_negative(self):
        for batch in self:
            if batch.quantity < 0:
                raise ValidationError('Batch quantity cannot be negative.')

    @api.constrains('expiry_date')
    def _check_expiry_date_not_in_past_on_create(self):
        for batch in self:
            if batch.expiry_date and batch.expiry_date < date.today():
                raise ValidationError(
                    'Expiry date for batch "%s" cannot be in the past.' % batch.batch_number
                )
