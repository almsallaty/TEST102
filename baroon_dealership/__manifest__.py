{
    'name': 'Baroon Dealership',
    'version': '19.0.40.0.1',
    'summary': 'VIN-first car dealership: shipment pipeline, CRM, test drives, dynamic dashboard, premium reports',
    'description': '''
Baroon Dealership for Odoo 19 Enterprise.

Core principles:
- Product = car model template
- Serial/Lot = physical car tracked by VIN
- Full lifecycle: Purchase → Shipment → Customs → Preparation → Available → Reserved → Sold → Delivered
- Dynamic OWL dashboard with ApexCharts analytics
- Premium PDF reports with branded styling
- Per-VIN costing, profitability, and audit trail
- Arabic + English with full RTL support
''',
    'author': 'Baroon',
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
    ],
    'assets': {
        'web.assets_backend': [
            'baroon_dealership/static/src/js/car_image_gallery_field.js',
            'baroon_dealership/static/src/xml/car_image_gallery_field.xml',
            'baroon_dealership/static/src/scss/car_image_gallery.scss',
            'baroon_dealership/static/src/scss/car_dashboard.scss',
        ],
    },
    'installable': True,
    'application': True,
}
