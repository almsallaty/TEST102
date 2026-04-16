# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
import secrets

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..utils import _display_rental_notification


class FleetVehicle(models.Model):
    """Fleet Vehicle"""
    _inherit = ['fleet.vehicle', 'mail.thread', 'mail.activity.mixin']  # ✅ إضافة التتبع
    _description = __doc__

    # ===== حقول الإيجار مع التتبع =====
    rent_day = fields.Monetary(string="Rent per Day", tracking=True)
    rent_week = fields.Monetary(string="Rent per Week", tracking=True)
    rent_month = fields.Monetary(string="Rent per Month", tracking=True)
    rent_km = fields.Monetary(string="Rent per Kilometer", tracking=True)
    rent_mi = fields.Monetary(string="Rent per Mile", tracking=True)

    rent_hour = fields.Monetary(string="Rent per Hour", tracking=True)
    rent_year = fields.Monetary(string="Rent per Year", tracking=True)

    extra_charge_day = fields.Monetary(string="Charge per Day", tracking=True)
    extra_charge_week = fields.Monetary(string="Charge per Week", tracking=True)
    extra_charge_month = fields.Monetary(string="Charge per Month", tracking=True)
    extra_charge_km = fields.Monetary(string="Charge per Kilometer", tracking=True)
    extra_charge_mi = fields.Monetary(string="Charge per Mile", tracking=True)

    extra_charge_hour = fields.Monetary(string="Charge per Hour", tracking=True)
    extra_charge_year = fields.Monetary(string="Charge per Year", tracking=True)

    rental_contract_count = fields.Integer(compute='_compute_total_rental_contract', string=" Contracts")
    
    # ✅ حالة المركبة مع التتبع
    status = fields.Selection(
        [('available', 'Operational'), ('in_maintenance', 'Under Maintenance')],
        string="Status", default="available", tracking=True)
    
    maintenance_schedule_id = fields.Many2one('maintenance.schedule', string="Maintenance Schedule", tracking=True)
    maintenance_request_id = fields.Many2one('maintenance.request', string="Maintenance Request")
    maintenance_request_count = fields.Integer(compute='_compute_maintenance_request_count')
    maintenance_bill_count = fields.Integer(compute='_compute_maintenance_bill_count')
    upcoming_maintenance_date = fields.Date(string="Upcoming Maintenance Date", tracking=True)
    reminder_days = fields.Integer(string="Maintenance Reminder Days", compute='_compute_reminder_days')

    # Vehicle Expanses
    is_any_vehicle_expense = fields.Boolean(tracking=True)
    fleet_expense_ids = fields.One2many(comodel_name='hr.expense', inverse_name='fleet_vehicle_id')
    minimum_km_per_day = fields.Float('Min KM per Day', tracking=True)

    access_token = fields.Char()

    features_ids = fields.Many2many('fleet.features', 'fleet_features_rel', 'fleet_id', 'feature_id', 'Features', tracking=True)
    rental_policy_ids = fields.One2many('fleet.rental.policy', 'fleet_id', 'Rental Policy')
    inclusion_ids = fields.One2many('fleet.inclusions', 'fleet_id', 'Inclusions')
    additional_info_ids = fields.One2many('fleet.additional.info', 'fleet_id', 'Additional Information')
    fleet_image_ids = fields.One2many('fleet.images', 'fleet_id')

    location = fields.Many2one(
        'stock.location',
        string='Location',
        domain="[('usage', 'in', ['internal', 'transit'])]",
        help="Select the warehouse location where this vehicle is stored",
        tracking=True  # ✅ تتبع تغيير الموقع
    )

    # ===== حقول من النموذج الأصلي مع إعادة تعريف للتتبع =====
    # ملاحظة: الحقول التالية موجودة في fleet.vehicle الأصلي، نعيد تعريفها فقط لإضافة tracking
    # إذا لم تعمل، يمكن إضافتها عبر xml أو تركها كما هي لأن التتبع يعمل على الحقول المضافة فقط

    # DEPRECATED
    bevrage = fields.Float('Bevrage')

    @api.model_create_multi
    def create(self, vals_list):
        """Create fleet record"""
        records = super().create(vals_list)
        for record in records:
            # Generate a URL-safe access token without underscores
            token = secrets.token_urlsafe(12).replace('_', '-')
            record.access_token = token
            # ✅ تسجيل إنشاء السجل في Chatter
            record.message_post(body=f"✅ تم إنشاء سجل مركبة جديد: {record.display_name}", message_type='notification')
        return records

    def write(self, vals):
        """Override write to log important changes"""
        result = super().write(vals)
        for rec in self:
            # ✅ تسجيل تغيير الحالة بشكل واضح
            if 'status' in vals:
                old_status = dict(self._fields['status'].selection).get(vals['status'], vals['status'])
                rec.message_post(
                    body=f"🔄 تم تغيير حالة المركبة إلى: <b>{old_status}</b>",
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment'
                )
            # ✅ تسجيل تغيير الموقع
            if 'location' in vals and vals['location']:
                location = self.env['stock.location'].browse(vals['location'])
                rec.message_post(
                    body=f"📍 تم تغيير موقع المركبة إلى: <b>{location.display_name}</b>",
                    message_type='notification'
                )
        return result

    @api.depends('reminder_days')
    def _compute_reminder_days(self):
        """Count reminder days"""
        for record in self:
            reminder_days = self.env['ir.config_parameter'].sudo().get_param(
                'vehicle_rental.maintenance_reminder_days')
            record.reminder_days = reminder_days

    @api.model
    def generate_fleets_missing_access_tokens(self):
        """Cron to generate access tokens for old records"""
        fleet_vehicles = self.search([('access_token', '=', False)])
        for record in fleet_vehicles:
            token = secrets.token_urlsafe(12).replace('_', '-')
            record.access_token = token

    # @api.constrains('rent_day', 'rent_week', 'rent_month', 'rent_km', 'rent_mi', 'rent_hour',
    #                 'rent_year', 'minimum_km_per_day')
    # def _check_rent_values(self):
    #     for record in self:
    #         if record.rent_hour <= 0:
    #             raise ValidationError(self.env._("Rent per Hour must be greater than 0"))
    #         if record.rent_day <= 0:
    #             raise ValidationError(self.env._("Rent per Day must be greater than 0"))
    #         if record.rent_week <= 0:
    #             raise ValidationError(self.env._("Rent per Week must be greater than 0"))
    #         if record.rent_month <= 0:
    #             raise ValidationError(self.env._("Rent per Month must be greater than 0"))
    #         if record.rent_year <= 0:
    #             raise ValidationError(self.env._("Rent per Year must be greater than 0"))
    #         if record.rent_km <= 0:
    #             raise ValidationError(self.env._("Rent per Kilometer must be greater than 0"))
    #         if record.rent_mi <= 0:
    #             raise ValidationError(self.env._("Rent per Mile must be greater than 0"))
    #         if record.minimum_km_per_day <= 0:
    #             raise ValidationError(self.env._("Minimum km per day must be greater than 0"))

    def available_to_in_maintenance(self):
        """Mark vehicle as 'In Maintenance' if no active contract is in progress."""
        for rec in self:
            existing_contract = self.env['vehicle.contract'].search(
                [('vehicle_id', '=', rec.id), ('status', '=', 'b_in_progress')]
            )
            if existing_contract:
                message = _display_rental_notification(
                    message="""A contract is already in progress for this vehicle. Please ensure
                     the car is returned before changing the status to 'Under Maintenance'.""",
                    message_type='warning')
                return message
            rec.status = 'in_maintenance'
            # ✅ تسجيل التغيير في Chatter
            rec.message_post(body="🔧 تم تغيير الحالة إلى: تحت الصيانة", message_type='notification')
        return None

    def in_maintenance_to_available(self):
        """In maintenance to available"""
        self.status = 'available'
        # ✅ تسجيل التغيير في Chatter
        self.message_post(body="✅ تم تغيير الحالة إلى: متاح للتأجير", message_type='notification')

    def _compute_total_rental_contract(self):
        """Total rental contract"""
        for rec in self:
            rec.rental_contract_count = self.env['vehicle.contract'].search_count(
                [('vehicle_id', '=', rec.id)])

    def action_rental_contract_view(self):
        """Action rental contract view"""
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Rental Contracts'),
            'res_model': 'vehicle.contract',
            'domain': [('vehicle_id', '=', self.id)],
            'view_mode': 'list,form,kanban,calendar,pivot,activity',
            'target': 'current',
            'context': {
                'create': False,
            }
        }

    def action_create_book_contract(self):
        """Action create book contract"""
        context = self.env.context
        customer = self.env['res.partner'].browse(context.get('customer_id'))
        data = {
            'vehicle_id': self.id,
            'driver_id': self.driver_id.id,
            'last_odometer': self.odometer,
            'odometer_unit': self.odometer_unit,
            'vehicle_model_year': self.model_year,
            'transmission': self.transmission,
            'fuel_type': self.fuel_type,
            'license_plate': self.license_plate,
            'customer_id': customer.id,
            'customer_phone': customer.phone,
            'customer_email': customer.email,
            'start_date': context.get('start_date'),
            'end_date': context.get('end_date'),
        }
        vehicle_contract = self.env['vehicle.contract'].create(data)
        # ✅ تسجيل إنشاء العقد في Chatter المركبة
        self.message_post(
            body=f"📄 تم إنشاء عقد إيجار جديد: <b>{vehicle_contract.reference_no}</b> للعميل: {customer.name}",
            message_type='notification'
        )
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Vehicle Contract'),
            'res_model': 'vehicle.contract',
            'res_id': vehicle_contract.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def return_action_to_open(self):
        """Return action to open"""
        self.ensure_one()
        context = self.env.context
        xml_id = context.get('xml_id')
        if not xml_id:
            return False
        if xml_id == 'fleet_vehicle_log_contract_action':
            return self.action_maintenances_request_view()
        action = self.env.ref(f'fleet.{xml_id}').sudo().read()[
            0]
        action.update(
            context=dict(context, default_vehicle_id=self.id, group_by=False),
            domain=[('vehicle_id', '=', self.id)]
        )
        return action

    def _compute_maintenance_request_count(self):
        """Compute maintenance request count"""
        for rec in self:
            rec.maintenance_request_count = self.env['maintenance.request'].search_count(
                [('fleet_vehicle_id', '=', rec.id)])

    def action_maintenances_request_view(self):
        """Action maintenance request view"""
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Maintenance Requests'),
            'res_model': 'maintenance.request',
            'view_mode': 'list,form,kanban',
            'target': 'current',
            'domain': [('fleet_vehicle_id', '=', self.id)],
            'context': {
                'default_fleet_vehicle_id': self.id,
                'create': False,
            },
        }

    def _compute_maintenance_bill_count(self):
        """Compute maintenance bill count"""
        for rec in self:
            rec.maintenance_bill_count = self.env['account.move'].search_count(
                [('fleet_vehicle_id', '=', rec.id)])

    def action_maintenance_bill_views(self):
        """Action maintenance bill views"""
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Maintenance Bills'),
            'res_model': 'account.move',
            'view_mode': 'list,form,kanban',
            'target': 'current',
            'domain': [('fleet_vehicle_id', '=', self.id)],
            'context': {
                'create': False,
            }
        }

    def action_create_maintenance_request(self):
        """Create Maintenance Request"""
        self.ensure_one()

        if not self.maintenance_schedule_id:
            return _display_rental_notification(message=self.env._("Please select a maintenance schedule."),
                                                message_type='warning')

        today_date = fields.Date.today()
        maintenance_days = self.maintenance_schedule_id.maintenance_days

        if not maintenance_days or maintenance_days <= 0:
            raise ValidationError(self.env._("Maintenance days must be greater than zero."))

        # Get last maintenance request
        last_request = self.env['maintenance.request'].search([('fleet_vehicle_id', '=', self.id)],
                                                              order='upcoming_maintenance_date desc', limit=1)
        # Determine base date
        base_date = (last_request.upcoming_maintenance_date
                     if last_request and last_request.upcoming_maintenance_date else today_date)

        # Calculate next maintenance date
        upcoming_maintenance_date = base_date + relativedelta(days=maintenance_days)

        # Prepare values
        vals = {
            'name': f"Maintenance Request - {self.display_name}",
            'request_date': base_date,
            'description': 'Scheduled maintenance',
            'maintenance_schedule_id': self.maintenance_schedule_id.id,
            'upcoming_maintenance_date': upcoming_maintenance_date,
            'fleet_vehicle_id': self.id,
        }
        maintenance_request = self.env['maintenance.request'].create(vals)
        # Link latest request
        self.maintenance_request_id = maintenance_request.id
        self.upcoming_maintenance_date = upcoming_maintenance_date
        
        # ✅ تسجيل إنشاء طلب الصيانة في Chatter
        self.message_post(
            body=f"🔧 تم إنشاء طلب صيانة جديد: <b>{maintenance_request.name}</b>\nتاريخ الصيانة القادم: {upcoming_maintenance_date}",
            message_type='notification'
        )
        
        # Send creation email
        ctx = {
            'request_date': base_date,
            'upcoming_maintenance_date': upcoming_maintenance_date,
        }
        mail_template = self.env.ref(
            'vehicle_rental.vehicle_maintenance_request_mail_template', raise_if_not_found=False)
        if mail_template:
            mail_template.with_context(ctx).send_mail(self.id, force_send=True)
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Maintenance Request'),
            'res_model': 'maintenance.request',
            'res_id': maintenance_request.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def cron_send_maintenance_reminder(self):
        """Send Maintenance Reminder"""
        reminder_days = int(self.env['ir.config_parameter'].sudo().get_param(
            'vehicle_rental.maintenance_reminder_days', 0))
        if reminder_days <= 0:
            return

        today = fields.Date.today()
        # Find all records having upcoming maintenance
        requests = self.search([('maintenance_schedule_id', '!=', False), ('upcoming_maintenance_date', '!=', False)])

        for request in requests:
            reminder_date = request.upcoming_maintenance_date - relativedelta(days=reminder_days)
            if reminder_date == today:
                template = self.env.ref('vehicle_rental.upcoming_maintenance_mail_template',
                                        raise_if_not_found=False)
                if template:
                    template.send_mail(request.id, force_send=True)


