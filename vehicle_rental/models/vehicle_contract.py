# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import calendar
import math
import secrets
import base64
import logging
import pytz
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from markupsafe import Markup

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from ..utils import _display_rental_notification

_logger = logging.getLogger(__name__)


class RentalVehicleImage(models.Model):
    """Rental Vehicle Image"""
    _name = "rental.vehicle.image"
    _description = __doc__

    avatar = fields.Binary(string='Image', attachment=True, required=True)
    name = fields.Char(translate=True, size=32)
    sequence = fields.Integer()
    image_filename = fields.Char(string='Filename')
    file_size = fields.Integer(string='File Size (bytes)', readonly=True)
    capture_date = fields.Datetime(string='Capture Date', default=fields.Datetime.now)
    capture_method = fields.Selection([('upload', 'Uploaded'), ('camera', 'Camera Capture')],
                                      string='Capture Method', default='upload')
    vehicle_contract_id = fields.Many2one('vehicle.contract', ondelete="cascade")


class VehicleDamageImage(models.Model):
    """Vehicle Damage Image"""
    _name = "vehicle.damage.image"
    _description = __doc__

    avatar = fields.Binary(string="Avatar")
    name = fields.Char(translate=True, size=32)
    sequence = fields.Integer()
    image_filename = fields.Char(string='Filename')
    file_size = fields.Integer(string='File Size (bytes)', readonly=True)
    capture_date = fields.Datetime(string='Capture Date', default=fields.Datetime.now)
    capture_method = fields.Selection([('upload', 'Uploaded'), ('camera', 'Camera Capture')],
                                      string='Capture Method', default='upload')
    vehicle_contract_id = fields.Many2one('vehicle.contract', ondelete="cascade")


