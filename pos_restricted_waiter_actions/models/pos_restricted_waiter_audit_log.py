from odoo import api, fields, models


class PosRestrictedWaiterAuditLog(models.Model):
    _name = 'pos.restricted.waiter.audit.log'
    _description = 'POS Restricted Waiter Audit Log'
    _order = 'create_date desc, id desc'

    timestamp = fields.Datetime(default=fields.Datetime.now, required=True, index=True)
    state = fields.Selection([
        ('allowed', 'Allowed'),
        ('denied', 'Denied'),
    ], required=True, default='denied', index=True)
    action = fields.Selection([
        ('decrease_sent_qty', 'Decrease Sent Quantity'),
        ('delete_sent_line', 'Delete Sent Line'),
        ('delete_order', 'Delete Entire Order'),
        ('open_payment', 'Open Payment Screen'),
        ('validate_payment', 'Validate Payment'),
        ('backspace', 'Backspace / Keyboard'),
    ], required=True, index=True)

    employee_id = fields.Many2one('hr.employee', required=False, index=True)
    user_id = fields.Many2one('res.users', required=False, index=True)
    session_id = fields.Many2one('pos.session', required=False, index=True)
    config_id = fields.Many2one('pos.config', required=False, index=True)
    order_ref = fields.Char(index=True)
    table_name = fields.Char()
    product_id = fields.Many2one('product.product', required=False)
    product_name = fields.Char()
    line_uuid = fields.Char()
    old_qty = fields.Float()
    new_qty = fields.Float()
    note = fields.Text()

    @api.model
    def create_from_pos_payload(self, payload):
        payload = payload or {}
        values = {
            'timestamp': fields.Datetime.now(),
            'state': payload.get('state') or 'denied',
            'action': payload.get('action') or 'decrease_sent_qty',
            'employee_id': payload.get('employee_id') or False,
            'user_id': payload.get('user_id') or self.env.user.id,
            'session_id': payload.get('session_id') or False,
            'config_id': payload.get('config_id') or False,
            'order_ref': payload.get('order_ref') or False,
            'table_name': payload.get('table_name') or False,
            'product_id': payload.get('product_id') or False,
            'product_name': payload.get('product_name') or False,
            'line_uuid': payload.get('line_uuid') or False,
            'old_qty': payload.get('old_qty') or 0.0,
            'new_qty': payload.get('new_qty') or 0.0,
            'note': payload.get('note') or False,
        }
        return self.sudo().create(values)
