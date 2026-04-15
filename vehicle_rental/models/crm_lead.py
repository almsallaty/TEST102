# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import secrets
import math
from odoo import models, fields, api


class BookingEnquiryLead(models.Model):
    """Booking Enquiry Lead"""
    _inherit = 'crm.lead'
    _description = __doc__

    access_token = fields.Char()
    # Booking Enquiry Details
    vehicle_ids = fields.Many2many('fleet.vehicle', string="Vehicles",
                                   compute='_compute_available_vehicles')
    vehicle_id = fields.Many2one(
        'fleet.vehicle', string="Vehicle", copy=False,
        domain="[('id', 'not in', vehicle_ids), ('status', '=', 'available')]")
    category_id = fields.Many2one(related='vehicle_id.category_id', string="Category")
    seats = fields.Integer(related='vehicle_id.seats', string="Number of Seats")
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    contract_id = fields.Many2one('vehicle.contract', string="Contract")
    # Pricing Details
    rent_price = fields.Monetary(string="Price")
    fleet_renting_days = fields.Integer(string="Days", compute='_compute_fleet_renting_days')
    fleet_price_type = fields.Selection(
        [('hour', "Hourly"),
         ('day', "Daily"),
         ('week', "Weekly"),
         ('month', "Monthly"),
         ('year', "Yearly"),
         ('kilometer', "Kilometer"),
         ('mile', "Mile")], string="Price Type")
    total_price = fields.Monetary(string="Total Price", compute='_compute_total_price')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string=' Currency', related="company_id.currency_id")
    is_website_enquiry = fields.Boolean(string="Website Enquiry")

    rental_duration = fields.Float(string="Rental Duration", compute='_compute_rental_duration')

    @api.model_create_multi
    def create(self, vals_list):
        """Create claim record"""
        records = super().create(vals_list)
        for record in records:
            # Generate a URL-safe access token without underscores
            token = secrets.token_urlsafe(12).replace('_', '-')
            record.access_token = token
        return records

    @api.depends('vehicle_id', 'start_date', 'end_date')
    def _compute_available_vehicles(self):
        """Compute available vehicles"""
        for rec in self:
            contract_id = self.env['vehicle.contract'].search(
                [('start_date', '<=', rec.end_date), ('end_date', '>=', rec.start_date),
                 ('status', '=', 'b_in_progress')]).mapped('vehicle_id').mapped('id')
            rec.vehicle_ids = contract_id

    @api.depends('start_date', 'end_date')
    def _compute_fleet_renting_days(self):
        """Compute fleet renting days"""
        for rec in self:
            rec.fleet_renting_days = 0
            if rec.start_date and rec.end_date and rec.start_date <= rec.end_date:
                total_seconds = (rec.end_date - rec.start_date).total_seconds()
                renting_days = math.ceil(total_seconds / 86400)
                rec.fleet_renting_days = renting_days

    @api.depends('start_date', 'end_date', 'fleet_price_type')
    def _compute_rental_duration(self):
        """Compute rental durations"""
        for rec in self:
            rec.rental_duration = 0.0
            if not (rec.start_date and rec.end_date):
                continue
            if rec.start_date > rec.end_date:
                continue
            delta = rec.end_date - rec.start_date
            rental_days = math.ceil(delta.total_seconds() / 86400) or 1
            if rec.fleet_price_type == 'hour':
                rec.rental_duration = delta.total_seconds() / 3600
            elif rec.fleet_price_type == 'week':
                rec.rental_duration = rental_days / 7
            elif rec.fleet_price_type == 'month':
                months = (
                        (rec.end_date.year - rec.start_date.year) * 12 +
                        (rec.end_date.month - rec.start_date.month)
                )
                rec.rental_duration = months + (
                        (rec.end_date.day - rec.start_date.day) / 30
                )
            elif rec.fleet_price_type == 'year':
                rec.rental_duration = (rental_days / 365)
            rec.rental_duration = round(rec.rental_duration, 2)

    @api.depends('rent_price', 'fleet_price_type', 'fleet_renting_days',
                 'rental_duration', 'vehicle_id.minimum_km_per_day')
    def _compute_total_price(self):
        """Compute total rental price based on pricing type"""
        for rec in self:
            if not rec.rent_price:
                rec.total_price = 0.0
                continue
            total = 0.0
            # Time-based pricing
            price_mapping = {
                'day': rec.fleet_renting_days,
                'week': rec.rental_duration,
                'month': rec.rental_duration,
                'hour': rec.rental_duration,
                'year': rec.rental_duration,
            }
            if rec.fleet_price_type in price_mapping:
                multiplier = price_mapping.get(rec.fleet_price_type, 0.0)
                total = rec.rent_price * multiplier

            rec.total_price = round(total, 2)

    @api.onchange('fleet_price_type', 'vehicle_id')
    def onchange_fleet_price_types(self):
        """Onchange fleet price types"""
        for rec in self:
            if not rec.vehicle_id:
                continue
            price_fields = {
                'hour': rec.vehicle_id.rent_hour,
                'day': rec.vehicle_id.rent_day,
                'week': rec.vehicle_id.rent_week,
                'month': rec.vehicle_id.rent_month,
                'year': rec.vehicle_id.rent_year,
                'kilometer': rec.vehicle_id.rent_km,
                'mile': rec.vehicle_id.rent_mi,
            }
            rec.rent_price = price_fields.get(rec.fleet_price_type, 0.0)

    def action_enquiry_submitted_mail_notification(self):
        """Action enquiry submitted notification"""
        self.ensure_one()
        template = self.env.ref('vehicle_rental.vehicle_rental_booking_enquiry_mail_template',
                                raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True,
                               email_values={'author_id': self.env.company.partner_id.id})
