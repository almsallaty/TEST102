# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for request in records:
            if request.fleet_vehicle_id:
                request.fleet_vehicle_id._create_movement_log(
                    'maintenance_opened',
                    _('Maintenance request created: %s') % (request.name or request.id),
                    maintenance_request_id=request,
                )
        return records

    def write(self, vals):
        before = {}
        for request in self:
            before[request.id] = {
                'stage_id': request.stage_id.display_name if request.stage_id else '',
                'sub_total': request.sub_total if hasattr(request, 'sub_total') else 0.0,
            }
        res = super().write(vals)
        for request in self:
            vehicle = request.fleet_vehicle_id
            if not vehicle:
                continue
            desc = _('Maintenance request updated: %s') % (request.name or request.id)
            event_type = 'maintenance_updated'
            if 'stage_id' in vals:
                old_stage = before[request.id]['stage_id']
                new_stage = request.stage_id.display_name if request.stage_id else ''
                if old_stage != new_stage:
                    desc = _('Maintenance stage changed from %s to %s') % (old_stage or '-', new_stage or '-')
                    event_type = 'maintenance_closed' if getattr(request.stage_id, 'done', False) else 'maintenance_updated'
                    vehicle._create_movement_log(event_type, desc, field_name='stage_id', old_value=old_stage, new_value=new_stage, maintenance_request_id=request)
            if 'sub_total' in vals or 'vehicle_maintenance_part_ids' in vals or 'vehicle_maintenance_service_ids' in vals:
                old_cost = before[request.id]['sub_total']
                new_cost = request.sub_total if hasattr(request, 'sub_total') else 0.0
                if old_cost != new_cost:
                    vehicle._create_movement_log(
                        'maintenance_updated',
                        _('Maintenance cost changed from %s to %s') % (old_cost, new_cost),
                        field_name='sub_total',
                        old_value=str(old_cost),
                        new_value=str(new_cost),
                        maintenance_request_id=request,
                    )
            if not any(k in vals for k in ('stage_id', 'sub_total', 'vehicle_maintenance_part_ids', 'vehicle_maintenance_service_ids')):
                vehicle._create_movement_log('maintenance_updated', desc, maintenance_request_id=request)
        return res
