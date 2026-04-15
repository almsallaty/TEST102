# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class VehicleContractInherit(models.Model):
    _inherit = 'vehicle.contract'
    
    # ============================================
    # ✅ Responsible Employees (with tracking)
    # ============================================
    delivery_employee_id = fields.Many2one(
        'hr.employee', 
        string="Delivery Employee",
        tracking=True
    )
    reception_employee_id = fields.Many2one(
        'hr.employee', 
        string="Reception Employee",
        tracking=True
    )
    admin_approval_id = fields.Many2one(
        'hr.employee', 
        string="Manager Approval",
        tracking=True
    )

    city = fields.Char(
        string='City / Residence',
        related='customer_id.city',
        store=True,
        readonly=True,
        help="This field is automatically fetched from the customer's city in the contact record."
    )
    
    # ============================================
    # ✅ Core Modification: vin_sn as Many2one for auto-search
    # ============================================
    vin_sn = fields.Many2one(
        'fleet.vehicle',
        string='VIN / Chassis Number',
        domain="[('vin_sn', '!=', False)]",
        help="Start typing the VIN or license plate to search. Upon selection, other details will be auto-filled.",
        tracking=True,
        options="{'no_create': True}"
    )
    
    # The following fields remain related to auto-update when vehicle_id changes
    license_plate = fields.Char(string='License Plate', related='vehicle_id.license_plate', store=True, readonly=True)
    engine_number = fields.Char(string='Engine Number', related='vehicle_id.engine_number', store=True, readonly=True)
    
    interior_color_ids = fields.Many2many('vehicle.color', 'fleet_vehicle_interior_color_rel',
        'vehicle_id', 'color_id', string='Interior Color', related='vehicle_id.interior_color_ids',
        store=True, readonly=True)
    exterior_color_ids = fields.Many2many('vehicle.color', 'fleet_vehicle_exterior_color_rel',
        'vehicle_id', 'color_id', string='Exterior Color', related='vehicle_id.exterior_color_ids',
        store=True, readonly=True)
    
    # ============================================
    # ✅ Remaining fields updated to English
    # ============================================
    delivery_odometer = fields.Float(string="Odometer at Delivery", tracking=True)
    last_odometer = fields.Float(string="Odometer at Return", tracking=True)
    
    delivery_photos = fields.Many2many('ir.attachment', 'vehicle_contract_photos_rel',
        'contract_id', 'attachment_id', string="Delivery Photos")

    delivery_fuel_level = fields.Selection([
        ('full', 'Full'), ('3/4', '3/4'), ('1/2', 'Half'), ('1/4', '1/4'), ('empty', 'Empty')
    ], string="Fuel Level at Delivery", default='full', tracking=True)
    
    return_fuel_level = fields.Selection([
        ('full', 'Full'), ('3/4', '3/4'), ('1/2', 'Half'), ('1/4', '1/4'), ('empty', 'Empty')
    ], string="Fuel Level at Return", tracking=True)
    
    vehicle_condition_delivery = fields.Selection([
        ('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'),
        ('poor', 'Poor'), ('damaged', 'Damaged')
    ], string="Vehicle Condition at Delivery", default='excellent', tracking=True)
    
    vehicle_condition_return = fields.Selection([
        ('excellent', 'Excellent'), ('good', 'Good'), ('fair', 'Fair'),
        ('poor', 'Poor'), ('damaged', 'Damaged')
    ], string="Vehicle Condition at Return", default='excellent', tracking=True)

    return_odometer = fields.Float(string="Odometer at Return", tracking=True)
    return_photos = fields.Many2many('ir.attachment', 'vehicle_contract_return_photos_rel',
        'contract_id', 'attachment_id', string="Return Photos")
    vehicle_condition_notes = fields.Text(string="Vehicle Condition Notes", tracking=True)
    
    contract_extension_date = fields.Datetime(string="Contract Extension Date", tracking=True)
    
    renter_license_number = fields.Char(string="License Number", tracking=True)
    renter_license_expiry = fields.Date(string="License Expiry Date", tracking=True)
    renter_license_issue_place = fields.Char(string="License Issue Place", tracking=True)
    renter_passport_number = fields.Char(string="Passport / ID Number", tracking=True)
    renter_date_of_birth = fields.Date(string="Date of Birth", tracking=True)
    renter_category = fields.Selection([
        ('vip', 'VIP'), ('economy', 'Economy'), ('luxury', 'Luxury'), ('corporate', 'Corporate')
    ], string="Rental Category", tracking=True)
    renter_phone_hidden = fields.Boolean(string="Hide Phone Number", tracking=True)
    renter_landmark = fields.Char(string="Nearest Landmark", tracking=True)
    
    employer_id = fields.Many2one('res.partner', string="Employer", 
                                   domain="[('is_company', '=', True)]", tracking=True)
    employer_name = fields.Char(related='employer_id.name', string="Company Name", readonly=True)
    
    guarantor_id = fields.Many2one('res.partner', string="Guarantor", 
                                    domain="[('id', '!=', customer_id)]",
                                    help="The guarantor must be a registered customer other than the renter (optional).",
                                    tracking=True)
    guarantor_phone = fields.Char(related='guarantor_id.phone', string="Guarantor Phone", readonly=True)
    guarantor_nationality = fields.Many2one(related='guarantor_id.country_id', string="Guarantor Nationality", readonly=True)
    guarantor_license_number = fields.Char(related='guarantor_id.license_number', string="Guarantor License Number", readonly=True)
    guarantor_license_expiry = fields.Date(related='guarantor_id.license_expiry', string="Guarantor License Expiry", readonly=True)
    guarantor_license_issue_place = fields.Char(related='guarantor_id.license_issue_place', string="Guarantor License Issue Place", readonly=True)
    guarantor_passport_number = fields.Char(related='guarantor_id.passport_number', string="Guarantor Passport Number", readonly=True)
    guarantor_date_of_birth = fields.Date(related='guarantor_id.date_of_birth', string="Guarantor Date of Birth", readonly=True)
    
    guarantor_signature = fields.Binary(string="Guarantor Signature", attachment=True)
    guarantor_signed_by = fields.Char(string="Signed By (Guarantor)", readonly=True, tracking=True)
    guarantor_signed_date = fields.Date(string="Signature Date (Guarantor)", readonly=True, tracking=True)
    
    payment_method = fields.Selection([
        ('cash', 'Cash'), ('certified_check', 'Certified Check'),
        ('bank_transfer', 'Bank Transfer'), ('card', 'Card')
    ], string="Payment Method", tracking=True)
    
    travel_inside_libya = fields.Boolean(string="Travel Inside Libya", default=True, tracking=True)
    travel_outside_libya = fields.Boolean(string="Travel Outside Libya", tracking=True)
    travel_country = fields.Selection([('tunisia', 'Tunisia'), ('algeria', 'Algeria')],
        string="Allowed Country", tracking=True)
    travel_permit_number = fields.Char(string="Permit Number", tracking=True)

    customer_nationality_id = fields.Many2one(
        related='customer_id.nationality_id',
        string="Customer Nationality (from Record)",
        readonly=True,
        store=False
    )
    
    # ============================================
    # ✅ Auto-fill function when VIN is selected
    # ============================================
    @api.onchange('vin_sn')
    def _onchange_vin_sn_auto_fill(self):
        """When a vehicle is selected via vin_sn, it links to vehicle_id and auto-fills related fields."""
        for rec in self:
            if rec.vin_sn:
                rec.vehicle_id = rec.vin_sn.id
                # Related fields (license_plate, engine_number, colors...) will auto-update
            else:
                rec.vehicle_id = False

    # ============================================
    # ✅ Tracking & Business Logic Methods
    # ============================================
    def write(self, vals):
        employee_changes = []
        if 'delivery_employee_id' in vals:
            old_emp = self.delivery_employee_id.name if self.delivery_employee_id else 'Not Specified'
            new_emp = self.env['hr.employee'].browse(vals['delivery_employee_id']).name if vals['delivery_employee_id'] else 'Not Specified'
            employee_changes.append(f"Delivery Employee: {old_emp} → {new_emp}")
        if 'reception_employee_id' in vals:
            old_emp = self.reception_employee_id.name if self.reception_employee_id else 'Not Specified'
            new_emp = self.env['hr.employee'].browse(vals['reception_employee_id']).name if vals['reception_employee_id'] else 'Not Specified'
            employee_changes.append(f"Reception Employee: {old_emp} → {new_emp}")
        if 'admin_approval_id' in vals:
            old_emp = self.admin_approval_id.name if self.admin_approval_id else 'Not Specified'
            new_emp = self.env['hr.employee'].browse(vals['admin_approval_id']).name if vals['admin_approval_id'] else 'Not Specified'
            employee_changes.append(f"Manager Approval: {old_emp} → {new_emp}")
        
        result = super().write(vals)
        
        if employee_changes:
            for rec in self:
                rec.message_post(
                    body=f"👥 <b>Contract Responsibilities Changed</b><br/>" + "<br/>".join(employee_changes),
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment'
                )
        return result
    
    @api.onchange('customer_id')
    def onchange_customer_details_inherit(self):
        for rec in self:
            rec.customer_phone = rec.customer_id.phone
            rec.customer_email = rec.customer_id.email
            rec.renter_license_number = rec.customer_id.license_number
            rec.renter_license_expiry = rec.customer_id.license_expiry
            rec.renter_license_issue_place = rec.customer_id.license_issue_place
            rec.customer_nationality_id = rec.customer_id.nationality_id.id
            rec.renter_passport_number = rec.customer_id.passport_number
            rec.renter_date_of_birth = rec.customer_id.date_of_birth
            rec.renter_category = rec.customer_id.rental_category
            rec.renter_phone_hidden = rec.customer_id.hide_phone
            rec.renter_landmark = rec.customer_id.nearest_landmark
            rec.employer_id = rec.customer_id.employer_id
    
    @api.onchange('guarantor_id')
    def _onchange_guarantor_id_auto_fill_data(self):
        if self.guarantor_id:
            if self.guarantor_id.id == self.customer_id.id:
                self.guarantor_id = False
                return {
                    'warning': {
                        'title': 'Alert',
                        'message': 'The guarantor cannot be the same as the renter!',
                    }
                }
    
    def action_update_customer_data(self):
        self.ensure_one()
        if self.customer_id:
            changes = []
            if self.customer_id.license_number != self.renter_license_number:
                changes.append(f"License Number: {self.customer_id.license_number} → {self.renter_license_number}")
            if self.customer_id.passport_number != self.renter_passport_number:
                changes.append(f"Passport Number: {self.customer_id.passport_number} → {self.renter_passport_number}")
            
            self.customer_id.write({
                'license_number': self.renter_license_number,
                'license_expiry': self.renter_license_expiry,
                'passport_number': self.renter_passport_number,
                'date_of_birth': self.renter_date_of_birth,
                'rental_category': self.renter_category,
                'hide_phone': self.renter_phone_hidden,
                'nearest_landmark': self.renter_landmark,
                'employer_id': self.employer_id.id if self.employer_id else False,
            })
            
            if changes:
                self.message_post(
                    body=f"🔄 <b>Customer Data Updated from Contract</b><br/>" + "<br/>".join(changes),
                    message_type='notification'
                )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Updated',
                    'message': 'Customer data has been successfully updated.',
                    'type': 'success',
                    'sticky': False,
                }
            }
        return False
    
    @api.constrains('customer_id')
    def _check_customer_license(self):
        for record in self:
            if record.customer_id and record.customer_id.license_expiry:
                if record.customer_id.license_expiry < fields.Date.today():
                    record.message_post(
                        body=f"⚠️ <b>Alert: Customer License Expired</b><br/>Expiry Date: {record.customer_id.license_expiry}",
                        message_type='notification'
                    )
                    raise ValidationError('Cannot create a rental contract for a customer with an expired license.')
    
    @api.constrains('guarantor_id', 'customer_id')
    def _check_guarantor_not_same_as_renter(self):
        for record in self:
            if record.guarantor_id and record.customer_id:
                if record.guarantor_id.id == record.customer_id.id:
                    raise ValidationError('The guarantor cannot be the same as the renter!')
    
    @api.constrains('travel_outside_libya', 'travel_country')
    def _check_travel_country_required(self):
        for record in self:
            if record.travel_outside_libya and not record.travel_country:
                raise ValidationError('Please select an allowed country when enabling travel outside Libya.')
    
    @api.constrains('start_date', 'end_date')
    def _check_contract_dates_inherit(self):
        for record in self:
            if record.start_date and record.end_date:
                if record.end_date < record.start_date:
                    raise ValidationError('End date cannot be earlier than the start date.')
    
    @api.constrains('vehicle_condition_delivery', 'vehicle_condition_return')
    def _check_vehicle_condition_change(self):
        for record in self:
            if record.vehicle_condition_delivery and record.vehicle_condition_return:
                if record.vehicle_condition_return == 'damaged' and record.vehicle_condition_delivery != 'damaged':
                    record.message_post(
                        body=f"🚨 <b>New Vehicle Damage Detected</b><br/>"
                             f"Condition at Delivery: {dict(self._fields['vehicle_condition_delivery'].selection).get(record.vehicle_condition_delivery)}<br/>"
                             f"Condition at Return: {dict(self._fields['vehicle_condition_return'].selection).get(record.vehicle_condition_return)}",
                        message_type='notification'
                    )
                    record.activity_schedule(
                        'fleet_rental_integration.mail_activity_vehicle_damage',
                        note='New vehicle damage detected upon return.'
                    )
    
    def action_confirm_rental(self):
        for record in self:
            old_status = dict(self._fields['status'].selection).get(record.status, record.status)
            record.status = 'b_in_progress'
            if record.vehicle_id:
                record.vehicle_id.availability_status = 'rented'
            
            record.message_post(
                body=f"✅ <b>Rental Contract Confirmed</b><br/>"
                     f"From: {old_status} → To: In Progress<br/>"
                     f"By: {self.env.user.name}",
                message_type='notification'
            )
            record.activity_schedule(
                'fleet_rental_integration.mail_activity_contract_approval',
                user_id=self.env.user.id,
                note='New rental contract confirmed.'
            )
        return True
    
    def action_return_vehicle(self):
        for record in self:
            old_status = dict(self._fields['status'].selection).get(record.status, record.status)
            record.status = 'c_return'
            if record.vehicle_id:
                record.vehicle_id.availability_status = 'available'
                record.vehicle_id.odometer = record.last_odometer
            
            record.message_post(
                body=f"🚗 <b>Vehicle Returned</b><br/>"
                     f"From: {old_status} → To: Returned<br/>"
                     f"Final Odometer: {record.last_odometer} {record.odometer_unit}<br/>"
                     f"By: {self.env.user.name}",
                message_type='notification'
            )
        return True
