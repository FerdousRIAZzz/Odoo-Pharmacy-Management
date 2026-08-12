# models/pharmacy_prescription_line.py
#
# Each line on a prescription says "this many units of this medicine,
# with these dosage instructions". This model also owns the FEFO
# (First-Expiry-First-Out) logic that actually deducts stock when the
# prescription is dispensed.

from odoo import models, fields, api
from odoo.exceptions import UserError


class PharmacyPrescriptionLine(models.Model):
    _name = 'pharmacy.prescription.line'
    _description = 'Prescription Line'

    prescription_id = fields.Many2one(
        'pharmacy.prescription',
        string='Prescription',
        required=True,
        ondelete='cascade',
    )
    medicine_id = fields.Many2one(
        'pharmacy.medicine',
        string='Medicine',
        required=True,
    )
    quantity = fields.Integer(string='Quantity', required=True, default=1)
    dosage_instructions = fields.Char(
        string='Dosage Instructions',
        help='e.g. "1 tablet twice daily after meals"',
    )

    # related=... pulls a field's value from a linked record and mirrors
    # it here — no need to look it up again in the view or in Python.
    # store=True lets it be used in the subtotal computation below.
    unit_price = fields.Float(
        string='Unit Price',
        related='medicine_id.unit_price',
        store=True,
        readonly=True,
    )
    subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True,
    )

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price

    # onchange fires immediately in the UI (before saving) whenever the
    # user picks a medicine, purely to help the user — e.g. warn them the
    # medicine needs a prescription reminder, or show current stock.
    @api.onchange('medicine_id')
    def _onchange_medicine_id(self):
        if self.medicine_id and self.medicine_id.total_quantity <= 0:
            return {
                'warning': {
                    'title': 'Out of Stock',
                    'message': '%s currently has no stock available.' % self.medicine_id.name,
                }
            }

    def _dispense_from_batches(self):
        """Deduct this line's quantity from the medicine's batches,
        oldest expiry date first (FEFO). Raises a UserError if the
        combined quantity across all batches isn't enough.

        This is called from PharmacyPrescription.action_dispense() —
        one call per line, inside the same database transaction.
        """
        self.ensure_one()
        remaining = self.quantity

        # batch_ids is already ordered oldest-expiry-first thanks to
        # _order = 'expiry_date asc' on pharmacy.medicine.batch, and we
        # filter out already-expired batches so we never dispense them.
        available_batches = self.medicine_id.batch_ids.filtered(
            lambda b: not b.is_expired and b.quantity > 0
        )

        for batch in available_batches:
            if remaining <= 0:
                break
            take = min(batch.quantity, remaining)
            batch.quantity -= take
            remaining -= take

        if remaining > 0:
            raise UserError(
                'Not enough stock for "%s". Missing %d unit(s).'
                % (self.medicine_id.name, remaining)
            )
