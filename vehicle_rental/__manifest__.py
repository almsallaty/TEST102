# -*- coding: utf-8 -*-
# Copyright 2022-Today TechKhedut.
# Part of TechKhedut. See LICENSE file for full copyright and licensing details.

{
    'name': "Vehicle Rental Management | Car Rent | Car Rental Management",
    'version': "3.2",
    'description': "A car rental, hire car or car hire agency is a company that rents automobiles for short periods.",
    'summary': "Vehicle Rental Management",
    'author': 'TechKhedut Inc.',
    'website': "https://techkhedut.com",
    'category': "Car Rental",

    'depends': [
        'mail',
        'contacts',
        'product',
        'fleet',
        'sale_management',
        'maintenance',
        'hr_expense',
        'crm',
        'website',
        'portal',
    ],

    'data': [
        # Data
        'data/vehicle_product_data_views.xml',
        'data/sequence_views.xml',
        'data/ir_cron.xml',
        'data/cron_data.xml',
        'data/website_menu.xml',

        # Security
        'security/ir.model.access.csv',
        'security/security.xml',

        # Wizards
        'wizards/vehicle_damage_views.xml',
        'wizards/rental_contract_booking_views.xml',
        'wizards/maintenance_request_bill_views.xml',
        'wizards/lead_rental_contract_views.xml',
        'wizards/return_deposit_views.xml',

        # Views
        'views/assets.xml',
        'views/res_partner_views.xml',
        'views/res_partner_rental_history_views.xml',
        'views/fleet_image_views.xml',
        'views/fleet_inherit_views.xml',
        'views/fleet_vehicle_two.xml',
        'views/account_asset_views.xml',
        'views/vehicle_contract_views.xml',
        'views/vehicle_contract_inherit_views.xml',
        'views/customer_document_views.xml',
        'views/cancellation_policy_views.xml',
        'views/invoice_inherit_views.xml',
        'views/vehicle_scratch_report_views.xml',
        'views/maintenance_schedule_views.xml',
        'views/maintenance_inherit_views.xml',
        'views/rental_agreement_terms_views.xml',
        'views/hr_expense_views.xml',
        'views/crm_lead_views.xml',
        'views/res_config_settings_views.xml',
        'views/fleet_features_views.xml',
        'views/vehicle_rental_checklist_views.xml',

        # Reports
        'report/vehicle_contract_report_views.xml',
        'report/scratch_report_views.xml',

        # Mail Templates
        'data/vehicle_rental_mail_template.xml',
        'data/vehicle_rental_scratch_mail.xml',
        'data/rental_booking_enquiry_mail.xml',
        'data/booking_created_mail.xml',
        'data/maintenance_request_mail.xml',
        'data/upcoming_maintenance_mail.xml',

        # Web Templates
        'views/templates/web_contract_booking_views.xml',
        'views/templates/scratch_report_approval_template.xml',

        # Menus
        'views/menus.xml',
    ],

    'assets': {
        'web.assets_backend': [
            # External libs
            'https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.2.4/fabric.min.js',

            # ✅ SAFE FIX (no freeze)

            # Existing assets
            'vehicle_rental/static/src/xml/template.xml',
            'vehicle_rental/static/src/scss/style.scss',
            'vehicle_rental/static/src/scss/image_capture_widget.scss',
            'vehicle_rental/static/src/js/lib/moment.min.js',
            'vehicle_rental/static/src/js/lib/apexcharts.js',
            'vehicle_rental/static/src/js/lib/xy.js',
            'vehicle_rental/static/src/js/lib/index.js',
            'vehicle_rental/static/src/js/lib/Animated.js',
            'vehicle_rental/static/src/js/lib/dhtmlxgantt.css',
            'vehicle_rental/static/src/js/lib/dhtmlxgantt.js',
            'vehicle_rental/static/src/xml/availability_template.xml',
            'vehicle_rental/static/src/js/availability_template.js',
            'vehicle_rental/static/src/js/dashboard/vehicle_rental_dashboard.js',
            'vehicle_rental/static/src/js/image_editor.js',
            'vehicle_rental/static/src/js/image_capture_field.js',
            'vehicle_rental/static/src/xml/image_editor_template.xml',
            'vehicle_rental/static/src/xml/image_capture_field.xml',
            'vehicle_rental/static/src/css/image_editor.css',
        ],

        'web.assets_frontend': [
            'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css',
            'vehicle_rental/static/src/css/lib/daterangepicker.css',
            'vehicle_rental/static/src/js/frontend/web_contract_booking_enquiry.js',
            'vehicle_rental/static/src/css/style.css',
        ],
    },

    'images': ['static/description/cover.gif'],
    'license': 'OPL-1',

    'installable': True,
    'application': True,
    'auto_install': False,

    'price': 99,
    'currency': 'USD',
}
