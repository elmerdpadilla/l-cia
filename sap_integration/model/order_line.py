# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp
from openerp import workflow
class sap_order(osv.osv):
    _inherit = 'sale.order'
    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, line.price_unit * (1-(line.discount or 0.0)/100.0)* (1-(line.max or 0.0)/100.0), line.product_uom_qty, line.product_id, line.order_id.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        return val
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
		'amount_discount':0.0,
            }
            val = val1 = val2= 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
		val2 += line.price_subtotal*line.max/100
		
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
	    res[order.id]['amount_discount'] = cur_obj.round(cr, uid, cur, val2)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']-res[order.id]['amount_discount']
        return res
    def button_dummy(self, cr, uid, ids, context=None):
	for order in self.browse(cr,uid,ids,context=context):
	    for line in order.order_line:
		dproduct=line.codebar_id.item_id.discount*100
		print dproduct
		final=order.disc;
		if order.disc>dproduct:
		    final = dproduct
		self.pool.get('sale.order.line').write(cr,uid,line.id,{'max':final},context=context)
		print line.id
        return True
    def discount_sap_change(self, cr, uid, ids,discount, partner_id=False, context=None):
	id=ids[0]
	print "%"*50
	if partner_id:
	    obj_partner=self.pool.get('res.partner').browse(cr,uid,partner_id,context=context)
	    price=discount
	    if( obj_partner.discount*100)<discount:
		price = obj_partner.discount*100
            return {'value': {'disc': price},}
	else:
	    return {'value': {'disc': 0.0},}	
    def _get_dated(self, cr, uid, ids, field, arg, context=None):
        result = {}
	for order in self.browse(cr,uid,ids,context=context):
	    dt = datetime.strptime(order.date_order, "%Y-%m-%d %H:%M:%S").date()
	    print "#"*50
	    result[order.id]=dt
	return result
    def _get_discount(self, cr, uid, ids, field, arg, context=None):
        result = {}
	for order in self.browse(cr,uid,ids,context=context):
	    dt = 0.0
	    for line in order.order_line:
		dt += line.price_subtotal*line.max/100
		print dt
		print "#"*50
	    result[order.id]=dt
	return result
    def _get_ediscount(self, cr, uid, ids, field, arg, context=None):
        result = {}
	for order in self.browse(cr,uid,ids,context=context):
	    dt = 0.0
	    dt = 100*order.amount_discount/order.amount_total
	    result[order.id]=dt
	return result
    _columns = {
		'date_end': fields.date(string="Date End"),
		'date_orderd':fields.function(_get_dated,type='date', string='Date'),
		'amount_discount':fields.function(_get_discount,type='float', string='Discount',digits_compute=dp.get_precision('Account')),
		'efective_discount':fields.function(_get_ediscount,type='float', string='Discount efective',digits_compute=dp.get_precision('Account')),
		'disc':fields.float(string='Discount',digits_compute=dp.get_precision('Account')),
		}
    _defaults = {
	'disc' : 0.0,
		}
