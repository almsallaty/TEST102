# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = ['res.partner', 'mail.thread', 'mail.activity.mixin']  # ✅ إضافة التتبع
    
    # ===== بيانات رخصة القيادة مع التتبع =====
    license_number = fields.Char(
        string="رقم رخصة القيادة",
        tracking=True  # ✅ تتبع تغيير رقم الرخصة
    )
    license_issue_date = fields.Date(
        string="تاريخ إصدار الرخصة",
        tracking=True
    )
    license_expiry = fields.Date(
        string="تاريخ انتهاء الرخصة",
        tracking=True  # ✅ تتبع انتهاء الرخصة
    )
    license_issue_place = fields.Char(
        string="مكان إصدار الرخصة",
        tracking=True
    )
    passport_number = fields.Char(
        string="رقم الجواز - البطاقة",
        tracking=True  # ✅ تتبع رقم الجواز
    )
    date_of_birth = fields.Date(
        string="تاريخ الميلاد",
        tracking=True
    )
    
    # ===== تصنيف العميل مع التتبع =====
    rental_category = fields.Selection([
        ('vip', 'VIP'),
        ('economy', 'اقتصادي'),
        ('luxury', 'فاخر'),
        ('corporate', 'شركات')
    ], string="فئة التأجير", default='economy', tracking=True)  # ✅ تتبع تغيير الفئة
    
    # ===== الخصوصية =====
    hide_phone = fields.Boolean(
        string="إخفاء رقم الهاتف",
        tracking=True
    )
    
    # ===== العملة =====
    rental_currency_id = fields.Many2one(
        'res.currency',
        string="عملة التعاملات",
        default=lambda self: self.env.company.currency_id.id,
        tracking=True  # ✅ تتبع تغيير العملة
    )
    
    # ===== التقييم =====
    customer_rating = fields.Float(
        string="تقييم العميل", 
        default=5.0, 
        digits=(3, 2),
        tracking=True  # ✅ تتبع تغيير التقييم
    )
    
    # ===== ملاحظات =====
    nearest_landmark = fields.Char(
        string="أقرب نقطة دالة",
        tracking=True
    )
    notes = fields.Text(
        string="ملاحظات إضافية",
        tracking=True  # ✅ تتبع تغيير الملاحظات
    )
    
    # ===== جهة العمل مع التتبع =====
    employer_id = fields.Many2one(
        'res.partner', 
        string="جهة العمل", 
        domain="[('is_company', '=', True)]",
        help="شركة / جهة العمل",
        tracking=True  # ✅ تتبع تغيير جهة العمل
    )
    
    # ✅ إضافة حقل الجنسية مع التتبع
    nationality_id = fields.Many2one(
        'res.country', 
        string="الجنسية", 
        help="جنسية العميل / حامل الجواز",
        tracking=True  # ✅ تتبع تغيير الجنسية
    )
    
    # ============================================
    # ✅ سجل عقود الإيجار
    # ============================================
    rental_contract_ids = fields.One2many(
        'vehicle.contract',
        'customer_id',
        string="عقود الإيجار"
    )
    
    rental_contract_count = fields.Integer(
        string="عدد العقود",
        compute='_compute_rental_contract_count'
    )
    
    last_rental_contract_id = fields.Many2one(
        'vehicle.contract',
        string="آخر عقد إيجار",
        compute='_compute_last_rental_contract'
    )
    
    total_rental_amount = fields.Monetary(
        string="إجمالي قيمة الإيجارات",
        compute='_compute_total_rental_amount',
        currency_field='rental_currency_id'
    )

    document_ids = fields.One2many(
        'customer.documents',
        'partner_id',
        string="المستندات"
    )
    
    document_count = fields.Integer(
        string="عدد المستندات",
        compute='_compute_document_count'
    )

    # ============================================
    # ✅ دوال التتبع المخصصة
    # ============================================
    
    @api.model_create_multi
    def create(self, vals_list):
        """تسجيل إنشاء عميل جديد في Chatter"""
        records = super().create(vals_list)
        for rec in records:
            if rec.customer_rank > 0:  # إذا كان عميل تأجير
                rec.message_post(
                    body=f"👤 <b>تم تسجيل عميل تأجير جديد</b><br/>الاسم: {rec.name}<br/>رقم الجواز: {rec.passport_number or 'غير محدد'}<br/>الجنسية: {rec.nationality_id.name or 'غير محددة'}",
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment'
                )
        return records

    def write(self, vals):
        """تسجيل التغييرات المهمة في بيانات العميل"""
        # جمع التغييرات المهمة لعرضها
        changes = []
        tracked_labels = {
            'license_number': 'رقم رخصة القيادة',
            'license_expiry': 'تاريخ انتهاء الرخصة',
            'passport_number': 'رقم الجواز',
            'nationality_id': 'الجنسية',
            'rental_category': 'فئة التأجير',
            'employer_id': 'جهة العمل',
            'customer_rating': 'تقييم العميل',
        }
        
        for field, label in tracked_labels.items():
            if field in vals:
                old_val = self[field]
                new_val = vals[field]
                # تحويل القيم لعرض أفضل
                if field == 'nationality_id' and isinstance(new_val, int):
                    new_val = self.env['res.country'].browse(new_val).name
                if field == 'employer_id' and isinstance(new_val, int):
                    new_val = self.env['res.partner'].browse(new_val).name
                if field == 'rental_category':
                    selection = dict(self._fields['rental_category'].selection)
                    old_val = selection.get(old_val, old_val)
                    new_val = selection.get(new_val, new_val)
                
                if old_val != new_val:
                    changes.append(f"{label}: {old_val or 'فارغ'} → {new_val}")
        
        result = super().write(vals)
        
        # نشر التغييرات في Chatter
        if changes:
            for rec in self:
                rec.message_post(
                    body=f"🔄 <b>تم تحديث بيانات العميل</b><br/>" + "<br/>".join(changes),
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment'
                )
        return result
    
    # ============================================
    # ✅ الدوال المحسوبة
    # ============================================
    
    def _compute_document_count(self):
        for record in self:
            record.document_count = self.env['customer.documents'].search_count(
                [('partner_id', '=', record.id)]
            )
    
    def _compute_rental_contract_count(self):
        for record in self:
            record.rental_contract_count = self.env['vehicle.contract'].search_count(
                [('customer_id', '=', record.id)]
            )
    
    def _compute_last_rental_contract(self):
        for record in self:
            last = self.env['vehicle.contract'].search(
                [('customer_id', '=', record.id)],
                order='create_date desc',
                limit=1
            )
            record.last_rental_contract_id = last.id if last else False
    
    def _compute_total_rental_amount(self):
        for record in self:
            contracts = self.env['vehicle.contract'].search([
                ('customer_id', '=', record.id),
                ('status', 'in', ['b_in_progress', 'c_return'])
            ])
            record.total_rental_amount = sum(contracts.mapped('total_vehicle_rent'))
    
    def action_view_rental_contracts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'عقود الإيجار',
            'res_model': 'vehicle.contract',
            'view_mode': 'tree,form,kanban',
            'domain': [('customer_id', '=', self.id)],
            'context': {'default_customer_id': self.id},
            'target': 'current',
        }

    def action_view_customer_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'مستندات العميل',
            'res_model': 'customer.documents',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
            'target': 'current',
        }
    
    # ============================================
    # ✅ قيود التحقق
    # ============================================
    
    @api.constrains('license_expiry')
    def _check_license_expiry(self):
        for record in self:
            if record.license_expiry and record.license_expiry < fields.Date.today():
                # ✅ تسجيل تحذير انتهاء الرخصة في Chatter
                record.message_post(
                    body=f"⚠️ <b>تنبيه: رخصة القيادة منتهية</b><br/>تاريخ الانتهاء: {record.license_expiry}",
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment'
                )
                record.activity_schedule(
                    'fleet_rental_integration.mail_activity_license_expired',
                    note='رخصة قيادة العميل منتهية الصلاحية'
                )
    
    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        for record in self:
            if record.date_of_birth and record.date_of_birth > fields.Date.today():
                raise UserError('تاريخ الميلاد لا يمكن أن يكون في المستقبل')
