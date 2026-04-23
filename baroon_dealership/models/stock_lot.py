
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockLot(models.Model):
    _inherit = ['stock.lot', 'mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(default=True, tracking=True)

    car_image = fields.Image(string='Car Image')
    notes = fields.Text(string='Notes')

    car_brand = fields.Char(string='Brand', tracking=True)
    car_model = fields.Char(string='Model', tracking=True)
    car_trim = fields.Char(string='Trim', tracking=True)
    body_style = fields.Selection([
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('coupe', 'Coupe'),
        ('pickup', 'Pickup'),
        ('hatchback', 'Hatchback'),
        ('wagon', 'Wagon'),
        ('van', 'Van'),
        ('other', 'Other'),
    ], tracking=True)
    seats = fields.Integer(tracking=True)
    doors = fields.Integer(tracking=True)
    drivetrain = fields.Selection([
        ('fwd', 'FWD'),
        ('rwd', 'RWD'),
        ('awd', 'AWD'),
        ('4wd', '4WD'),
        ('other', 'Other'),
    ], tracking=True)

    engine_number = fields.Char(tracking=True, index=True)
    plate_number = fields.Char(tracking=True, index=True)
    year = fields.Integer(tracking=True)
    mileage = fields.Float(tracking=True)
    horse_power = fields.Integer(tracking=True)
    engine_size = fields.Char(tracking=True)
    fuel_type = fields.Selection([
        ('gasoline', 'Gasoline'),
        ('diesel', 'Diesel'),
        ('hybrid', 'Hybrid'),
        ('electric', 'Electric'),
        ('other', 'Other'),
    ], tracking=True)
    gearbox_type = fields.Selection([
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('cvt', 'CVT'),
        ('other', 'Other'),
    ], tracking=True)
    condition = fields.Selection([
        ('new', 'New'),
        ('used', 'Used'),
        ('damaged', 'Damaged'),
        ('under_preparation', 'Under Preparation'),
    ], default='new', tracking=True)

    exterior_color_ids = fields.Many2many(
        'car.exterior.color', 'stock_lot_exterior_color_rel', 'lot_id', 'color_id',
        string='Exterior Colors', tracking=True,
    )
    interior_color_ids = fields.Many2many(
        'car.interior.color', 'stock_lot_interior_color_rel', 'lot_id', 'color_id',
        string='Interior Colors', tracking=True,
    )

    purchase_partner_id = fields.Many2one('res.partner', string='Vendor', tracking=True)
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', tracking=True)
    purchase_date = fields.Date(tracking=True)
    shipping_reference = fields.Char(tracking=True)
    port_of_loading = fields.Char(tracking=True)
    destination_port = fields.Char(tracking=True)
    expected_arrival_date = fields.Date(tracking=True)
    arrival_date = fields.Date(tracking=True)
    customs_release_date = fields.Date(tracking=True)
    shipping_notes = fields.Text(string='Notes')
    branch_location = fields.Char(string='Display / Yard Location', tracking=True)

    sale_price = fields.Monetary(currency_field='currency_id', tracking=True)
    minimum_sale_price = fields.Monetary(currency_field='currency_id', tracking=True)
    purchase_cost = fields.Monetary(currency_field='currency_id', tracking=True)
    landed_cost = fields.Monetary(currency_field='currency_id', tracking=True)
    reconditioning_cost = fields.Monetary(currency_field='currency_id', tracking=True)
    total_cost = fields.Monetary(currency_field='currency_id', compute='_compute_profitability', store=True)
    gross_margin = fields.Monetary(currency_field='currency_id', compute='_compute_profitability', store=True)
    margin_percent = fields.Float(compute='_compute_profitability', store=True)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)

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
    ], default='draft', tracking=True)

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
    dashboard_label = fields.Char(compute='_compute_dashboard_label')
    dashboard_stage_color = fields.Char(compute='_compute_dashboard_stage_color')
    inventory_state_label = fields.Char(compute='_compute_inventory_state_label')
    days_in_stock = fields.Integer(compute='_compute_inventory_kpis', store=True, string='Days in Stock')
    days_to_arrival = fields.Integer(compute='_compute_inventory_kpis', store=True, string='Days to Arrival')
    arriving_soon = fields.Boolean(compute='_compute_inventory_kpis', store=True, index=True, string='Arriving Soon')
    website_display_status = fields.Char(compute='_compute_inventory_state_label')
    current_location_id = fields.Many2one('stock.location', compute='_compute_current_location_id', string='Current Location')

    is_car_vehicle = fields.Boolean(related='product_id.product_tmpl_id.is_car_vehicle', string='Is Car Vehicle', readonly=True)
    is_car_profile_complete = fields.Boolean(compute='_compute_is_car_profile_complete', store=True)

    website_published = fields.Boolean(default=False, tracking=True)
    website_sequence = fields.Integer(default=10)
    website_short_description = fields.Text()
    website_description = fields.Html()
    website_url = fields.Char(compute='_compute_website_url')
    display_name_website = fields.Char(compute='_compute_display_name_website')
    display_cover_image = fields.Image(compute='_compute_display_cover_image')
    purchase_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line', tracking=True)

    _sql_constraints = [
        ('engine_number_uniq', 'unique(engine_number)', 'Engine number must be unique.'),
    ]

    _STATE_TRANSITIONS = {
        'draft': ['incoming'],
        'incoming': ['in_shipment'],
        'in_shipment': ['customs'],
        'customs': ['received'],
        'received': ['in_preparation'],
        'in_preparation': ['available'],
        'available': ['reserved', 'sold', 'cancelled'],
        'reserved': ['available', 'sold', 'cancelled'],
        'sold': ['delivered'],
        'delivered': [],
        'cancelled': ['incoming'],
    }

    @api.depends('car_image')
    def _compute_display_cover_image(self):
        for lot in self:
            lot.display_cover_image = lot.car_image

    @api.model
    def name_create(self, name):
        vals = {'name': name}
        product_id = self.env.context.get('default_product_id')
        if product_id:
            vals['product_id'] = product_id
        purchase_order_id = self.env.context.get('default_purchase_order_id')
        if purchase_order_id:
            vals['purchase_order_id'] = purchase_order_id
        purchase_line_id = self.env.context.get('default_purchase_line_id')
        if purchase_line_id:
            vals['purchase_line_id'] = purchase_line_id
        car_status = self.env.context.get('default_car_status')
        if car_status:
            vals['car_status'] = car_status
        lot = self.create(vals)
        return lot.name_get()[0]


    def _compute_website_url(self):
        for lot in self:
            lot.website_url = '/cars/%s' % lot.id if lot.id else False

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

    def _compute_related_counts(self):
        sale_line_model = self.env['sale.order.line'].sudo().with_context(active_test=False)
        lead_model = self.env['crm.lead'].sudo().with_context(active_test=False)
        for lot in self:
            lot.crm_lead_count = lead_model.search_count([('car_lot_id', '=', lot.id)])
            lot.quotation_count = sale_line_model.search_count([('car_lot_id', '=', lot.id), ('display_type', '=', False)])

    @api.depends('car_brand', 'car_model', 'car_trim', 'name', 'year')
    def _compute_dashboard_label(self):
        for lot in self:
            title = ' '.join(filter(None, [lot.car_brand, lot.car_model, lot.car_trim])).strip()
            title = title or lot.product_id.display_name or _('Car')
            vin = lot.name or '-'
            lot.dashboard_label = '%s • VIN %s' % (title, vin)

    @api.depends('car_status')
    def _compute_dashboard_stage_color(self):
        mapping = {
            'draft': 'secondary',
            'incoming': 'info',
            'in_shipment': 'info',
            'customs': 'warning',
            'received': 'primary',
            'in_preparation': 'primary',
            'available': 'success',
            'reserved': 'warning',
            'sold': 'danger',
            'delivered': 'dark',
            'cancelled': 'secondary',
        }
        for lot in self:
            lot.dashboard_stage_color = mapping.get(lot.car_status, 'secondary')

    @api.depends('car_status', 'arriving_soon', 'days_to_arrival')
    def _compute_inventory_state_label(self):
        for lot in self:
            if lot.arriving_soon and lot.days_to_arrival >= 0:
                label = _('Arrives in %s days') % lot.days_to_arrival
            elif lot.car_status in ('incoming', 'in_shipment', 'customs', 'received', 'in_preparation'):
                label = _('Coming Soon')
            else:
                label = dict(self._fields['car_status'].selection).get(lot.car_status, lot.car_status or '')
            lot.inventory_state_label = label
            lot.website_display_status = label

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

    @api.depends('name', 'display_name_website', 'display_cover_image')
    def _compute_is_car_profile_complete(self):
        for lot in self:
            if not lot.is_car_vehicle:
                lot.is_car_profile_complete = True
                continue
            lot.is_car_profile_complete = bool(lot.name and lot.display_name_website and lot.display_cover_image)

    @api.depends('quant_ids.location_id', 'quant_ids.quantity')
    def _compute_current_location_id(self):
        for lot in self:
            quants = lot.quant_ids.filtered(lambda q: q.quantity > 0 and q.location_id)
            lot.current_location_id = quants[:1].location_id if quants else False

    @api.depends('purchase_cost', 'landed_cost', 'reconditioning_cost', 'sale_price')
    def _compute_profitability(self):
        for lot in self:
            lot.total_cost = (lot.purchase_cost or 0.0) + (lot.landed_cost or 0.0) + (lot.reconditioning_cost or 0.0)
            lot.gross_margin = (lot.sale_price or 0.0) - lot.total_cost
            lot.margin_percent = lot.total_cost and ((lot.gross_margin / lot.total_cost) * 100.0) or 0.0

    @api.constrains('year')
    def _check_year(self):
        current_year = fields.Date.today().year + 1
        for lot in self:
            if lot.year and (lot.year < 1900 or lot.year > current_year):
                raise ValidationError(_('Year must be between 1900 and %s.') % current_year)

    @api.constrains('horse_power', 'mileage', 'sale_price', 'minimum_sale_price', 'purchase_cost', 'landed_cost', 'reconditioning_cost')
    def _check_numeric_values(self):
        for lot in self:
            values = {
                _('Horse power'): lot.horse_power,
                _('Mileage'): lot.mileage,
                _('Sale price'): lot.sale_price,
                _('Minimum sale price'): lot.minimum_sale_price,
                _('Purchase cost'): lot.purchase_cost,
                _('Landed cost'): lot.landed_cost,
                _('Reconditioning cost'): lot.reconditioning_cost,
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

    @api.constrains('website_published', 'car_status', 'display_cover_image')
    def _check_website_publication_rules(self):
        for lot in self:
            if not lot.is_car_vehicle or not lot.website_published:
                continue
            if lot.car_status in ('sold', 'delivered'):
                raise ValidationError(_('Sold or delivered cars cannot be published on the website.'))
            if not lot.display_cover_image:
                raise ValidationError(_('Upload at least one image before publishing the car on the website.'))

    @api.constrains('name', 'engine_number', 'plate_number')
    def _check_duplicates_including_archived(self):
        for lot in self:
            if not lot.is_car_vehicle:
                continue
            checks = [
                (_('VIN'), 'name', lot.name),
                (_('engine number'), 'engine_number', lot.engine_number),
                (_('plate number'), 'plate_number', lot.plate_number),
            ]
            for label, field_name, value in checks:
                if value:
                    duplicate = self.with_context(active_test=False).search([
                        (field_name, '=', value),
                        ('id', '!=', lot.id),
                        ('is_car_vehicle', '=', True),
                    ], limit=1)
                    if duplicate:
                        raise ValidationError(_('This %s already exists on another car record, including archived or sold cars: %s') % (label, duplicate.display_name))

    
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

    def _apply_state_rules_after_write(self):
        for lot in self.filtered('is_car_vehicle'):
            vals = {}
            if lot.car_status in ('sold', 'delivered'):
                vals.update({'website_published': False, 'active': False})
            elif not lot.active and lot.car_status not in ('sold', 'delivered'):
                vals['active'] = True
            if lot.car_status != 'reserved' and lot.reservation_order_id and not lot.sale_order_id:
                vals.update({
                    'reservation_order_id': False,
                    'reservation_partner_id': False,
                    'reserved_until': False,
                })
            if vals:
                super(StockLot, lot).write(vals)

    def write(self, vals):
        result = super().write(vals)
        self._apply_state_rules_after_write()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records.filtered('is_car_vehicle'):
            defaults = record._prepare_car_data_from_product()
            if defaults:
                super(StockLot, record).write(defaults)
        records._apply_state_rules_after_write()
        return records


    def action_print_car_profile(self):
        return self.env.ref('baroon_dealership.action_report_car_profile').report_action(self)

    def action_print_car_profitability(self):
        return self.env.ref('baroon_dealership.action_report_car_profitability').report_action(self)

    def action_print_car_accounting(self):
        return self.env.ref('baroon_dealership.action_report_car_accounting').report_action(self)

    def action_print_executive_summary(self):
        return self.env.ref('baroon_dealership.action_report_car_executive_summary').report_action(self)

    def action_open_website(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.website_url or '/cars/%s' % self.id,
            'target': 'new',
        }

    def action_view_opportunities(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Opportunities'),
            'res_model': 'crm.lead',
            'view_mode': 'list,form',
            'domain': [('car_lot_id', '=', self.id)],
            'context': {
                'default_type': 'opportunity',
                'default_car_lot_id': self.id,
                'default_name': _('Opportunity for %s') % (self.display_name_website or self.display_name),
            },
        }

    def action_view_sales_documents(self):
        self.ensure_one()
        sale_lines = self.env['sale.order.line'].with_context(active_test=False).search([
            ('car_lot_id', '=', self.id),
            ('display_type', '=', False),
        ])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Documents'),
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', sale_lines.order_id.ids)],
            'context': {'create': False},
        }

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
            allowed = self._STATE_TRANSITIONS.get(lot.car_status, [])
            if new_state not in allowed:
                raise ValidationError(_('You cannot move VIN %s from %s to %s.') % (
                    lot.name or lot.display_name,
                    dict(self._fields['car_status'].selection).get(lot.car_status, lot.car_status),
                    dict(self._fields['car_status'].selection).get(new_state, new_state),
                ))
            values = {'car_status': new_state}
            if new_state == 'available':
                values.update({
                    'reservation_order_id': False,
                    'reservation_partner_id': False,
                    'reserved_until': False,
                })
            if new_state == 'sold':
                values.update({
                    'sold_date': fields.Datetime.now(),
                    'website_published': False,
                    'active': False,
                })
            if new_state == 'delivered':
                values.update({
                    'delivered_date': fields.Datetime.now(),
                    'website_published': False,
                    'active': False,
                })
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
            lot.write({
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
        self.write({
            'car_status': 'reserved',
            'reservation_order_id': line.order_id.id,
            'reservation_partner_id': line.order_id.partner_id.id,
            'reserved_until': line.order_id.validity_date,
            'sale_order_id': False,
            'buyer_id': False,
            'salesperson_id': False,
            'active': True,
        })

    def _release_reservation(self, order=False):
        for lot in self:
            if order and lot.reservation_order_id and lot.reservation_order_id != order:
                continue
            if lot.sale_order_id:
                continue
            values = {
                'reservation_order_id': False,
                'reservation_partner_id': False,
                'reserved_until': False,
            }
            if lot.car_status == 'reserved':
                values['car_status'] = 'available'
            lot.write(values)

    def action_release_reservation(self):
        sale_line_model = self.env['sale.order.line'].with_context(active_test=False)
        for lot in self:
            live_lines = sale_line_model.search([
                ('car_lot_id', '=', lot.id),
                ('display_type', '=', False),
                ('state', 'not in', ['cancel']),
                ('order_id.state', 'in', ['draft', 'sent', 'sale', 'done']),
            ], limit=1)
            if live_lines and live_lines.order_id.state in ('draft', 'sent'):
                raise ValidationError(_('Cancel or remove the open quotation before releasing VIN %s back to Available.') % (lot.name or lot.display_name))
            if live_lines and live_lines.order_id.state in ('sale', 'done'):
                raise ValidationError(_('VIN %s is already linked to a confirmed sale and cannot be released to Available.') % (lot.name or lot.display_name))
            lot._release_reservation()
        return True

    def _mark_sold_from_order_line(self, line):
        self.ensure_one()
        if self.minimum_sale_price and line.price_unit < self.minimum_sale_price:
            raise ValidationError(_('The confirmed unit price for VIN %s is below the minimum sale price.') % (self.name or self.display_name))
        self.write({
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