class sap_order_line(osv.osv):
    _inherit = 'sale.order.line'
    def _get_name(self, cr, uid, ids, field, arg, context=None):
        result = {}
	for line in self.browse(cr,uid,ids,context=context):
	    result[line.id]=line.codebar_id.description
	return result
    def product_uom_change(self, cursor, user, ids, pricelist, codebar_id, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, context=None):
        context = context or {}
        lang = lang or ('lang' in context and context['lang'])
        if not uom:
            return {'value': {'price_unit': 0.0, 'product_uom' : uom or False}}
        return self.barcode_id_change(cursor, user, ids, pricelist, codebar_id,
                qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name,
                partner_id=partner_id, lang=lang, update_tax=update_tax,
                date_order=date_order, context=context)

    def discount_sap_change(self, cr, uid, ids,discount, pricelist, barcode, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        context = context or {}
        lang = lang or ('lang' in context and context['lang'])
	obj_codebars=self.pool.get('product.codebars').browse(cr,uid,barcode,context=context)
	obj_product=self.pool.get('product.template').browse(cr,uid,obj_codebars.item_id.id,context=context)
	print "%"*50
	price= discount
	if (obj_product.discount*100)<discount:
	    price= obj_product.discount*100		
        return {'value': {'discount': price},}


    def barcode_id_change(self, cr, uid, ids, pricelist, barcode, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):

	obj_codebars=self.pool.get('product.codebars').browse(cr,uid,barcode,context=context)
	    #return {'value': {'product_id': obj_codebars.item_id.id,}}
	print "$"*50
	flag=True
        if not uom:
	    uom=obj_codebars.uom_id.id
	    flag=False
	product=0
        domain = {}


	product=obj_codebars.item_id.id
	ratio = obj_codebars.uom_id.factor
	
	domain = {'product_uom':
                        [('category_id', '=', obj_codebars.uom_id.category_id.id)],}
	name=obj_codebars.description
	if obj_codebars.uom_id.uom_type == 'smaller' and uom == obj_codebars.uom_id.id:
	    ratio= 1/ratio
	qtyreal=ratio*qty
	discount=0
	price =0
	price2=0
	color=False
	arraysequence=[]
	if pricelist and barcode:
	    product_tmp=self.pool.get('product.product').search(cr,uid,[('product_tmpl_id','=',product)],context=context)
	    obj_tarifa=self.pool.get('product.pricelist').browse(cr,uid,pricelist,context=context)
            price=0
            for tarifa in obj_tarifa:
	        for version in tarifa.version_id:
		    #print version.product_id.id
                    if version.product_id.id == product:
		        #print (version.product_id.id)
			price = version.price;

			for sequence in version.product_pricelist_discount_ids:
			    arraysequence.append([sequence.amount,sequence.discount])
			inc=1
			if len(arraysequence)>0:
			    tam = len(arraysequence)
			    for inc in range(1,tam,inc*3+1):
				while inc>0:
				    for i in range(inc,tam):
					j=i
					temp=arraysequence[i]
					while j>=inc and arraysequence[j-inc][0]<temp[0]:
					    arraysequence[j]=arraysequence[j-inc]
					    j=j-inc
					arraysequence[j]=temp
				    inc=inc/2
			    for sequence in arraysequence:
				if qtyreal>=sequence[0]:
				    discount=sequence[1]
				    print discount
				    print "#"*50
				    color=True
				    break
			    price-=price*discount/100
		        price2=price
		        price*=ratio
	    if flag:
	        return {'value': {'price_unit': price,'price': price2,'product_id':product_tmp[0],'name':name,'color':color,},'domain':domain}
	    else:
		return {'value': {'price_unit': price,'product_uom':uom,'price': price2,'product_id':product_tmp[0],'name':name,'color':color},'domain':domain}		
        context = context or {}
        lang = lang or context.get('lang', False)
        if not partner_id:
            raise osv.except_osv(_('No Customer Defined!'), _('Before choosing a product,\n select a customer in the sales form.'))
        warning = False
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        context = {'lang': lang, 'partner_id': partner_id}
        partner = partner_obj.browse(cr, uid, partner_id)
        lang = partner.lang
        context_partner = {'lang': lang, 'partner_id': partner_id}
        if not product:
            return {'value': {'th_weight': 0,
                'product_uos_qty': qty}, 'domain': {'product_uom': [],
                   'product_uos': []}}
        if not date_order:
            date_order = time.strftime(DEFAULT_SERVER_DATE_FORMAT)

        result = {}
        warning_msgs = ''
        product_obj = product_obj.browse(cr, uid, product, context=context_partner)

        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False

        fpos = False
        if not fiscal_position:
            fpos = partner.property_account_position or False
        else:
            fpos = self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position)
        if update_tax: #The quantity only have changed
            result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, product_obj.taxes_id)

        if not flag:
            result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context_partner)[0][1]
            if product_obj.description_sale:
                result['name'] += '\n'+product_obj.description_sale
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            result['th_weight'] = qty * product_obj.weight
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}
        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
            result['th_weight'] = result['product_uom_qty'] * product_obj.weight
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
            result['th_weight'] = q * product_obj.weight        # Round the quantity up

        if not uom2:
            uom2 = product_obj.uom_id
        # get unit price

        if not pricelist:
            warn_msg = _('You have to select a pricelist or a customer in the sales form !\n'
                    'Please set one before choosing a product.')
            warning_msgs += _("No Pricelist ! : ") + warn_msg +"\n\n"
        else:
            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                    product, qty or 1.0, partner_id, {
                        'uom': uom or result.get('product_uom'),
                        'date': date_order,
                        })[pricelist]
            if price is False:
                warn_msg = _("Cannot find a pricelist line matching this product and quantity.\n"
                        "You have to change either the product, the quantity or the pricelist.")

                warning_msgs += _("No valid pricelist line found ! :") + warn_msg +"\n\n"
            else:
                result.update({'price_unit': price})
        if warning_msgs:
            warning = {
                       'title': _('Configuration Error!'),
                       'message' : warning_msgs
                    }
        return {'value': result, 'domain': domain, 'warning': warning}

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
	print "#"*50
	print pricelist
	if pricelist:
	    product_tmp=self.pool.get('product.product').browse(cr,uid,product,context=context).product_tmpl_id
	    idproduct= product_tmp.id
	    obj_tarifa=self.pool.get('product.pricelist').browse(cr,uid,pricelist,context=context)
            precio=0
            for tarifa in obj_tarifa:
	        for version in tarifa.version_id:
		    #print version.product_id.id
                    if version.product_id.id == idproduct:
			print "#"*50
		        #print (version.product_id.id)
			precio = version.price;
	    print (product)	
	    print precio
	    		
        context = context or {}
        lang = lang or context.get('lang', False)
        if not partner_id:
            raise osv.except_osv(_('No Customer Defined!'), _('Before choosing a product,\n select a customer in the sales form.'))
        warning = False
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        context = {'lang': lang, 'partner_id': partner_id}
        partner = partner_obj.browse(cr, uid, partner_id)
        lang = partner.lang
        context_partner = {'lang': lang, 'partner_id': partner_id}
        if not product:
            return {'value': {'th_weight': 0,
                'product_uos_qty': qty}, 'domain': {'product_uom': [],
                   'product_uos': []}}
        if not date_order:
            date_order = time.strftime(DEFAULT_SERVER_DATE_FORMAT)

        result = {}
        warning_msgs = ''
        product_obj = product_obj.browse(cr, uid, product, context=context_partner)

        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False

        fpos = False
        if not fiscal_position:
            fpos = partner.property_account_position or False
        else:
            fpos = self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position)
        if update_tax: #The quantity only have changed
            result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, product_obj.taxes_id)

        if not flag:
            result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context_partner)[0][1]
            if product_obj.description_sale:
                result['name'] += '\n'+product_obj.description_sale
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            result['th_weight'] = qty * product_obj.weight
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}
        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
            result['th_weight'] = result['product_uom_qty'] * product_obj.weight
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
            result['th_weight'] = q * product_obj.weight        # Round the quantity up

        if not uom2:
            uom2 = product_obj.uom_id
        # get unit price

        if not pricelist:
            warn_msg = _('You have to select a pricelist or a customer in the sales form !\n'
                    'Please set one before choosing a product.')
            warning_msgs += _("No Pricelist ! : ") + warn_msg +"\n\n"
        else:
            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                    product, qty or 1.0, partner_id, {
                        'uom': uom or result.get('product_uom'),
                        'date': date_order,
                        })[pricelist]
            if price is False:
                warn_msg = _("Cannot find a pricelist line matching this product and quantity.\n"
                        "You have to change either the product, the quantity or the pricelist.")

                warning_msgs += _("No valid pricelist line found ! :") + warn_msg +"\n\n"
            else:
                result.update({'price_unit': price})
        if warning_msgs:
            warning = {
                       'title': _('Configuration Error!'),
                       'message' : warning_msgs
                    }
        return {'value': result, 'domain': domain, 'warning': warning}



    _columns = {
		'codebar_id': fields.many2one('product.codebars',string="Codebars"),
		'price': fields.float(string="Precio Unitario",digits_compute=dp.get_precision('Product Price')),
		'color': fields.boolean(string="color"),
		'name':fields.function(_get_name,type='char', string='name'),
		'comment':fields.text(string="Comentario"),
		'max':fields.integer(string="discount MAX"),
		}
    _defaults = {
	'color' : False,
		}
