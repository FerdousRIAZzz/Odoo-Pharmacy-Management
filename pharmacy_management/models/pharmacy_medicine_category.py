# models/pharmacy_medicine_category.py
#
# This is the simplest possible Odoo model: a small "master data" list
# (like Product Categories in the Inventory app). We start here because
# it's the easiest place to see the basic anatomy of an Odoo model.

from odoo import models, fields


class PharmacyMedicineCategory(models.Model):
    # _name is the technical name Odoo uses internally (and in the database
    # table, which will literally be called "pharmacy_medicine_category").
    _name = 'pharmacy.medicine.category'

    # _description is a human-readable label used in logs and some UI spots.
    _description = 'Medicine Category'

    # _order controls the default sort order when records are listed.
    _order = 'name'

    name = fields.Char(string='Category Name', required=True)
    description = fields.Text(string='Description')

    # A computed, stored count of how many medicines belong to this
    # category. We compute it with a small Python method below instead
    # of asking the user to fill it in.
    medicine_count = fields.Integer(
        string='Medicines',
        compute='_compute_medicine_count',
    )

    def _compute_medicine_count(self):
        # 'self' here can be a RECORDSET containing several category
        # records at once (e.g. when Odoo renders a list view). That's
        # why we loop over 'self' instead of assuming there's only one.
        for category in self:
            category.medicine_count = self.env['pharmacy.medicine'].search_count(
                [('category_id', '=', category.id)]
            )
