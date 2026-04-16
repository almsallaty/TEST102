# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import pytz
from datetime import datetime
from odoo import http
from odoo.http import request

def _utc_to_local(dt):
    if not dt:
        return False

    user_tz = pytz.timezone(request.env.user.tz or 'UTC')
    utc_dt = pytz.UTC.localize(dt)
    local_dt = utc_dt.astimezone(user_tz)

    return local_dt.replace(tzinfo=None)

class VehicleContractController(http.Controller):
    """Vehicle contract controller"""

    @http.route('/get/contract/data', type='jsonrpc', auth="user")
    def get_contract_data(self):
        """
        Retrieve vehicle contract data for Gantt chart visualization.
        """

        data = []
        selected_company_ids = request.httprequest.cookies.get('cids')
        if selected_company_ids:
            company_ids = list(map(int, selected_company_ids.split('-')))
        else:
            company_ids = [request.env.company.id]

        fleet_vehicles = request.env['fleet.vehicle'].sudo().search([('company_id', 'in', company_ids)])
        count = 1

        today_date = datetime.today()
        for vehicle in fleet_vehicles:
            my_bookings = request.env['vehicle.contract'].sudo().search(
                [('vehicle_id', '=', vehicle.id),
                 ('status', 'in', ['b_in_progress', 'c_return']),
                 ('end_date', '>=', today_date),
                 ('company_id', 'in', company_ids)
                 ])

            # Always add the vehicle (parent) to the data
            parent_count = count
            data.append({
                'id': count,
                'text': vehicle.name,
                'order': vehicle.id,
                'open': True,
                "color": "#0dcaf0",
                "prop": "main"
            })
            count += 1

            # Add bookings if they exist
            if my_bookings:
                for booking in my_bookings:
                    start = _utc_to_local(booking.start_date)
                    end = _utc_to_local(booking.end_date)
                    duration = (booking.end_date - booking.start_date).total_seconds() / 3600
                    
                    # ✅ إضافة الحقول الجديدة
                    customer_name = booking.customer_id.name if booking.customer_id else ''
                    reference_no = booking.reference_no or ''
                    
                    data.append({
                        'id': count,
                        'text': booking.reference_no,
                        'start_date': start.strftime("%d-%m-%Y %H:%M:%S"),
                        'end_date': end.strftime("%d-%m-%Y %H:%M:%S"),
                        'duration': duration,
                        'duration_hours': duration,
                        'order': booking.id,
                        'progress': 0.5,
                        'parent': parent_count,
                        "color": "#0dcaf0",
                        "prop": "sub",
                        # ✅ الحقول الجديدة
                        'reference_no': reference_no,
                        'customer_name': customer_name,
                    })
                    count += 1

        return {
            'data': data
        }

    @http.route('/get/vehicle/status/by/date', type='jsonrpc', auth='user')
    def get_vehicle_status_by_date(self, **kw):
        """
        Retrieve vehicle contract data filtered by date range for Gantt chart visualization.
        """

        data = []
        selected_company_ids = request.httprequest.cookies.get('cids')
        if selected_company_ids:
            company_ids = list(map(int, selected_company_ids.split('-')))
        else:
            company_ids = [request.env.company.id]

        start_date = datetime.strptime(kw.get('start_date'), '%d-%m-%Y')
        end_date = datetime.strptime(kw.get('end_date'), '%d-%m-%Y').replace(hour=23, minute=59, second=59)

        fleet_vehicles = request.env['fleet.vehicle'].sudo().search([('company_id', 'in', company_ids)])
        count = 1

        for vehicle in fleet_vehicles:
            my_bookings = request.env['vehicle.contract'].sudo().search(
                [('vehicle_id', '=', vehicle.id),
                 ('status', 'in', ['b_in_progress', 'c_return']),
                 ('start_date', '>=', start_date),
                 ('start_date', '<=', end_date),
                 ('company_id', 'in', company_ids)])

            # Always add the vehicle (parent) to the data
            parent_count = count
            data.append({
                'id': count,
                'text': vehicle.name,
                'order': vehicle.id,
                'open': True,
                "color": "#0dcaf0",
                "prop": "main"
            })
            count += 1

            # Add bookings if they exist
            if my_bookings:
                for booking in my_bookings:
                    start = _utc_to_local(booking.start_date)
                    end = _utc_to_local(booking.end_date)
                    duration = (booking.end_date - booking.start_date).total_seconds() / 3600
                    
                    # ✅ إضافة الحقول الجديدة
                    customer_name = booking.customer_id.name if booking.customer_id else ''
                    reference_no = booking.reference_no or ''
                    
                    data.append({
                        'id': count,
                        'text': booking.reference_no,
                        'start_date': start.strftime("%d-%m-%Y %H:%M:%S"),
                        'end_date': end.strftime("%d-%m-%Y %H:%M:%S"),
                        'duration': duration,
                        'duration_hours': duration,
                        'order': booking.id,
                        'progress': 0.5,
                        'parent': parent_count,
                        "color": "#0dcaf0",
                        "prop": "sub",
                        # ✅ الحقول الجديدة
                        'reference_no': reference_no,
                        'customer_name': customer_name,
                    })
                    count += 1

        return {
            'data': data
        }
