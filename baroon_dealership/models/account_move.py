from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    dealership_lot_ids = fields.Many2many(
        'stock.lot', 'baroon_account_move_lot_rel', 'move_id', 'lot_id',
        string='Cars', domain="[('is_car_vehicle', '=', True)]"
    )
