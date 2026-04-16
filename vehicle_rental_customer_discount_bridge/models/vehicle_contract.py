# -*- coding: utf-8 -*-
import calendar
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from odoo.addons.vehicle_rental.utils import _display_rental_notification


class VehicleContract(models.Model):
    _inherit = 'vehicle.contract'

    available_discount_profile_ids = fields.Many2many(
        'vehicle.customer.discount', compute='_compute_available_discount_profiles', string='Available Discounts'
    )
    discount_profile_id = fields.Many2one(
        'vehicle.customer.discount',
        string='Customer Discount Template',
        domain="[('id', 'in', available_discount_profile_ids)]",
        copy=False,
        help='Optional: load values from a saved customer discount template. You can still edit the fields below for this contract only.',
    )
    discount_reason = fields.Text(copy=False)
    discount_type = fields.Selection([
        ('free_days', 'Free Days'),
        ('fixed_amount', 'Fixed Amount'),
        ('percentage', 'Percentage'),
    ], copy=False)
    discount_free_days = fields.Float(copy=False)
    discount_fixed_amount = fields.Monetary(currency_field='currency_id', copy=False)
    discount_percentage = fields.Float(copy=False)
    discount_product_id = fields.Many2one(
        'product.product', string='Discount Product', copy=False,
        default=lambda self: self.env.ref('vehicle_rental_customer_discount_bridge.product_vehicle_rental_discount', raise_if_not_found=False)
    )
    discount_applied = fields.Boolean(default=False, copy=False)
    discount_amount = fields.Monetary(compute='_compute_discount_totals', store=True, currency_field='currency_id')
    total_after_discount = fields.Monetary(compute='_compute_discount_totals', store=True, currency_field='currency_id')
    has_customer_discount = fields.Boolean(compute='_compute_discount_totals', store=True)
    discount_locked = fields.Boolean(compute='_compute_discount_locked')
    discount_lock_reason = fields.Char(compute='_compute_discount_locked')

    @api.depends('customer_id', 'company_id', 'start_date')
    def _compute_available_discount_profiles(self):
        for rec in self:
            profiles = self.env['vehicle.customer.discount']
            if rec.customer_id:
                profiles = rec.customer_id.vehicle_discount_profile_ids.filtered(lambda p: p.is_valid_for_contract(rec))
            rec.available_discount_profile_ids = profiles

    @api.depends(
        'total_vehicle_rent',
        'discount_applied', 'discount_type',
        'discount_free_days', 'discount_fixed_amount', 'discount_percentage',
        'rent_type', 'rent', 'total_days'
    )
    def _compute_discount_totals(self):
        for rec in self:
            amount = 0.0
            if rec.discount_applied:
                amount = rec._get_discount_amount()
            gross = rec.total_vehicle_rent or 0.0
            amount = min(amount, gross)
            rec.discount_amount = amount
            rec.total_after_discount = gross - amount
            rec.has_customer_discount = bool(amount)

    @api.depends('vehicle_payment_option_ids.invoice_id', 'vehicle_payment_option_ids.payment_state')
    def _compute_discount_locked(self):
        for rec in self:
            locked = False
            reason = False
            paid_lines = rec.vehicle_payment_option_ids.filtered(
                lambda p: p.invoice_id and p.payment_state in ('partial', 'paid', 'in_payment')
            )
            if paid_lines:
                locked = True
                reason = _('Discount is locked because at least one rental payment is partially paid or fully paid.')
            rec.discount_locked = locked
            rec.discount_lock_reason = reason

    @api.onchange('customer_id')
    def _onchange_customer_id_discount(self):
        for rec in self:
            rec.discount_profile_id = False
            if rec.discount_applied and not rec.discount_locked:
                rec.action_clear_customer_discount()

    @api.onchange('discount_profile_id')
    def _onchange_discount_profile_id(self):
        for rec in self:
            if rec.discount_profile_id:
                rec._load_discount_profile_values(rec.discount_profile_id)

    def _load_discount_profile_values(self, profile):
        self.ensure_one()
        self.discount_reason = profile.reason
        self.discount_type = profile.discount_type
        self.discount_free_days = profile.free_days
        self.discount_fixed_amount = profile.fixed_amount
        self.discount_percentage = profile.percentage
        self.discount_product_id = profile.discount_product_id

    def _get_discount_amount(self):
        self.ensure_one()
        gross = self.total_vehicle_rent or 0.0
        amount = 0.0
        if self.discount_type == 'free_days':
            if self.rent_type != 'days':
                return 0.0
            free_days = min(self.discount_free_days or 0.0, self.total_days or 0.0)
            amount = (self.rent or 0.0) * free_days
        elif self.discount_type == 'fixed_amount':
            amount = self.discount_fixed_amount or 0.0
        elif self.discount_type == 'percentage':
            amount = gross * ((self.discount_percentage or 0.0) / 100.0)
        return min(round(amount, 2), gross)

    def _validate_discount_setup(self):
        self.ensure_one()
        if self.discount_locked:
            raise ValidationError(self.discount_lock_reason or _('This discount can no longer be changed.'))
        if not self.customer_id:
            raise ValidationError(_('Please select the customer first.'))
        if not self.discount_type:
            raise ValidationError(_('Please choose a discount type.'))
        if self.discount_type == 'free_days':
            if self.rent_type != 'days':
                raise ValidationError(_('Free Days discount can only be used when Rent Type is Days.'))
            if self.discount_free_days <= 0:
                raise ValidationError(_('Free Days must be greater than zero.'))
        elif self.discount_type == 'fixed_amount':
            if self.discount_fixed_amount <= 0:
                raise ValidationError(_('Fixed Amount must be greater than zero.'))
        elif self.discount_type == 'percentage':
            if self.discount_percentage <= 0 or self.discount_percentage > 100:
                raise ValidationError(_('Percentage must be greater than zero and at most 100.'))
        if not self.discount_product_id:
            raise ValidationError(_('Please select the discount product.'))

    def _prepare_discount_split(self, base_amounts, total_discount):
        total_base = sum(base_amounts)
        if not base_amounts or total_base <= 0 or total_discount <= 0:
            return [0.0 for _ in base_amounts]
        allocated = []
        running = 0.0
        for idx, amount in enumerate(base_amounts, start=1):
            if idx == len(base_amounts):
                share = round(total_discount - running, 2)
            else:
                share = round(total_discount * (amount / total_base), 2)
                running += share
            allocated.append(share)
        return allocated

    def _apply_discount_to_existing_uninvoiced_options(self):
        self.ensure_one()
        uninvoiced_options = self.vehicle_payment_option_ids.filtered(lambda p: not p.invoice_id)
        if not uninvoiced_options:
            return

        invoiced_discount = sum(self.vehicle_payment_option_ids.filtered(lambda p: p.invoice_id).mapped('discount_amount_applied'))
        remaining_discount = max((self.discount_amount if self.discount_applied else 0.0) - invoiced_discount, 0.0)
        base_amounts = []
        for option in uninvoiced_options:
            base_amount = option.base_payment_amount or option.payment_amount
            if not option.base_payment_amount:
                option.base_payment_amount = base_amount
            base_amounts.append(round(base_amount, 2))
        discount_split = self._prepare_discount_split(base_amounts, remaining_discount)
        for option, gross_amount, discount_share in zip(uninvoiced_options, base_amounts, discount_split):
            option.write({
                'base_payment_amount': gross_amount,
                'discount_amount_applied': discount_share,
                'payment_amount': round(gross_amount - discount_share, 2),
            })

    def _clear_discount_from_existing_uninvoiced_options(self):
        self.ensure_one()
        uninvoiced_options = self.vehicle_payment_option_ids.filtered(lambda p: not p.invoice_id)
        for option in uninvoiced_options:
            gross_amount = option.base_payment_amount or option.payment_amount
            option.write({
                'base_payment_amount': gross_amount,
                'discount_amount_applied': 0.0,
                'payment_amount': gross_amount,
            })

    def action_apply_customer_discount(self):
        for rec in self:
            if rec.discount_profile_id:
                rec._load_discount_profile_values(rec.discount_profile_id)
            rec._validate_discount_setup()
            rec.discount_applied = True
            if rec.vehicle_payment_option_ids:
                rec._apply_discount_to_existing_uninvoiced_options()
            elif rec.installment_created:
                rec.installment_created = False
        return True

    def action_clear_customer_discount(self):
        for rec in self:
            if rec.discount_locked:
                raise ValidationError(rec.discount_lock_reason or _('This discount can no longer be changed.'))
            had_payment_options = bool(rec.vehicle_payment_option_ids)
            if had_payment_options:
                rec._clear_discount_from_existing_uninvoiced_options()
            rec.discount_applied = False
            rec.discount_profile_id = False
            rec.discount_reason = False
            rec.discount_type = False
            rec.discount_free_days = 0.0
            rec.discount_fixed_amount = 0.0
            rec.discount_percentage = 0.0
            rec.discount_product_id = self.env.ref(
                'vehicle_rental_customer_discount_bridge.product_vehicle_rental_discount',
                raise_if_not_found=False,
            )
            if rec.installment_created and not had_payment_options:
                rec.installment_created = False
        return True

    def _create_discounted_payment_options(self, installment_specs):
        self.ensure_one()
        discount_total = self.discount_amount if self.discount_applied else 0.0
        base_amounts = [round(spec['payment_amount'], 2) for spec in installment_specs]
        discount_split = self._prepare_discount_split(base_amounts, discount_total)
        PaymentOption = self.env['vehicle.payment.option']
        for spec, discount_share in zip(installment_specs, discount_split):
            gross_amount = round(spec['payment_amount'], 2)
            net_amount = round(gross_amount - discount_share, 2)
            vals = {
                'invoice_item_id': spec['invoice_item_id'],
                'name': spec['name'],
                'payment_date': spec['payment_date'],
                'payment_amount': net_amount,
                'vehicle_contract_id': self.id,
                'base_payment_amount': gross_amount,
                'discount_amount_applied': discount_share,
            }
            PaymentOption.create(vals)

    def action_create_vehicle_payment(self):
        for rec in self:
            if not rec.payment_type:
                return _display_rental_notification(
                    message="""Please add the payment type first""",
                    message_type='warning')
            if not rec.invoice_item_id:
                return _display_rental_notification(
                    message="""Please add the invoice item first""",
                    message_type='warning')
            if rec.vehicle_payment_option_ids:
                rec.vehicle_payment_option_ids.unlink()
            elif rec.installment_created:
                rec.installment_created = False

            total_rent = rec.total_vehicle_rent or 0.0
            installment_specs = []
            if rec.payment_type == 'full_payment':
                installment_specs.append({
                    'invoice_item_id': rec.invoice_item_id.id,
                    'name': '%s Full Payment' % rec.reference_no,
                    'payment_date': rec.start_date.date() if rec.start_date else fields.Date.context_today(rec),
                    'payment_amount': total_rent,
                })
            else:
                payment_delta = {
                    'daily': relativedelta(days=1),
                    'weekly': relativedelta(weeks=1),
                    'monthly': relativedelta(months=1),
                    'quarterly': relativedelta(months=3),
                    'yearly': relativedelta(years=1),
                }.get(rec.payment_type)
                if not payment_delta:
                    return _display_rental_notification(
                        message="""Unsupported payment type selected""",
                        message_type='warning')
                current_date = rec.start_date
                installment = 1
                while current_date and rec.end_date and current_date < rec.end_date:
                    next_date = current_date + payment_delta
                    end_boundary = rec.end_date if next_date > rec.end_date else next_date
                    payment_amount = rec._compute_prorated_installment_amount(current_date, end_boundary)
                    if payment_amount > 0:
                        installment_specs.append({
                            'invoice_item_id': rec.invoice_item_id.id,
                            'name': '%s Installment %s' % (rec.reference_no, installment),
                            'payment_date': current_date.date(),
                            'payment_amount': round(payment_amount, 2),
                        })
                        installment += 1
                    current_date = next_date

            if installment_specs:
                rec._create_discounted_payment_options(installment_specs)
            rec.installment_created = True
        return True

    def _compute_prorated_installment_amount(self, period_start, period_end):
        self.ensure_one()
        if not period_start or not period_end or period_end <= period_start:
            return 0.0

        total_period_seconds = (self.end_date - self.start_date).total_seconds() if self.start_date and self.end_date else 0.0
        installment_seconds = (period_end - period_start).total_seconds()
        if total_period_seconds <= 0 or installment_seconds <= 0:
            return 0.0

        return (self.total_vehicle_rent or 0.0) * (installment_seconds / total_period_seconds)
