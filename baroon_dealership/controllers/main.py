from odoo import _, http
from odoo.http import request
from werkzeug.exceptions import NotFound
from werkzeug.urls import url_encode


class CarSaleWebsiteController(http.Controller):

    UPCOMING_STATES = ['incoming', 'in_shipment', 'customs', 'received', 'in_preparation']
    PUBLIC_STATES = UPCOMING_STATES + ['available', 'reserved']

    def _base_domain(self):
        return [
            ('is_car_vehicle', '=', True),
            ('website_published', '=', True),
            ('active', '=', True),
            ('car_status', 'in', self.PUBLIC_STATES),
        ]

    def _prepare_portal_quote(self, lead, lot):
        user = request.env.user
        if not user or user._is_public():
            return False
        partner = user.partner_id.commercial_partner_id
        if not partner:
            return False
        existing = request.env['sale.order'].sudo().search([
            ('partner_id', 'child_of', partner.id),
            ('order_line.car_lot_id', '=', lot.id),
            ('state', 'in', ['draft', 'sent', 'sale', 'done']),
        ], limit=1)
        if existing:
            if not existing.opportunity_id:
                existing.opportunity_id = lead.id
            return existing
        order = request.env['sale.order'].sudo().create({
            'partner_id': partner.id,
            'opportunity_id': lead.id,
            'origin': lead.name,
            'note': lead.description or False,
        })
        request.env['sale.order.line'].sudo().create({
            'order_id': order.id,
            'product_id': lot.product_id.id,
            'product_uom_qty': 1.0,
            'price_unit': lot.sale_price or lot.product_id.lst_price,
            'car_lot_id': lot.id,
            'name': _('%s • VIN %s') % (
                ' '.join(filter(None, [lot.car_brand, lot.car_model, lot.car_trim])).strip() or lot.product_id.display_name,
                lot.name or '-',
            ),
        })
        lead.message_post(body=_('Portal quotation %s created for website reservation.') % order.name)
        return order

    def _get_user_order_for_car(self, lot):
        user = request.env.user
        if not user or user._is_public():
            return request.env['sale.order']
        partner = user.partner_id.commercial_partner_id
        return request.env['sale.order'].sudo().search([
            ('partner_id', 'child_of', partner.id),
            ('order_line.car_lot_id', '=', lot.id),
            ('state', 'in', ['draft', 'sent', 'sale', 'done']),
        ], limit=1)

    @http.route(['/cars'], type='http', auth='public', website=True, sitemap=True)
    def cars_listing(self, **kwargs):
        lot_model = request.env['stock.lot'].sudo()
        domain = self._base_domain()

        search = (kwargs.get('search') or '').strip()
        brand = (kwargs.get('brand') or '').strip()
        model_name = (kwargs.get('model') or '').strip()
        year = (kwargs.get('year') or '').strip()
        status = (kwargs.get('status') or '').strip()
        min_price = (kwargs.get('min_price') or '').strip()
        max_price = (kwargs.get('max_price') or '').strip()

        if search:
            domain += ['|', '|', '|', '|',
                       ('name', 'ilike', search),
                       ('plate_number', 'ilike', search),
                       ('engine_number', 'ilike', search),
                       ('car_brand', 'ilike', search),
                       ('car_model', 'ilike', search)]
        if brand:
            domain.append(('car_brand', '=ilike', brand))
        if model_name:
            domain.append(('car_model', '=ilike', model_name))
        if year:
            try:
                domain.append(('year', '=', int(year)))
            except ValueError:
                pass
        if status:
            domain.append(('car_status', '=', status))
        if min_price:
            try:
                domain.append(('sale_price', '>=', float(min_price)))
            except ValueError:
                pass
        if max_price:
            try:
                domain.append(('sale_price', '<=', float(max_price)))
            except ValueError:
                pass

        cars = lot_model.search(domain, order='website_sequence asc, create_date desc, id desc')
        all_cars = lot_model.search(self._base_domain(), order='car_brand asc, car_model asc, year desc')
        values = {
            'cars': cars,
            'search': search,
            'selected_brand': brand,
            'selected_model': model_name,
            'selected_year': year,
            'selected_status': status,
            'selected_min_price': min_price,
            'selected_max_price': max_price,
            'brands': [b for b in sorted(set(filter(None, all_cars.mapped('car_brand'))))],
            'models': [m for m in sorted(set(filter(None, all_cars.mapped('car_model'))))],
            'years': sorted(set(filter(None, all_cars.mapped('year'))), reverse=True),
            'statuses': [item for item in lot_model._fields['car_status'].selection if item[0] in self.PUBLIC_STATES],
            'upcoming_states': self.UPCOMING_STATES,
        }
        return request.render('baroon_dealership.website_cars_listing', values)

    @http.route(['/cars/<int:lot_id>'], type='http', auth='public', website=True, sitemap=True)
    def car_detail(self, lot_id, **kwargs):
        lot = request.env['stock.lot'].sudo().browse(lot_id)
        if not lot.exists() or not lot.website_published or not lot.active or not lot.is_car_vehicle:
            raise NotFound()

        existing_order = self._get_user_order_for_car(lot)
        values = {
            'car': lot,
            'reserve_success': kwargs.get('reserve_success'),
            'reserve_error': kwargs.get('reserve_error'),
            'can_reserve_online': lot.car_status == 'available',
            'coming_soon': lot.car_status in self.UPCOMING_STATES,
            'existing_order': existing_order,
        }
        return request.render('baroon_dealership.website_car_detail', values)

    @http.route(['/cars/<int:lot_id>/reserve'], type='http', auth='public', website=True, methods=['POST'])
    def reserve_car(self, lot_id, **post):
        lot = request.env['stock.lot'].sudo().browse(lot_id)
        if not lot.exists() or not lot.website_published or not lot.active or not lot.is_car_vehicle:
            raise NotFound()
        if lot.car_status != 'available':
            return request.redirect('/cars/%s?%s' % (
                lot.id,
                url_encode({'reserve_error': _('This car is not currently open for website reservation. Please contact us directly.')})
            ))

        partner_name = (post.get('partner_name') or '').strip()
        phone = (post.get('phone') or '').strip()
        email = (post.get('email') or '').strip()
        note = (post.get('note') or '').strip()
        if not partner_name:
            return request.redirect('/cars/%s?%s' % (lot.id, url_encode({'reserve_error': _('Please enter your name.')})))
        if not phone and not email:
            return request.redirect('/cars/%s?%s' % (lot.id, url_encode({'reserve_error': _('Please provide a phone number or email address.')})))

        lead = request.env['crm.lead'].sudo().create({
            'name': _('Website reservation for %s') % (lot.display_name_website or lot.display_name),
            'type': 'opportunity',
            'contact_name': partner_name,
            'partner_name': partner_name,
            'phone': phone,
            'email_from': email,
            'description': note,
            'car_lot_id': lot.id,
        })
        lead.message_post(body=_('Created from website reservation form for VIN %s.') % (lot.name or lot.display_name))

        quotation = self._prepare_portal_quote(lead, lot)
        success_msg = _('Your reservation request was received. Our team will contact you shortly.')
        if quotation:
            success_msg = _('Your reservation request was received and added to My Reservations.')
        return request.redirect('/cars/%s?%s' % (lot.id, url_encode({'reserve_success': success_msg})))
