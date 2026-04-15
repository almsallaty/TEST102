from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    shipment_reference = fields.Char(string='Shipment Reference', tracking=True)
    shipment_booking_reference = fields.Char(string='Booking Reference', tracking=True)
    container_reference = fields.Char(string='Container Reference', tracking=True)
    shipment_status = fields.Selection([
        ('draft', 'Draft'),
        ('incoming', 'Incoming'),
        ('in_shipment', 'In Shipment'),
        ('customs', 'Customs'),
        ('received', 'Received'),
        ('available', 'Available'),
    ], string='Import Status', default='draft', tracking=True)
    port_of_loading = fields.Char(tracking=True)
    destination_port = fields.Char(tracking=True)
    eta = fields.Date(string='ETA', tracking=True)
    actual_arrival = fields.Date(string='Actual Arrival', tracking=True)
    customs_release_date = fields.Date(tracking=True)
    shipment_notes = fields.Text(tracking=True)
    car_lot_ids = fields.One2many('stock.lot', 'purchase_order_id', string='Cars')
    car_count = fields.Integer(compute='_compute_car_count')
    created_car_count = fields.Integer(compute='_compute_car_count')

    @api.depends('car_lot_ids')
    def _compute_car_count(self):
        for order in self:
            order.car_count = len(order.car_lot_ids)
            order.created_car_count = len(order.car_lot_ids)

    def action_view_po_cars(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('PO Cars'),
            'res_model': 'stock.lot',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', self.car_lot_ids.ids)],
            'context': {
                'default_purchase_order_id': self.id,
                'search_default_filter_car_vehicle': 1,
                'active_test': False,
            },
        }

    def button_confirm(self):
        res = super().button_confirm()
        for order in self:
            car_lines = order.order_line.filtered(lambda l: l.product_id and l.product_id.product_tmpl_id.is_car_vehicle)
            if car_lines and order.shipment_status == 'draft':
                order.shipment_status = 'incoming'
        return res

    def _get_target_lots(self):
        return self.mapped('car_lot_ids').filtered(lambda l: l.is_car_vehicle)

    def _sync_po_status_to_cars(self, new_status):
        for order in self:
            lots = order._get_target_lots().with_context(active_test=False)
            if not lots:
                continue
            vals = {
                'purchase_partner_id': order.partner_id.id,
                'purchase_date': order.date_order.date() if order.date_order else False,
                'shipping_reference': order.shipment_reference,
            'shipment_booking_reference': order.shipment_booking_reference,
            'container_reference': order.container_reference,
                'shipment_booking_reference': order.shipment_booking_reference,
                'container_reference': order.container_reference,
                'port_of_loading': order.port_of_loading,
                'destination_port': order.destination_port,
                'expected_arrival_date': order.eta,
                'arrival_date': order.actual_arrival if new_status in ('received', 'available') else False,
                'customs_release_date': order.customs_release_date if new_status == 'available' else False,
                'shipping_notes': order.shipment_notes,
                'car_status': new_status,
            }
            if new_status == 'available':
                vals['active'] = True
            lots.write(vals)

    def action_mark_po_incoming(self):
        self.write({'shipment_status': 'incoming'})
        self._sync_po_status_to_cars('incoming')
        return True

    def action_mark_po_in_shipment(self):
        self.write({'shipment_status': 'in_shipment'})
        self._sync_po_status_to_cars('in_shipment')
        return True

    def action_mark_po_customs(self):
        self.write({'shipment_status': 'customs'})
        self._sync_po_status_to_cars('customs')
        return True

    def action_mark_po_received(self):
        self.write({'shipment_status': 'received', 'actual_arrival': fields.Date.context_today(self)})
        self._sync_po_status_to_cars('received')
        return True

    def action_mark_po_available(self):
        self.write({'shipment_status': 'available'})
        self._sync_po_status_to_cars('available')
        return True

    def action_advance_import_stage(self):
        for order in self:
            if order.shipment_status == 'draft':
                order.action_mark_po_incoming()
            elif order.shipment_status == 'incoming':
                order.action_mark_po_in_shipment()
            elif order.shipment_status == 'in_shipment':
                order.action_mark_po_customs()
            elif order.shipment_status == 'customs':
                order.action_mark_po_received()
            elif order.shipment_status == 'received':
                order.action_mark_po_available()
        return True

    def action_create_cars_from_vins(self):
        StockLot = self.env['stock.lot'].with_context(active_test=False)
        created = StockLot.browse()
        for order in self:
            if order.state not in ('purchase', 'done'):
                raise ValidationError(_('Confirm the purchase order before creating cars from VINs.'))
            for line in order.order_line.filtered(lambda l: l.product_id and l.product_id.product_tmpl_id.is_car_vehicle):
                vins = line._get_all_vins()
                if not vins:
                    continue
                qty = int(round(line.product_qty or 0.0))
                if qty and len(vins) != qty:
                    raise ValidationError(_(
                        'The number of VINs on line %s must match the quantity. Quantity: %s, VINs: %s.'
                    ) % (line.product_id.display_name, qty, len(vins)))
                for vin in vins:
                    existing = (line.vin_lot_ids.with_context(active_test=False).filtered(lambda l: l.name == vin and l.product_id == line.product_id)[:1] or StockLot.search([('name', '=', vin), ('product_id', '=', line.product_id.id)], limit=1))
                    if existing:
                        if existing.purchase_order_id and existing.purchase_order_id != order:
                            raise ValidationError(_('VIN %s already belongs to another purchase order.') % vin)
                        existing.write(line._prepare_existing_lot_vals(order))
                        if existing not in line.vin_lot_ids:
                            line.vin_lot_ids = [(4, existing.id)]
                        created |= existing
                        continue
                    lot = StockLot.create(line._prepare_new_lot_vals(order, vin))
                    line.vin_lot_ids = [(4, lot.id)]
                    created |= lot
            if created and order.shipment_status == 'draft':
                order.shipment_status = 'incoming'
        if not created:
            raise ValidationError(_('No VINs were found to create cars. Fill the VIN list on the purchase order lines first.'))
        return self.action_view_po_cars()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    vin_list = fields.Text(string='VIN / Serial Numbers', help='Enter one VIN per line, or separate multiple VINs with commas.')
    vin_lot_ids = fields.Many2many(
        'stock.lot', 'purchase_line_stock_lot_rel', 'purchase_line_id', 'lot_id',
        string='VIN Records',
        help='Create or select VIN records directly from the purchase order line.',
    )
    created_car_ids = fields.One2many('stock.lot', 'purchase_line_id', string='Created Cars')
    created_car_count = fields.Integer(compute='_compute_created_car_count')

    @api.depends('created_car_ids', 'vin_lot_ids')
    def _compute_created_car_count(self):
        for line in self:
            line.created_car_count = len((line.created_car_ids | line.vin_lot_ids).with_context(active_test=False))


    def _get_vin_records(self):
        self.ensure_one()
        return self.vin_lot_ids.with_context(active_test=False).filtered(lambda l: l.name)

    def _get_all_vins(self):
        self.ensure_one()
        vins = []
        seen = set()
        for vin in self._parse_vin_entries() + self._get_vin_records().mapped('name'):
            if vin and vin not in seen:
                vins.append(vin)
                seen.add(vin)
        return vins

    @api.onchange('product_id')
    def _onchange_product_id_reset_vin_candidates(self):
        for line in self:
            if line.vin_lot_ids:
                line.vin_lot_ids = line.vin_lot_ids.filtered(lambda l: not line.product_id or l.product_id == line.product_id)

    def _parse_vin_entries(self):
        self.ensure_one()
        raw = self.vin_list or ''
        items = []
        for chunk in raw.replace(',', '\n').splitlines():
            vin = (chunk or '').strip()
            if vin:
                items.append(vin)
        duplicates = sorted({vin for vin in items if items.count(vin) > 1})
        if duplicates:
            raise ValidationError(_('Duplicate VINs found on purchase line %s: %s') % (self.product_id.display_name, ', '.join(duplicates)))
        return items

    def _prepare_lot_common_vals(self, order):
        self.ensure_one()
        tmpl = self.product_id.product_tmpl_id
        return {
            'product_id': self.product_id.id,
            'company_id': order.company_id.id,
            'purchase_order_id': order.id,
            'purchase_line_id': self.id,
            'purchase_partner_id': order.partner_id.id,
            'purchase_date': order.date_order.date() if order.date_order else False,
            'purchase_cost': self.price_unit,
            'car_brand': tmpl.brand,
            'car_model': tmpl.model_name,
            'car_trim': tmpl.trim,
            'body_style': tmpl.body_style,
            'seats': tmpl.seats,
            'doors': tmpl.doors,
            'drivetrain': tmpl.drivetrain,
            'sale_price': self.product_id.lst_price,
            'shipping_reference': order.shipment_reference,
            'shipment_booking_reference': order.shipment_booking_reference,
            'container_reference': order.container_reference,
            'port_of_loading': order.port_of_loading,
            'destination_port': order.destination_port,
            'expected_arrival_date': order.eta,
            'shipping_notes': order.shipment_notes,
            'car_status': order.shipment_status if order.shipment_status != 'draft' else 'incoming',
            'active': True,
        }

    def _prepare_new_lot_vals(self, order, vin):
        vals = self._prepare_lot_common_vals(order)
        vals.update({'name': vin})
        return vals

    def _prepare_existing_lot_vals(self, order):
        return self._prepare_lot_common_vals(order)
