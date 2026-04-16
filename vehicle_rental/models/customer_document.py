# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api


class CustomerDocument(models.Model):
    """Customer Documents"""
    _name = 'customer.documents'
    _description = __doc__
    _rec_name = 'document_type'
    _order = 'create_date desc'

    # ✅ ربط المستند بالعميل (جديد)
    partner_id = fields.Many2one(
        'res.partner',
        string="العميل",
        ondelete='cascade',
        help="العميل الذي يملك هذه الوثيقة"
    )
    
    # ✅ ربط المستند بالعقد (اختياري - للعقود السابقة)
    vehicle_contract_id = fields.Many2one(
        "vehicle.contract",
        string="عقد الإيجار",
        ondelete='set null'
    )
    
    vehicle_id = fields.Many2one(
        related='vehicle_contract_id.vehicle_id',
        string="المركبة",
        readonly=True,
        store=True
    )
    
    file_name = fields.Char(string="اسم الملف")
    avatar = fields.Binary(string="المستند", required=True, attachment=True)
    document_type = fields.Selection([
        ('dl', "رخصة القيادة"),
        ('passport', "جواز السفر / البطاقة الشخصية"),
        ('aadhaar_card', "بطاقة الهوية"),
        ('voter_id', "بطاقة الناخب"),
        ('ration_card', "بطاقة التموين"),
        ('photo_id', "بطاقة تعريف مصورة"),
        ('bank_statement', "كشف حساب بنكي"),
        ('proof_address', "إثبات عنوان"),
        ('other', "أخرى")
    ], string="نوع الوثيقة", required=True)
    
    issue_date = fields.Date(string="تاريخ الإصدار")
    expiry_date = fields.Date(string="تاريخ الانتهاء")
    notes = fields.Text(string="ملاحظات")
    
    # ✅ حقل مساعد للبحث
    partner_name = fields.Char(
        string="اسم العميل",
        related='partner_id.name',
        readonly=True,
        store=True
    )

    @api.onchange('partner_id')
    def _onchange_partner_id_auto_fill(self):
        """تعبئة تلقائية لبيانات العميل"""
        if self.partner_id:
            # يمكن إضافة منطق إضافي هنا إذا لزم
            pass

    def action_view_customer_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'مستندات العميل',
            'res_model': 'customer.documents',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
