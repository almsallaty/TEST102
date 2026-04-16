# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import fields, api, models


class LeadRentalContract(models.TransientModel):
    """Lead Rental Contract"""
    _name = 'lead.rental.contract'
    _description = __doc__

    crm_lead_id = fields.Many2one('crm.lead', string="Lead")
    partner_id = fields.Many2one("res.partner", string="Customer")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle",
                                 domain="[('status', '=', 'available')]")
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")

    @api.model
    def default_get(self, field_names):
        """Set default values from crm lead"""
        res = super().default_get(field_names)
        active_id = self.env.context.get('active_id')
        if active_id:
            lead = self.env['crm.lead'].browse(active_id)
            if lead:
                res.update({
                    'crm_lead_id': lead.id,
                    'partner_id': lead.partner_id.id if lead.partner_id else False,
                    'start_date': lead.start_date,
                    'end_date': lead.end_date,
                    'vehicle_id': lead.vehicle_id.id if lead.vehicle_id else False,
                })
        return res

    def action_create_rental_contract(self):
        """Create rental contract from lead"""
        mapping = {
            'hour': 'hour',
            'day': 'days',
            'week': 'week',
            'month': 'month',
            'year': 'year',
            'kilometer': 'km',
            'mile': 'mi',
        }

        rent_type = mapping.get(self.crm_lead_id.fleet_price_type)
        minimum_km = self.vehicle_id.minimum_km_per_day or 0.0
        # Convert KM to Miles if rent type is miles
        if self.crm_lead_id.fleet_price_type == 'mi':
            minimum_km_per_day = minimum_km * 0.621371
        else:
            minimum_km_per_day = minimum_km

        contract = self.env['vehicle.contract'].create({
            'crm_lead_id': self.crm_lead_id.id,
            'customer_id': self.partner_id.id,
            'customer_phone': self.partner_id.phone,
            'customer_email': self.partner_id.email,
            'vehicle_id': self.vehicle_id.id,
            'vehicle_model_year': self.vehicle_id.model_year,
            'transmission': self.vehicle_id.transmission,
            'last_odometer': self.vehicle_id.odometer,
            'odometer_unit': self.vehicle_id.odometer_unit,
            'minimum_km_per_day': minimum_km_per_day,
            'fuel_type': self.vehicle_id.fuel_type,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'rent_type': rent_type,
            'rent': self.crm_lead_id.rent_price,
        })
        self.crm_lead_id.contract_id = contract.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'vehicle.contract',
            'res_id': contract.id,
            'view_mode': 'form',
            'target': 'current',
        }
