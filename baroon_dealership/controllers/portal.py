from odoo import _, http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class BaroonCustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'car_reservation_count' in counters:
            partner = request.env.user.partner_id.commercial_partner_id
            domain = [
                ('partner_id', 'child_of', partner.id),
                ('order_line.car_lot_id', '!=', False),
            ]
            values['car_reservation_count'] = request.env['sale.order'].sudo().search_count(domain)
        return values

    @http.route(['/my/car-reservations', '/my/car-reservations/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_car_reservations(self, page=1, sortby='date', **kw):
        partner = request.env.user.partner_id.commercial_partner_id
        values = self._prepare_portal_layout_values()
        sale_order_model = request.env['sale.order'].sudo()

        domain = [
            ('partner_id', 'child_of', partner.id),
            ('order_line.car_lot_id', '!=', False),
        ]

        sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc, id desc'},
            'name': {'label': _('Reference'), 'order': 'name desc'},
            'status': {'label': _('Status'), 'order': 'state asc, id desc'},
        }
        sortby = sortby if sortby in sortings else 'date'
        order = sortings[sortby]['order']

        total = sale_order_model.search_count(domain)
        pager = portal_pager(url="/my/car-reservations", total=total, page=page, step=20, url_args={'sortby': sortby})
        orders = sale_order_model.search(domain, order=order, limit=20, offset=pager['offset'])
        values.update({
            'orders': orders,
            'page_name': 'car_reservations',
            'pager': pager,
            'default_url': '/my/car-reservations',
            'sortings': sortings,
            'sortby': sortby,
            'page': page,
        })
        return request.render('baroon_dealership.portal_my_car_reservations', values)

    @http.route(['/my/car-reservations/<int:order_id>/cancel'], type='http', auth='user', website=True, methods=['POST'])
    def portal_cancel_car_reservation(self, order_id, **post):
        partner = request.env.user.partner_id.commercial_partner_id
        order = request.env['sale.order'].sudo().browse(order_id)
        if not order.exists() or order.partner_id.commercial_partner_id != partner:
            return request.redirect('/my/car-reservations')
        if order.state not in ('draft', 'sent'):
            return request.redirect('/my/car-reservations')
        order.message_post(body=_('Reservation cancelled from website portal by the customer.'))
        order.action_cancel()
        return request.redirect('/my/car-reservations')
