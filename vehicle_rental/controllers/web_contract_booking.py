# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import logging
import pytz
import math
from datetime import datetime, date, time

from odoo.addons.portal.controllers.portal import CustomerPortal, pager

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


def validate_mandatory_fields(mandate_fields, kw):
    """Validate mandatory fields"""
    data = {}
    for key, value in mandate_fields.items():
        if not kw.get(key):
            return f"Mandatory field {value} is missing", {}
        data[key] = kw.get(key)
    return None, data


def get_auto_price_type(total_hours):
    """
    Auto-detect the appropriate price type based on rental duration in hours.

    Rules:
      - < 24 hours              → hour
      - 24 hours to < 7 days   → day
      - 7 days to < 28 days    → week
      - 28 days to < 365 days  → month
      - >= 365 days             → year
    """
    if total_hours < 24:
        return 'hour'
    total_days = total_hours / 24
    if total_days < 7:
        return 'day'
    elif total_days < 28:
        return 'week'
    elif total_days < 365:
        return 'month'
    else:
        return 'year'


def get_price_type_label(price_type):
    """Return a human-readable label for the auto-detected price type."""
    labels = {
        'hour': 'Hourly Rate',
        'day': 'Daily Rate',
        'week': 'Weekly Rate',
        'month': 'Monthly Rate',
        'year': 'Yearly Rate',
    }
    return labels.get(price_type, price_type.title())


