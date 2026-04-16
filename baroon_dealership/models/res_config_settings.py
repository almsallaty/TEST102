from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dealership_require_complete_profile = fields.Boolean(
        string='Require complete profile before website publishing',
        config_parameter='baroon_dealership.require_complete_profile',
        default=True,
    )
    dealership_allow_manual_status = fields.Boolean(
        string='Allow manual status actions on cars',
        config_parameter='baroon_dealership.allow_manual_status',
        default=True,
    )
    dealership_auto_receipt_status = fields.Boolean(
        string='Update car status from validated receipts',
        config_parameter='baroon_dealership.auto_receipt_status',
        default=True,
    )
