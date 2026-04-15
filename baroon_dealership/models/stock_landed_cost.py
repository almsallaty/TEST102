from odoo import fields, models


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    dealership_lot_ids = fields.Many2many(
        'stock.lot', 'baroon_landed_cost_lot_rel', 'cost_id', 'lot_id',
        string='Cars', domain="[('is_car_vehicle', '=', True)]"
    )
    dealership_lot_count = fields.Integer(compute='_compute_dealership_lot_count')

    def _compute_dealership_lot_count(self):
        for rec in self:
            rec.dealership_lot_count = len(rec.dealership_lot_ids)

    def _get_dealership_total_cost(self):
        self.ensure_one()
        if 'amount_total' in self._fields and self.amount_total:
            return self.amount_total
        return sum(self.cost_lines.mapped('price_unit'))

    def _get_dealership_allocation_map(self):
        self.ensure_one()
        lots = self.dealership_lot_ids.filtered('is_car_vehicle')
        if not lots:
            return {}
        total = self._get_dealership_total_cost()
        share = total / len(lots) if lots else 0.0
        return {lot.id: share for lot in lots}

    def button_validate(self):
        result = super().button_validate()
        self.mapped('dealership_lot_ids')._compute_and_store_cost_snapshot()
        return result

    def button_cancel(self):
        result = super().button_cancel()
        self.mapped('dealership_lot_ids')._compute_and_store_cost_snapshot()
        return result
