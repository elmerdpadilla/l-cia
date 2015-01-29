# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.fields import Many2one



class product_codebars(osv.Model):
 	_name = 'product.codebars'
	#_rec_name= 'description'
	def _get_name(self, cr, uid, ids, field, arg, context=None):
		result = {}
		for codebar in self.browse(cr,uid,ids,context=context):
			result[codebar.id]="["+str(codebar.bar_code)+"] "+codebar.description+" "+str(codebar.item_code)
		return result
	def name_get(self, cr, uid, ids, context=None):
		res = [(r['id'], r['description'] and '[%s] %s' % (r['bar_code'], r['description']) or r['description'] ) for r in self.read(cr, uid, ids, ['bar_code', 'description'], context=context) ]
		return res
	_columns = {
		'sap_id': fields.integer('sap_id'),
		'item_id': fields.many2one('product.template', 'Product'),		
		'bar_code': fields.char('Bar Code'),
		'description': fields.char('Description'),
		'uom_id': fields.many2one('product.uom', ' UoM'),
		'item_code':fields.char('Item Code'),
		'name':fields.function(_get_name,type='char', string='name',store=True),
		
     }
