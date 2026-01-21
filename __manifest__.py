# -*- coding: utf-8 -*-
{
    'name': 'yousentech_sale_ou',
	'version': '17.0.1.0.0',
	'summary': 'yousentech_sale_ou',
	'category': 'Tools',
	'author': 'Developers team',
	'maintainer': 'qimamhd-tech Techno Solutions',
	'company': 'qimamhd-tech Techno Solutions',
	'website': 'https://www.qimamhd-tech.com',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
   

    # any module necessary for this one to work correctly
    'depends': ['base','account','sale','yousentech_invoicing_ou'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/security.xml',
        
        'views/views.xml',
 

	#'wizards/recap.xml',
    ],
    # only loaded in demonstration mode
    
    'installable': True,
    'auto_install': False,
    'application': True,
}
