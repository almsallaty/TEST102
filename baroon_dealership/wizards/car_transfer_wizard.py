from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CarTransferWizard(models.TransientModel):
    _name = 'car.transfer.wizard'
    _description = 'Car Transfer Wizard'

    lot_id = fields.Many2one('stock.lot', string='Car', required=True, readonly=True)
    source_location_id = fields.Many2one('stock.location', string='Source Location', required=True)
    destination_location_id = fields.Many2one('stock.location', string='Destination Location', required=True)
    picking_type_id = fields.Many2one('stock.picking.type', string='Operation Type', required=True, domain="[('code', '=', 'internal')]")
    scheduled_date = fields.Datetime(default=fields.Datetime.now, required=True)
    note = fields.Char()

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        lot = self.env['stock.lot'].browse(self.env.context.get('default_lot_id'))
        internal_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id.company_id', '=', lot.company_id.id if lot else self.env.company.id)
        ], limit=1)
        if lot:
            res.setdefault('source_location_id', lot.current_location_id.id)
        if internal_type:
            res.setdefault('picking_type_id', internal_type.id)
        return res

    def action_create_transfer(self):
        self.ensure_one()
        lot = self.lot_id.with_context(active_test=False)
        if not lot or not lot.product_id:
            raise ValidationError(_('Select a valid car record.'))
        if self.source_location_id == self.destination_location_id:
            raise ValidationError(_('Source and destination locations must be different.'))
        if not self.picking_type_id:
            raise ValidationError(_('No internal transfer operation type was found.'))
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.destination_location_id.id,
            'scheduled_date': self.scheduled_date,
            'origin': _('Car Transfer %s') % (lot.name or lot.display_name),
            'note': self.note,
            'move_ids': [(0, 0, {
                'name': lot.display_name,
                'product_id': lot.product_id.id,
                'product_uom_qty': 1.0,
                'product_uom': lot.product_id.uom_id.id,
                'location_id': self.source_location_id.id,
                'location_dest_id': self.destination_location_id.id,
            })],
        })
        picking.action_confirm()
        move = picking.move_ids[:1]
        move_line = move.move_line_ids[:1]
        if move_line:
            move_line.write({
                'lot_id': lot.id,
                'qty_done': 1,
                'location_id': self.source_location_id.id,
                'location_dest_id': self.destination_location_id.id,
            })
        else:
            self.env['stock.move.line'].create({
                'picking_id': picking.id,
                'move_id': move.id,
                'company_id': picking.company_id.id,
                'product_id': lot.product_id.id,
                'product_uom_id': lot.product_id.uom_id.id,
                'location_id': self.source_location_id.id,
                'location_dest_id': self.destination_location_id.id,
                'lot_id': lot.id,
                'qty_done': 1,
            })
        picking.message_post(body=_('Created from car transfer wizard for VIN %s.') % (lot.name or lot.display_name))
        lot.message_post(body=_('Internal transfer %s created from %s to %s.') % (
            picking.name,
            self.source_location_id.display_name,
            self.destination_location_id.display_name,
        ))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Transfer'),
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': picking.id,
        }
