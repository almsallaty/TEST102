from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    car_lot_id = fields.Many2one('stock.lot', string='Car VIN', copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves.mapped('car_lot_id')._compute_dealership_counts()
        return moves

    def write(self, vals):
        lots_before = self.mapped('car_lot_id')
        result = super().write(vals)
        (lots_before | self.mapped('car_lot_id'))._compute_dealership_counts()
        return result
