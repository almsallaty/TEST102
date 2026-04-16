# -*- coding: utf-8 -*-
{
    'name': 'Vehicle Rental Customer Discount Bridge',
    'version': '19.0.1.0.1',
    'summary': 'Customer-linked rental discounts with accounting integration',
    'description': '''Adds customer discount profiles to vehicle rental contracts,
with support for free days, fixed amount, and percentage discounts.
Discounts are applied to installments and shown on invoices as negative lines.''',
    'category': 'Fleet',
    'author': 'OpenAI',
    'license': 'LGPL-3',
    'depends': ['vehicle_rental', 'account', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'data/discount_product_data.xml',
        'views/res_partner_views.xml',
        'views/vehicle_customer_discount_views.xml',
        'views/vehicle_contract_views.xml',
        'views/vehicle_payment_option_views.xml',
    ],
    'installable': True,
    'application': False,
}