class FleetVehicleLogContract(models.Model):
    """Fleet Vehicle Log Contract"""
    _inherit = 'fleet.vehicle.log.contract'
    _description = __doc__

    license_plate = fields.Char(string="License Plate")


class FleetFeatures(models.Model):
    """Fleet Features"""
    _name = 'fleet.features'
    _description = __doc__

    name = fields.Char('', required=True)


class FleetRentalPolicies(models.Model):
    """Fleet Rental Policies"""
    _name = 'fleet.rental.policy'
    _description = __doc__

    sequence = fields.Integer()
    policy = fields.Char('Policy', required=True)
    fleet_id = fields.Many2one('fleet.vehicle', 'Vehicle')


class FleetInclusions(models.Model):
    """Fleet Inclusions"""
    _name = 'fleet.inclusions'
    _description = __doc__

    sequence = fields.Integer()
    inclusion = fields.Char('Inclusion', required=True)
    fleet_id = fields.Many2one('fleet.vehicle', 'Vehicle')


class FleetAdditionalInfo(models.Model):
    """Fleet Additional Info"""
    _name = 'fleet.additional.info'
    _description = __doc__

    sequence = fields.Integer()
    name = fields.Char(required=True)
    description = fields.Char()
    fleet_id = fields.Many2one('fleet.vehicle', 'Vehicle')


class FleetImages(models.Model):
    """Fleet Images """
    _name = 'fleet.images'
    _description = __doc__
    _inherit = ["image.mixin"]
    _order = "sequence, id"
    _rec_name = "title"

    title = fields.Char(string='Title', translate=True)
    sequence = fields.Integer(default=10)
    fleet_id = fields.Many2one('fleet.vehicle', string='Fleet', readonly=True)
    image = fields.Image(string='Images')
