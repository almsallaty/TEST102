from odoo import _, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    car_lot_count = fields.Integer(compute='_compute_car_lot_count')
    car_lot_summary = fields.Char(compute='_compute_car_lot_count')

    def _compute_car_lot_count(self):
        for picking in self:
            lots = picking.move_line_ids.mapped('lot_id')
            picking.car_lot_count = len(lots)
            picking.car_lot_summary = ', '.join(lots.mapped('name')[:5])

    def _baroon_prepare_incoming_serials(self):
        MoveLine = self.env['stock.move.line']
        for picking in self.filtered(lambda p: p.picking_type_id.code == 'incoming' and p.purchase_id):
            moves = getattr(picking, 'move_ids', self.env['stock.move'])
            for move in moves.filtered(lambda m: m.product_id.tracking == 'serial' and m.purchase_line_id):
                lots = move.purchase_line_id.vin_lot_ids.filtered(lambda l: l.product_id == move.product_id)
                if not lots:
                    continue
                existing_identifiers = set()
                blank_lines = self.env['stock.move.line']
                for line in move.move_line_ids:
                    if line.lot_id:
                        existing_identifiers.add(line.lot_id.name)
                    lot_name = getattr(line, 'lot_name', False)
                    if lot_name:
                        existing_identifiers.add(lot_name)
                    if not line.lot_id and not lot_name:
                        blank_lines |= line
                lots_to_assign = lots.filtered(lambda l: l.name not in existing_identifiers)
                if not lots_to_assign:
                    continue
                for idx, lot in enumerate(lots_to_assign):
                    target_line = blank_lines[idx] if idx < len(blank_lines) else False
                    vals = {
                        'company_id': picking.company_id.id,
                        'picking_id': picking.id,
                        'move_id': move.id,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_uom.id,
                        'quantity': 1.0,
                        'lot_id': lot.id,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                    }
                    if target_line:
                        target_line.write(vals)
                    else:
                        MoveLine.create(vals)

    def button_validate(self):
        self._baroon_prepare_incoming_serials()
        result = super().button_validate()
        self._baroon_log_completed_car_moves()
        return result

    def _baroon_log_completed_car_moves(self):
        history_model = self.env['car.location.history'].sudo()
        for picking in self.filtered(lambda p: p.state == 'done'):
            for line in picking.move_line_ids.filtered(lambda ml: ml.lot_id and ml.lot_id.is_car_vehicle):
                lot = line.lot_id.with_context(active_test=False)
                movement_type = 'internal'
                status_vals = {}
                if picking.picking_type_id.code == 'incoming':
                    movement_type = 'receipt'
                    if not lot.arrival_date:
                        status_vals['arrival_date'] = fields.Date.today()
                    if lot.car_status in ('draft', 'incoming', 'in_shipment', 'customs'):
                        status_vals['car_status'] = 'received'
                elif picking.picking_type_id.code == 'outgoing':
                    movement_type = 'delivery'
                    status_vals.update({
                        'car_status': 'delivered',
                        'delivered_date': fields.Datetime.now(),
                        'active': False,
                        'website_published': False,
                    })
                else:
                    movement_type = 'internal'
                if status_vals:
                    lot.sudo().write(status_vals)
                history_model.create({
                    'lot_id': lot.id,
                    'picking_id': picking.id,
                    'source_location_id': line.location_id.id,
                    'destination_location_id': line.location_dest_id.id,
                    'movement_type': movement_type,
                    'note': _('Created from transfer %s') % picking.name,
                })
                lot._baroon_log_change('movement', description=_('Moved from %s to %s through %s') % (line.location_id.display_name, line.location_dest_id.display_name, picking.name))

    def action_view_car_lots(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cars'),
            'res_model': 'stock.lot',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.move_line_ids.mapped('lot_id').ids)],
        }
