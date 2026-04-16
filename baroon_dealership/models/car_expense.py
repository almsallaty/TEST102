from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CarExpense(models.Model):
    _name = 'car.expense'
    _description = 'Car Expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expense_date desc, id desc'

    name = fields.Char(required=True, tracking=True)
    lot_id = fields.Many2one('stock.lot', required=True, ondelete='cascade', index=True, tracking=True)
    product_id = fields.Many2one(related='lot_id.product_id', store=True, readonly=True)
    company_id = fields.Many2one(related='lot_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='lot_id.currency_id', readonly=True)
    expense_type = fields.Selection([
        ('shipping', 'Shipping'),
        ('customs', 'Customs'),
        ('insurance', 'Insurance'),
        ('registration', 'Registration'),
        ('reconditioning', 'Reconditioning'),
        ('parts', 'Parts'),
        ('detailing', 'Detailing'),
        ('marketing', 'Marketing'),
        ('fees', 'Fees'),
        ('other', 'Other'),
    ], default='other', required=True, tracking=True)
    expense_date = fields.Date(default=fields.Date.context_today, required=True, tracking=True)
    amount = fields.Monetary(required=True, tracking=True)
    vendor_id = fields.Many2one('res.partner', tracking=True)
    account_move_id = fields.Many2one('account.move', string='Vendor Bill', tracking=True)
    landed_cost_id = fields.Many2one('stock.landed.cost', tracking=True)
    purchase_order_id = fields.Many2one(related='lot_id.purchase_order_id', store=True, readonly=True)
    note = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
    ], default='approved', tracking=True)

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount < 0:
                raise ValidationError(_('Expense amount cannot be negative.'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec.lot_id._baroon_log_change(
                'expense',
                description=_('Expense added: %s (%s)') % (rec.name, rec.amount),
            )
        return records
