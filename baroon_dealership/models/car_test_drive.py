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
    deposit_invoice_id = fields.Many2one('account.move', string='Deposit Invoice', copy=False, tracking=True)
    deposit_refund_id = fields.Many2one('account.move', string='Deposit Refund', copy=False, tracking=True)
    deposit_payment_state = fields.Selection(related='deposit_invoice_id.payment_state', string='Deposit Payment Status', readonly=True)
    deposit_refund_state = fields.Selection(related='deposit_refund_id.payment_state', string='Refund Payment Status', readonly=True)
    deposit_applied_to_sale = fields.Boolean(copy=False, tracking=True)
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
            updates = {}
            if rec.name == 'New':
                updates['name'] = 'TD/%05d' % rec.id
            desired_deposit_collected = bool(rec.deposit_invoice_id and rec.deposit_invoice_id.payment_state == 'paid')
            if rec.deposit_collected != desired_deposit_collected:
                updates['deposit_collected'] = desired_deposit_collected
            if updates:
                super(CarTestDrive, rec.with_context(skip_deposit_sync=True)).write(updates)
            rec.lot_id._baroon_log_change('test_drive', description=_('Test drive created: %s') % rec.name)
        return records

    def _get_or_create_deposit_product(self):
        product = self.env['product.product'].search([('default_code', '=', 'BAROON_TEST_DRIVE_DEPOSIT')], limit=1)
        if product:
            return product
        vals = {
            'name': 'Test Drive Deposit',
            'default_code': 'BAROON_TEST_DRIVE_DEPOSIT',
            'purchase_ok': False,
            'sale_ok': True,
            'list_price': 0.0,
            'standard_price': 0.0,
        }
        if 'type' in self.env['product.template']._fields:
            vals['type'] = 'service'
        elif 'detailed_type' in self.env['product.template']._fields:
            vals['detailed_type'] = 'service'
        if 'invoice_policy' in self.env['product.template']._fields:
            vals['invoice_policy'] = 'order'
        tmpl = self.env['product.template'].create(vals)
        return tmpl.product_variant_id

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

    def action_create_deposit_invoice(self):
        self.ensure_one()
        if self.deposit_invoice_id:
            return self.action_open_deposit_invoice()
        if not self.partner_id:
            raise ValidationError(_('Select a customer before creating the deposit invoice.'))
        if not self.security_deposit:
            raise ValidationError(_('Set a security deposit amount first.'))
        product = self._get_or_create_deposit_product()
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_origin': self.name,
            'car_lot_id': self.lot_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'name': _('%s - Test Drive Deposit') % (self.lot_id.name or self.name),
                'quantity': 1.0,
                'price_unit': self.security_deposit,
            })],
        })
        if move.state == 'draft':
            move.action_post()
        self.deposit_invoice_id = move.id
        self.deposit_collected = move.payment_state == 'paid'
        self.lot_id._baroon_log_change('test_drive', description=_('Deposit invoice created for test drive %s.') % self.name)
        return self.action_open_deposit_invoice()

    def action_open_deposit_invoice(self):
        self.ensure_one()
        if not self.deposit_invoice_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Deposit Invoice'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.deposit_invoice_id.id,
        }

    def action_refund_deposit(self):
        self.ensure_one()
        if not self.deposit_invoice_id:
            raise ValidationError(_('Create the deposit invoice first.'))
        if self.deposit_invoice_id.payment_state != 'paid':
            raise ValidationError(_('The deposit must be fully paid before you can create the refund.'))
        if self.deposit_refund_id:
            return self.action_open_deposit_refund()
        product = self._get_or_create_deposit_product()
        refund_vals = {
            'move_type': 'out_refund',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_origin': self.name,
            'car_lot_id': self.lot_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'name': _('%s - Deposit Refund') % self.name,
                'quantity': 1.0,
                'price_unit': self.security_deposit,
            })],
        }
        if 'reversed_entry_id' in self.env['account.move']._fields:
            refund_vals['reversed_entry_id'] = self.deposit_invoice_id.id
        refund = self.env['account.move'].create(refund_vals)
        if refund.state == 'draft':
            refund.action_post()
        self.deposit_refund_id = refund.id
        self.lot_id._baroon_log_change('test_drive', description=_('Deposit refund created for test drive %s.') % self.name)
        return self.action_open_deposit_refund()

    def action_open_deposit_refund(self):
        self.ensure_one()
        if not self.deposit_refund_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Deposit Refund'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.deposit_refund_id.id,
        }


    def action_register_deposit_payment(self):
        self.ensure_one()
        if not self.deposit_invoice_id:
            raise ValidationError(_('Create the deposit invoice first.'))
        if self.deposit_invoice_id.state == 'draft':
            self.deposit_invoice_id.action_post()
        return self.deposit_invoice_id.action_register_payment()

    def action_register_deposit_refund_payment(self):
        self.ensure_one()
        if not self.deposit_refund_id:
            raise ValidationError(_('Create the deposit refund first.'))
        if self.deposit_refund_id.state == 'draft':
            self.deposit_refund_id.action_post()
        return self.deposit_refund_id.action_register_payment()

    def write(self, vals):
        result = super().write(vals)
        if self.env.context.get('skip_deposit_sync'):
            return result
        for rec in self:
            desired_deposit_collected = bool(rec.deposit_invoice_id and rec.deposit_invoice_id.payment_state == 'paid')
            if rec.deposit_collected != desired_deposit_collected:
                super(CarTestDrive, rec.with_context(skip_deposit_sync=True)).write({
                    'deposit_collected': desired_deposit_collected,
                })
        return result

    def action_apply_deposit_to_sale(self):
        self.ensure_one()
        if not self.sale_order_id:
            raise ValidationError(_('Create a quotation or sale order first.'))
        if not self.deposit_invoice_id:
            raise ValidationError(_('Create the deposit invoice first.'))
        if self.deposit_invoice_id.payment_state != 'paid':
            raise ValidationError(_('The deposit must be fully paid before it can be applied to the sale order.'))
        if self.deposit_refund_id:
            raise ValidationError(_('This deposit has already been refunded.'))
        if self.deposit_applied_to_sale:
            raise ValidationError(_('This deposit has already been applied to the sale order.'))
        product = self._get_or_create_deposit_product()
        self.env['sale.order.line'].create({
            'order_id': self.sale_order_id.id,
            'product_id': product.id,
            'name': _('%s - Applied Test Drive Deposit') % self.name,
            'product_uom_qty': 1.0,
            'price_unit': -(self.security_deposit or 0.0),
        })
        self.deposit_applied_to_sale = True
        self.lot_id._baroon_log_change('test_drive', description=_('Deposit applied to sale order %s from test drive %s.') % (self.sale_order_id.name, self.name))
        return self.action_open_quotation()
