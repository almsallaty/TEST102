
from datetime import date, timedelta
from odoo import http
from odoo.http import request


class BaroonDashboardController(http.Controller):

    @http.route('/baroon/dashboard/data', type='json', auth='user')
    def dashboard_data(self):
        env = request.env
        lot_model = env['stock.lot'].with_context(active_test=False)
        sale_model = env['sale.order'].with_context(active_test=False)

        today = date.today()
        first_month = today.replace(day=1)
        last_month_end = first_month - timedelta(days=1)
        first_last_month = last_month_end.replace(day=1)

        active_cars = lot_model.search([('is_car_vehicle', '=', True), ('active', '=', True)])
        available_cars = active_cars.filtered(lambda l: l.car_status == 'available')
        reserved_cars = active_cars.filtered(lambda l: l.car_status == 'reserved')

        inventory_count = len(active_cars)
        inventory_cost = sum(active_cars.mapped('total_cost'))
        expected_revenue = sum(active_cars.mapped('sale_price'))

        sold_this_month = lot_model.search_count([
            ('is_car_vehicle', '=', True),
            ('car_status', 'in', ['sold', 'delivered']),
            ('sold_date', '>=', first_month),
        ])
        sold_last_month = lot_model.search_count([
            ('is_car_vehicle', '=', True),
            ('car_status', 'in', ['sold', 'delivered']),
            ('sold_date', '>=', first_last_month),
            ('sold_date', '<=', last_month_end),
        ])
        percent_change = ((sold_this_month - sold_last_month) / sold_last_month * 100.0) if sold_last_month else 0.0

        alerts = []
        aging_critical = lot_model.search([('is_car_vehicle', '=', True), ('car_status', 'in', ['available', 'reserved']), ('days_in_stock', '>', 90)])
        if aging_critical:
            alerts.append({'level': 'danger', 'message': f'{len(aging_critical)} cars > 90 days', 'action': 'open_aging'})
        missing_images = lot_model.search([('is_car_vehicle', '=', True), ('display_cover_image', '=', False)])
        if missing_images:
            alerts.append({'level': 'warning', 'message': f'{len(missing_images)} cars missing images', 'action': 'open_missing_images'})

        sales_trend = []
        for m in range(1, today.month + 1):
            start = today.replace(month=m, day=1)
            end = (start + timedelta(days=32)).replace(day=1)
            count = lot_model.search_count([
                ('is_car_vehicle', '=', True),
                ('car_status', 'in', ['sold', 'delivered']),
                ('sold_date', '>=', start),
                ('sold_date', '<', end),
            ])
            sales_trend.append({'month': m, 'count': count})

        stock_distribution = {
            'available': len(available_cars),
            'reserved': len(reserved_cars),
            'pipeline': lot_model.search_count([('is_car_vehicle', '=', True), ('car_status', 'in', ['incoming', 'in_shipment', 'customs', 'received', 'in_preparation'])]),
            'sold': lot_model.search_count([('is_car_vehicle', '=', True), ('car_status', '=', 'sold')]),
            'delivered': lot_model.search_count([('is_car_vehicle', '=', True), ('car_status', '=', 'delivered')]),
        }

        top_models = lot_model.read_group(
            [('is_car_vehicle', '=', True), ('car_status', 'in', ['sold', 'delivered']), ('sold_date', '>=', first_month)],
            ['car_model', 'id:count'], ['car_model'], limit=5, orderby='id_count desc')
        top_models_data = [{'model': rec.get('car_model') or 'Unknown', 'count': rec.get('car_model_count', rec.get('id_count', 0))} for rec in top_models]

        leaderboard = sale_model.read_group(
            [('state', 'in', ['sale', 'done']), ('date_order', '>=', first_month)],
            ['user_id', 'amount_total:sum'], ['user_id'], limit=5, orderby='amount_total_sum desc')
        salespeople = []
        for rec in leaderboard:
            if rec.get('user_id'):
                salespeople.append({'name': rec['user_id'][1], 'total': rec.get('amount_total_sum', 0.0)})

        currency = env.company.currency_id
        return {
            'hero': {
                'inventory_count': inventory_count,
                'inventory_cost': inventory_cost,
                'expected_revenue': expected_revenue,
                'available': len(available_cars),
                'reserved': len(reserved_cars),
                'sold_month': sold_this_month,
                'change': round(percent_change, 1),
            },
            'alerts': alerts,
            'sales_trend': sales_trend,
            'stock_distribution': stock_distribution,
            'top_models': top_models_data,
            'salespeople': salespeople,
            'currency': {'id': currency.id, 'symbol': currency.symbol},
        }
