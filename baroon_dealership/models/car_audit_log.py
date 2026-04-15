from odoo import fields, models


class CarAuditLog(models.Model):
    _name = 'car.audit.log'
    _description = 'Car Audit Log'
    _order = 'change_datetime desc, id desc'

    lot_id = fields.Many2one('stock.lot', string='Car', required=True, ondelete='cascade', index=True)
    change_datetime = fields.Datetime(default=fields.Datetime.now, required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Changed By')
    field_name = fields.Char(required=True)
    field_label = fields.Char(required=True)
    old_value = fields.Text()
    new_value = fields.Text()
    message = fields.Text()
    company_id = fields.Many2one(related='lot_id.company_id', store=True, readonly=True)
