from odoo import _, api, fields, models


class BaroonDealershipDashboard(models.TransientModel):
    _name = 'baroon.dealership.dashboard'
    _description = 'Baroon Dealership Dashboard'

    active_inventory_count = fields.Integer(readonly=True)
    available_count = fields.Integer(readonly=True)
    reserved_count = fields.Integer(readonly=True)
    sold_count = fields.Integer(readonly=True)
    arriving_soon_count = fields.Integer(readonly=True)
    inventory_value = fields.Monetary(currency_field='currency_id', readonly=True)
    average_margin = fields.Float(readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)
    incoming_ids = fields.Many2many(
        'stock.lot', 'baroon_dash_incoming_rel', 'dashboard_id', 'lot_id',
        string='Incoming Cars', readonly=True,
    )
    available_ids = fields.Many2many(
        'stock.lot', 'baroon_dash_available_rel', 'dashboard_id', 'lot_id',
        string='Available Cars', readonly=True,
    )
    reserved_ids = fields.Many2many(
        'stock.lot', 'baroon_dash_reserved_rel', 'dashboard_id', 'lot_id',
        string='Reserved Cars', readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        lot_model = self.env['stock.lot'].with_context(active_test=False)
        domain = [('is_car_vehicle', '=', True)]
        active_domain = domain + [('active', '=', True), ('car_status', 'not in', ['sold', 'delivered'])]
        available_domain = domain + [('car_status', '=', 'available'), ('active', '=', True)]
        reserved_domain = domain + [('car_status', '=', 'reserved'), ('active', '=', True)]
        sold_domain = domain + [('car_status', 'in', ['sold', 'delivered'])]
        arriving_domain = domain + [('arriving_soon', '=', True), ('active', '=', True)]

        active_cars = lot_model.search(active_domain)
        values.update({
            'active_inventory_count': len(active_cars),
            'available_count': lot_model.search_count(available_domain),
            'reserved_count': lot_model.search_count(reserved_domain),
            'sold_count': lot_model.search_count(sold_domain),
            'arriving_soon_count': lot_model.search_count(arriving_domain),
            'inventory_value': sum(active_cars.mapped('sale_price')),
            'average_margin': (sum(active_cars.mapped('margin_percent')) / len(active_cars)) if active_cars else 0.0,
            'currency_id': self.env.company.currency_id.id,
            'incoming_ids': [(6, 0, lot_model.search(domain + [('car_status', 'in', ['incoming', 'in_shipment', 'customs'])], limit=8, order='expected_arrival_date asc, id desc').ids)],
            'available_ids': [(6, 0, lot_model.search(available_domain, limit=8, order='sale_price desc, id desc').ids)],
            'reserved_ids': [(6, 0, lot_model.search(reserved_domain, limit=8, order='write_date desc, id desc').ids)],
        })
        return values

    def action_open_inventory(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Active Inventory'),
            'res_model': 'stock.lot',
            'view_mode': 'kanban,list,form',
            'domain': [('is_car_vehicle', '=', True), ('active', '=', True), ('car_status', 'not in', ['sold', 'delivered'])],
            'context': {'search_default_filter_car_vehicle': 1},
        }

    def action_open_reports(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Dealership Reports'),
            'res_model': 'stock.lot',
            'view_mode': 'pivot,graph,list',
            'domain': [('is_car_vehicle', '=', True)],
            'context': {'search_default_filter_car_vehicle': 1, 'active_test': False},
        }


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
