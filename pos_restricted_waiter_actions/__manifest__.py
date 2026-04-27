{
    'name': 'POS Restricted Waiter Actions',
    'version': '19.0.1.0.1',
    'summary': 'Per-employee POS restrictions for sent lines, payment, order deletion, and keypad visibility with audit logging.',
    'category': 'Point of Sale',
    'author': 'OpenAI',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'hr', 'pos_restaurant'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/pos_restricted_waiter_audit_log_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_restricted_waiter_actions/static/src/js/restricted_waiter_actions.js',
            'pos_restricted_waiter_actions/static/src/css/restricted_waiter_actions.css',
        ],
    },
    'installable': True,
    'application': False,
}
