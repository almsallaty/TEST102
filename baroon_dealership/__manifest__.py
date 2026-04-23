{
    'name': 'Baroon Dealership',
    'version': '19.0.30.0.14',
    'summary': 'Premium VIN-first car dealership management with inventory, sales, purchase, CRM, accounting, website, and reporting',
    'description': '''
Tag Team Company Dealership for Odoo 19.

A premium VIN-first dealership management module for tracking physical vehicles as unique serial/lot records and managing the full operational cycle across purchase, inventory, CRM, sales, accounting, website, and reporting.

Main capabilities:
- Product = vehicle model, Serial/Lot = physical car by VIN
- Vehicle reservation, quotation, sale, delivery, and archival flow
- Purchase receipt, movement tracking, and shipment visibility
- CRM linkage for opportunities and customer follow-up
- Costing support including landed costs, expenses, and profit visibility
- Website and portal vehicle publishing flows
- Dashboard, operational reports, and management reports

Prepared for Tag Team Company.
''',
    'author': 'Tag Team Company',
    'license': 'LGPL-3',
    'category': 'Sales/Sales',
    'depends': [
        'stock',
        'product',
        'purchase_stock',
        'sale_stock',
        'crm',
        'sale_crm',
        'mail',
        'website',
        'portal',
        'account',
        'stock_landed_costs',
    ],
    'data': [
        'security/ir.model.access.csv',
        'reports/car_reports.xml',
        'views/color_views.xml',
        'views/product_template_views.xml',
        'views/crm_lead_views.xml',
        'views/purchase_order_views.xml',
        'views/sale_order_views.xml',
        'views/stock_lot_views.xml',
        'views/car_expense_views.xml',
        'views/car_test_drive_views.xml',
        'views/car_analysis_views.xml',
        'views/res_config_settings_views.xml',
        'views/stock_landed_cost_views.xml',
        'views/account_move_views.xml',
        'views/dealership_dashboard_views.xml',
        'wizards/car_transfer_wizard_views.xml',
        'views/car_sale_menus.xml',
        'views/website_car_templates.xml',
        'views/portal_templates.xml',
        'views/website_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'baroon_dealership/static/src/js/car_image_gallery_field.js',
            'baroon_dealership/static/src/xml/car_image_gallery_field.xml',
            'baroon_dealership/static/src/scss/car_image_gallery.scss',
            'baroon_dealership/static/src/scss/car_dashboard.scss',
        ],
        'web.assets_frontend': [
            'baroon_dealership/static/src/css/car_sale_website.css',
            'baroon_dealership/static/src/js/car_sale_website.js',
        ],
    },
    'installable': True,
    'application': True,
}