class WebContractBooking(CustomerPortal):
    """Web Contract Booking"""

    @staticmethod
    def _get_initial_values():
        """ Get Initial Values """
        vehicle_categories = request.env['fleet.vehicle.model.category'].sudo().search([])
        return {
            'vehicle_categories': vehicle_categories,
        }

    @http.route('/web/booking-enquiry', auth='public', website=True, type='http')
    def contract_booking_enquiry(self):
        """Contract Booking Enquiry"""
        values = self._get_initial_values()
        return request.render('vehicle_rental.booking_enquiry_web_template', values)

    @http.route(['/get/available/vehicles', '/get/available/vehicles/page/<int:page>'], type='http',
                auth='public', website=True)
    def get_available_vehicles(self, page=0, **kw):
        """Return available vehicles between given start_date and end_date."""
        values = self._get_initial_values()
        error = None
        # Mandatory field validation
        mandate_fields = {
            'start_date': "Start Date",
            'end_date': "End Date",
        }
        error, data = validate_mandatory_fields(mandate_fields, kw)
        if error:
            values.update({'error': error, 'kw': kw})
            return request.render('vehicle_rental.searched_fleet_vehicles', values)

        try:
            start_dt = datetime.strptime(kw.get('start_date'), "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(kw.get('end_date'), "%Y-%m-%d %H:%M")
        except ValueError:
            values.update({'error': "Invalid date format.", 'kw': kw})
            return request.render('vehicle_rental.searched_fleet_vehicles', values)

        now = datetime.now()

        if start_dt < now:
            values.update({'error': "Start date and time cannot be in the past.", 'kw': kw})
            return request.render('vehicle_rental.searched_fleet_vehicles', values)

        if end_dt < start_dt:
            values.update({'error': "End date and time cannot be earlier than start date and time.", 'kw': kw})
            return request.render('vehicle_rental.searched_fleet_vehicles', values)

        # Auto-detect price type from date range
        total_seconds = (end_dt - start_dt).total_seconds()
        total_hours = total_seconds / 3600
        auto_price_type = get_auto_price_type(total_hours)
        price_type_label = get_price_type_label(auto_price_type)

        # Map auto_price_type to the vehicle field for price filtering
        price_type_field_map = {
            'hour': 'rent_hour',
            'day': 'rent_day',
            'week': 'rent_week',
            'month': 'rent_month',
            'year': 'rent_year',
        }
        price_type_field = price_type_field_map.get(auto_price_type, 'rent_day')

        # Find already booked vehicles
        booked_contracts = request.env['vehicle.contract'].sudo().search([
            ('start_date', '<=', end_dt),
            ('end_date', '>=', start_dt),
            ('status', '=', 'b_in_progress')
        ])
        booked_vehicle_ids = booked_contracts.mapped('vehicle_id.id')
        vehicle_domain = [
            ('id', 'not in', booked_vehicle_ids),
            ('status', '=', 'available')]

        if kw.get('vehicle_category_id') and str(kw.get('vehicle_category_id')).isdigit():
            vehicle_domain.append(('category_id', '=', int(kw.get('vehicle_category_id'))))

        if kw.get('seat_number') and str(kw.get('seat_number')).isdigit():
            vehicle_domain.append(('seats', '>=', int(kw.get('seat_number'))))

        # Handle price filter using the auto-detected price type field
        if kw.get('price'):
            price_range = kw.get('price')
            if price_range == '0-50':
                vehicle_domain.append((price_type_field, '>=', 0))
                vehicle_domain.append((price_type_field, '<=', 50))
            elif price_range == '50-100':
                vehicle_domain.append((price_type_field, '>', 50))
                vehicle_domain.append((price_type_field, '<=', 100))
            elif price_range == '100+':
                vehicle_domain.append((price_type_field, '>', 100))

        if kw.get('tr'):
            vehicle_domain.append(('transmission', '=', kw.get('tr')))

        if kw.get('ft'):
            vehicle_domain.append(('fuel_type', '=', kw.get('ft')))

        if kw.get('seats'):
            seats_value = kw.get('seats').strip()
            if seats_value.endswith('_plus'):
                try:
                    min_seats = int(seats_value.replace('_plus', ''))
                    vehicle_domain.append(('seats', '>=', min_seats))
                except ValueError:
                    return request.redirect('/web/booking-enquiry')

        fleets_per_page = request.env['ir.config_parameter'].sudo().get_param(
            'vehicle_rental.pagination_item_per_page') or "5"
        vehicle_count = request.env['fleet.vehicle'].sudo().search_count(vehicle_domain)

        pager = request.website.pager(
            url=request.httprequest.path.partition('page/')[0],
            total=vehicle_count,
            page=page,
            step=int(fleets_per_page),
            url_args=kw,
        )

        vehicles = request.env['fleet.vehicle'].sudo().search(
            vehicle_domain, offset=pager['offset'], limit=int(fleets_per_page))
        values.update({
            'fleets_per_page': fleets_per_page,
            'vehicles': vehicles,
            'kw': kw,
            'pager': pager,
            'auto_price_type': auto_price_type,
            'price_type_label': price_type_label,
        })
        return request.render('vehicle_rental.searched_fleet_vehicles', values)

    @http.route('/vehicle/details/<string:access_token>', type='http', auth='public', website=True)
    def get_vehicle_details(self, access_token, **kw):
        """Get vehicle details"""
        if not access_token:
            _logger.warning("Access Token not found")
            return request.redirect('/web/booking-enquiry')
        if not kw.get('start_date') and kw.get('end_date'):
            _logger.warning("Start and end date not found")
            return request.redirect('/web/booking-enquiry')

        try:
            start_date = datetime.strptime(kw.get('start_date'), "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(kw.get('end_date'), "%Y-%m-%d %H:%M")
        except ValueError as e:
            _logger.warning(f"Date Format mismatch. {e}", exc_info=True)
            return request.redirect('/web/booking-enquiry')

        now = datetime.now()

        if start_date < now:
            _logger.warning(f"Start date {start_date} is before current datetime {now}")
            return request.redirect('/web/booking-enquiry')

        if end_date < now:
            _logger.warning(f"End date {end_date} is before current datetime {now}")
            return request.redirect('/web/booking-enquiry')

        if end_date < start_date:
            _logger.warning(f"End date {end_date} is before start date {start_date}")
            return request.redirect('/web/booking-enquiry')

        # Auto-detect price type
        total_seconds = (end_date - start_date).total_seconds()
        total_hours = total_seconds / 3600
        auto_price_type = get_auto_price_type(total_hours)
        price_type_label = get_price_type_label(auto_price_type)

        vehicle = request.env['fleet.vehicle'].sudo().search([
            ('access_token', '=', access_token)
        ], limit=1)

        if not vehicle:
            return request.redirect('/web/booking-enquiry')

        return request.render('vehicle_rental.vehicle_details_template', {
            'vehicle': vehicle,
            'kw': kw,
            'auto_price_type': auto_price_type,
            'price_type_label': price_type_label,
        })

    @http.route('/vehicle/enquiry/<string:access_token>', website=True, auth='public', type='http')
    def get_vehicle_for_enquiry(self, access_token, **kw):
        """Get vehicle for enquiries"""
        if not kw.get('start_date') and kw.get('end_date'):
            _logger.warning("Start and end date not found")
            return request.redirect('/web/booking-enquiry')

        try:
            start_date = datetime.strptime(kw.get('start_date'), "%Y-%m-%d %H:%M")
            end_date = datetime.strptime(kw.get('end_date'), "%Y-%m-%d %H:%M")
        except ValueError as e:
            _logger.warning(f"Date Format mismatch. {e}", exc_info=True)
            return request.redirect('/web/booking-enquiry')

        today = datetime.now()

        if start_date < today:
            _logger.warning(f"Start date {start_date} is before today's date {today}")
            return request.redirect('/web/booking-enquiry')

        if end_date < today:
            _logger.warning(f"End date {end_date} is before today's date {today}")
            return request.redirect('/web/booking-enquiry')

        if end_date < start_date:
            _logger.warning(f"End date {end_date} is before start date {start_date}")
            return request.redirect('/web/booking-enquiry')

        if not access_token:
            return request.redirect('/web/booking-enquiry')

        vehicle = request.env['fleet.vehicle'].sudo().search([
            ('access_token', '=', access_token)
        ], limit=1)

        if not vehicle:
            return request.redirect('/web/booking-enquiry')

        existing_contract = request.env['vehicle.contract'].sudo().search(
            [('vehicle_id', '=', vehicle.id),
             ('status', '=', 'b_in_progress'), ('start_date', '<=', kw.get('end_date')),
             ('end_date', '>=', kw.get('start_date'))], limit=1)

        if existing_contract:
            _logger.warning("""There is already a running contract for this vehicle""")
            return request.redirect('/web/booking-enquiry')

        # Auto-detect price type from the date range
        total_seconds = (end_date - start_date).total_seconds()
        total_hours = total_seconds / 3600
        total_days = total_seconds / 86400
        auto_price_type = get_auto_price_type(total_hours)
        price_type_label = get_price_type_label(auto_price_type)

        renting_days = math.ceil(total_days) or 1
        renting_hours = math.ceil(total_hours) or 1
        renting_weeks = round(total_days / 7, 2)
        months = (
                (end_date.year - start_date.year) * 12 +
                (end_date.month - start_date.month)
        )
        renting_months = months + round(
                (end_date.day - start_date.day) / 30, 2
        )
        renting_years = round(total_days / 365, 2)

        if auto_price_type == 'hour':
            price = vehicle.rent_hour
            final_price = round(renting_hours * price, 2)
            price_string = 'Hourly'
        elif auto_price_type == 'day':
            price = vehicle.rent_day
            final_price = round(renting_days * price, 2)
            price_string = 'Daily'
        elif auto_price_type == 'week':
            price = vehicle.rent_week
            final_price = round(renting_weeks * price, 2)
            price_string = 'Weekly'
        elif auto_price_type == 'month':
            price = vehicle.rent_month
            final_price = round(renting_months * price, 2)
            price_string = 'Monthly'
        elif auto_price_type == 'year':
            price = vehicle.rent_year
            final_price = round(renting_years * price, 2)
            price_string = 'Yearly'
        else:
            price = vehicle.rent_day
            final_price = round(renting_days * price, 2)
            price_string = 'Daily'

        res_config = request.env['ir.config_parameter']
        terms_link = res_config.sudo().get_param('vehicle_rental.terms_conditions_link') or '#'
        privacy_policy_link = res_config.sudo().get_param('vehicle_rental.privacy_policy_link') or '#'

        return request.render('vehicle_rental.vehicle_enquiry_booking', {
            'vehicle': vehicle,
            'kw': kw,
            'price': price,
            'renting_days': renting_days,
            'renting_hours': renting_hours,
            'renting_weeks': renting_weeks,
            'renting_months': renting_months,
            'renting_years': renting_years,
            'final_price': final_price,
            'price_string': price_string,
            'auto_price_type': auto_price_type,
            'price_type_label': price_type_label,
            'terms_link': terms_link,
            'privacy_policy_link': privacy_policy_link
        })

    @http.route("/rental/booking-enquiry", type="http", auth="public", website=True)
    def rental_booking_enquiry_submit(self, **kw):
        """Handle rental booking enquiry form submission."""
        values = self._get_initial_values()

        # Get Default Config Values
        icp = request.env["ir.config_parameter"].sudo()
        tz = None

        salesperson_id = icp.get_param("vehicle_rental.salesperson_id")
        sale_team_id = icp.get_param("vehicle_rental.sale_team_id")

        salesperson_id = (int(salesperson_id) if salesperson_id else False)
        sale_team_id = (int(sale_team_id) if sale_team_id else False)

        # Define mandatory fields for validation
        mandatory_fields = {
            "start_date": "Start Date",
            "end_date": "End Date",
            "vehicle_id": "Vehicle",
            "contact_name": "Customer Name",
            "email_from": "Email",
            "phone": "Phone Number"
        }
        if salesperson_id:
            salesperson_user_id = request.env['res.users'].sudo().browse(salesperson_id)
            tz = salesperson_user_id.tz

        error, lead_data = validate_mandatory_fields(mandatory_fields, kw)
        if error:
            values["error"] = error
            kw.update(values)
            return request.render("vehicle_rental.booking_enquiry_web_template", kw)

        try:
            start_date_str = kw.get('start_date')
            end_date_str = kw.get('end_date')

            start_dt_naive = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M")
            end_dt_naive = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M")

        except ValueError as e:
            _logger.warning(f"Date Format mismatch. {e}", exc_info=True)
            values["error"] = "Invalid date format"
            kw.update(values)
            return request.render("vehicle_rental.booking_enquiry_web_template", kw)

        existing_contract = request.env['vehicle.contract'].sudo().search(
            [('vehicle_id', '=', int(kw.get('vehicle_id'))),
             ('status', '=', 'b_in_progress'),
             ('start_date', '<=', end_dt_naive),
             ('end_date', '>=', start_dt_naive)], limit=1)

        if existing_contract:
            _logger.warning(
                """There is already a running contract for this vehicle on given start date and date""")
            return request.redirect('/web/booking-enquiry')

        company = request.env.company

        country_id = False
        state_id = False
        if kw.get("country_id"):
            country_id = int(kw.get("country_id"))
        if kw.get("state_id"):
            state_id = int(kw.get("state_id"))
        if not country_id and company.country_id:
            country_id = company.country_id.id
        if not state_id and company.state_id:
            state_id = company.state_id.id

        # fleet_price_type is now auto-detected and passed as hidden field from the form
        fleet_price_type = kw.get("fleet_price_type")
        if not fleet_price_type:
            # Fallback: re-detect from dates if missing
            total_seconds = (end_dt_naive - start_dt_naive).total_seconds()
            fleet_price_type = get_auto_price_type(total_seconds / 3600)

        lead_data.update({
            "name": f"Enquiry for {kw.get('vehicle_name')}",
            "contact_name": kw.get("contact_name"),
            "phone": kw.get("phone"),
            "email_from": kw.get("email_from"),
            "type": "lead",

            "user_id": salesperson_id,
            "team_id": sale_team_id,

            "company_id": company.id,
            "country_id": country_id,
            "state_id": state_id,

            "fleet_price_type": fleet_price_type,
            "start_date": start_dt_naive,
            "end_date": end_dt_naive,
        })
        try:
            lead_data.update({
                "rent_price": float(kw.get("rent_price", 0.0)),
                "total_price": float(kw.get("total_price", 0.0)),
                "fleet_renting_days": int(kw.get("fleet_renting_days", 0)),
                'vehicle_id': int(kw.get('vehicle_id')),
                'is_website_enquiry': True,
            })
        except (ValueError, TypeError) as e:
            _logger.warning("Price parsing issue in booking enquiry: %s", e)

        if request.env.user.id != request.env.ref("base.public_user").id:
            lead_data["partner_id"] = request.env.user.partner_id.id

        lead = request.env["crm.lead"].sudo().create(lead_data)
        lead.sudo().with_context(start_date=start_dt_naive,
                                 end_date=end_dt_naive).action_enquiry_submitted_mail_notification()
        return request.redirect(f"/lead/success/{lead.access_token}")

    @http.route("/lead/success/<string:access_token>", type="http", auth="public", website=True)
    def rental_lead_success_page(self, access_token):
        """Rental lead success page"""
        if not access_token:
            return request.redirect('/')
        leads = request.env['crm.lead'].sudo().search([('access_token', '=', access_token)], limit=1)
        if not leads:
            return request.redirect('/')
        return request.render("vehicle_rental.rental_booking_enquiry_success", {"lead": leads})

    def local_datetime_to_utc_from_string(self, datetime_str, tz=None):
        """
        Convert local datetime string (YYYY-MM-DD HH:MM) to UTC naive datetime for Odoo
        """
        local_dt_naive = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        user_tz = pytz.timezone(tz or request.env.user.tz or 'UTC')
        local_dt = user_tz.localize(local_dt_naive)
        utc_dt = local_dt.astimezone(pytz.UTC).replace(tzinfo=None)
        return utc_dt

    @http.route(["/rental/booking-enquiries", "/rental/booking-enquiries/page/<int:page>"],
                type="http", auth="public", website=True)
    def rental_booking_enquiry_list(self, page=1, **kw):
        """Display list of rental booking enquiries for the logged-in customer."""
        partner_id = request.env.user.partner_id.id

        domain = [
            ("partner_id", "=", partner_id),
            ("type", "=", "lead"),
            ("vehicle_id", "!=", False),
        ]
        page_size = 10
        offset = (page - 1) * page_size

        search = kw.get('search')
        if search:
            domain = domain + ['|', '|', '|',
                               ('name', 'ilike', search),
                               ('vehicle_id', 'ilike', search),
                               ('category_id', 'ilike', search),
                               ('seats', 'ilike', search)]

        lead = request.env['crm.lead'].sudo()
        total_enquiries = lead.search_count(domain)
        enquiries = lead.search(domain, limit=page_size, offset=offset)
        pager_details = pager(
            url="/rental/booking-enquiries",
            total=total_enquiries,
            page=page,
            step=page_size,
            scope=5)
        return request.render("vehicle_rental.rental_booking_enquiry_list", {
            "enquiries": enquiries,
            "page_name": "rental_booking_enquiry_list",
            "pager": pager_details,
        })

    @http.route("/rental/booking-inquiry/<string:access_token>", type="http", auth="user",
                website=True)
    def rental_booking_inquiry(self, access_token):
        """Display rental booking inquiry details for the logged-in user."""
        lead = request.env["crm.lead"].sudo().search([
            ("access_token", "=", access_token),
            ('type', '=', 'lead'),
            ("partner_id", "=", request.env.user.partner_id.id)
        ], limit=1)
        if not lead:
            return request.redirect("/")
        user_leads = request.env["crm.lead"].sudo().search([
            ("partner_id", "=", request.env.user.partner_id.id),
            ('type', '=', 'lead')])
        lead_ids = user_leads.ids
        current_index = lead_ids.index(lead.id) if lead.id in lead_ids else -1
        if current_index == -1:
            return request.redirect("/")
        prev_url = None
        next_url = None
        if current_index > 0:
            prev_url = f"/rental/booking-inquiry/{user_leads[current_index - 1].access_token}"
        if current_index < len(lead_ids) - 1:
            next_url = f"/rental/booking-inquiry/{user_leads[current_index + 1].access_token}"

        return request.render("vehicle_rental.vehicle_booking_enquiry_detail", {
            "lead": lead,
            "page_name": "rental_booking_inquiry",
            "prev_record": prev_url,
            "next_record": next_url,
        })


class VehicleBookingEnquiryPortal(CustomerPortal):
    """ Vehicle Booking Enquiry Portal """

    def _prepare_home_portal_values(self, counters):
        """Prepare portal values including vehicle enquiry count."""
        values = super()._prepare_home_portal_values(counters)
        count = request.env['crm.lead'].sudo().search_count([
            ('partner_id', '=', request.env.user.partner_id.id),
            ('type', '=', 'lead'),
            ('vehicle_id', '!=', False),
        ])
        if counters:
            values['count'] = count
        return values