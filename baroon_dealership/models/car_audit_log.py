from odoo import fields, models


class CarAuditLog(models.Model):
    _name = 'car.audit.log'
    _description = 'Car Audit Log'
    _order = 'event_datetime desc, id desc'

    lot_id = fields.Many2one('stock.lot', required=True, ondelete='cascade', index=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, required=True)
    event_datetime = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    change_type = fields.Selection([
        ('create', 'Created'),
        ('update', 'Updated'),
        ('status', 'Status Change'),
        ('movement', 'Movement'),
        ('expense', 'Expense'),
        ('sale', 'Sale'),
        ('test_drive', 'Test Drive'),
    ], default='update', required=True, index=True)
    field_name = fields.Char(index=True)
    old_value = fields.Text()
    new_value = fields.Text()
    description = fields.Text(required=True)
