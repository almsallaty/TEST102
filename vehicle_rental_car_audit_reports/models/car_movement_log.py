# -*- coding: utf-8 -*-
from odoo import fields, models


class CarMovementLog(models.Model):
    _name = 'car.movement.log'
    _description = 'Car Movement Log'
    _order = 'event_datetime desc, id desc'

    vehicle_id = fields.Many2one('fleet.vehicle', required=True, ondelete='cascade', index=True)
    contract_id = fields.Many2one('vehicle.contract', index=True)
    maintenance_request_id = fields.Many2one('maintenance.request', index=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, required=True)
    event_datetime = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    event_type = fields.Selection([
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('status_changed', 'Status Changed'),
        ('contract_linked', 'Contract Linked'),
        ('maintenance_opened', 'Maintenance Opened'),
        ('maintenance_updated', 'Maintenance Updated'),
        ('maintenance_closed', 'Maintenance Closed'),
        ('expense_added', 'Expense Added'),
        ('archived', 'Archived'),
        ('restored', 'Restored'),
    ], required=True, default='updated', index=True)
    field_name = fields.Char(index=True)
    old_value = fields.Text()
    new_value = fields.Text()
    description = fields.Text(required=True)
