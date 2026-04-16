from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    car_lot_id = fields.Many2one('stock.lot', string='Car VIN', copy=False)
