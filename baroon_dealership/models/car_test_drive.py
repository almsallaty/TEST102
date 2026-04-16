from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CarTestDrive(models.Model):
    _name = 'car.test.drive'
    _description = 'Car Test Drive'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_datetime desc, id desc'

    name = fields.Char(default='New', copy=False, readonly=True)
    lot_id = fields.Many2one('stock.lot', required=True, ondelete='cascade', tracking=True)
    partner_id = fields.Many2one('res.partner', required=True, tracking=True)
    lead_id = fields.Many2one('crm.lead', tracking=True)
    sale_order_id = fields.Many2one('sale.order', tracking=True)
    user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user, required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('checked_out', 'Checked Out'),
        ('returned', 'Returned'),
        ('quoted', 'Quoted'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)
    scheduled_datetime = fields.Datetime(required=True, default=fields.Datetime.now, tracking=True)
    expected_return_datetime = fields.Datetime(tracking=True)
    actual_checkout_datetime = fields.Datetime(tracking=True)
    actual_return_datetime = fields.Datetime(tracking=True)
    pickup_location_id = fields.Many2one('stock.location', tracking=True)
    return_location_id = fields.Many2one('stock.location', tracking=True)
    odometer_out = fields.Float(tracking=True)
    odometer_in = fields.Float(tracking=True)
    fuel_out = fields.Float(tracking=True)
    fuel_in = fields.Float(tracking=True)
    driver_license_no = fields.Char(tracking=True)
    passport_no = fields.Char(tracking=True)
    national_id_no = fields.Char(tracking=True)
    insurance_provider = fields.Char(tracking=True)
    insurance_policy_no = fields.Char(tracking=True)
    security_deposit = fields.Monetary(currency_field='currency_id', tracking=True)
    deposit_collected = fields.Boolean(tracking=True)
    currency_id = fields.Many2one(related='lot_id.currency_id', readonly=True)
    scratch_report_out = fields.Text()
    scratch_report_in = fields.Text()
    pickup_checklist = fields.Text()
    return_checklist = fields.Text()
    route_notes = fields.Text()
    note = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.name == 'New':
                rec.name = 'TD/%05d' % rec.id
            rec.lot_id._baroon_log_change('test_drive', description=_('Test drive created: %s') % rec.name)
        return records

    def action_schedule(self):
        self.write({'state': 'scheduled'})

    def action_checkout(self):
        for rec in self:
            if rec.lot_id.car_status not in ('available', 'reserved'):
                raise ValidationError(_('Only available or reserved cars can be checked out for a test drive.'))
            rec.write({'state': 'checked_out', 'actual_checkout_datetime': fields.Datetime.now()})

    def action_return(self):
        self.write({'state': 'returned', 'actual_return_datetime': fields.Datetime.now()})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_create_quotation(self):
        self.ensure_one()
        if self.sale_order_id:
            return self.action_open_quotation()
        order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'opportunity_id': self.lead_id.id,
            'user_id': self.user_id.id,
            'origin': self.name,
        })
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.lot_id.product_id.id,
            'product_uom_qty': 1.0,
            'price_unit': self.lot_id.sale_price or self.lot_id.product_id.lst_price,
            'car_lot_id': self.lot_id.id,
            'name': _('%s • VIN %s') % (
                ' '.join(filter(None, [self.lot_id.car_brand, self.lot_id.car_model, self.lot_id.car_trim])).strip() or self.lot_id.product_id.display_name,
                self.lot_id.name or '-',
            ),
        })
        self.write({'sale_order_id': order.id, 'state': 'quoted'})
        return self.action_open_quotation()

    def action_open_quotation(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
            'name': _('Quotation'),
        }
