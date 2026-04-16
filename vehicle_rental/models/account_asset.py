# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', copy=False)
    vehicle_vin = fields.Char(string='Vehicle VIN', copy=False)
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', copy=False)
    vendor_bill_id = fields.Many2one(
        'account.move',
        string='Vendor Bill',
        domain="[('move_type', '=', 'in_invoice')]",
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_vehicle_backlinks()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._sync_vehicle_backlinks()
        return res

    @api.constrains('vehicle_id', 'vehicle_vin')
    def _check_vehicle_link_consistency(self):
        for record in self:
            if record.vehicle_id and record.vehicle_vin and record.vehicle_id.vin_sn and record.vehicle_vin != record.vehicle_id.vin_sn:
                raise ValidationError(_('Asset VIN must match the linked vehicle VIN.'))
            if record.vehicle_id:
                duplicate = self.search([
                    ('id', '!=', record.id),
                    ('vehicle_id', '=', record.vehicle_id.id),
                ], limit=1)
                if duplicate:
                    raise ValidationError(_('A vehicle can only be linked to one asset.'))

    def _sync_vehicle_backlinks(self):
        for record in self.filtered('vehicle_id'):
            updates = {}
            if record.vehicle_id.asset_id != record:
                updates['asset_id'] = record.id
            if record.vendor_bill_id and record.vehicle_id.vendor_bill_id != record.vendor_bill_id:
                updates['vendor_bill_id'] = record.vendor_bill_id.id
            if record.purchase_order_id and record.vehicle_id.purchase_order_id != record.purchase_order_id:
                updates['purchase_order_id'] = record.purchase_order_id.id
            if updates:
                record.vehicle_id.sudo().write(updates)

    def action_open_vehicle(self):
        self.ensure_one()
        if not self.vehicle_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vehicle'),
            'res_model': 'fleet.vehicle',
            'res_id': self.vehicle_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
