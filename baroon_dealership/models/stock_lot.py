from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockLot(models.Model):
    _inherit = ['stock.lot', 'mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(default=True, tracking=True)
    kanban_image = fields.Image(string='Kanban Image')
    car_image = fields.Image(string='Profile Cover Image')
    car_image_ids = fields.One2many('car.lot.image', 'lot_id', string='Gallery Images')
    image_count = fields.Integer(compute='_compute_related_counts')
    notes = fields.Text(string='Notes')

    car_brand = fields.Char(string='Brand', tracking=True, index=True)
    car_model = fields.Char(string='Model', tracking=True, index=True)
    car_trim = fields.Char(string='Trim', tracking=True)
    body_style = fields.Selection([
        ('sedan', 'Sedan'), ('suv', 'SUV'), ('coupe', 'Coupe'), ('pickup', 'Pickup'),
        ('hatchback', 'Hatchback'), ('wagon', 'Wagon'), ('van', 'Van'), ('other', 'Other'),
    ], tracking=True)
    seats = fields.Integer(tracking=True)
    doors = fields.Integer(tracking=True)
    drivetrain = fields.Selection([
        ('fwd', 'FWD'), ('rwd', 'RWD'), ('awd', 'AWD'), ('4wd', '4WD'), ('other', 'Other'),
    ], tracking=True)
    engine_number = fields.Char(tracking=True, index=True)
    plate_number = fields.Char(tracking=True, index=True)
    year = fields.Integer(tracking=True, index=True)
    mileage = fields.Float(tracking=True)
    horse_power = fields.Integer(tracking=True)
    engine_size = fields.Char(tracking=True)
    fuel_type = fields.Selection([
        ('gasoline', 'Gasoline'), ('diesel', 'Diesel'), ('hybrid', 'Hybrid'), ('electric', 'Electric'), ('other', 'Other'),
    ], tracking=True)
    gearbox_type = fields.Selection([
        ('manual', 'Manual'), ('automatic', 'Automatic'), ('cvt', 'CVT'), ('other', 'Other'),
    ], tracking=True)
    condition = fields.Selection([
        ('new', 'New'), ('used', 'Used'), ('damaged', 'Damaged'), ('under_preparation', 'Under Preparation'),
    ], default='new', tracking=True)
    exterior_color_ids = fields.Many2many('car.exterior.color', 'stock_lot_exterior_color_rel', 'lot_id', 'color_id', string='Exterior Colors', tracking=True)
    interior_color_ids = fields.Many2many('car.interior.color', 'stock_lot_interior_color_rel', 'lot_id', 'color_id', string='Interior Colors', tracking=True)

    purchase_partner_id = fields.Many2one('res.partner', string='Vendor', tracking=True)
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', tracking=True)
    purchase_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line', tracking=True)
    purchase_date = fields.Date(tracking=True)
    shipping_reference = fields.Char(tracking=True)
    shipment_booking_reference = fields.Char(tracking=True)
    container_reference = fields.Char(tracking=True)
    port_of_loading = fields.Char(tracking=True)
    destination_port = fields.Char(tracking=True)
    expected_arrival_date = fields.Date(tracking=True)
    arrival_date = fields.Date(tracking=True)
    customs_release_date = fields.Date(tracking=True)
    shipping_notes = fields.Text(string='Shipment Notes')
    branch_location = fields.Char(string='Display / Yard Label', tracking=True)

    sale_price = fields.Monetary(currency_field='currency_id', tracking=True)
    minimum_sale_price = fields.Monetary(currency_field='currency_id', tracking=True)
    purchase_cost = fields.Monetary(currency_field='currency_id', tracking=True)
    landed_cost = fields.Monetary(currency_field='currency_id', compute='_compute_cost_fields', store=True)
    reconditioning_cost = fields.Monetary(currency_field='currency_id', compute='_compute_cost_fields', store=True)
    extra_expense_total = fields.Monetary(currency_field='currency_id', compute='_compute_cost_fields', store=True)
    shipping_cost = fields.Monetary(currency_field='currency_id', compute='_compute_cost_fields', store=True)
    customs_cost = fields.Monetary(currency_field='currency_id', compute='_compute_cost_fields', store=True)
    total_cost = fields.Monetary(currency_field='currency_id', compute='_compute_cost_fields', store=True)
    gross_margin = fields.Monetary(currency_field='currency_id', compute='_compute_cost_fields', store=True)
    margin_percent = fields.Float(compute='_compute_cost_fields', store=True)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)

    expense_ids = fields.One2many('car.expense', 'lot_id', string='Expenses')
    expense_count = fields.Integer(compute='_compute_related_counts')
    location_history_ids = fields.One2many('car.location.history', 'lot_id', string='Location History')
    location_history_count = fields.Integer(compute='_compute_related_counts')
    audit_log_ids = fields.One2many('car.audit.log', 'lot_id', string='Audit Logs')
    audit_log_count = fields.Integer(compute='_compute_related_counts')
    test_drive_ids = fields.One2many('car.test.drive', 'lot_id', string='Test Drives')
    test_drive_count = fields.Integer(compute='_compute_related_counts')
    landed_cost_record_ids = fields.Many2many('stock.landed.cost', 'baroon_landed_cost_lot_rel', 'lot_id', 'cost_id', string='Landed Cost Records', readonly=True)
    vendor_bill_ids = fields.Many2many('account.move', compute='_compute_vendor_bill_ids', string='Vendor Bills')
    vendor_bill_count = fields.Integer(compute='_compute_vendor_bill_ids')

    car_status = fields.Selection([
        ('draft', 'Draft'),
        ('incoming', 'Incoming'),
        ('in_shipment', 'In Shipment'),
        ('customs', 'Customs'),
        ('received', 'Received'),
        ('in_preparation', 'In Preparation'),
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('sold', 'Sold'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True, index=True)

    reservation_order_id = fields.Many2one('sale.order', string='Reserved By Order', copy=False, tracking=True)
    reservation_partner_id = fields.Many2one('res.partner', string='Reserved For', copy=False, tracking=True)
    reserved_until = fields.Date(copy=False, tracking=True)
    sale_order_id = fields.Many2one('sale.order', string='Sold On Order', copy=False, tracking=True)
    buyer_id = fields.Many2one('res.partner', string='Buyer', copy=False, tracking=True)
    salesperson_id = fields.Many2one('res.users', string='Salesperson', copy=False, tracking=True)
    sold_date = fields.Datetime(copy=False, tracking=True)
    delivered_date = fields.Datetime(copy=False, tracking=True)

    crm_lead_ids = fields.One2many('crm.lead', 'car_lot_id', string='Opportunities')
    crm_lead_count = fields.Integer(compute='_compute_related_counts')
    quotation_count = fields.Integer(compute='_compute_related_counts')
    transfer_count = fields.Integer(compute='_compute_related_counts')
    dashboard_label = fields.Char(compute='_compute_dashboard_fields')
    inventory_state_label = fields.Char(compute='_compute_dashboard_fields')
    website_display_status = fields.Char(compute='_compute_dashboard_fields')
    days_in_stock = fields.Integer(compute='_compute_inventory_kpis', store=True, string='Days in Stock')
    days_to_arrival = fields.Integer(compute='_compute_inventory_kpis', store=True, string='Days to Arrival')
    arriving_soon = fields.Boolean(compute='_compute_inventory_kpis', store=True, index=True, string='Arriving Soon')
    current_location_id = fields.Many2one('stock.location', compute='_compute_current_location_id', store=True, string='Current Location')

    is_car_vehicle = fields.Boolean(related='product_id.product_tmpl_id.is_car_vehicle', string='Is Car Vehicle', readonly=True)
    is_car_profile_complete = fields.Boolean(compute='_compute_is_car_profile_complete', store=True)

    website_published = fields.Boolean(default=False, tracking=True)
    website_sequence = fields.Integer(default=10)
    website_short_description = fields.Text()
    website_description = fields.Html()
    website_url = fields.Char(compute='_compute_website_url')
    display_name_website = fields.Char(compute='_compute_display_name_website', store=True)
    display_cover_image = fields.Image(compute='_compute_display_cover_image')

    _sql_constraints = [
        ('engine_number_uniq', 'unique(engine_number)', 'Engine number must be unique.'),
    ]

    _STATE_TRANSITIONS = {
        'draft': ['incoming', 'cancelled'],
        'incoming': ['in_shipment', 'received', 'cancelled'],
        'in_shipment': ['customs', 'received', 'cancelled'],
        'customs': ['received', 'cancelled'],
        'received': ['in_preparation', 'available', 'cancelled'],
        'in_preparation': ['available', 'cancelled'],
        'available': ['reserved', 'sold', 'cancelled', 'in_preparation'],
        'reserved': ['available', 'sold', 'cancelled'],
        'sold': ['delivered'],
        'delivered': [],
        'cancelled': ['incoming', 'draft'],
    }

    @api.model
    def _param_bool(self, key, default=True):
        return self.env['ir.config_parameter'].sudo().get_param(key, 'True' if default else 'False') == 'True'

    @api.model
    def _param_int(self, key, default=0):
        try:
            return int(self.env['ir.config_parameter'].sudo().get_param(key, default))
        except Exception:
            return default

    @api.depends('car_image', 'car_image_ids.avatar')
    def _compute_display_cover_image(self):
        for lot in self:
            lot.display_cover_image = lot.car_image or (lot.car_image_ids[:1].avatar if lot.car_image_ids else False)

    @api.depends('car_brand', 'car_model', 'car_trim', 'year', 'name', 'product_id')
    def _compute_display_name_website(self):
        for lot in self:
            title = ' '.join(filter(None, [lot.car_brand, lot.car_model, lot.car_trim])).strip()
            title = title or lot.product_id.display_name or _('Car')
            parts = [title]
            if lot.year:
                parts.append(str(lot.year))
            if lot.name:
                parts.append(_('VIN %s') % lot.name)
            lot.display_name_website = ' • '.join(filter(None, parts))

    def _compute_website_url(self):
        for lot in self:
            lot.website_url = '/cars/%s' % lot.id if lot.id else False


    @api.depends('expense_ids.account_move_id', 'expense_ids.account_move_id.state')
    def _compute_vendor_bill_ids(self):
        for lot in self:
            direct = self.env['account.move'].sudo().search([('dealership_lot_ids', 'in', lot.id)])
            bills = direct | lot.expense_ids.mapped('account_move_id')
            lot.vendor_bill_ids = bills
            lot.vendor_bill_count = len(bills)

    @api.depends('crm_lead_ids', 'expense_ids', 'location_history_ids', 'audit_log_ids', 'car_image_ids', 'test_drive_ids')
    def _compute_related_counts(self):
        sale_line_model = self.env['sale.order.line'].sudo().with_context(active_test=False)
        picking_model = self.env['stock.picking'].sudo().with_context(active_test=False)
        for lot in self:
            lot.crm_lead_count = len(lot.crm_lead_ids)
            lot.quotation_count = sale_line_model.search_count([('car_lot_id', '=', lot.id), ('display_type', '=', False)])
            lot.expense_count = len(lot.expense_ids)
            lot.location_history_count = len(lot.location_history_ids)
            lot.audit_log_count = len(lot.audit_log_ids)
            lot.test_drive_count = len(lot.test_drive_ids)
            pickings = self.env['stock.move.line'].sudo().search([('lot_id', '=', lot.id), ('picking_id', '!=', False)]).mapped('picking_id')
            lot.transfer_count = len(pickings)
            lot.image_count = len(lot.car_image_ids)

    @api.depends('car_status', 'arriving_soon', 'days_to_arrival', 'car_brand', 'car_model', 'car_trim', 'name')
    def _compute_dashboard_fields(self):
        labels = dict(self._fields['car_status'].selection)
        for lot in self:
            title = ' '.join(filter(None, [lot.car_brand, lot.car_model, lot.car_trim])).strip() or lot.product_id.display_name or _('Car')
            lot.dashboard_label = '%s • VIN %s' % (title, lot.name or '-')
            if lot.arriving_soon and lot.days_to_arrival >= 0:
                state = _('Arrives in %s days') % lot.days_to_arrival
            elif lot.car_status in ('incoming', 'in_shipment', 'customs', 'received', 'in_preparation'):
                state = _('Pipeline')
            else:
                state = labels.get(lot.car_status, lot.car_status or '')
            lot.inventory_state_label = state
            lot.website_display_status = state

    @api.depends('purchase_date', 'expected_arrival_date', 'car_status')
    def _compute_inventory_kpis(self):
        today = fields.Date.today()
        for lot in self:
            lot.days_in_stock = 0
            lot.days_to_arrival = 0
            lot.arriving_soon = False
            if lot.purchase_date:
                lot.days_in_stock = max((today - lot.purchase_date).days, 0)
            if lot.expected_arrival_date and lot.car_status in ('incoming', 'in_shipment', 'customs', 'received', 'in_preparation'):
                lot.days_to_arrival = (lot.expected_arrival_date - today).days
                lot.arriving_soon = 0 <= lot.days_to_arrival <= 30

    @api.depends('quant_ids.location_id', 'quant_ids.quantity', 'quant_ids.reserved_quantity')
    def _compute_current_location_id(self):
        for lot in self:
            quants = lot.quant_ids.filtered(lambda q: q.quantity > 0 and q.location_id.usage == 'internal')
            lot.current_location_id = quants[:1].location_id if quants else False

    @api.depends('name', 'product_id', 'car_brand', 'car_model', 'year', 'condition', 'sale_price', 'display_cover_image', 'car_status')
    def _compute_is_car_profile_complete(self):
        for lot in self:
            if not lot.is_car_vehicle:
                lot.is_car_profile_complete = True
                continue
            lot.is_car_profile_complete = bool(
                lot.name and lot.product_id and lot.car_brand and lot.car_model and lot.year and lot.condition and lot.sale_price and lot.display_cover_image and lot.car_status
            )

    @api.depends(
        'purchase_cost',
        'sale_price',
        'expense_ids.amount', 'expense_ids.expense_type',
        'landed_cost_record_ids.state', 'landed_cost_record_ids.cost_lines.price_unit', 'landed_cost_record_ids.dealership_lot_ids'
    )
    def _compute_cost_fields(self):
        for lot in self:
            shipping = sum(lot.expense_ids.filtered(lambda e: e.expense_type == 'shipping').mapped('amount'))
            customs = sum(lot.expense_ids.filtered(lambda e: e.expense_type == 'customs').mapped('amount'))
            reconditioning = sum(lot.expense_ids.filtered(lambda e: e.expense_type == 'reconditioning').mapped('amount'))
            extra = sum(lot.expense_ids.filtered(lambda e: e.expense_type not in ('shipping', 'customs', 'reconditioning')).mapped('amount'))
            landed = 0.0
            for cost in lot.landed_cost_record_ids.filtered(lambda c: c.state == 'done'):
                allocation = cost._get_dealership_allocation_map()
                landed += allocation.get(lot.id, 0.0)
            lot.shipping_cost = shipping
            lot.customs_cost = customs
            lot.reconditioning_cost = reconditioning
            lot.extra_expense_total = extra
            lot.landed_cost = landed
            lot.total_cost = (lot.purchase_cost or 0.0) + shipping + customs + reconditioning + extra + landed
            lot.gross_margin = (lot.sale_price or 0.0) - lot.total_cost
            lot.margin_percent = lot.total_cost and ((lot.gross_margin / lot.total_cost) * 100.0) or 0.0

    @api.constrains('year')
    def _check_year(self):
        current_year = fields.Date.today().year + 1
        for lot in self:
            if lot.year and (lot.year < 1900 or lot.year > current_year):
                raise ValidationError(_('Year must be between 1900 and %s.') % current_year)

    @api.constrains('horse_power', 'mileage', 'sale_price', 'minimum_sale_price', 'purchase_cost')
    def _check_numeric_values(self):
        for lot in self:
            values = {
                _('Horse power'): lot.horse_power,
                _('Mileage'): lot.mileage,
                _('Sale price'): lot.sale_price,
                _('Minimum sale price'): lot.minimum_sale_price,
                _('Purchase cost'): lot.purchase_cost,
            }
            for label, value in values.items():
                if value is not None and value < 0:
                    raise ValidationError(_('%s cannot be negative.') % label)
            if lot.minimum_sale_price and lot.sale_price and lot.minimum_sale_price > lot.sale_price:
                raise ValidationError(_('Minimum sale price cannot be greater than sale price.'))

    @api.constrains('product_id')
    def _check_product_tracking(self):
        for lot in self:
            if lot.is_car_vehicle and lot.product_id and lot.product_id.tracking != 'serial':
                raise ValidationError(_('The car product must use tracking by unique serial number.'))

    @api.constrains('website_published', 'car_status', 'display_cover_image', 'is_car_profile_complete')
    def _check_website_publication_rules(self):
        for lot in self:
            if not lot.is_car_vehicle or not lot.website_published:
                continue
            if lot.car_status in ('sold', 'delivered'):
                raise ValidationError(_('Sold or delivered cars cannot be published on the website.'))
            if not lot.display_cover_image:
                raise ValidationError(_('Upload at least one profile image before publishing the car on the website.'))
            if self._param_bool('baroon_dealership.require_complete_profile', True) and not lot.is_car_profile_complete:
                raise ValidationError(_('Complete the car profile before publishing it on the website.'))

    @api.constrains('name', 'is_car_vehicle')
    def _check_vin_length(self):
        for lot in self:
            if lot.is_car_vehicle and lot.name:
                size = len((lot.name or '').strip())
                if size < 17 or size > 23:
                    raise ValidationError(_('VIN / serial number must be between 17 and 23 characters.'))

    @api.constrains('name', 'engine_number', 'plate_number')
    def _check_duplicates_including_archived(self):
        for lot in self:
            if not lot.is_car_vehicle:
                continue
            checks = [(_('VIN'), 'name', lot.name), (_('engine number'), 'engine_number', lot.engine_number), (_('plate number'), 'plate_number', lot.plate_number)]
            for label, field_name, value in checks:
                if value:
                    duplicate = self.with_context(active_test=False).search([(field_name, '=', value), ('id', '!=', lot.id), ('is_car_vehicle', '=', True)], limit=1)
                    if duplicate:
                        raise ValidationError(_('This %s already exists on another car record, including archived or sold cars: %s') % (label, duplicate.display_name))

    @api.model
    def name_create(self, name):
        vals = {'name': name}
        for key in ('product_id', 'purchase_order_id', 'purchase_line_id', 'car_status'):
            value = self.env.context.get('default_%s' % key)
            if value:
                vals[key] = value
        lot = self.create(vals)
        return lot.name_get()[0]

    @api.model
    def _normalize_identity_value(self, value):
        return (value or '').strip().upper() or False

    @api.onchange('name', 'engine_number', 'plate_number')
    def _onchange_identity_uppercase(self):
        for lot in self:
            lot.name = lot._normalize_identity_value(lot.name)
            lot.engine_number = lot._normalize_identity_value(lot.engine_number)
            lot.plate_number = lot._normalize_identity_value(lot.plate_number)

    def _prepare_car_data_from_product(self):
        self.ensure_one()
        template = self.product_id.product_tmpl_id
        if not template:
            return {}
        vals = {}
        mapping = {
            'car_brand': template.brand,
            'car_model': template.model_name,
            'car_trim': template.trim,
            'body_style': template.body_style,
            'seats': template.seats,
            'doors': template.doors,
            'drivetrain': template.drivetrain,
        }
        for field_name, value in mapping.items():
            if not self[field_name] and value:
                vals[field_name] = value
        if not self.sale_price and self.product_id.lst_price:
            vals['sale_price'] = self.product_id.lst_price
        if self.car_status == 'draft':
            vals['car_status'] = 'incoming'
        return vals

    @api.onchange('product_id')
    def _onchange_product_id_car_defaults(self):
        for lot in self:
            if lot.product_id and lot.product_id.product_tmpl_id.is_car_vehicle:
                vals = lot._prepare_car_data_from_product()
                for field_name, value in vals.items():
                    lot[field_name] = value

    def _create_location_history(self, source_location=False, destination_location=False, picking=False, note=False):
        self.ensure_one()
        return self.env['car.location.history'].create({
            'lot_id': self.id,
            'source_location_id': source_location.id if source_location else False,
            'destination_location_id': destination_location.id if destination_location else False,
            'picking_id': picking.id if picking else False,
            'reference': picking.name if picking else False,
            'note': note,
        })

    def _display_value_for_audit(self, field_name, value):
        field = self._fields.get(field_name)
        if not field:
            return str(value) if value not in (False, None) else ''
        if field.type == 'many2one':
            return value.display_name if value else ''
        if field.type in ('one2many', 'many2many'):
            return ', '.join(value.mapped('display_name')) if value else ''
        if field.type == 'selection':
            return dict(field.selection).get(value, value or '')
        if field.type == 'boolean':
            return _('Yes') if value else _('No')
        if field.type in ('date', 'datetime'):
            return str(value) if value else ''
        return str(value) if value not in (False, None) else ''

    def _log_field_changes(self, old_values_map, fields_to_log):
        Audit = self.env['car.audit.log'].sudo()
        for record in self.filtered('is_car_vehicle'):
            entries = []
            for field_name in fields_to_log:
                if field_name not in record._fields:
                    continue
                old_val = old_values_map.get(record.id, {}).get(field_name)
                new_val = record[field_name]
                old_display = record._display_value_for_audit(field_name, old_val)
                new_display = record._display_value_for_audit(field_name, new_val)
                if old_display == new_display:
                    continue
                field_label = record._fields[field_name].string or field_name
                entries.append({
                    'lot_id': record.id,
                    'field_name': field_name,
                    'field_label': field_label,
                    'old_value': old_display,
                    'new_value': new_display,
                    'message': _('%s changed from "%s" to "%s"') % (field_label, old_display or '-', new_display or '-'),
                })
            if entries:
                Audit.create(entries)

    def _apply_state_rules_after_write(self):
        for lot in self.filtered('is_car_vehicle'):
            vals = {}
            if lot.car_status in ('sold', 'delivered'):
                vals.update({'website_published': False, 'active': False})
            elif not lot.active and lot.car_status not in ('sold', 'delivered'):
                vals['active'] = True
            if lot.car_status != 'reserved' and lot.reservation_order_id and not lot.sale_order_id:
                vals.update({'reservation_order_id': False, 'reservation_partner_id': False, 'reserved_until': False})
            if vals:
                super(StockLot, lot).write(vals)

    def _check_manual_status_permission(self, vals):
        if self.env.context.get('baroon_system_write'):
            return
        if 'car_status' in vals and not self._param_bool('baroon_dealership.allow_manual_status_change', True):
            raise ValidationError(_('Manual car status changes are disabled in settings.'))

    def write(self, vals):
        vals = dict(vals)
        for field_name in ('name', 'engine_number', 'plate_number'):
            if field_name in vals:
                vals[field_name] = self._normalize_identity_value(vals.get(field_name))
        self._check_manual_status_permission(vals)
        fields_to_log = list(vals.keys())
        old_values_map = {record.id: {field: record[field] for field in fields_to_log if field in record._fields} for record in self}
        result = super().write(vals)
        self._apply_state_rules_after_write()
        self._log_field_changes(old_values_map, fields_to_log)
        return result

    @api.model_create_multi
    def create(self, vals_list):
        normalized_list = []
        for vals in vals_list:
            vals = dict(vals)
            for field_name in ('name', 'engine_number', 'plate_number'):
                if field_name in vals:
                    vals[field_name] = self._normalize_identity_value(vals.get(field_name))
            normalized_list.append(vals)
        records = super().create(normalized_list)
        for record in records.filtered('is_car_vehicle'):
            defaults = record._prepare_car_data_from_product()
            if defaults:
                super(StockLot, record).write(defaults)
        records._apply_state_rules_after_write()
        records._log_field_changes({record.id: {} for record in records}, list(set().union(*[vals.keys() for vals in normalized_list]) if normalized_list else []))
        return records

    def unlink(self):
        self.mapped('audit_log_ids').unlink()
        self.mapped('location_history_ids').unlink()
        return super().unlink()

    def _compute_and_store_cost_snapshot(self):
        return True

    def action_view_location_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Location History'),
            'res_model': 'car.location.history',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'context': {'default_lot_id': self.id},
        }

    def action_view_audit_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Audit Log'),
            'res_model': 'car.audit.log',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'context': {'default_lot_id': self.id},
        }

    def action_view_expenses(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Expenses'),
            'res_model': 'car.expense',
            'view_mode': 'list,form,pivot,graph',
            'domain': [('lot_id', '=', self.id)],
            'context': {'default_lot_id': self.id},
        }

    def action_view_vendor_bills(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Bills'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.vendor_bill_ids.ids)],
            'context': {'default_move_type': 'in_invoice'},
        }

    def action_view_test_drives(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Test Drives'),
            'res_model': 'car.test.drive',
            'view_mode': 'list,form,calendar',
            'domain': [('lot_id', '=', self.id)],
            'context': {'default_lot_id': self.id},
        }

    def action_schedule_test_drive(self):
        self.ensure_one()
        action = self.action_view_test_drives()
        action['context'] = dict(action.get('context', {}), default_lot_id=self.id, default_partner_id=self.buyer_id.id if self.buyer_id else False)
        return action

    def action_view_transfers(self):
        self.ensure_one()
        move_lines = self.env['stock.move.line'].sudo().search([('lot_id', '=', self.id), ('picking_id', '!=', False)])
        pickings = move_lines.mapped('picking_id')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Transfers'),
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', pickings.ids)],
            'context': {'default_partner_id': self.buyer_id.id if self.buyer_id else False},
        }

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

    def action_view_opportunities(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Opportunities'),
            'res_model': 'crm.lead',
            'view_mode': 'list,form',
            'domain': [('car_lot_id', '=', self.id)],
            'context': {'default_type': 'opportunity', 'default_car_lot_id': self.id},
        }

    def action_view_sales_documents(self):
        self.ensure_one()
        sale_lines = self.env['sale.order.line'].with_context(active_test=False).search([('car_lot_id', '=', self.id), ('display_type', '=', False)])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Documents'),
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', sale_lines.order_id.ids)],
            'context': {'create': False},
        }

    def action_open_website(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_url', 'url': self.website_url or '/cars/%s' % self.id, 'target': 'new'}

    def _ensure_can_reserve(self, order=None):
        for lot in self:
            if lot.car_status in ('sold', 'delivered') or not lot.active:
                raise ValidationError(_('Sold or archived cars cannot be reserved again.'))
            if lot.car_status not in ('available', 'reserved'):
                raise ValidationError(_('Only cars in Available or Reserved state can be linked to a sales reservation.'))
            if lot.car_status == 'reserved' and lot.reservation_order_id and order and lot.reservation_order_id != order:
                raise ValidationError(_('This VIN is already reserved by another sales document.'))

    def _transition_to(self, new_state):
        for lot in self:
            if not lot.is_car_vehicle:
                continue
            if new_state == lot.car_status:
                continue
            if not self._param_bool('baroon_dealership.allow_manual_status_change', True):
                raise ValidationError(_('Manual status buttons are disabled in settings.'))
            allowed = self._STATE_TRANSITIONS.get(lot.car_status, [])
            if new_state not in allowed:
                raise ValidationError(_('You cannot move VIN %s from %s to %s.') % (
                    lot.name or lot.display_name,
                    dict(self._fields['car_status'].selection).get(lot.car_status, lot.car_status),
                    dict(self._fields['car_status'].selection).get(new_state, new_state),
                ))
            values = {'car_status': new_state}
            if new_state == 'available':
                values.update({'reservation_order_id': False, 'reservation_partner_id': False, 'reserved_until': False})
            if new_state == 'sold':
                values.update({'sold_date': fields.Datetime.now(), 'website_published': False, 'active': False})
            if new_state == 'delivered':
                values.update({'delivered_date': fields.Datetime.now(), 'website_published': False, 'active': False})
            lot.write(values)
        return True

    def action_mark_incoming(self):
        return self._transition_to('incoming')

    def action_mark_in_shipment(self):
        return self._transition_to('in_shipment')

    def action_mark_customs(self):
        return self._transition_to('customs')

    def action_mark_received(self):
        return self._transition_to('received')

    def action_mark_preparation(self):
        return self._transition_to('in_preparation')

    def action_mark_available(self):
        return self._transition_to('available')

    def action_reserve(self):
        self._ensure_can_reserve()
        for lot in self:
            if lot.car_status == 'available':
                lot.write({'car_status': 'reserved'})
        return True

    def action_mark_sold(self):
        for lot in self:
            if lot.minimum_sale_price and lot.sale_price and lot.sale_price < lot.minimum_sale_price:
                raise ValidationError(_('The sale price is below the minimum sale price for VIN %s.') % (lot.name or lot.display_name))
        return self._transition_to('sold')

    def action_deliver(self):
        return self._transition_to('delivered')

    def action_restore_to_inventory(self):
        for lot in self:
            lot.with_context(baroon_system_write=True).write({
                'active': True,
                'car_status': 'available',
                'website_published': False,
                'sale_order_id': False,
                'buyer_id': False,
                'salesperson_id': False,
                'reservation_order_id': False,
                'reservation_partner_id': False,
                'reserved_until': False,
                'sold_date': False,
                'delivered_date': False,
            })
        return True

    def _reserve_for_sale_line(self, line):
        self.ensure_one()
        self._ensure_can_reserve(order=line.order_id)
        hold_days = self._param_int('baroon_dealership.reservation_hold_days', 7)
        reserved_until = line.order_id.validity_date or fields.Date.add(fields.Date.today(), days=hold_days)
        self.write({
            'car_status': 'reserved',
            'reservation_order_id': line.order_id.id,
            'reservation_partner_id': line.order_id.partner_id.id,
            'reserved_until': reserved_until,
            'sale_order_id': False,
            'buyer_id': False,
            'salesperson_id': False,
            'active': True,
        })

    def _release_reservation(self, order=False):
        for lot in self:
            if order and lot.reservation_order_id and lot.reservation_order_id != order:
                continue
            if lot.car_status == 'reserved' and not lot.sale_order_id:
                lot.with_context(baroon_system_write=True).write({'car_status': 'available', 'reservation_order_id': False, 'reservation_partner_id': False, 'reserved_until': False})

    def _mark_sold_from_order_line(self, line):
        self.ensure_one()
        if self.minimum_sale_price and line.price_unit < self.minimum_sale_price:
            raise ValidationError(_('The confirmed unit price for VIN %s is below the minimum sale price.') % (self.name or self.display_name))
        self.with_context(baroon_system_write=True).write({
            'car_status': 'sold',
            'sale_order_id': line.order_id.id,
            'buyer_id': line.order_id.partner_id.id,
            'salesperson_id': line.order_id.user_id.id,
            'sold_date': fields.Datetime.now(),
            'reservation_order_id': False,
            'reservation_partner_id': False,
            'reserved_until': False,
            'website_published': False,
            'active': False,
        })

    @api.model
    def _cron_release_expired_reservations(self):
        today = fields.Date.today()
        expired = self.with_context(active_test=False).search([
            ('is_car_vehicle', '=', True),
            ('car_status', '=', 'reserved'),
            ('reserved_until', '!=', False),
            ('reserved_until', '<', today),
            ('sale_order_id', '=', False),
        ])
        expired._release_reservation()

    def action_print_car_profile(self):
        return self.env.ref('baroon_dealership.action_report_car_profile').report_action(self)

    def action_print_car_profitability(self):
        return self.env.ref('baroon_dealership.action_report_car_profitability').report_action(self)

    def action_print_car_accounting(self):
        return self.env.ref('baroon_dealership.action_report_car_cost_sheet').report_action(self)

    def action_print_executive_summary(self):
        return self.env.ref('baroon_dealership.action_report_car_executive_summary').report_action(self)

    def action_print_handover_sheet(self):
        return self.env.ref('baroon_dealership.action_report_car_handover').report_action(self)

    def action_print_car_history(self):
        return self.env.ref('baroon_dealership.action_report_car_history').report_action(self)

    def name_get(self):
        result = []
        for lot in self.with_context(active_test=False):
            title = ' '.join(filter(None, [lot.car_brand, lot.car_model, lot.car_trim])).strip()
            title = title or lot.product_id.display_name or ''
            display_name = f"{title} - {lot.name}" if lot.name and title else (lot.name or title or _('Car'))
            if not lot.active:
                display_name = f"{display_name} [{_('Archived')}]"
            result.append((lot.id, display_name))
        return result
