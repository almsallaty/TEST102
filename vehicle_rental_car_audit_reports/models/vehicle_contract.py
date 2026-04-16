# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


SYSTEM_FIELDS = {
    'id', 'display_name', '__last_update',
    'create_uid', 'create_date', 'write_uid', 'write_date',
    'message_ids', 'message_follower_ids', 'message_partner_ids',
    'message_needaction', 'message_needaction_counter',
    'message_has_error', 'message_has_error_counter',
    'activity_ids', 'activity_state', 'activity_type_icon',
    'activity_summary', 'activity_type_id', 'activity_date_deadline',
}
FINANCIAL_FIELDS = {
    'rent', 'driver_charge', 'total_vehicle_rent', 'extra_charge', 'total_extra_charges',
    'extra_service_charge', 'damage_amount', 'deposit', 'total_deposit', 'cancellation_charge'
}
DATE_FIELDS = {'start_date', 'end_date'}


class VehicleContract(models.Model):
    _inherit = 'vehicle.contract'

    audit_log_ids = fields.One2many('rental.contract.audit.log', 'contract_id', string='Audit Logs')
    audit_log_count = fields.Integer(compute='_compute_audit_metrics')
    x_contract_total_days = fields.Float(string='Contract Days', compute='_compute_audit_metrics')
    x_contract_total_hours = fields.Float(string='Contract Hours', compute='_compute_audit_metrics')
    x_contract_revenue_total = fields.Monetary(string='Contract Revenue', compute='_compute_audit_metrics', currency_field='currency_id')

    def _field_label(self, field_name):
        field = self._fields.get(field_name)
        return field.string if field else field_name

    def _format_field_value(self, field_name, value):
        field = self._fields.get(field_name)
        if value in (False, None):
            return ''
        if not field:
            return str(value)
        if field.type == 'many2one':
            return value.display_name if value else ''
        if field.type in ('many2many', 'one2many'):
            return ', '.join(value.mapped('display_name')) if value else ''
        if field.type == 'selection':
            selection = field.selection(self) if callable(field.selection) else field.selection
            return dict(selection).get(value, value)
        if field.type == 'boolean':
            return _('Yes') if value else _('No')
        if field.type in ('float', 'monetary'):
            return ('%.2f' % value) if value is not None else ''
        if field.type == 'date':
            return fields.Date.to_string(value)
        if field.type == 'datetime':
            return fields.Datetime.to_string(value)
        return str(value)

    def _auditable_fields(self, vals):
        names = []
        for field_name in vals:
            if field_name in SYSTEM_FIELDS:
                continue
            field = self._fields.get(field_name)
            if not field:
                continue
            if field.compute and not field.store:
                continue
            names.append(field_name)
        return names

    def _create_audit_log(self, action_type, description, field_name=False, old_value=False, new_value=False):
        Log = self.env['rental.contract.audit.log'].sudo()
        for contract in self:
            Log.create({
                'contract_id': contract.id,
                'vehicle_id': contract.vehicle_id.id if contract.vehicle_id else False,
                'customer_id': contract.customer_id.id if contract.customer_id else False,
                'action_type': action_type,
                'field_name': field_name or False,
                'old_value': old_value or False,
                'new_value': new_value or False,
                'description': description,
            })
            if contract.vehicle_id:
                contract.vehicle_id._create_movement_log(
                    'contract_linked',
                    _('Contract %s: %s') % (contract.reference_no or contract.id, description),
                    field_name=field_name or False,
                    old_value=old_value or False,
                    new_value=new_value or False,
                    contract_id=contract,
                )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record, vals in zip(records, vals_list):
            record._create_audit_log('created', _('Contract created'))
            for field_name in record._auditable_fields(vals):
                new_value = record._format_field_value(field_name, record[field_name])
                if new_value:
                    action_type = 'updated'
                    if field_name == 'status':
                        action_type = 'status_changed'
                    elif field_name == 'vehicle_id':
                        action_type = 'vehicle_changed'
                    elif field_name == 'customer_id':
                        action_type = 'customer_changed'
                    elif field_name in DATE_FIELDS:
                        action_type = 'date_changed'
                    elif field_name in FINANCIAL_FIELDS:
                        action_type = 'financial_changed'
                    record._create_audit_log(
                        action_type,
                        _('%s set to %s') % (record._field_label(field_name), new_value),
                        field_name=field_name,
                        old_value='',
                        new_value=new_value,
                    )
        return records

    def write(self, vals):
        tracked = {}
        for contract in self:
            tracked[contract.id] = {}
            for field_name in contract._auditable_fields(vals):
                tracked[contract.id][field_name] = contract._format_field_value(field_name, contract[field_name])
        res = super().write(vals)
        for contract in self:
            for field_name, old_value in tracked.get(contract.id, {}).items():
                new_value = contract._format_field_value(field_name, contract[field_name])
                if old_value == new_value:
                    continue
                action_type = 'updated'
                if field_name == 'status':
                    if contract.status == 'c_return':
                        action_type = 'returned'
                    elif contract.status == 'd_cancel':
                        action_type = 'cancelled'
                    else:
                        action_type = 'status_changed'
                elif field_name == 'vehicle_id':
                    action_type = 'vehicle_changed'
                elif field_name == 'customer_id':
                    action_type = 'customer_changed'
                elif field_name in DATE_FIELDS:
                    action_type = 'date_changed'
                elif field_name in FINANCIAL_FIELDS:
                    action_type = 'financial_changed'
                contract._create_audit_log(
                    action_type,
                    _('%s changed from %s to %s') % (contract._field_label(field_name), old_value or '-', new_value or '-'),
                    field_name=field_name,
                    old_value=old_value,
                    new_value=new_value,
                )
        return res

    @api.depends('audit_log_ids', 'start_date', 'end_date', 'total_days', 'total_vehicle_rent', 'total_extra_charges', 'extra_service_charge', 'damage_amount', 'cancellation_charge')
    def _compute_audit_metrics(self):
        for contract in self:
            hours = 0.0
            if contract.start_date and contract.end_date:
                delta = contract.end_date - contract.start_date
                hours = max(delta.total_seconds() / 3600.0, 0.0)
            contract.audit_log_count = len(contract.audit_log_ids)
            contract.x_contract_total_hours = hours
            contract.x_contract_total_days = contract.total_days or (hours / 24.0)
            contract.x_contract_revenue_total = (contract.total_vehicle_rent or 0.0) + (contract.total_extra_charges or 0.0) + (contract.extra_service_charge or 0.0) + (contract.damage_amount or 0.0) + (contract.cancellation_charge or 0.0)

    def action_open_audit_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contract Audit Logs'),
            'res_model': 'rental.contract.audit.log',
            'view_mode': 'list,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id, 'create': False},
            'target': 'current',
        }

    def action_print_contract_audit(self):
        self.ensure_one()
        return self.env.ref('vehicle_rental_car_audit_reports.action_report_contract_audit').report_action(self)
