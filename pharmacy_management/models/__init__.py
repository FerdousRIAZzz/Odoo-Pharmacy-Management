# models/__init__.py
# Every model file we create must be imported here, otherwise Odoo
# will never know that file (and the model inside it) exists.
from . import pharmacy_medicine_category
from . import pharmacy_medicine
from . import pharmacy_medicine_batch
from . import res_partner
from . import pharmacy_prescription
from . import pharmacy_prescription_line
