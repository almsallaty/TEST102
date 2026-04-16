# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import http, fields
from odoo.http import request


class RentalScratchWebsite(http.Controller):
    """ Rental Scratch Website """

    # Rental Scratch Report Controller
    @http.route('/rental/customer/sign/<string:access_token>', type='http', auth='public', website=True)
    def cus_sign_page(self, access_token):
        """Customer Sign Page"""
        contracts = request.env['vehicle.contract'].sudo().search([('access_token', '=', access_token)], limit=1)
        if not contracts:
            return request.not_found()
        return request.render("vehicle_rental.rental_contract_scratch_customer_sign_template", {'contracts': contracts})

    @http.route('/vehicle-rental/protocol-form/<string:access_token>/Vehicle scratch protocol form', type='http',
                auth='public')
    def vehicle_scratch_protocol_form(self, access_token):
        """Vehicle Scratch Protocol Form"""
        contract_scratch = request.env['vehicle.contract'].sudo().search([('access_token', '=', access_token)])
        if not contract_scratch:
            return request.redirect('/')
        pdf_content = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            "vehicle_rental.action_rental_scratch_report_template", contract_scratch.id)
        response = request.make_response(pdf_content, headers=[('Content-Type', 'application/pdf')])
        response.headers.add('Content-Disposition', 'inline; filename=Rental Contract Protocol.pdf')
        return response

    @http.route("/vehicle-rental/scratch/<string:access_token>/accept", type='jsonrpc', auth="public", website=True)
    def vehicle_contract_scratch_report_accept(self, access_token=None, **kw):
        """Accept Scratch Report"""
        rent_contracts = request.env['vehicle.contract'].sudo().search([('access_token', '=', access_token)])
        if rent_contracts:
            rent_contracts.write({
                'customer_signature': kw.get('signature'),
                'customer_signed_by': kw.get('name'),
                'customer_signed_date': fields.Date.today(),
            })
        return {
            'force_refresh': True,
            'redirect_url': f"/rental/customer/sign/{access_token}",
        }


class ImageEditorController(http.Controller):
    """Image Editor Controller"""

    @http.route('/image_editor/save', type='jsonrpc', auth='user')
    def save_image(self, record_id, model, field_name, image_data):
        """Scratch Report Save image"""
        record = request.env[model].browse(int(record_id))
        if record.exists() and field_name in record._fields:
            img_base64 = image_data.split(",")[1]
            record.write({field_name: img_base64})
            return {"status": "success"}
        return {"status": "error", "message": f"Invalid model/field: {model}.{field_name}"}
