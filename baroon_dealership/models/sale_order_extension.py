from odoo import models


class SaleOrderDealershipExtension(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        if self.selected_car_lot_id:
            vals['car_lot_id'] = self.selected_car_lot_id.id
        return vals