class VehicleContract(models.Model):
    """Vehicle Contract"""
    _name = 'vehicle.contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = __doc__
    _rec_name = 'reference_no'

    reference_no = fields.Char(
        string='Reference No', 
        required=True, 
        readonly=True,
        default=lambda self: _('New'), 
        copy=False,
        tracking=True
    )
    
    # ✅ ✅ التعديل الأساسي: vin_sn كـ Many2one للبحث التلقائي عن المركبة
    vin_sn = fields.Many2one(
        'fleet.vehicle',
        string='رقم الهيكل (VIN)',
        domain="[('vin_sn', '!=', False)]",
        help="ابدأ بكتابة رقم الهيكل أو اللوحة للبحث. عند الاختيار، ستملأ باقي التفاصيل تلقائياً.",
        tracking=True,
        options="{'no_create': True}"
    )
    
    # ❌ تم حذف حقل vin_sn_search نهائياً
    
    vehicle_ids = fields.Many2many('fleet.vehicle', string="Vehicles", compute='_compute_available_vehicles')
    
    # ✅ vehicle_id مبسط (بدون compute/inverse المعقدة)
    vehicle_id = fields.Many2one(
        'fleet.vehicle', 
        string="Vehicle", 
        copy=False,
        readonly=False,  # ✅ قابل للتعديل المباشر إذا لزم
        domain="[('id', 'not in', vehicle_ids), ('status', '=', 'available'), ('vin_sn', '!=', False)]",
        tracking=True
    )
    
    vehicle_display_name = fields.Char(string="المركبة", related='vehicle_id.name', readonly=True)
    vehicle_model_year = fields.Selection(related='vehicle_id.model_year')
    
    license_plate = fields.Char(string="License Plate", tracking=True)
    last_odometer = fields.Float(string="Last Odometer", copy=False, tracking=True)
    odometer_unit = fields.Selection([('kilometers', 'km'), ('miles', 'mi')], 'Odometer Unit',
                                     default='kilometers', copy=False)
    fuel_type = fields.Selection([('diesel', 'Diesel'), ('gasoline', 'Gasoline'),
                                  ('full_hybrid', 'Full Hybrid'), ('plug_in_hybrid_diesel', 'Plug-in Hybrid Diesel'),
                                  ('plug_in_hybrid_gasoline', 'Plug-in Hybrid Gasoline'), ('cng', 'CNG'),
                                  ('lpg', 'LPG'), ('hydrogen', 'Hydrogen'), ('electric', 'Electric')],
                                 string="Fuel Type", tracking=True)
    transmission = fields.Selection([('manual', 'Manual'), ('automatic', 'Automatic')],
        string="Transmission", copy=False, tracking=True)

    is_driver_required = fields.Boolean(string="Driver Required", tracking=True)
    driver_id = fields.Many2one('res.partner', string="Driver", 
                                domain=[('employee_ids', '!=', False)], tracking=True)
    driver_charge_type = fields.Selection([('including', "Including in rent charge"),
                                           ('excluding', "Excluding in rent charge")],
                                          string="Charges Type", default='including', tracking=True)
    driver_charge = fields.Monetary(string="Charges", default=1.0, tracking=True)

    customer_id = fields.Many2one("res.partner", tracking=True)
    customer_phone = fields.Char(string="Phone", tracking=True)
    customer_email = fields.Char(string="Email", tracking=True)
    customer_document_id = fields.Many2one("customer.documents", string="Document")
    document_count = fields.Integer(compute='_compute_document_count')

    rent_type = fields.Selection([
        ('hour', "Hours"), ('days', "Days"), ('week', "Weeks"), ('month', "Months"),
        ('year', "Years"), ('km', "Kilometers"), ('mi', 'Miles')],
        string="Rent Type", tracking=True)
    total_days = fields.Float(string="Total Days", compute="_compute_total_rental_days")
    minimum_km_per_day = fields.Float('Min KM per Day', tracking=True)
    rent = fields.Monetary(string="Rent", tracking=True)
    total_vehicle_rent = fields.Monetary(string="Total Rental Charges",
                                         compute='_compute_total_vehicle_rent', tracking=True)

    is_any_extra_charges = fields.Boolean(string="If Any Extra Charges", tracking=True)
    total_extra_days = fields.Integer(string="Total Extra Days", default=1, tracking=True)
    total_extra_week = fields.Integer(string="Total Extra Weeks", default=1, tracking=True)
    total_extra_month = fields.Integer(string="Total Extra Months", default=1, tracking=True)
    total_extra_hour = fields.Integer(string="Total Extra Hours", default=1, tracking=True)
    total_extra_year = fields.Integer(string="Total Extra Years", default=1, tracking=True)
    total_extra_km = fields.Float(string="Total Extra KM", default=1, tracking=True)
    total_extra_mi = fields.Float(string="Total Extra Miles", default=1, tracking=True)
    extra_charge = fields.Monetary(string="Extra Charge", tracking=True)
    total_extra_charges = fields.Monetary(string="Total Extra Charges",
                                          compute='_compute_total_extra_charges', tracking=True)

    start_date = fields.Datetime(string="Pick-up Date", copy=False, tracking=True)
    start_date_ui = fields.Char(
        string="Pick-up Date",
        compute="_compute_english_datetime_ui",
        inverse="_inverse_start_date_ui",
    )
    pick_up_street = fields.Char(translate=True, tracking=True)
    pick_up_street2 = fields.Char(translate=True)
    pick_up_city = fields.Char(translate=True, tracking=True)
    pick_up_state_id = fields.Many2one("res.country.state", string='State',
                                       domain="[('country_id', '=?', pick_up_country_id)]")
    pick_up_zip = fields.Char()

    end_date = fields.Datetime(string="Drop-off Date", copy=False, tracking=True)
    end_date_ui = fields.Char(
        string="Drop-off Date",
        compute="_compute_english_datetime_ui",
        inverse="_inverse_end_date_ui",
    )
    drop_off_street = fields.Char(translate=True, tracking=True)
    drop_off_street2 = fields.Char(translate=True)
    drop_off_city = fields.Char(translate=True, tracking=True)
    drop_off_state_id = fields.Many2one("res.country.state", string=' State',
                                        domain="[('country_id', '=?', drop_off_country_id)]")
    drop_off_zip = fields.Char()

    responsible_id = fields.Many2one('res.users', default=lambda self: self.env.user, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', related="company_id.currency_id")
    
    cancellation_policy_id = fields.Many2one("cancellation.policy", string="Policy", tracking=True)
    terms_and_conditions = fields.Html(string="Terms and Conditions", tracking=True)
    cancellation_reason = fields.Html(string="Cancellation Reason", tracking=True)
    cancellation_charge = fields.Monetary(string="Cancellation Charge", tracking=True)
    cancellation_invoice_id = fields.Many2one('account.move', tracking=True)
    cancellation_invoice_state = fields.Selection(related='cancellation_invoice_id.payment_state',
                                                  string="Cancellation Invoice State")

    rental_agreement_terms_id = fields.Many2one('rental.agreement.terms', string="Rental Agreement", tracking=True)
    rental_terms = fields.Html(tracking=True)
    
    rental_vehicle_image_ids = fields.One2many('rental.vehicle.image', 'vehicle_contract_id')
    vehicle_damage_image_ids = fields.One2many('vehicle.damage.image', 'vehicle_contract_id')
    insurance_policy_ids = fields.One2many('insurance.policy', 'vehicle_contract_id')
    extra_service_ids = fields.One2many('extra.service', 'vehicle_contract_id')
    extra_service_charge = fields.Monetary(compute="_compute_total_extra_service_charge", store=True)

    description = fields.Html(string="Description", tracking=True)
    damage_amount = fields.Monetary(string="Damage Amount", tracking=True)

    tax_ids = fields.Many2many('account.tax', string='Taxes', tracking=True)
    invoice_id = fields.Many2one('account.move', tracking=True)
    is_invoice_done = fields.Boolean(tracking=True)
    invoice_count = fields.Integer(compute='_compute_invoice_count')
    
    status = fields.Selection([
        ('a_draft', 'New'), ('b_in_progress', 'In Progress'),
        ('c_return', 'Return'), ('d_cancel', 'Cancel')],
        default="a_draft", copy=False, tracking=True)
    
    if_any_deposit = fields.Boolean(tracking=True)
    deposit = fields.Monetary(string="Deposit", tracking=True)
    deposit_invoice_id = fields.Many2one('account.move', string="Deposit Invoice", tracking=True)
    deposit_payment_state = fields.Selection(related="deposit_invoice_id.payment_state", string=" Payment State")
    total_deposit = fields.Monetary(string="Total Deposit", tracking=True)

    return_deposit_invoice_id = fields.Many2one('account.move', string="Return Deposit Invoice", tracking=True)
    return_deposit_state = fields.Selection(related="return_deposit_invoice_id.payment_state",
                                            string="Return Payment State")

    payment_type = fields.Selection(
        [('daily', "Daily"), ('weekly', "Weekly"), ('monthly', "Monthly"),
         ('quarterly', "Quarterly"), ('yearly', "Yearly"), ('full_payment', "Full Payment")],
        string="Payment Type", tracking=True)
    vehicle_payment_option_ids = fields.One2many('vehicle.payment.option', 'vehicle_contract_id')
    invoice_item_id = fields.Many2one('product.product', string="Invoice Item", required=True,
        default=lambda self: self.env.ref('vehicle_rental.vehicle_rent_charge', raise_if_not_found=False), tracking=True)
    installment_created = fields.Boolean(tracking=True)
    extra_charge_invoice_id = fields.Many2one('account.move', string="Extra Charge Invoice", tracking=True)
    extra_charge_payment_state = fields.Selection(related='extra_charge_invoice_id.payment_state',
                                                  string="Extra Charge Payment State")
    extra_service_invoice_id = fields.Many2one('account.move', string="Extra Service Invoice", tracking=True)
    payment_state = fields.Selection(related="extra_service_invoice_id.payment_state", string="Payment State")

    is_scratch_report = fields.Boolean(string="Custom Scratch Report", tracking=True)
    vehicle_scratch_report_id = fields.Many2one('vehicle.scratch.report', string="Scratch Report", tracking=True)
    scratch_image = fields.Binary("Image", attachment=True)

    is_any_trip_expense = fields.Boolean(tracking=True)
    contract_expense_ids = fields.One2many(comodel_name='hr.expense', inverse_name='vehicle_contract_id')
    crm_lead_id = fields.Many2one('crm.lead', string="Lead", tracking=True)

    vehicle_rental_checklist_id = fields.Many2one('vehicle.rental.checklist', string="Vehicle Checklist", tracking=True)
    rental_contract_checklist_ids = fields.One2many(comodel_name='rental.contract.checklist',
                                                    inverse_name='vehicle_contract_id')

    authorized_sign_by_id = fields.Many2one(comodel_name='res.partner', string=" Sign By", tracking=True)
    date = fields.Date(string="Date", tracking=True)
    signature = fields.Binary(string="Signature")

    customer_signature = fields.Binary(string="Customer Signature")
    customer_signed_by = fields.Char(string="Sign By", tracking=True)
    customer_signed_date = fields.Date(string="Signed Date", tracking=True)

    access_token = fields.Char(string="Access Token", copy=False)

    total_day_rent = fields.Monetary()
    total_km_rent = fields.Monetary()
    total_mi_rent = fields.Monetary()
    total_km = fields.Float(string="Total Kilometers", default=1)
    total_mi = fields.Float(string="Total Miles", default=1)

    account_payment_id = fields.Many2one('account.payment', string="Deposit Payment", tracking=True)
    account_payment_state = fields.Selection(related='account_payment_id.state', string="Account Payment State")
    journal_id = fields.Many2one('account.journal', domain=[('type', 'in', ('bank', 'cash'))],
                                 string="Deposit Journal", tracking=True)
    pick_up_country_id = fields.Many2one("res.country", tracking=True)
    drop_off_country_id = fields.Many2one("res.country", tracking=True)
    model_year = fields.Char(string="Model", copy=False)
    
    customer_document_ids = fields.One2many('customer.documents', 'vehicle_contract_id', string="مستندات العقد")

    @api.model_create_multi
    def create(self, vals_list):
        """Create vehicle contract record"""
        records = super().create(vals_list)
        for record in records:
            if record.reference_no == self.env._('New'):
                record.reference_no = self.env['ir.sequence'].next_by_code('vehicle.contract') or self.env._('New')
            token = secrets.token_urlsafe(12).replace('_', '-')
            record.access_token = token
            
            record.message_post(
                body=f"📄 <b>تم إنشاء عقد إيجار جديد</b><br/>"
                     f"رقم العقد: {record.reference_no}<br/>"
                     f"العميل: {record.customer_id.name or 'غير محدد'}<br/>"
                     f"المركبة: {record.vehicle_id.name or 'غير محدد'}<br/>"
                     f"تاريخ البداية: {record.start_date or 'غير محدد'}",
                message_type='notification',
                subtype_xmlid='mail.mt_comment'
            )
            
            mail_template = self.env.ref(
                'vehicle_rental.successful_booking_creation_mail_template', raise_if_not_found=False)
            if mail_template:
                mail_template.send_mail(record.id, force_send=True)
        return records

    @api.model
    def generate_missing_access_token_contract(self):
        """Cron to generate access tokens for old records"""
        vehicle_contracts = self.search([('access_token', '=', False)])
        for record in vehicle_contracts:
            token = secrets.token_urlsafe(12).replace('_', '-')
            record.access_token = token

    def write(self, vals):
        """تسجيل التغييرات المهمة في Chatter"""
        changes = []
        tracked_labels = {
            'customer_id': 'العميل',
            'vehicle_id': 'المركبة',
            'vin_sn': 'رقم الهيكل',
            'start_date': 'تاريخ البداية',
            'end_date': 'تاريخ الانتهاء',
            'status': 'حالة العقد',
            'total_vehicle_rent': 'إجمالي الإيجار',
            'deposit': 'المبلغ التأميني',
            'driver_id': 'السائق',
            'rent_type': 'نوع الإيجار',
        }
        
        for field, label in tracked_labels.items():
            if field in vals:
                old_val = self[field]
                new_val = vals[field]
                if field in ['customer_id', 'vehicle_id', 'vin_sn', 'driver_id'] and isinstance(new_val, int):
                    new_val = self.env[self._fields[field].comodel_name].browse(new_val).name
                if field == 'status':
                    selection = dict(self._fields['status'].selection)
                    old_val = selection.get(old_val, old_val)
                    new_val = selection.get(new_val, new_val)
                
                if old_val != new_val:
                    changes.append(f"{label}: {old_val or 'فارغ'} → {new_val}")
        
        result = super().write(vals)
        
        if changes:
            for rec in self:
                rec.message_post(
                    body=f"🔄 <b>تم تعديل بيانات العقد</b><br/>" + "<br/>".join(changes),
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment'
                )
        return result

    @api.constrains('start_date', 'end_date', 'rent_type')
    def _check_date_rent_type(self):
        """Check rent type"""
        rent_min_days = {
            'week': 7,
            'month': 28,
            'year': 365,
        }
        for rec in self:
            if rec.start_date and rec.end_date:
                diff_days = (rec.end_date - rec.start_date).days
                min_days = rent_min_days.get(rec.rent_type)
                if min_days and diff_days < min_days:
                    raise ValidationError(self.env._(
                        f"Rent Type '{rec.rent_type.capitalize()}' requires at least {min_days} days duration."))

    @api.constrains('rent_type', 'rent')
    def _validate_non_positive_values(self):
        """Validate rent is greater than zero based on rent type"""
        type_labels = {
            'hour': self.env._("Hour"),
            'days': self.env._("Day"),
            'week': self.env._("Week"),
            'month': self.env._("Month"),
            'year': self.env._("Year"),
            'km': self.env._("KM"),
            'mi': self.env._("MI"),
        }
        for record in self:
            if record.status != 'a_draft':
                if record.rent_type in type_labels and record.rent <= 0:
                    raise ValidationError(
                        self.env._("The Rent per %s must be greater than zero.") % type_labels[record.rent_type])

    def a_draft_to_b_in_progress(self):
        """Change status from draft to in-progress"""
        for rec in self:
            if not rec.rent_type:
                message = _display_rental_notification(
                    message="""Choose your preferred rental unit (hours, days, weeks,
                     months, years, kilometers, or miles) and proceed accordingly.""",
                    message_type='warning')
                return message
            vehicle_id = rec.vehicle_id.id if rec.vehicle_id else False
            if vehicle_id:
                existing_contract = self.env['vehicle.contract'].search(
                    [('vehicle_id', '=', vehicle_id), ('status', '=', 'b_in_progress'),
                     ('start_date', '<=', rec.end_date), ('end_date', '>=', rec.start_date)], limit=1)
                if existing_contract:
                    message = _display_rental_notification(
                        message="""There is already a running contract for this vehicle. Please
                         return the car before selecting a new contract.""",
                        message_type='warning')
                    return message
            
            old_status = dict(self._fields['status'].selection).get(rec.status, rec.status)
            rec.status = 'b_in_progress'
            rec.message_post(
                body=f"✅ <b>تم تأكيد العقد وتغيير الحالة</b><br/>من: {old_status} → إلى: جاري التنفيذ",
                message_type='notification'
            )
        return True

    def b_in_progress_to_c_return(self):
        """In progress to return"""
        for rec in self:
            old_status = dict(self._fields['status'].selection).get(rec.status, rec.status)
            rec.status = 'c_return'
            rec.message_post(
                body=f"🚗 <b>تم استلام السيارة</b><br/>من: {old_status} → إلى: تم الاستلام",
                message_type='notification'
            )
        return True

    def c_return_to_d_cancel(self):
        """Return to cancel"""
        for rec in self:
            old_status = dict(self._fields['status'].selection).get(rec.status, rec.status)
            rec.status = 'd_cancel'
            rec.message_post(
                body=f"❌ <b>تم إلغاء العقد</b><br/>من: {old_status} → إلى: ملغي",
                message_type='notification'
            )
        return True

    def action_send_contract_email(self):
        """Open email composer popup to send contract confirmation email - Odoo 19 Compatible."""
        self.ensure_one()
        
        template = self.env.ref(
            "vehicle_rental.vehicle_rental_booking_confirmation_mail_template", 
            raise_if_not_found=False
        )
        
        partner_ids = [(4, self.customer_id.id)] if self.customer_id else [(4, False)]
        
        email_context = {
            'default_composition_mode': 'comment',
            'default_model': 'vehicle.contract',
            'default_res_ids': [self.id],
            'default_template_id': template.id if template else False,
            'default_use_template': bool(template),
            'default_partner_ids': partner_ids,
            'default_email_from': self.env.company.email or self.env.user.email,
            'default_reply_to': self.env.company.email or self.env.user.email,
            'force_email': True,
            'active_id': self.id,
            'active_ids': self.ids,
            'active_model': 'vehicle.contract',
            'mark_as_read': True,
        }
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Compose Email'),
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'view_id': self.env.ref('mail.email_compose_message_wizard_form').id,
            'target': 'new',
            'context': email_context,
            'flags': {'mode': 'extended'},
        }

    def action_send_whatsapp_contract(self):
        """Open WhatsApp composer or send directly with contract details - Odoo 19 Compatible."""
        self.ensure_one()
        
        phone = self.customer_id.phone
        if not phone:
            raise UserError(self.env._("Customer has no phone number. Please add a phone number to send WhatsApp."))
        
        message = (
            f"مرحبًا {self.customer_id.name} 👋\n\n"
            f"تم تأكيد عقد الإيجار الخاص بك 🚗\n"
            f"📋 رقم العقد: {self.reference_no}\n"
            f"🚙 السيارة: {self.vehicle_id.name or 'N/A'}\n"
            f"📅 تاريخ الاستلام: {self.start_date.strftime('%Y-%m-%d %H:%M') if self.start_date else 'N/A'}\n"
            f"📅 تاريخ التسليم: {self.end_date.strftime('%Y-%m-%d %H:%M') if self.end_date else 'N/A'}\n"
            f"💰 إجمالي الإيجار: {self.total_vehicle_rent:.2f} {self.currency_id.name}\n\n"
            f"نشكرك على ثقتك بنا 💚\n"
            f"لأي استفسار، يرجى التواصل معنا."
        )
        
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Send WhatsApp'),
            'res_model': 'whatsapp.composer',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_phone': phone,
                'default_body': message,
                'default_res_model': self._name,
                'default_res_id': self.id,
            },
        }

    def action_send_whatsapp_contract_pdf(self):
        """Send contract PDF via WhatsApp with attachment - Odoo 19 Compatible."""
        self.ensure_one()
        
        phone = self.customer_id.phone
        if not phone:
            raise UserError(self.env._("Customer has no phone number."))
        
        report_name = 'vehicle_rental.vehicle_contract_report_template'
        
        try:
            report = self.env['ir.actions.report'].sudo()._get_report_from_name(report_name)
        except Exception as e:
            _logger.error("WhatsApp PDF Report Error: %s", e)
            raise UserError(self.env._("Contract PDF report not found. Please check report configuration."))
        
        pdf_content, _ = report.sudo()._render_qweb_pdf(
            report_ref=report_name,
            res_ids=self.ids
        )
        
        pdf_base64 = base64.b64encode(pdf_content)
        filename = f"Contract_{self.reference_no}.pdf"
        
        whatsapp_msg = self.env['adv.whatsapp.out'].sudo().create({
            'type': 'media',
            'phone': phone,
            'body': f"🚗 عقد الإيجار {self.reference_no}\n\n"
                    f"السيارة: {self.vehicle_id.name or 'N/A'}\n"
                    f"العميل: {self.customer_id.name}\n"
                    f"تاريخ الاستلام: {self.start_date.strftime('%Y-%m-%d') if self.start_date else 'N/A'}\n"
                    f"تاريخ التسليم: {self.end_date.strftime('%Y-%m-%d') if self.end_date else 'N/A'}\n\n"
                    f"شكراً لثقتك بنا 💚",
            'media': pdf_base64,
            'media_filename': filename,
            'status': 'pending',
        })
        
        whatsapp_msg.sudo().action_send_whatsapp()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._('WhatsApp Sent'),
                'message': self.env._('Contract PDF has been sent successfully via WhatsApp.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_vehicle_rent_deposit(self):
        """Handle vehicle rent deposit process."""
        if self.if_any_deposit and not self.deposit:
            message = _display_rental_notification(
                message="""Please note: A rented vehicle deposit is required.""",
                message_type='warning')
            return message
        if self.if_any_deposit and self.deposit:
            invoice_lines = []
            invoice_line_vals = {
                'product_id': self.env.ref('vehicle_rental.vehicle_rent_deposit').id,
                'name': f"Deposit for - {self.reference_no} - {self.vehicle_id.name}",
                'quantity': 1,
                'price_unit': self.deposit,
            }
            invoice_lines.append((0, 0, invoice_line_vals))
            data = {
                'partner_id': self.customer_id.id,
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': invoice_lines,
                'vehicle_contract_id': self.id
            }
            deposit_invoice_id = self.env['account.move'].sudo().create(data)
            self.deposit_invoice_id = deposit_invoice_id.id
            return {
                'type': 'ir.actions.act_window',
                'name': self.env._('Deposit Invoice'),
                'res_model': 'account.move',
                'res_id': deposit_invoice_id.id,
                'view_mode': 'form',
                'target': 'current'
            }
        return True

    @api.depends('start_date', 'end_date')
    def _compute_english_datetime_ui(self):
        for rec in self:
            rec.start_date_ui = rec._format_datetime_en(rec.start_date)
            rec.end_date_ui = rec._format_datetime_en(rec.end_date)

    def _format_datetime_en(self, value):
        if not value:
            return ""
        dt = fields.Datetime.to_datetime(value)
        dt = fields.Datetime.context_timestamp(self, dt)
        return dt.strftime("%d-%m-%Y %I:%M %p")

    def _parse_datetime_en(self, value):
        if not value:
            return False
        value = str(value).strip()
        formats = [
            "%d-%m-%Y %I:%M %p",
            "%d/%m/%Y %I:%M %p",
            "%d-%m-%Y %H:%M",
            "%d/%m/%Y %H:%M",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %I:%M %p",
        ]
        parsed = None
        for fmt in formats:
            try:
                parsed = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
        if not parsed:
            raise ValidationError(_(
                "Use this date format: DD-MM-YYYY HH:MM AM/PM, for example 28-04-2026 01:00 PM"
            ))
        tz_name = self.env.context.get('tz') or self.env.user.tz or 'UTC'
        user_tz = pytz.timezone(tz_name)
        local_dt = user_tz.localize(parsed)
        utc_dt = local_dt.astimezone(pytz.UTC).replace(tzinfo=None)
        return utc_dt

    def _inverse_start_date_ui(self):
        for rec in self:
            rec.start_date = rec._parse_datetime_en(rec.start_date_ui)

    def _inverse_end_date_ui(self):
        for rec in self:
            rec.end_date = rec._parse_datetime_en(rec.end_date_ui)

    @api.onchange('start_date_ui', 'end_date_ui')
    def _onchange_datetime_ui_fields(self):
        for rec in self:
            if rec.start_date_ui:
                rec.start_date = rec._parse_datetime_en(rec.start_date_ui)
            else:
                rec.start_date = False
            if rec.end_date_ui:
                rec.end_date = rec._parse_datetime_en(rec.end_date_ui)
            else:
                rec.end_date = False

    @api.constrains('start_date')
    def _check_start_date(self):
        """Ensure start date is not in the past (based on current datetime)."""
        current_datetime = fields.Datetime.now()
        for record in self:
            if record.start_date and record.start_date < current_datetime:
                raise ValidationError(
                    _("The start date must be greater than or equal to the current date and time."))

    @api.constrains('date')
    def _check_date(self):
        """Check that the sign date is not before today"""
        today = fields.Date.today()
        for record in self:
            if record.date and record.date < today:
                raise ValidationError(self.env._("The sign date cannot be earlier than today."))

    # @api.constrains('minimum_km_per_day')
    # def _check_minimum_km_per_day(self):
    #     """Minimum km per day"""
    #     for record in self:
    #         if record.minimum_km_per_day <= 0:
    #             raise ValidationError(self.env._("Minimum km per day must be greater than zero"))

    @api.onchange('start_date', 'end_date')
    def get_vehicle_select(self):
        """Vehicle select"""
        for rec in self:
            if not rec.start_date or not rec.end_date:
                rec.vehicle_id = False

    def action_update_vehicle_details(self):
        """Update vehicle details and log odometer changes."""
        self.ensure_one()
        if not self.vehicle_id:
            raise ValidationError(_("Please select a vehicle before updating the details."))
        vehicle = self.vehicle_id
        last_odometer_record = self.env['fleet.vehicle.odometer'].sudo().search(
            [('vehicle_id', '=', vehicle.id)], order="value desc", limit=1)
        last_value = last_odometer_record.value if last_odometer_record else vehicle.odometer
        last_unit = last_odometer_record.unit if last_odometer_record else vehicle.odometer_unit

        if self.last_odometer <= last_value:
            return _display_rental_notification(
                message=_("The new odometer reading must be greater than the previous reading (%s %s).") % (last_value,
                                                                                                            last_unit),
                message_type='warning')
        vehicle.write({
            'transmission': self.transmission,
            'fuel_type': self.fuel_type,
            'odometer': self.last_odometer,
            'odometer_unit': self.odometer_unit,
        })

        body = Markup(_(
            "Vehicle details updated successfully.<br/>"
            "Previous odometer reading: <strong>%(last_value)s %(last_unit)s</strong><br/>"
            "New odometer reading: <strong>%(new_value)s %(new_unit)s</strong>"
        ) % {'last_value': last_value, 'last_unit': last_unit,
             'new_value': self.last_odometer, 'new_unit': self.odometer_unit})
        self.message_post(
            body=body,
            message_type='comment',
            author_id=self.env.user.partner_id.id,
        )
        return True

    @api.onchange('customer_id')
    def onchange_customer_details(self):
        """Onchange customer details"""
        for rec in self:
            rec.customer_phone = rec.customer_id.phone
            rec.customer_email = rec.customer_id.email

    @api.onchange('vehicle_id', 'rent_type')
    def onchange_vehicle_details(self):
        """Update vehicle-related fields when vehicle or rent type changes"""
        for rec in self:
            vehicle = rec.vehicle_id
            if vehicle:
                rec.driver_id = vehicle.driver_id
                rec.last_odometer = vehicle.odometer or 0.0
                rec.odometer_unit = vehicle.odometer_unit
                rec.transmission = vehicle.transmission
                rec.fuel_type = vehicle.fuel_type
                rec.license_plate = vehicle.license_plate
                minimum_km = vehicle.minimum_km_per_day or 0.0
                if rec.rent_type == 'mi':
                    rec.minimum_km_per_day = minimum_km * 0.621371
                else:
                    rec.minimum_km_per_day = minimum_km

    @api.onchange('cancellation_policy_id')
    def onchange_policy_terms(self):
        """Onchange policy terms"""
        for rec in self:
            rec.terms_and_conditions = rec.cancellation_policy_id.terms_and_conditions

    @api.onchange('rental_agreement_terms_id')
    def onchange_rental_agreement(self):
        """Onchange rental agreement"""
        for rec in self:
            rec.rental_terms = rec.rental_agreement_terms_id.rental_terms

    @api.onchange('rent_type', 'vehicle_id')
    def onchange_vehicle_rent_details(self):
        """Onchange vehicle rental details"""
        for rec in self:
            if rec.vehicle_id:
                if rec.rent_type == 'days':
                    rec.rent = rec.vehicle_id.rent_day
                    rec.extra_charge = rec.vehicle_id.extra_charge_day
                elif rec.rent_type == 'week':
                    rec.rent = rec.vehicle_id.rent_week
                    rec.extra_charge = rec.vehicle_id.extra_charge_week
                elif rec.rent_type == 'month':
                    rec.rent = rec.vehicle_id.rent_month
                    rec.extra_charge = rec.vehicle_id.extra_charge_month
                elif rec.rent_type == 'hour':
                    rec.rent = rec.vehicle_id.rent_hour
                    rec.extra_charge = rec.vehicle_id.extra_charge_hour
                elif rec.rent_type == 'year':
                    rec.rent = rec.vehicle_id.rent_year
                    rec.extra_charge = rec.vehicle_id.extra_charge_year
                elif rec.rent_type == 'km':
                    rec.rent = rec.vehicle_id.rent_km
                    rec.extra_charge = rec.vehicle_id.extra_charge_km
                elif rec.rent_type == 'mi':
                    rec.rent = rec.vehicle_id.rent_mi
                    rec.extra_charge = rec.vehicle_id.extra_charge_mi

    @api.depends('extra_service_ids.amount', 'extra_service_ids.product_qty')
    def _compute_total_extra_service_charge(self):
        """Total extra service charge"""
        for rec in self:
            rec.extra_service_charge = sum(
                charge.amount * charge.product_qty for charge in rec.extra_service_ids)

    @api.depends('vehicle_id', 'start_date', 'end_date')
    def _compute_available_vehicles(self):
        """Compute available vehicles"""
        for rec in self:
            contract_id = self.env['vehicle.contract'].search(
                [('start_date', '<=', rec.end_date), ('end_date', '>=', rec.start_date),
                 ('status', '=', 'b_in_progress')]).mapped('vehicle_id').mapped('id')
            rec.vehicle_ids = contract_id

    @api.constrains('start_date', 'end_date')
    def _contract_check_dates(self):
        """Rental contract dates"""
        for record in self:
            if record.start_date > record.end_date:
                raise ValidationError(
                    self.env._("Please ensure that the Drop-off Date is greater than the Pick-up Date"))

    @api.depends('start_date', 'end_date', 'rent_type')
    def _compute_total_rental_days(self):
        """Total rental days"""
        for rec in self:
            rec.total_days = 0.0
            if not (rec.start_date and rec.end_date):
                continue
            if rec.start_date > rec.end_date:
                continue

            delta = rec.end_date - rec.start_date
            rental_days = math.ceil(delta.total_seconds() / 86400) or 1
            if rec.rent_type == 'days':
                rec.total_days = math.ceil(delta.total_seconds() / 86400) or 1
            elif rec.rent_type == 'hour':
                rec.total_days = delta.total_seconds() / 3600
            elif rec.rent_type == 'week':
                rec.total_days = rental_days / 7
            elif rec.rent_type == 'month':
                months = (
                        (rec.end_date.year - rec.start_date.year) * 12 +
                        (rec.end_date.month - rec.start_date.month)
                )
                rec.total_days = months + (
                        (rec.end_date.day - rec.start_date.day) / 30
                )
            elif rec.rent_type == 'year':
                rec.total_days = (rental_days / 365)

            rec.total_days = round(rec.total_days, 2)

    @api.constrains('driver_charge')
    def _check_driver_charge(self):
        """Ensure driver charge are greater than zero."""
        for record in self:
            if record.is_driver_required:
                if record.driver_charge <= 0:
                    raise ValidationError(self.env._("The driver charges must be greater than zero."))

    @api.depends(
        'rent_type', 'rent', 'total_days',
        'driver_charge', 'driver_charge_type',
        'vehicle_id.minimum_km_per_day',
        'start_date', 'end_date'
    )
    def _compute_total_vehicle_rent(self):
        """Compute total vehicle rent safely"""
        for rec in self:
            total_vehicle_rent = 0.0
            delta = 0
            if rec.start_date and rec.end_date:
                start = fields.Date.to_date(rec.start_date)
                end = fields.Date.to_date(rec.end_date)
                delta = (end - start).days
                if delta < 0:
                    delta = 0
            rent_mapping = {
                'days': rec.total_days,
                'week': rec.total_days,
                'month': rec.total_days,
                'hour': rec.total_days,
                'year': rec.total_days,
            }

            if rec.rent and rec.rent_type in rent_mapping:
                total_vehicle_rent = rec.rent * (rent_mapping[rec.rent_type] or 0)
            elif rec.rent_type == 'km' and rec.vehicle_id:
                total_vehicle_rent = rec.rent * (rec.vehicle_id.minimum_km_per_day or 0) * delta
            elif rec.rent_type == 'mi' and rec.vehicle_id:
                total_vehicle_rent = (rec.rent * ((rec.vehicle_id.minimum_km_per_day or 0) * 0.621371) * delta)
            if rec.driver_charge_type == 'excluding':
                total_vehicle_rent += rec.driver_charge or 0.0
            rec.total_vehicle_rent = round(total_vehicle_rent, 2)

    @api.depends('extra_charge', 'rent_type',
                 'total_extra_days', 'total_extra_week',
                 'total_extra_month', 'total_extra_hour',
                 'total_extra_year', 'total_extra_km',
                 'total_extra_mi')
    def _compute_total_extra_charges(self):
        """Compute total extra charge"""
        for rec in self:
            total_extra_charges = 0.0
            if rec.extra_charge and rec.rent_type:
                rent_type_map = {
                    'days': rec.total_extra_days,
                    'week': rec.total_extra_week,
                    'month': rec.total_extra_month,
                    'hour': rec.total_extra_hour,
                    'year': rec.total_extra_year,
                    'km': rec.total_extra_km,
                    'mi': rec.total_extra_mi,
                }
                total_extra_charges = rec.extra_charge * rent_type_map.get(rec.rent_type, 0.0)
            rec.total_extra_charges = total_extra_charges

    @api.constrains(
        'is_any_extra_charges', 'rent_type', 'total_extra_hour', 'total_extra_days',
        'total_extra_week', 'total_extra_month', 'total_extra_year', 'total_extra_km',
        'total_extra_mi')
    def _validate_extra_charge_positive_values(self):
        """Validate extra charge positive values"""
        for record in self:
            if not record.is_any_extra_charges:
                continue
            if record.rent_type == 'hour' and record.total_extra_hour <= 0:
                raise ValidationError(self.env._("The total extra hours must be greater than zero."))
            elif record.rent_type == 'days' and record.total_extra_days <= 0:
                raise ValidationError(self.env._("The total extra days must be greater than zero."))
            elif record.rent_type == 'week' and record.total_extra_week <= 0:
                raise ValidationError(self.env._("The total extra weeks must be greater than zero."))
            elif record.rent_type == 'month' and record.total_extra_month <= 0:
                raise ValidationError(self.env._("The total extra months must be greater than zero."))
            elif record.rent_type == 'year' and record.total_extra_year <= 0:
                raise ValidationError(self.env._("The total extra years must be greater than zero."))
            elif record.rent_type == 'km' and record.total_extra_km <= 0:
                raise ValidationError(self.env._("The total extra km must be greater than zero."))
            elif record.rent_type == 'mi' and record.total_extra_mi <= 0:
                raise ValidationError(self.env._("The total extra miles must be greater than zero."))

    @api.constrains('rent_type', 'extra_charge', 'is_any_extra_charges')
    def _validate_extra_charge_values(self):
        """Validate extra charge greater than zero based on rent type"""
        type_labels = {
            'hour': self.env._("Hour"),
            'days': self.env._("Day"),
            'week': self.env._("Week"),
            'month': self.env._("Month"),
            'year': self.env._("Year"),
            'km': self.env._("KM"),
            'mi': self.env._("MI"),
        }
        for record in self:
            if (record.is_any_extra_charges
                    and record.rent_type in type_labels
                    and record.extra_charge <= 0):
                raise ValidationError(
                    _("The extra charge per %s must be greater than zero.")
                    % type_labels[record.rent_type])

    def action_create_extra_charge_invoice(self):
        """Create an extra charge invoice if applicable."""
        rent_type_mapping = {
            'days': self.total_extra_days,
            'week': self.total_extra_week,
            'month': self.total_extra_month,
            'hour': self.total_extra_hour,
            'year': self.total_extra_year,
            'km': self.total_extra_km,
            'mi': self.total_extra_mi,
        }
        quantity = rent_type_mapping.get(self.rent_type, 0)
        if quantity <= 0:
            return None
        extra_charge_line = {
            'product_id': self.env.ref('vehicle_rental.vehicle_rent_extra_charge').id,
            'name': self.vehicle_id.name if self.vehicle_id else '',
            'quantity': quantity,
            'price_unit': self.extra_charge,
        }
        invoice_lines = [(0, 0, extra_charge_line)]
        data = {
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'vehicle_contract_id': self.id,
        }
        extra_charge_invoice = self.env['account.move'].sudo().create(data)
        self.extra_charge_invoice_id = extra_charge_invoice.id
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Extra Charge Invoice'),
            'res_model': 'account.move',
            'res_id': extra_charge_invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_vehicle_payment(self):
        """Create vehicle payment"""
        for rec in self:
            if not rec.payment_type:
                message = _display_rental_notification(
                    message="""Select your preferred payment method to proceed.""",
                    message_type='warning')
                return message
            if not rec.total_vehicle_rent:
                message = _display_rental_notification(
                    message="""Please total rental charges that are greater than zero.""",
                    message_type='warning')
                return message
            if rec.end_date and rec.start_date:
                days_diff = rec.end_date - rec.start_date
                diff = relativedelta(rec.end_date, rec.start_date)
                total_days = days_diff.days
                total_months = (diff.years * 12) + diff.months
                total_weeks = total_days // 7
                quarter = (
                        (rec.end_date.year - rec.start_date.year) * 12
                        + rec.end_date.month - rec.start_date.month
                )
                total_quarters = quarter // 3
                year_diff = relativedelta(rec.end_date, rec.start_date)
                total_years = year_diff.years + year_diff.months / 12 + year_diff.days / 365
                amount = self.total_vehicle_rent
                if self.payment_type == 'full_payment':
                    payment_data = {
                        'invoice_item_id': self.invoice_item_id.id,
                        'name': 'Full Payment Invoice',
                        'payment_date': fields.Date.today(),
                        'payment_amount': amount,
                        'vehicle_contract_id': self.id,
                    }
                    self.env['vehicle.payment.option'].create(payment_data)
                elif self.payment_type == 'daily':
                    day_amount = amount / total_days if total_days else 0
                    invoice_date = self.start_date.date()
                    for i in range(total_days):
                        payment_data = {
                            'invoice_item_id': self.invoice_item_id.id,
                            'name': f'Installment {i + 1}',
                            'payment_date': invoice_date,
                            'payment_amount': day_amount,
                            'vehicle_contract_id': self.id,
                        }
                        self.env['vehicle.payment.option'].create(payment_data)
                        invoice_date = invoice_date + relativedelta(days=1)
                elif self.payment_type == 'monthly':
                    day_amount = amount / total_days
                    remain_amount = amount
                    invoice_date = self.start_date.date()
                    for i in range(total_months):
                        current_month_days = calendar.monthrange(invoice_date.year, invoice_date.month)[1]
                        monthly_payment_amount = current_month_days * day_amount
                        payment_data = {
                            'invoice_item_id': self.invoice_item_id.id,
                            'name': f'Installment {i + 1}',
                            'payment_date': invoice_date,
                            'payment_amount': monthly_payment_amount,
                            'vehicle_contract_id': self.id,
                        }
                        self.env['vehicle.payment.option'].create(payment_data)
                        invoice_date = invoice_date + relativedelta(months=1)
                        remain_amount -= monthly_payment_amount
                    if remain_amount > 0:
                        payment_data = {
                            'invoice_item_id': self.invoice_item_id.id,
                            'name': 'Remain Days',
                            'payment_date': invoice_date,
                            'payment_amount': remain_amount,
                            'vehicle_contract_id': self.id,
                        }
                        self.env['vehicle.payment.option'].create(payment_data)
                elif self.payment_type == 'weekly':
                    day_amount = amount / total_days
                    remain_amount = amount
                    invoice_date = self.start_date.date()
                    for i in range(total_weeks):
                        q_end_date = invoice_date + relativedelta(days=7)
                        q_days = (q_end_date - invoice_date).days
                        weekly_payment_amount = q_days * day_amount
                        payment_data = {
                            'invoice_item_id': self.invoice_item_id.id,
                            'name': f'Installment {i + 1}',
                            'payment_date': invoice_date,
                            'payment_amount': weekly_payment_amount,
                            'vehicle_contract_id': self.id,
                        }
                        self.env['vehicle.payment.option'].create(payment_data)
                        invoice_date = invoice_date + relativedelta(days=7)
                        remain_amount -= weekly_payment_amount
                    if remain_amount > 0:
                        payment_data = {
                            'invoice_item_id': self.invoice_item_id.id,
                            'name': 'Remain Days',
                            'payment_date': invoice_date,
                            'payment_amount': remain_amount,
                            'vehicle_contract_id': self.id,
                        }
                        self.env['vehicle.payment.option'].create(payment_data)
                elif self.payment_type == 'quarterly':
                    day_amount = amount / total_days
                    remain_amount = amount
                    start_date = self.start_date
                    for i in range(total_quarters):
                        q_end_date = start_date + relativedelta(months=3)
                        q_days = (q_end_date - start_date).days
                        quarterly_payment_amount = q_days * day_amount
                        payment_data = {
                            'invoice_item_id': self.invoice_item_id.id,
                            'name': f'Installment {i + 1}',
                            'payment_date': start_date,
                            'payment_amount': quarterly_payment_amount,
                            'vehicle_contract_id': self.id,
                        }
                        self.env['vehicle.payment.option'].create(payment_data)
                        start_date = q_end_date + relativedelta(days=1)
                        remain_amount -= quarterly_payment_amount
                    if remain_amount > 0:
                        payment_data = {
                            'invoice_item_id': self.invoice_item_id.id,
                            'name': 'Remain Days',
                            'payment_date': start_date,
                            'payment_amount': remain_amount,
                            'vehicle_contract_id': self.id,
                        }
                        self.env['vehicle.payment.option'].create(payment_data)
                elif self.payment_type == 'yearly':
                    day_amount = amount / total_days
                    current_year = self.start_date.year
                    current_year_start_date = datetime(current_year, 1, 1)
                    current_year_end_date = datetime(current_year + 1, 1, 1)
                    number_of_days_in_current_year = (
                            current_year_end_date - current_year_start_date).days
                    full_year_amount = round(number_of_days_in_current_year * day_amount, 2)
                    remain_amount = amount
                    start_date = self.start_date
                    for i in range(int(total_years)):
                        payment_data = {
                            'invoice_item_id': self.invoice_item_id.id,
                            'name': f'Installment {i + 1}',
                            'payment_date': start_date,
                            'payment_amount': full_year_amount,
                            'vehicle_contract_id': self.id,
                        }
                        self.env['vehicle.payment.option'].create(payment_data)
                        start_date = start_date + relativedelta(years=1)
                        remain_amount -= full_year_amount
                    if remain_amount > 0:
                        payment_data = {
                            'invoice_item_id': self.invoice_item_id.id,
                            'name': 'Remain Days',
                            'payment_date': start_date,
                            'payment_amount': remain_amount,
                            'vehicle_contract_id': self.id,
                        }
                        self.env['vehicle.payment.option'].create(payment_data)
            self.installment_created = True
        return True

    def action_create_extra_service_charge_invoice(self):
        """Action create extra service charge invoice"""
        invoice_lines = []
        for record in self.extra_service_ids:
            extra_service = {
                'product_id': record.product_id.id,
                'name': record.description,
                'quantity': record.product_qty,
                'price_unit': record.amount,
            }
            invoice_lines.append((0, 0, extra_service))
        data = {
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'vehicle_contract_id': self.id
        }
        extra_service_invoice_id = self.env['account.move'].sudo().create(data)
        self.extra_service_invoice_id = extra_service_invoice_id.id
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Extra Service Invoice'),
            'res_model': 'account.move',
            'res_id': extra_service_invoice_id.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def _compute_document_count(self):
        """Compute document count"""
        for rec in self:
            rec.document_count = self.env['customer.documents'].search_count(
                [('vehicle_contract_id', '=', rec.id)])

    def action_customer_document(self):
        """Action view customer documents"""
        context = {
            'default_vehicle_contract_id': self.id,
        }
        if self.status == 'c_return':
            context['create'] = False
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Documents'),
            'res_model': 'customer.documents',
            'domain': [('vehicle_contract_id', '=', self.id)],
            'view_mode': 'list',
            'target': 'current',
            'context': context,
        }

    def _compute_invoice_count(self):
        """Compute invoice count"""
        for rec in self:
            rec.invoice_count = self.env['account.move'].search_count(
                [('vehicle_contract_id', '=', rec.id)])

    def view_customer_invoice(self):
        """View customer invoice"""
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Invoices'),
            'res_model': 'account.move',
            'domain': [('vehicle_contract_id', '=', self.id)],
            'context': {
                'default_vehicle_contract_id': self.id,
                'create': False,
            },
            'view_mode': 'list,form',
            'target': 'current',
        }

    def cancellation_charge_invoice(self):
        """Cancellation charge invoice"""
        invoice_line = []
        for rec in self:
            if not rec.cancellation_charge:
                message = _display_rental_notification(
                    message="""Please note: A vehicle contract cancellation charge is required.""",
                    message_type='warning')
                return message
            cancellation_data = {
                'product_id': self.env.ref(
                    'vehicle_rental.vehicle_contract_cancellation_charge').id,
                'name': rec.cancellation_policy_id.title,
                'quantity': 1,
                'price_unit': rec.cancellation_charge
            }
            invoice_line = [(0, 0, cancellation_data)]
        data = {
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_line,
            'vehicle_contract_id': self.id
        }
        cancellation_invoice_id = self.env['account.move'].sudo().create(data)
        self.cancellation_invoice_id = cancellation_invoice_id.id
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Cancellation Invoice'),
            'res_model': 'account.move',
            'res_id': cancellation_invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def create_contract_trip_expense_report(self):
        """Create Trip Expense Reports"""
        all_draft_expenses = self.contract_expense_ids.filtered(lambda e: e.state == 'draft')
        if not all_draft_expenses:
            message = _display_rental_notification(
                message="""All expenses already submitted.""",
                message_type='warning')
            return message
        all_draft_expenses.action_submit()
        message = _display_rental_notification(
            message="""Draft expenses submitted successfully.""",
            message_type='warning')
        return message

    @api.onchange('vehicle_scratch_report_id')
    def _onchange_rental_scratch_report(self):
        """Onchange rental scratch report"""
        for rec in self:
            if rec.vehicle_scratch_report_id:
                rec.scratch_image = False

    def action_open_rental_image_editor(self):
        """Action open image editor"""
        other_record_id = self.vehicle_scratch_report_id.id if self.vehicle_scratch_report_id else False
        return {
            'type': 'ir.actions.client',
            'name': 'Image Editor',
            'tag': 'image_editor_action',
            'context': {
                'record_id': self.id,
                'model': 'vehicle.contract',
                'field_name': 'scratch_image',
                'image_url': f'/web/image/vehicle.scratch.report/{other_record_id}/avatar' if other_record_id else '',
            },
            'target': 'new',
        }

    def action_send_scratch_approval_mail(self):
        """Action send scratch approval mail"""
        mail_template = self.env.ref('vehicle_rental.scratch_report_review_signature_required_mail_template')
        if mail_template:
            mail_template.send_mail(self.id, force_send=True)

    def get_scratch_report_url(self):
        """Return signed URL using secure"""
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/rental/customer/sign/{self.access_token}"

    @api.onchange('vehicle_rental_checklist_id')
    def _onchange_vehicle_rental_checklist_id(self):
        """Onchange Vehicle Rental Checklist"""
        for rec in self:
            rec.rental_contract_checklist_ids = [(5, 0, 0)]
            lines = []
            if rec.vehicle_rental_checklist_id:
                for data in rec.vehicle_rental_checklist_id.rental_checklist_item_ids.sorted('sequence'):
                    lines.append((0, 0, {
                        'name': data.name,
                        'sequence': data.sequence,
                        'display_type': data.display_type,
                    }))
            rec.rental_contract_checklist_ids = lines

    @api.model
    def action_create_rent_payment_invoice(self):
        """Action create rent payment invoice"""
        rental_contract = self.env['vehicle.contract'].sudo().search([('status', '=', 'b_in_progress')])
        today_date = fields.Date.today()
        for data in rental_contract:
            for rec in data.vehicle_payment_option_ids:
                if rec.payment_date == today_date:
                    rec.action_create_payment_invoice()

    # ✅ ✅ دالة التعبئة التلقائية عند اختيار رقم الهيكل
    @api.onchange('vin_sn')
    def _onchange_vin_sn_auto_fill(self):
        """عند اختيار سيارة من حقل vin_sn، يتم ربطها بـ vehicle_id وتعبئة الحقول المرتبطة تلقائياً"""
        for rec in self:
            if rec.vin_sn:
                rec.vehicle_id = rec.vin_sn.id
                # الحقول التالية (license_plate, engine_number, colors...) ستُحدَّث تلقائياً
                # إذا كانت محددة كـ related في ملف vehicle_contract_inherit.py
                rec.onchange_vehicle_details()  # تحديث الحقول الأخرى يدوياً إذا لزم
            else:
                rec.vehicle_id = False

    @api.model
    def cron_send_whatsapp_reminders(self):
        """Cron job to send WhatsApp reminders 1 day before pickup and drop-off dates."""
        today = fields.Date.today()
        tomorrow = today + timedelta(days=1)
        
        pickup_reminder_contracts = self.search([
            ('status', '=', 'b_in_progress'),
            ('start_date', '>=', fields.Datetime.start_of(tomorrow, 'day')),
            ('start_date', '<', fields.Datetime.start_of(tomorrow + timedelta(days=1), 'day')),
            ('customer_id', '!=', False),
            '|', ('customer_id.mobile', '!=', False), ('customer_id.phone', '!=', False),
        ])
        
        dropoff_reminder_contracts = self.search([
            ('status', '=', 'b_in_progress'),
            ('end_date', '>=', fields.Datetime.start_of(tomorrow, 'day')),
            ('end_date', '<', fields.Datetime.start_of(tomorrow + timedelta(days=1), 'day')),
            ('customer_id', '!=', False),
            '|', ('customer_id.mobile', '!=', False), ('customer_id.phone', '!=', False),
        ])
        
        sent_count = 0
        for contract in pickup_reminder_contracts:
            try:
                contract._send_whatsapp_pickup_reminder()
                sent_count += 1
            except Exception as e:
                _logger.error("Failed to send pickup reminder for contract %s: %s", 
                            contract.reference_no, str(e))
        
        for contract in dropoff_reminder_contracts:
            try:
                contract._send_whatsapp_dropoff_reminder()
                sent_count += 1
            except Exception as e:
                _logger.error("Failed to send drop-off reminder for contract %s: %s", 
                            contract.reference_no, str(e))
        
        return True

    def _send_whatsapp_pickup_reminder(self):
        """Internal method to send pickup reminder via WhatsApp."""
        self.ensure_one()
        phone = self.customer_id.mobile or self.customer_id.phone
        if not phone:
            return False
        
        message = (
            f"مرحبًا {self.customer_id.name} 👋\n\n"
            f"🔔 تذكير: غدًا موعد استلام سيارتك المستأجرة 🚗\n\n"
            f"📋 تفاصيل العقد:\n"
            f"• رقم العقد: {self.reference_no}\n"
            f"• السيارة: {self.vehicle_id.name or 'N/A'}\n"
            f"• موعد الاستلام: {self.start_date.strftime('%Y-%m-%d %H:%M') if self.start_date else 'N/A'}\n"
            f"• موقع الاستلام: {self.pick_up_city or 'N/A'}\n\n"
            f"يرجى إحضار رخصة القيادة وبطاقة الهوية.\n"
            f"لأي استفسار، تواصل معنا 💚"
        )
        
        whatsapp_msg = self.env['adv.whatsapp.out'].sudo().create({
            'type': 'text',
            'phone': phone,
            'body': message,
            'status': 'pending',
        })
        whatsapp_msg.sudo().action_send_whatsapp()
        return True

    def _send_whatsapp_dropoff_reminder(self):
        """Internal method to send drop-off reminder via WhatsApp."""
        self.ensure_one()
        phone = self.customer_id.mobile or self.customer_id.phone
        if not phone:
            return False
        
        message = (
            f"مرحبًا {self.customer_id.name} 👋\n\n"
            f"🔔 تذكير: غدًا موعد إعادة السيارة المستأجرة 🚗\n\n"
            f"📋 تفاصيل العقد:\n"
            f"• رقم العقد: {self.reference_no}\n"
            f"• السيارة: {self.vehicle_id.name or 'N/A'}\n"
            f"• موعد التسليم: {self.end_date.strftime('%Y-%m-%d %H:%M') if self.end_date else 'N/A'}\n"
            f"• موقع التسليم: {self.drop_off_city or 'N/A'}\n\n"
            f"⚠️ ملاحظات هامة:\n"
            f"• يرجى إعادة السيارة بنفس مستوى الوقود عند الاستلام\n"
            f"• تأكد من عدم وجود أضرار جديدة لتجنب رسوم إضافية\n"
            f"• أحضر جميع متعلقاتك الشخصية قبل التسليم\n\n"
            f"شكراً لثقتك بنا 💚"
        )
        
        whatsapp_msg = self.env['adv.whatsapp.out'].sudo().create({
            'type': 'text',
            'phone': phone,
            'body': message,
            'status': 'pending',
        })
        whatsapp_msg.sudo().action_send_whatsapp()
        return True
