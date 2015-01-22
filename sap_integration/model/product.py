# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.fields import Many2one



class product_template(osv.osv):
    _inherit = 'product.template'

    _columns = {
		'sap_id': fields.integer('sap_id'),
		'item_code': fields.char('Item Code'),
		'supplier_cat_num': fields.char('Supplier Catalog Num'),
		'property_product_maker': fields.property(
			type='many2one',
            		relation='sap_integration.product.maker',
            		string='Product Maker', 
            		help="Product Maker"),
		'discount': fields.float('Discount',digits=(9,4))
     }
