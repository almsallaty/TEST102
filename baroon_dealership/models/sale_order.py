from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    selected_car_lot_id = fields.Many2one('stock.lot', string='Selected VIN', compute='_compute_selected_car_lot_id')
    selected_car_label = fields.Char(string='Selected Car', compute='_compute_selected_car_lot_id')

    @api.depends('order_line.car_lot_id', 'opportunity_id.car_lot_id')
    def _compute_selected_car_lot_id(self):
        for order in self:
            lot = order.order_line.filtered('car_lot_id')[:1].car_lot_id or order.opportunity_id.car_lot_id
            order.selected_car_lot_id = lot
            if lot:
                title = ' '.join(filter(None, [lot.car_brand, lot.car_model, lot.car_trim])).strip()
                title = title or lot.product_id.display_name
                order.selected_car_label = f"{title} - VIN {lot.name or '-'}"
            else:
                order.selected_car_label = False

    def action_confirm(self):
        result = super().action_confirm()
        self.order_line.mapped('car_lot_id').with_context(active_test=False)._sync_from_sale_documents()
        return result

    def action_cancel(self):
        lots = self.order_line.mapped('car_lot_id').with_context(active_test=False)
        result = super().action_cancel()
        lots._sync_from_sale_documents()
        return result

    def action_draft(self):
        result = super().action_draft()
        self.order_line.mapped('car_lot_id').with_context(active_test=False)._sync_from_sale_documents()
        return result
