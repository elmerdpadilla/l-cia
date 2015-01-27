# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.fields import Many2one



class product_codebars(osv.Model):
    _name = 'product.codebars'

    _columns = {
		'sap_id': fields.integer('sap_id'),
		'item_id': fields.many2one('product.template', 'Product'),		
		'bar_code': fields.char('Bar Code'),
		'description': fields.char('Description'),
		'uom_id': fields.many2one('product.uom', ' UoM')
     }
