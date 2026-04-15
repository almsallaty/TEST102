from odoo import _, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    dealership_lot_ids = fields.Many2many('stock.lot', compute='_compute_dealership_lots', string='Cars')
    dealership_lot_count = fields.Integer(compute='_compute_dealership_lots')

    def _compute_dealership_lots(self):
        for picking in self:
            lots = (picking.move_line_ids.mapped('lot_id') | picking.move_ids.move_line_ids.mapped('lot_id')).filtered('is_car_vehicle')
            picking.dealership_lot_ids = lots
            picking.dealership_lot_count = len(lots)

    def action_view_dealership_cars(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cars'),
            'res_model': 'stock.lot',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', self.dealership_lot_ids.ids)],
            'context': {'active_test': False, 'search_default_filter_car_vehicle': 1},
        }

    def button_validate(self):
        result = super().button_validate()
        auto_sync = self.env['ir.config_parameter'].sudo().get_param('baroon_dealership.auto_update_from_pickings', 'True') == 'True'
        if auto_sync:
            self.filtered(lambda p: p.state == 'done')._apply_dealership_updates()
        return result

    def _apply_dealership_updates(self):
        for picking in self:
            move_lines = (picking.move_line_ids | picking.move_ids.move_line_ids).filtered(lambda ml: ml.lot_id and ml.lot_id.is_car_vehicle and ml.qty_done)
            for ml in move_lines:
                lot = ml.lot_id.with_context(active_test=False)
                lot._create_location_history(
                    source_location=ml.location_id,
                    destination_location=ml.location_dest_id,
                    picking=picking,
                    note=_('Transfer validated from stock picking %s') % (picking.name or picking.origin or ''),
                )
                vals = {}
                if picking.picking_type_id.code == 'incoming':
                    vals.update({
                        'arrival_date': fields.Date.context_today(picking),
                        'car_status': 'received',
                        'active': True,
                    })
                elif picking.picking_type_id.code == 'outgoing':
                    vals.update({
                        'car_status': 'delivered',
                        'delivered_date': fields.Datetime.now(),
                        'website_published': False,
                        'active': False,
                    })
                    if getattr(picking, 'sale_id', False):
                        vals.update({
                            'sale_order_id': picking.sale_id.id,
                            'buyer_id': picking.partner_id.id or picking.sale_id.partner_id.id,
                            'salesperson_id': picking.sale_id.user_id.id,
                        })
                elif picking.picking_type_id.code == 'internal':
                    dest_name = (ml.location_dest_id.complete_name or ml.location_dest_id.name or '').lower()
                    if any(token in dest_name for token in ['workshop', 'service', 'prep', 'prepare']):
                        vals['car_status'] = 'in_preparation'
                    elif lot.car_status not in ('reserved', 'sold', 'delivered'):
                        vals['car_status'] = 'available'
                if vals:
                    lot.with_context(baroon_system_write=True).write(vals)
