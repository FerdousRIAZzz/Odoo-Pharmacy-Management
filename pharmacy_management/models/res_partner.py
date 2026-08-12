# models/res_partner.py
#
# res.partner is Odoo's built-in "Contacts" model — it already represents
# people and companies everywhere in Odoo (customers, vendors, employees).
# Rather than building a brand new "Patient" model from scratch, we EXTEND
# the existing one. This is a core Odoo skill: _inherit lets us add fields
# and behaviour to a model that already exists, without touching Odoo's
# own source code.

from odoo import models, fields


class ResPartner(models.Model):
    # Using the SAME _name as an existing model, together with _inherit,
    # means "add the following fields/methods onto this existing model"
    # instead of creating a new database table.
    _inherit = 'res.partner'

    is_pharmacy_patient = fields.Boolean(
        string='Is Patient',
        help='Check this box to make this contact selectable as a patient '
             'on prescriptions.',
    )
    date_of_birth = fields.Date(string='Date of Birth')
    blood_group = fields.Selection(
        selection=[
            ('a+', 'A+'), ('a-', 'A-'),
            ('b+', 'B+'), ('b-', 'B-'),
            ('ab+', 'AB+'), ('ab-', 'AB-'),
            ('o+', 'O+'), ('o-', 'O-'),
        ],
        string='Blood Group',
    )
    known_allergies = fields.Text(string='Known Allergies')
    emergency_contact = fields.Char(string='Emergency Contact')

    prescription_ids = fields.One2many(
        'pharmacy.prescription',
        'patient_id',
        string='Prescriptions',
    )
    prescription_count = fields.Integer(
        string='Prescription Count',
        compute='_compute_prescription_count',
    )

    def _compute_prescription_count(self):
        for partner in self:
            partner.prescription_count = len(partner.prescription_ids)

    def action_view_prescriptions(self):
        """Smart-button on the Contact form: jump to this patient's prescriptions."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Prescriptions',
            'res_model': 'pharmacy.prescription',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }
