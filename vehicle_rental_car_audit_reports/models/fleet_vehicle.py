# -*- coding: utf-8 -*-
from datetime import date, datetime, time, timedelta

from odoo import _, api, fields, models




def _coerce_to_datetime(value):
    if not value:
        return False
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    try:
        return fields.Datetime.to_datetime(value)
    except Exception:
        try:
            d = fields.Date.to_date(value)
            return datetime.combine(d, time.min) if d else False
        except Exception:
            return False


SYSTEM_FIELDS = {
    'id', 'display_name', '__last_update',
    'create_uid', 'create_date', 'write_uid', 'write_date',
    'message_ids', 'message_follower_ids', 'message_partner_ids',
    'message_needaction', 'message_needaction_counter',
    'message_has_error', 'message_has_error_counter',
    'activity_ids', 'activity_state', 'activity_type_icon',
    'activity_summary', 'activity_type_id', 'activity_date_deadline',
}


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    movement_log_ids = fields.One2many('car.movement.log', 'vehicle_id', string='Movement Logs')
    movement_log_count = fields.Integer(compute='_compute_report_metrics')

    x_rental_contract_total = fields.Integer(string='Rental Contracts', compute='_compute_report_metrics')
    x_total_rented_days = fields.Float(string='Total Rented Days', compute='_compute_report_metrics')
    x_total_rented_hours = fields.Float(string='Total Rented Hours', compute='_compute_report_metrics')
    x_total_rental_revenue = fields.Monetary(string='Total Rental Revenue', compute='_compute_report_metrics', currency_field='currency_id')
    x_total_deposit_amount = fields.Monetary(string='Total Deposits', compute='_compute_report_metrics', currency_field='currency_id')
    x_first_rental_date = fields.Datetime(string='First Rental Date', compute='_compute_report_metrics')
    x_last_rental_date = fields.Datetime(string='Last Rental Date', compute='_compute_report_metrics')

    x_maintenance_count = fields.Integer(string='Maintenance Count', compute='_compute_report_metrics')
    x_total_maintenance_cost = fields.Monetary(string='Total Maintenance Cost', compute='_compute_report_metrics', currency_field='currency_id')
    x_last_maintenance_date = fields.Datetime(string='Last Maintenance Date', compute='_compute_report_metrics')
    x_total_downtime_days = fields.Float(string='Maintenance Downtime Days', compute='_compute_report_metrics')
    x_total_downtime_hours = fields.Float(string='Maintenance Downtime Hours', compute='_compute_report_metrics')

    x_total_trip_expense_cost = fields.Monetary(string='Trip Expense Cost', compute='_compute_report_metrics', currency_field='currency_id')
    x_total_operating_cost = fields.Monetary(string='Total Operating Cost', compute='_compute_report_metrics', currency_field='currency_id')
    x_acquisition_cost = fields.Monetary(string='Acquisition Cost', compute='_compute_report_metrics', currency_field='currency_id')
    x_net_profit = fields.Monetary(string='Net Profit', compute='_compute_report_metrics', currency_field='currency_id')
    x_avg_revenue_per_contract = fields.Monetary(string='Average Revenue / Contract', compute='_compute_report_metrics', currency_field='currency_id')
    x_avg_maintenance_cost = fields.Monetary(string='Average Maintenance Cost', compute='_compute_report_metrics', currency_field='currency_id')
    x_utilization_rate = fields.Float(string='Utilization %', compute='_compute_report_metrics')
    x_idle_days = fields.Float(string='Idle Days', compute='_compute_report_metrics')
    x_total_cost_per_day = fields.Monetary(string='Cost per Rented Day', compute='_compute_report_metrics', currency_field='currency_id')
    contract_audit_count = fields.Integer(compute='_compute_report_metrics')

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
        if isinstance(value, timedelta):
            return str(value)
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

    def _create_movement_log(self, event_type, description, field_name=False, old_value=False, new_value=False,
                             contract_id=False, maintenance_request_id=False):
        Log = self.env['car.movement.log'].sudo()
        for vehicle in self:
            Log.create({
                'vehicle_id': vehicle.id,
                'contract_id': contract_id.id if hasattr(contract_id, 'id') else contract_id or False,
                'maintenance_request_id': maintenance_request_id.id if hasattr(maintenance_request_id, 'id') else maintenance_request_id or False,
                'event_type': event_type,
                'field_name': field_name or False,
                'old_value': old_value or False,
                'new_value': new_value or False,
                'description': description,
            })

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record, vals in zip(records, vals_list):
            record._create_movement_log('created', _('Vehicle created'))
            for field_name in record._auditable_fields(vals):
                new_value = record._format_field_value(field_name, record[field_name])
                if new_value:
                    record._create_movement_log(
                        'updated',
                        _('%s set to %s') % (record._field_label(field_name), new_value),
                        field_name=field_name,
                        old_value='',
                        new_value=new_value,
                    )
        return records

    def write(self, vals):
        tracked = {}
        for record in self:
            tracked[record.id] = {}
            for field_name in record._auditable_fields(vals):
                tracked[record.id][field_name] = record._format_field_value(field_name, record[field_name])
            tracked[record.id]['active'] = getattr(record, 'active', True)
        res = super().write(vals)
        for record in self:
            before_active = tracked.get(record.id, {}).get('active', True)
            after_active = getattr(record, 'active', True)
            if before_active and not after_active:
                record._create_movement_log('archived', _('Vehicle archived'))
            elif (not before_active) and after_active:
                record._create_movement_log('restored', _('Vehicle restored'))

            for field_name, old_value in tracked.get(record.id, {}).items():
                if field_name == 'active':
                    continue
                new_value = record._format_field_value(field_name, record[field_name])
                if old_value == new_value:
                    continue
                event_type = 'updated'
                if field_name == 'status':
                    event_type = 'status_changed'
                description = _('%s changed from %s to %s') % (
                    record._field_label(field_name), old_value or '-', new_value or '-'
                )
                record._create_movement_log(
                    event_type,
                    description,
                    field_name=field_name,
                    old_value=old_value,
                    new_value=new_value,
                )
        return res

    @api.depends('movement_log_ids', 'movement_log_ids.event_datetime')
    def _compute_report_metrics(self):
        Contract = self.env['vehicle.contract']
        Maintenance = self.env['maintenance.request']
        Expense = self.env['hr.expense']
        ContractLog = self.env['rental.contract.audit.log']
        now = fields.Datetime.now()
        for vehicle in self:
            contracts = Contract.search([('vehicle_id', '=', vehicle.id)])
            maintenance_requests = Maintenance.search([('fleet_vehicle_id', '=', vehicle.id)])
            expenses = Expense.search([('fleet_vehicle_id', '=', vehicle.id)])
            vehicle_contract_logs = ContractLog.search_count([('vehicle_id', '=', vehicle.id)])

            total_days = 0.0
            total_hours = 0.0
            total_revenue = 0.0
            total_deposit = 0.0
            first_rental = False
            last_rental = False
            for contract in contracts:
                diff_hours = 0.0
                if contract.start_date and contract.end_date:
                    end_dt = _coerce_to_datetime(contract.end_date)
                    start_dt = _coerce_to_datetime(contract.start_date)
                    delta = end_dt - start_dt if end_dt and start_dt else timedelta(0)
                    diff_hours = max(delta.total_seconds() / 3600.0, 0.0)
                total_hours += diff_hours
                total_days += contract.total_days or (diff_hours / 24.0)
                total_revenue += (contract.total_vehicle_rent or 0.0) + (contract.total_extra_charges or 0.0) + (contract.extra_service_charge or 0.0) + (contract.damage_amount or 0.0) + (contract.cancellation_charge or 0.0)
                total_deposit += contract.total_deposit or contract.deposit or 0.0
                contract_start = _coerce_to_datetime(contract.start_date)
                if contract_start and (not first_rental or contract_start < first_rental):
                    first_rental = contract_start
                if contract_start and (not last_rental or contract_start > last_rental):
                    last_rental = contract_start

            total_maintenance_cost = sum((req.sub_total or 0.0) for req in maintenance_requests)
            last_maintenance_date = False
            downtime_hours = 0.0
            for req in maintenance_requests:
                req_dt = _coerce_to_datetime(req.request_date)
                if req_dt and (not last_maintenance_date or req_dt > last_maintenance_date):
                    last_maintenance_date = req_dt
                if req.request_date:
                    end_dt = _coerce_to_datetime(req.close_date) or _coerce_to_datetime(now)
                    start_dt = _coerce_to_datetime(req.request_date)
                    if end_dt and start_dt:
                        delta = end_dt - start_dt
                        downtime_hours += max(delta.total_seconds() / 3600.0, 0.0)

            trip_expense_cost = sum((exp.total_amount or 0.0) for exp in expenses)
            acquisition_cost = getattr(vehicle, 'acquisition_value', 0.0) or 0.0
            operating_cost = total_maintenance_cost + trip_expense_cost
            net_profit = total_revenue - operating_cost - acquisition_cost
            avg_revenue = total_revenue / len(contracts) if contracts else 0.0
            avg_maintenance = total_maintenance_cost / len(maintenance_requests) if maintenance_requests else 0.0
            utilization = 0.0
            idle_days = 0.0
            if vehicle.create_date:
                total_elapsed_days = max((fields.Datetime.to_datetime(now) - fields.Datetime.to_datetime(vehicle.create_date)).total_seconds() / 86400.0, 0.0)
                utilization = (total_days / total_elapsed_days * 100.0) if total_elapsed_days else 0.0
                idle_days = max(total_elapsed_days - total_days - (downtime_hours / 24.0), 0.0)

            vehicle.movement_log_count = len(vehicle.movement_log_ids)
            vehicle.contract_audit_count = vehicle_contract_logs
            vehicle.x_rental_contract_total = len(contracts)
            vehicle.x_total_rented_days = total_days
            vehicle.x_total_rented_hours = total_hours
            vehicle.x_total_rental_revenue = total_revenue
            vehicle.x_total_deposit_amount = total_deposit
            vehicle.x_first_rental_date = first_rental
            vehicle.x_last_rental_date = last_rental
            vehicle.x_maintenance_count = len(maintenance_requests)
            vehicle.x_total_maintenance_cost = total_maintenance_cost
            vehicle.x_last_maintenance_date = last_maintenance_date
            vehicle.x_total_downtime_hours = downtime_hours
            vehicle.x_total_downtime_days = downtime_hours / 24.0
            vehicle.x_total_trip_expense_cost = trip_expense_cost
            vehicle.x_total_operating_cost = operating_cost
            vehicle.x_acquisition_cost = acquisition_cost
            vehicle.x_net_profit = net_profit
            vehicle.x_avg_revenue_per_contract = avg_revenue
            vehicle.x_avg_maintenance_cost = avg_maintenance
            vehicle.x_utilization_rate = utilization
            vehicle.x_idle_days = idle_days
            vehicle.x_total_cost_per_day = (operating_cost / total_days) if total_days else 0.0

    def action_open_movement_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Car Movement Logs'),
            'res_model': 'car.movement.log',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id, 'create': False},
            'target': 'current',
        }

    def _print_report(self, xmlid):
        self.ensure_one()
        return self.env.ref(xmlid).report_action(self)

    def action_print_car_profile(self):
        return self._print_report('vehicle_rental_car_audit_reports.action_report_car_profile')

    def action_print_car_history(self):
        return self._print_report('vehicle_rental_car_audit_reports.action_report_car_history')

    def action_print_car_rental(self):
        return self._print_report('vehicle_rental_car_audit_reports.action_report_car_rental')

    def action_print_car_maintenance(self):
        return self._print_report('vehicle_rental_car_audit_reports.action_report_car_maintenance')

    def action_print_car_financial(self):
        return self._print_report('vehicle_rental_car_audit_reports.action_report_car_financial')

    def action_print_car_utilization(self):
        return self._print_report('vehicle_rental_car_audit_reports.action_report_car_utilization')

    def action_print_car_documents(self):
        return self._print_report('vehicle_rental_car_audit_reports.action_report_car_documents')

    def action_print_car_customer_history(self):
        return self._print_report('vehicle_rental_car_audit_reports.action_report_car_customer_history')

    def action_print_car_downtime(self):
        return self._print_report('vehicle_rental_car_audit_reports.action_report_car_downtime')

    def action_print_fleet_summary(self):
        return self._print_report('vehicle_rental_car_audit_reports.action_report_fleet_summary')
