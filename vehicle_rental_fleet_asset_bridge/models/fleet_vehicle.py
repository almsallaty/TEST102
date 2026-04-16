# -*- coding: utf-8 -*-
import re

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


VIN_PATTERN = re.compile(r'^[A-Z0-9]{17,23}$')


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    asset_id = fields.Many2one('account.asset', string='Fixed Asset', copy=False, readonly=True)
    vendor_bill_id = fields.Many2one(
        'account.move',
        string='Vendor Bill',
        domain="[('move_type', '=', 'in_invoice')]",
        copy=False,
    )
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', copy=False)
    asset_status = fields.Selection(
        [('no_asset', 'No Asset'), ('linked', 'Linked')],
        compute='_compute_asset_status',
        string='Asset Status',
        store=True,
    )
    interior_color_ids = fields.Many2many(
        'vehicle.color',
        'fleet_vehicle_interior_color_rel',
        'vehicle_id',
        'color_id',
        string='Interior Colors',
        help='Choose one or more interior colors/tags.',
    )
    exterior_color_ids = fields.Many2many(
        'vehicle.color',
        'fleet_vehicle_exterior_color_rel',
        'vehicle_id',
        'color_id',
        string='Exterior Colors',
        help='Choose one or more exterior colors/tags.',
    )
    engine_number = fields.Char(string='Engine Number', copy=False)
    purchase_partner_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        compute='_compute_purchase_snapshot',
        store=True,
    )
    acquisition_date = fields.Date(
        string='Acquisition Date',
        compute='_compute_purchase_snapshot',
        store=True,
    )
    acquisition_value = fields.Monetary(
        string='Acquisition Value',
        currency_field='currency_id',
        compute='_compute_purchase_snapshot',
        store=True,
    )

    @api.depends('asset_id')
    def _compute_asset_status(self):
        for record in self:
            record.asset_status = 'linked' if record.asset_id else 'no_asset'

    @api.depends('vendor_bill_id', 'vendor_bill_id.invoice_date', 'vendor_bill_id.amount_untaxed',
                 'vendor_bill_id.partner_id', 'purchase_order_id', 'purchase_order_id.partner_id',
                 'purchase_order_id.date_order', 'purchase_order_id.amount_total')
    def _compute_purchase_snapshot(self):
        for record in self:
            vendor = False
            date_value = False
            amount = 0.0
            if record.vendor_bill_id:
                vendor = record.vendor_bill_id.partner_id
                date_value = record.vendor_bill_id.invoice_date
                amount = record.vendor_bill_id.amount_untaxed or record.vendor_bill_id.amount_total
            elif record.purchase_order_id:
                vendor = record.purchase_order_id.partner_id
                date_value = fields.Date.to_date(record.purchase_order_id.date_order) if record.purchase_order_id.date_order else False
                amount = record.purchase_order_id.amount_total
            record.purchase_partner_id = vendor
            record.acquisition_date = date_value
            record.acquisition_value = amount

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [self._normalize_identity_values(vals) for vals in vals_list]
        records = super().create(vals_list)
        records._sync_asset_backlinks()
        return records

    def write(self, vals):
        vals = self._normalize_identity_values(vals)
        res = super().write(vals)
        self._sync_asset_backlinks()
        return res

    def _normalize_identity_values(self, vals):
        vals = dict(vals)
        for field_name in ('vin_sn', 'license_plate', 'engine_number'):
            if field_name in vals and vals[field_name]:
                vals[field_name] = vals[field_name].strip().upper()
        return vals

    def _find_duplicate(self, field_name, value):
        self.ensure_one()
        return self.search([
            (field_name, '=', value),
            ('id', '!=', self.id),
        ], limit=1)

    @api.constrains('vin_sn')
    def _check_vin_sn(self):
        for record in self:
            if not record.vin_sn:
                continue
            vin = record.vin_sn.strip().upper()
            if not VIN_PATTERN.fullmatch(vin):
                raise ValidationError(_(
                    'VIN must be 17 to 23 characters and contain only letters and numbers.'
                ))
            if record._find_duplicate('vin_sn', vin):
                raise ValidationError(_('VIN must be unique.'))

    @api.constrains('license_plate')
    def _check_license_plate_unique(self):
        for record in self:
            if record.license_plate and record._find_duplicate('license_plate', record.license_plate.strip().upper()):
                raise ValidationError(_('Plate Number must be unique.'))

    @api.constrains('engine_number')
    def _check_engine_number_unique(self):
        for record in self:
            if record.engine_number and record._find_duplicate('engine_number', record.engine_number.strip().upper()):
                raise ValidationError(_('Engine Number must be unique.'))

    @api.constrains('asset_id')
    def _check_asset_link(self):
        for record in self:
            if record.asset_id and record.asset_id.vehicle_id and record.asset_id.vehicle_id != record:
                raise ValidationError(_('This asset is already linked to another vehicle.'))
            if record.asset_id and record.asset_id.vehicle_vin and record.vin_sn and record.asset_id.vehicle_vin != record.vin_sn:
                raise ValidationError(_('The linked asset VIN does not match the vehicle VIN.'))

    def _sync_asset_backlinks(self):
        for record in self.filtered('asset_id'):
            updates = {}
            if record.asset_id.vehicle_id != record:
                updates['vehicle_id'] = record.id
            if record.vin_sn and record.asset_id.vehicle_vin != record.vin_sn:
                updates['vehicle_vin'] = record.vin_sn
            if record.vendor_bill_id and record.asset_id.vendor_bill_id != record.vendor_bill_id:
                updates['vendor_bill_id'] = record.vendor_bill_id.id
            if record.purchase_order_id and record.asset_id.purchase_order_id != record.purchase_order_id:
                updates['purchase_order_id'] = record.purchase_order_id.id
            if updates:
                record.asset_id.sudo().write(updates)

    def action_create_linked_asset(self):
        self.ensure_one()
        if not self.env.user.has_group('account.group_account_user'):
            raise AccessError(_('Only accounting users can create or link assets.'))

        if self.asset_id:
            return self.action_open_linked_asset()

        existing_asset = self.env['account.asset'].search([
            '|',
            ('vehicle_id', '=', self.id),
            ('vehicle_vin', '=', self.vin_sn),
        ], limit=1)
        if existing_asset:
            self.asset_id = existing_asset.id
            self._sync_asset_backlinks()
            return self.action_open_linked_asset()

        ctx = {
            'default_name': f'{self.model_id.display_name or self.name or "Vehicle"} - {self.license_plate or self.vin_sn or self.id}',
            'default_vehicle_id': self.id,
            'default_vehicle_vin': self.vin_sn,
            'default_purchase_order_id': self.purchase_order_id.id,
            'default_vendor_bill_id': self.vendor_bill_id.id,
            'default_original_value': self.acquisition_value,
            'default_acquisition_date': self.acquisition_date,
        }
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Asset'),
            'res_model': 'account.asset',
            'view_mode': 'form',
            'target': 'current',
            'context': ctx,
        }

    def action_open_linked_asset(self):
        self.ensure_one()
        if not self.asset_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Fixed Asset'),
            'res_model': 'account.asset',
            'res_id': self.asset_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_vendor_bill(self):
        self.ensure_one()
        if not self.vendor_bill_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Bill'),
            'res_model': 'account.move',
            'res_id': self.vendor_bill_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_purchase_order(self):
        self.ensure_one()
        if not self.purchase_order_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Order'),
            'res_model': 'purchase.order',
            'res_id': self.purchase_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
