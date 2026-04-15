from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dealership_require_complete_profile = fields.Boolean(
        string='Require complete profile before website publish',
        config_parameter='baroon_dealership.require_complete_profile',
        default=True,
    )
    dealership_require_vin_on_sale = fields.Boolean(
        string='Require VIN on car quotation lines',
        config_parameter='baroon_dealership.require_vin_on_sale',
        default=True,
    )
    dealership_allow_manual_status_change = fields.Boolean(
        string='Allow manual car status buttons',
        config_parameter='baroon_dealership.allow_manual_status_change',
        default=True,
    )
    dealership_auto_update_from_pickings = fields.Boolean(
        string='Update car workflow automatically from validated pickings',
        config_parameter='baroon_dealership.auto_update_from_pickings',
        default=True,
    )
    dealership_reservation_hold_days = fields.Integer(
        string='Default reservation hold days',
        config_parameter='baroon_dealership.reservation_hold_days',
        default=7,
    )
