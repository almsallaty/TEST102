from odoo import _, api, fields, models


class BaroonDealershipDashboard(models.TransientModel):
    _name = 'baroon.dealership.dashboard'
    _description = 'Baroon Dealership Executive Dashboard'

    currency_id = fields.Many2one('res.currency', readonly=True)

    active_inventory_count = fields.Integer(readonly=True)
    available_count = fields.Integer(readonly=True)
    reserved_count = fields.Integer(readonly=True)
    in_transit_count = fields.Integer(readonly=True)
    preparation_count = fields.Integer(readonly=True)
    sold_count = fields.Integer(readonly=True)
    delivered_count = fields.Integer(readonly=True)
    arriving_soon_count = fields.Integer(readonly=True)

    open_opportunity_count = fields.Integer(readonly=True)
    open_quotation_count = fields.Integer(readonly=True)
    active_test_drive_count = fields.Integer(readonly=True)
    approved_expense_count = fields.Integer(readonly=True)
    pending_bill_count = fields.Integer(readonly=True)
    landed_cost_count = fields.Integer(readonly=True)

    inventory_value = fields.Monetary(currency_field='currency_id', readonly=True)
    reserved_value = fields.Monetary(currency_field='currency_id', readonly=True)
    sold_value = fields.Monetary(currency_field='currency_id', readonly=True)
    total_pipeline_value = fields.Monetary(currency_field='currency_id', readonly=True)
    total_cost_value = fields.Monetary(currency_field='currency_id', readonly=True)
    total_margin_value = fields.Monetary(currency_field='currency_id', readonly=True)
    average_margin = fields.Float(readonly=True)
    average_days_in_stock = fields.Float(readonly=True)
    average_days_to_arrival = fields.Float(readonly=True)

    incoming_ids = fields.Many2many('stock.lot', 'baroon_dash_incoming_rel', 'dashboard_id', 'lot_id', string='Pipeline Cars', readonly=True)
    available_ids = fields.Many2many('stock.lot', 'baroon_dash_available_rel', 'dashboard_id', 'lot_id', string='Available Cars', readonly=True)
    reserved_ids = fields.Many2many('stock.lot', 'baroon_dash_reserved_rel', 'dashboard_id', 'lot_id', string='Reserved Cars', readonly=True)
    top_margin_ids = fields.Many2many('stock.lot', 'baroon_dash_top_margin_rel', 'dashboard_id', 'lot_id', string='Top Margin Cars', readonly=True)
    aging_ids = fields.Many2many('stock.lot', 'baroon_dash_aging_rel', 'dashboard_id', 'lot_id', string='Aging Cars', readonly=True)
    test_drive_ids = fields.Many2many('car.test.drive', 'baroon_dash_test_drive_rel', 'dashboard_id', 'test_drive_id', string='Recent Test Drives', readonly=True)
    expense_ids = fields.Many2many('car.expense', 'baroon_dash_expense_rel', 'dashboard_id', 'expense_id', string='Recent Expenses', readonly=True)

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        lot_model = self.env['stock.lot'].with_context(active_test=False)
        lead_model = self.env['crm.lead'].with_context(active_test=False)
        sale_model = self.env['sale.order'].with_context(active_test=False)
        test_drive_model = self.env['car.test.drive'].with_context(active_test=False)
        expense_model = self.env['car.expense'].with_context(active_test=False)
        bill_model = self.env['account.move'].with_context(active_test=False)
        landed_cost_model = self.env['stock.landed.cost'].with_context(active_test=False)

        domain = [('is_car_vehicle', '=', True)]
        active_domain = domain + [('active', '=', True), ('car_status', 'not in', ['sold', 'delivered', 'cancelled'])]
        available_domain = domain + [('active', '=', True), ('car_status', '=', 'available')]
        reserved_domain = domain + [('active', '=', True), ('car_status', '=', 'reserved')]
        in_transit_domain = domain + [('active', '=', True), ('car_status', 'in', ['incoming', 'in_shipment', 'customs', 'received'])]
        preparation_domain = domain + [('active', '=', True), ('car_status', '=', 'in_preparation')]
        sold_domain = domain + [('car_status', '=', 'sold')]
        delivered_domain = domain + [('car_status', '=', 'delivered')]
        arriving_domain = domain + [('arriving_soon', '=', True), ('active', '=', True)]

        active_cars = lot_model.search(active_domain)
        available_cars = lot_model.search(available_domain)
        reserved_cars = lot_model.search(reserved_domain)
        sold_cars = lot_model.search(sold_domain)
        all_live_cars = lot_model.search(domain + [('active', '=', True)])

        open_leads = lead_model.search_count([('type', '=', 'opportunity'), ('probability', '<', 100), ('active', '=', True)])
        open_quotes = sale_model.search_count([('state', 'in', ['draft', 'sent'])])
        active_test_drives = test_drive_model.search_count([('state', 'in', ['scheduled', 'checked_out', 'quoted'])])
        approved_expenses = expense_model.search_count([('state', '=', 'approved')])
        pending_vendor_bills = bill_model.search_count([('move_type', '=', 'in_invoice'), ('state', '=', 'posted'), ('payment_state', 'not in', ['paid', 'reversed'])])
        done_landed_costs = landed_cost_model.search_count([('state', '=', 'done')])

        avg_days_stock = sum(all_live_cars.mapped('days_in_stock')) / len(all_live_cars) if all_live_cars else 0.0
        arrival_candidates = all_live_cars.filtered(lambda l: l.days_to_arrival and l.car_status in ('incoming', 'in_shipment', 'customs', 'received'))
        avg_days_arrival = sum(arrival_candidates.mapped('days_to_arrival')) / len(arrival_candidates) if arrival_candidates else 0.0

        values.update({
            'currency_id': self.env.company.currency_id.id,
            'active_inventory_count': len(active_cars),
            'available_count': len(available_cars),
            'reserved_count': len(reserved_cars),
            'in_transit_count': lot_model.search_count(in_transit_domain),
            'preparation_count': lot_model.search_count(preparation_domain),
            'sold_count': lot_model.search_count(sold_domain),
            'delivered_count': lot_model.search_count(delivered_domain),
            'arriving_soon_count': lot_model.search_count(arriving_domain),
            'open_opportunity_count': open_leads,
            'open_quotation_count': open_quotes,
            'active_test_drive_count': active_test_drives,
            'approved_expense_count': approved_expenses,
            'pending_bill_count': pending_vendor_bills,
            'landed_cost_count': done_landed_costs,
            'inventory_value': sum(active_cars.mapped('sale_price')),
            'reserved_value': sum(reserved_cars.mapped('sale_price')),
            'sold_value': sum(sold_cars.mapped('sale_price')),
            'total_pipeline_value': sum(all_live_cars.mapped('sale_price')),
            'total_cost_value': sum(all_live_cars.mapped('total_cost')),
            'total_margin_value': sum(all_live_cars.mapped('gross_margin')),
            'average_margin': (sum(active_cars.mapped('margin_percent')) / len(active_cars)) if active_cars else 0.0,
            'average_days_in_stock': avg_days_stock,
            'average_days_to_arrival': avg_days_arrival,
            'incoming_ids': [(6, 0, lot_model.search(domain + [('car_status', 'in', ['incoming', 'in_shipment', 'customs', 'received'])], limit=10, order='expected_arrival_date asc, id desc').ids)],
            'available_ids': [(6, 0, available_cars.sorted(lambda l: l.sale_price or 0.0, reverse=True)[:10].ids)],
            'reserved_ids': [(6, 0, lot_model.search(reserved_domain, limit=10, order='reserved_until asc, write_date desc').ids)],
            'top_margin_ids': [(6, 0, lot_model.search(domain + [('active', '=', True)], limit=10, order='gross_margin desc, sale_price desc').ids)],
            'aging_ids': [(6, 0, lot_model.search(domain + [('active', '=', True), ('car_status', 'not in', ['sold', 'delivered', 'cancelled'])], limit=10, order='days_in_stock desc, id desc').ids)],
            'test_drive_ids': [(6, 0, test_drive_model.search([], limit=10, order='scheduled_datetime desc, id desc').ids)],
            'expense_ids': [(6, 0, expense_model.search([], limit=10, order='expense_date desc, id desc').ids)],
        })
        return values

    @api.model
    def open_dashboard_action(self):
        dashboard = self.create({})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Executive Dashboard'),
            'res_model': 'baroon.dealership.dashboard',
            'view_mode': 'form',
            'res_id': dashboard.id,
            'target': 'current',
        }

    def action_refresh_dashboard(self):
        self.ensure_one()
        self.unlink()
        return self.open_dashboard_action()

    def _open_window(self, name, model, domain=None, view_mode='list,form,kanban,graph,pivot', context=None):
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': model,
            'view_mode': view_mode,
            'domain': domain or [],
            'context': context or {},
        }

    def action_open_inventory(self):
        return self._open_window(_('Active Inventory'), 'stock.lot', [('is_car_vehicle', '=', True), ('active', '=', True), ('car_status', 'not in', ['sold', 'delivered', 'cancelled'])], context={'search_default_filter_car_vehicle': 1})

    def action_open_pipeline(self):
        return self._open_window(_('Pipeline Cars'), 'stock.lot', [('is_car_vehicle', '=', True), ('active', '=', True), ('car_status', 'in', ['incoming', 'in_shipment', 'customs', 'received', 'in_preparation'])], context={'group_by': 'car_status'})

    def action_open_reservations(self):
        return self._open_window(_('Reserved Cars'), 'stock.lot', [('is_car_vehicle', '=', True), ('car_status', '=', 'reserved')])

    def action_open_test_drives(self):
        return self._open_window(_('Test Drives'), 'car.test.drive', [('state', 'in', ['scheduled', 'checked_out', 'quoted'])], view_mode='list,form,kanban,calendar,pivot,graph')

    def action_open_expenses(self):
        return self._open_window(_('Car Expenses'), 'car.expense', [('state', '=', 'approved')], view_mode='list,form,pivot,graph')

    def action_open_quotations(self):
        return self._open_window(_('Open Quotations'), 'sale.order', [('state', 'in', ['draft', 'sent'])], view_mode='list,form,kanban,pivot,graph')

    def action_open_opportunities(self):
        return self._open_window(_('Open Opportunities'), 'crm.lead', [('type', '=', 'opportunity'), ('probability', '<', 100), ('active', '=', True)], view_mode='list,form,kanban,pivot,graph')

    def action_open_reports(self):
        return self._open_window(_('Dealership Reports'), 'stock.lot', [('is_car_vehicle', '=', True)], view_mode='pivot,graph,list,kanban,form', context={'search_default_filter_car_vehicle': 1, 'active_test': False})

    def action_open_profitability(self):
        return self._open_window(_('Profitability Review'), 'stock.lot', [('is_car_vehicle', '=', True)], view_mode='list,pivot,graph,kanban,form', context={'search_default_filter_car_vehicle': 1, 'active_test': False})
