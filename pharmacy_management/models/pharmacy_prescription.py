# models/pharmacy_prescription.py
#
# This is the "business process" heart of the module. A Prescription goes
# through a simple state machine:
#
#   draft --(Verify)--> verified --(Dispense)--> dispensed
#     \                    |
#      \--(Cancel)---------+--(Cancel)--> cancelled
#
# Only in the "Dispense" step do we actually touch stock — deducting
# quantity from the oldest-expiring batches first (this is the standard
# pharmacy practice called FEFO: First-Expiry-First-Out).

from odoo import models, fields, api
from odoo.exceptions import UserError


class PharmacyPrescription(models.Model):
    _name = 'pharmacy.prescription'
    _description = 'Prescription'

    # _inherit (used together with _name) means: keep this as a NEW model,
    # but also mix in the reusable behaviour from mail.thread (chatter /
    # log notes / followers) and mail.activity.mixin (scheduled activities
    # like "Follow up on 12/08"). This is different from the res.partner
    # file above, where _inherit alone extended an EXISTING model.
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'prescription_date desc, id desc'

    # tracking=True on a field means every change to it is automatically
    # logged in the chatter — free audit trail, no extra code needed.
    name = fields.Char(
        string='Reference',
        default='New',
        copy=False,       # don't copy the reference number when someone duplicates a record
        readonly=True,
    )

    patient_id = fields.Many2one(
        'res.partner',
        string='Patient',
        required=True,
        domain=[('is_pharmacy_patient', '=', True)],
        tracking=True,
    )
    doctor_name = fields.Char(string='Prescribing Doctor', required=True)
    prescription_date = fields.Date(
        string='Prescription Date',
        default=fields.Date.context_today,
        required=True,
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('verified', 'Verified'),
            ('dispensed', 'Dispensed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        tracking=True,
    )

    line_ids = fields.One2many(
        'pharmacy.prescription.line',
        'prescription_id',
        string='Medicines',
    )

    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_total_amount',
        store=True,
    )

    dispensed_date = fields.Datetime(string='Dispensed On', readonly=True)
    pharmacist_id = fields.Many2one(
        'res.users',
        string='Dispensed By',
        readonly=True,
    )

    @api.depends('line_ids.subtotal')
    def _compute_total_amount(self):
        for prescription in self:
            prescription.total_amount = sum(prescription.line_ids.mapped('subtotal'))

    # --- Sequence number on creation ---------------------------------
    # @api.model_create_multi tells Odoo this method creates several
    # records at once (a list of dicts in), which is the modern,
    # performance-friendly way to override create() in Odoo.
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                # ir.sequence is Odoo's built-in tool for generating
                # gapless, prefixed numbers like "RX/2026/00001".
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'pharmacy.prescription'
                ) or 'New'
        return super().create(vals_list)

    # --- Workflow buttons ----------------------------------------------
    def action_verify(self):
        for prescription in self:
            if prescription.state != 'draft':
                raise UserError('Only draft prescriptions can be verified.')
            if not prescription.line_ids:
                raise UserError('Add at least one medicine before verifying.')
            prescription.state = 'verified'

    def action_dispense(self):
        for prescription in self:
            if prescription.state != 'verified':
                raise UserError('Only verified prescriptions can be dispensed.')
            # Deduct stock for every line using FEFO logic before flipping
            # the status, so if ANY line fails (not enough stock) the
            # whole transaction rolls back automatically — Odoo wraps
            # each button call in a database transaction for us.
            for line in prescription.line_ids:
                line._dispense_from_batches()
            prescription.write({
                'state': 'dispensed',
                'dispensed_date': fields.Datetime.now(),
                'pharmacist_id': self.env.user.id,
            })

    def action_cancel(self):
        for prescription in self:
            if prescription.state == 'dispensed':
                raise UserError('A dispensed prescription cannot be cancelled.')
            prescription.state = 'cancelled'

    def action_reset_to_draft(self):
        for prescription in self:
            prescription.state = 'draft'
