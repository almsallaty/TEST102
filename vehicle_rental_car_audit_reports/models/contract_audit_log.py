# -*- coding: utf-8 -*-
from odoo import fields, models


class RentalContractAuditLog(models.Model):
    _name = 'rental.contract.audit.log'
    _description = 'Rental Contract Audit Log'
    _order = 'event_datetime desc, id desc'

    contract_id = fields.Many2one('vehicle.contract', required=True, ondelete='cascade', index=True)
    vehicle_id = fields.Many2one('fleet.vehicle', index=True)
    customer_id = fields.Many2one('res.partner', index=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, required=True)
    event_datetime = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    action_type = fields.Selection([
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('status_changed', 'Status Changed'),
        ('vehicle_changed', 'Vehicle Changed'),
        ('customer_changed', 'Customer Changed'),
        ('date_changed', 'Date Changed'),
        ('financial_changed', 'Financial Changed'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    ], required=True, default='updated', index=True)
    field_name = fields.Char(index=True)
    old_value = fields.Text()
    new_value = fields.Text()
    description = fields.Text(required=True)
