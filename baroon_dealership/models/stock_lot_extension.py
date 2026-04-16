from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockLotDealershipExtension(models.Model):
    _inherit = 'stock.lot'

    kanban_image = fields.Image(string='Kanban Image')
    current_location_id = fields.Many2one('stock.location', compute='_compute_current_location_id', string='Current Location', store=True)
    gallery_image_ids = fields.One2many('car.lot.image', 'lot_id', string='Gallery Images')
    expense_ids = fields.One2many('car.expense', 'lot_id', string='Expenses')
    expense_total = fields.Monetary(currency_field='currency_id', compute='_compute_extra_costs', store=True)
    landed_cost_total = fields.Monetary(currency_field='currency_id', compute='_compute_extra_costs', store=True)
    vendor_bill_ids = fields.One2many('account.move', 'car_lot_id', string='Related Bills')
    vendor_bill_count = fields.Integer(compute='_compute_dealership_counts')
    landed_cost_ids = fields.Many2many('stock.landed.cost', 'stock_landed_cost_car_lot_rel', 'lot_id', 'landed_cost_id', string='Landed Costs')
    landed_cost_count = fields.Integer(compute='_compute_dealership_counts')
    transfer_count = fields.Integer(compute='_compute_dealership_counts')
    location_history_ids = fields.One2many('car.location.history', 'lot_id', string='Location History')
    audit_log_ids = fields.One2many('car.audit.log', 'lot_id', string='Audit Trail')
    audit_log_count = fields.Integer(compute='_compute_dealership_counts')
    test_drive_ids = fields.One2many('car.test.drive', 'lot_id', string='Test Drives')
    test_drive_count = fields.Integer(compute='_compute_dealership_counts')
    invoice_count = fields.Integer(compute='_compute_dealership_counts')
    last_movement_date = fields.Datetime(compute='_compute_dealership_counts')
    movement_command = fields.Char(compute='_compute_movement_command')

    @api.depends('expense_ids.amount', 'expense_ids.state', 'expense_ids.landed_cost_id', 'landed_cost_ids.amount_total', 'landed_cost_ids.state', 'landed_cost_ids.car_lot_ids')
    def _compute_extra_costs(self):
        for lot in self:
            approved = lot.expense_ids.filtered(lambda e: e.state == 'approved')
            lot.expense_total = sum(approved.filtered(lambda e: not e.landed_cost_id).mapped('amount'))
            landed_from_expenses = sum(approved.filtered(lambda e: e.landed_cost_id).mapped('amount'))
            landed_from_records = 0.0
            for cost in lot.landed_cost_ids.filtered(lambda c: c.state == 'done' and lot in c.car_lot_ids):
                count = len(cost.car_lot_ids) or 1
                landed_from_records += (cost.amount_total or 0.0) / count
            lot.landed_cost_total = max(landed_from_expenses, landed_from_records)

    @api.depends('vendor_bill_ids', 'landed_cost_ids', 'location_history_ids', 'audit_log_ids', 'test_drive_ids', 'expense_ids.account_move_id')
    def _compute_dealership_counts(self):
        for lot in self:
            vendor_bills = (lot.vendor_bill_ids | lot.expense_ids.mapped('account_move_id')).filtered(lambda m: m and m.move_type in ('in_invoice', 'in_refund'))
            customer_moves = lot.vendor_bill_ids.filtered(lambda m: m and m.move_type in ('out_invoice', 'out_refund'))
            landed_costs = (lot.landed_cost_ids | lot.expense_ids.mapped('landed_cost_id')).filtered(lambda c: c)
            lot.vendor_bill_count = len(vendor_bills)
            sale_invoices = lot.sale_order_id.invoice_ids.filtered(lambda m: m.move_type in ('out_invoice', 'out_refund')) if lot.sale_order_id else self.env['account.move']
            lot.invoice_count = len((customer_moves | sale_invoices))
            lot.landed_cost_count = len(landed_costs)
            lot.transfer_count = len(lot.location_history_ids.filtered(lambda h: h.movement_type == 'internal'))
            lot.audit_log_count = len(lot.audit_log_ids)
            lot.test_drive_count = len(lot.test_drive_ids)
            lot.last_movement_date = lot.location_history_ids[:1].movement_date if lot.location_history_ids else False

    @api.depends('current_location_id', 'buyer_id', 'sale_order_id', 'car_status')
    def _compute_movement_command(self):
        for lot in self:
            if lot.car_status == 'delivered' and lot.buyer_id:
                lot.movement_command = _('Deliver to %s') % lot.buyer_id.display_name
            elif lot.current_location_id:
                lot.movement_command = _('Currently in %s') % lot.current_location_id.display_name
            else:
                lot.movement_command = False

    @api.depends('car_image', 'gallery_image_ids.avatar')
    def _compute_display_cover_image(self):
        for lot in self:
            lot.display_cover_image = lot.car_image or (lot.gallery_image_ids[:1].avatar if lot.gallery_image_ids else False)

    @api.depends('purchase_cost', 'landed_cost', 'landed_cost_total', 'reconditioning_cost', 'expense_total', 'sale_price')
    def _compute_profitability(self):
        for lot in self:
            lot.total_cost = (lot.purchase_cost or 0.0) + (lot.landed_cost or 0.0) + (lot.landed_cost_total or 0.0) + (lot.reconditioning_cost or 0.0) + (lot.expense_total or 0.0)
            lot.gross_margin = (lot.sale_price or 0.0) - lot.total_cost
            lot.margin_percent = lot.total_cost and ((lot.gross_margin / lot.total_cost) * 100.0) or 0.0

    @api.depends('name', 'display_name_website', 'display_cover_image', 'sale_price', 'car_brand', 'car_model', 'year')
    def _compute_is_car_profile_complete(self):
        for lot in self:
            if not lot.is_car_vehicle:
                lot.is_car_profile_complete = True
                continue
            lot.is_car_profile_complete = bool(
                lot.name and lot.display_name_website and lot.display_cover_image and lot.sale_price and lot.car_brand and lot.car_model and lot.year
            )

    @api.constrains('name')
    def _check_vin_length(self):
        for lot in self.filtered('is_car_vehicle'):
            vin = (lot.name or '').strip()
            if vin and not (17 <= len(vin) <= 23):
                raise ValidationError(_('VIN / serial length must be between 17 and 23 characters.'))

    def _baroon_normalize_vals(self, vals):
        vals = dict(vals)
        for field_name in ('name', 'engine_number', 'plate_number'):
            if field_name in vals and vals[field_name]:
                vals[field_name] = str(vals[field_name]).strip().upper()
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [self._baroon_normalize_vals(vals) for vals in vals_list]
        records = super().create(vals_list)
        for record in records.filtered('is_car_vehicle'):
            record._baroon_log_change('create', description=_('Car record created.'))
        return records

    def write(self, vals):
        vals = self._baroon_normalize_vals(vals)
        tracked_fields = {'name', 'engine_number', 'plate_number', 'sale_price', 'minimum_sale_price', 'purchase_cost', 'landed_cost', 'reconditioning_cost', 'car_status', 'branch_location', 'buyer_id', 'salesperson_id', 'purchase_partner_id', 'shipping_reference', 'expected_arrival_date', 'arrival_date', 'customs_release_date'}
        before = {}
        if tracked_fields.intersection(vals.keys()):
            for rec in self:
                before[rec.id] = {f: rec[f] for f in tracked_fields if f in vals}
        result = super().write(vals)
        if before:
            for rec in self:
                previous = before.get(rec.id, {})
                for field_name, old_value in previous.items():
                    new_value = rec[field_name]
                    if old_value != new_value:
                        rec._baroon_log_change(
                            'status' if field_name == 'car_status' else 'update',
                            field_name=field_name,
                            old_value=old_value,
                            new_value=new_value,
                            description=_('%s changed on the car record.') % rec._fields[field_name].string,
                        )
        return result

    def _baroon_log_change(self, change_type, field_name=False, old_value=False, new_value=False, description=False):
        self.ensure_one()
        self.env['car.audit.log'].sudo().create({
            'lot_id': self.id,
            'change_type': change_type,
            'field_name': field_name or False,
            'old_value': old_value if old_value not in (False, None) else False,
            'new_value': new_value if new_value not in (False, None) else False,
            'description': description or _('Car record updated.'),
        })

    def action_transfer_car(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Transfer Car'),
            'res_model': 'car.transfer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_lot_id': self.id},
        }

    def action_view_transfers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Car Movement History'),
            'res_model': 'car.location.history',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'context': {'default_lot_id': self.id},
        }

    def action_view_expenses(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Car Expenses'),
            'res_model': 'car.expense',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'context': {'default_lot_id': self.id},
        }

    def action_view_test_drives(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Test Drives'),
            'res_model': 'car.test.drive',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'context': {'default_lot_id': self.id, 'default_partner_id': self.reservation_partner_id.id or self.buyer_id.id},
        }

    def action_create_test_drive(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Test Drive'),
            'res_model': 'car.test.drive',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_lot_id': self.id,
                'default_pickup_location_id': self.current_location_id.id,
                'default_return_location_id': self.current_location_id.id,
            },
        }

    def action_view_vendor_bills(self):
        self.ensure_one()
        linked_bills = (self.vendor_bill_ids | self.expense_ids.mapped('account_move_id')).filtered(lambda m: m.move_type in ('in_invoice', 'in_refund'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Bills'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', linked_bills.ids)],
            'context': {'default_car_lot_id': self.id, 'default_move_type': 'in_invoice'},
        }

    def action_view_landed_costs(self):
        self.ensure_one()
        linked_costs = (self.landed_cost_ids | self.expense_ids.mapped('landed_cost_id')).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Landed Costs'),
            'res_model': 'stock.landed.cost',
            'view_mode': 'list,form',
            'domain': ['|', ('id', 'in', linked_costs), ('car_lot_ids', 'in', self.id)],
            'context': {
                'default_car_lot_ids': [self.id],
            },
        }

    def action_view_audit_log(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Audit Trail'),
            'res_model': 'car.audit.log',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
        }
