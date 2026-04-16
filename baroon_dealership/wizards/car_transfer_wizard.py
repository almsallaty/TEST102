from odoo import _, fields, models
from odoo.exceptions import ValidationError


class CarTransferWizard(models.TransientModel):
    _name = 'car.transfer.wizard'
    _description = 'Car Transfer Wizard'

    lot_id = fields.Many2one('stock.lot', required=True, readonly=True)
    product_id = fields.Many2one(related='lot_id.product_id', readonly=True)
    source_location_id = fields.Many2one('stock.location', readonly=True)
    destination_location_id = fields.Many2one('stock.location', required=True, domain="[('usage', '!=', 'view')]")
    picking_type_id = fields.Many2one('stock.picking.type', required=True, domain="[('code', '=', 'internal')]")
    note = fields.Text()

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        lot = self.env['stock.lot'].browse(self.env.context.get('default_lot_id')) if self.env.context.get('default_lot_id') else self.env['stock.lot']
        if lot:
            res['source_location_id'] = lot.current_location_id.id
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal'), ('warehouse_id.company_id', '=', lot.company_id.id)], limit=1) or self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)
            if picking_type:
                res['picking_type_id'] = picking_type.id
        return res

    def action_confirm_transfer(self):
        self.ensure_one()
        lot = self.lot_id.with_context(active_test=False)
        if not self.source_location_id:
            raise ValidationError(_('The car has no current stock location to transfer from.'))
        if self.source_location_id == self.destination_location_id:
            raise ValidationError(_('Choose a different destination location.'))
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.destination_location_id.id,
            'origin': lot.name,
            'note': self.note,
        })
        move = self.env['stock.move'].create({
            'name': lot.product_id.display_name,
            'picking_id': picking.id,
            'product_id': lot.product_id.id,
            'product_uom_qty': 1.0,
            'product_uom': lot.product_id.uom_id.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.destination_location_id.id,
        })
        self.env['stock.move.line'].create({
            'picking_id': picking.id,
            'move_id': move.id,
            'product_id': lot.product_id.id,
            'product_uom_id': lot.product_id.uom_id.id,
            'quantity': 1.0,
            'lot_id': lot.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.destination_location_id.id,
        })
        if hasattr(picking, 'action_confirm'):
            picking.action_confirm()
        if hasattr(picking, 'action_assign'):
            picking.action_assign()
        lot._baroon_log_change('movement', description=_('Internal transfer %s created from car form.') % picking.name)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Internal Transfer'),
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': picking.id,
        }
