from odoo import _, api, fields, models


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    car_lot_ids = fields.Many2many('stock.lot', 'stock_landed_cost_car_lot_rel', 'landed_cost_id', 'lot_id', string='Cars')
    car_count = fields.Integer(compute='_compute_car_count')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.car_lot_ids:
                rec.car_lot_ids._compute_extra_costs()
                rec.car_lot_ids._compute_dealership_counts()
        return records

    def write(self, vals):
        result = super().write(vals)
        for rec in self:
            if rec.car_lot_ids:
                rec.car_lot_ids._compute_extra_costs()
                rec.car_lot_ids._compute_dealership_counts()
        return result

    def _compute_car_count(self):
        for rec in self:
            rec.car_count = len(rec.car_lot_ids)

    def button_validate(self):
        result = super().button_validate()
        expense_model = self.env['car.expense'].sudo()
        for cost in self.filtered(lambda c: c.state == 'done' and c.car_lot_ids):
            share = cost.amount_total / len(cost.car_lot_ids) if cost.car_lot_ids else 0.0
            for lot in cost.car_lot_ids:
                if expense_model.search_count([('lot_id', '=', lot.id), ('landed_cost_id', '=', cost.id)]):
                    continue
                expense_model.create({
                    'name': _('%s - Landed Cost Share') % cost.name,
                    'lot_id': lot.id,
                    'expense_type': 'shipping',
                    'amount': share,
                    'landed_cost_id': cost.id,
                    'state': 'approved',
                    'vendor_id': cost.vendor_bill_id.partner_id.id if getattr(cost, 'vendor_bill_id', False) and cost.vendor_bill_id and cost.vendor_bill_id.partner_id else False,
                })
        return result
