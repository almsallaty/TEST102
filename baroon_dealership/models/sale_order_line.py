from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    car_lot_id = fields.Many2one(
        'stock.lot',
        string='Car VIN / Serial',
        domain="[('is_car_vehicle', '=', True), ('active', '=', True)]",
        copy=False,
    )

    def _prepare_car_line_description(self, lot):
        self.ensure_one()
        car_title = ' '.join(filter(None, [lot.car_brand, lot.car_model, lot.car_trim])).strip()
        car_title = car_title or lot.product_id.display_name
        vin_part = _('VIN %s') % (lot.name or '-')
        engine_part = _('Engine %s') % lot.engine_number if lot.engine_number else False
        details = ' • '.join(filter(None, [car_title, vin_part, engine_part]))
        return details

    @api.onchange('car_lot_id')
    def _onchange_car_lot_id(self):
        for line in self:
            lot = line.car_lot_id
            if lot:
                if lot.car_status in ('sold', 'delivered') or not lot.active:
                    raise ValidationError(_('This VIN is already sold or archived.'))
                if lot.car_status not in ('available', 'reserved') and line.order_id.state in ('draft', 'sent'):
                    raise ValidationError(_('This VIN is not yet ready for sale. Move it to Available first.'))
                line.product_id = lot.product_id
                line.product_uom_qty = 1.0
                line.price_unit = lot.sale_price or lot.product_id.lst_price
                if hasattr(line, 'product_uom_id') and lot.product_id.uom_id:
                    line.product_uom_id = lot.product_id.uom_id
                line.name = line._prepare_car_line_description(lot)

    @api.onchange('product_id')
    def _onchange_product_id_clear_lot(self):
        for line in self:
            if line.car_lot_id and line.product_id and line.product_id != line.car_lot_id.product_id:
                line.car_lot_id = False

    @api.constrains('car_lot_id', 'product_uom_qty')
    def _check_car_line_quantity(self):
        for line in self:
            if line.car_lot_id and line.product_uom_qty != 1:
                raise ValidationError(_('A VIN sale line must always use quantity 1.'))
            if line.car_lot_id and line.product_id != line.car_lot_id.product_id:
                raise ValidationError(_('The selected product must match the VIN record product.'))

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines.filtered('car_lot_id'):
            if not line.name:
                line.name = line._prepare_car_line_description(line.car_lot_id)
        lines._sync_car_reservation_state()
        return lines

    def write(self, vals):
        previous_lots = self.mapped('car_lot_id').with_context(active_test=False)
        result = super().write(vals)
        for line in self.filtered('car_lot_id'):
            if not line.name or 'car_lot_id' in vals:
                line.name = line._prepare_car_line_description(line.car_lot_id)
        (previous_lots | self.mapped('car_lot_id')).with_context(active_test=False)._sync_from_sale_documents()
        return result

    def unlink(self):
        lots = self.mapped('car_lot_id').with_context(active_test=False)
        result = super().unlink()
        lots._sync_from_sale_documents()
        return result

    def _sync_car_reservation_state(self):
        self.mapped('car_lot_id').with_context(active_test=False)._sync_from_sale_documents()


class StockLotSaleSync(models.Model):
    _inherit = 'stock.lot'

    def _sync_from_sale_documents(self):
        sale_line_model = self.env['sale.order.line']
        for lot in self.with_context(active_test=False):
            active_lines = sale_line_model.search([
                ('car_lot_id', '=', lot.id),
                ('display_type', '=', False),
                ('state', 'not in', ['cancel']),
                ('order_id.state', 'in', ['draft', 'sent']),
            ], order='create_date asc, id asc')
            confirmed_lines = sale_line_model.search([
                ('car_lot_id', '=', lot.id),
                ('display_type', '=', False),
                ('state', 'not in', ['cancel']),
                ('order_id.state', 'in', ['sale', 'done']),
            ], order='create_date asc, id asc', limit=1)
            if len(active_lines) > 1:
                raise ValidationError(_('VIN %s is linked to more than one open quotation. Keep only one active sales document per VIN.') % (lot.name or lot.display_name))
            if confirmed_lines:
                lot._mark_sold_from_order_line(confirmed_lines)
                continue
            if active_lines:
                line = active_lines[0]
                if lot.car_status in ('sold', 'delivered') or not lot.active:
                    raise ValidationError(_('VIN %s is already sold or archived and cannot be quoted again.') % (lot.name or lot.display_name))
                lot._reserve_for_sale_line(line)
            elif lot.car_status == 'reserved' and lot.reservation_order_id and not lot.sale_order_id:
                lot._release_reservation(order=lot.reservation_order_id)
