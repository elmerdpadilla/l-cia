# -*- coding: utf-8 -*-
import pyodbc
#import schedule
import time
import json
import random
import urllib2
import logging
import logging.config
from openerp import models, fields, api, _


###Logging
#logging.basicConfig(filename='logging.log',level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
#logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
#logging.debug('This message should go to the log file')
#logging.info('So should this')
#logging.warning('And this, too')

#logging.config.fileConfig('config/logging.cfg') #logfile config


##SQL Server
dsn = 'larachdatasource'
user =  'odoosync'
password = 'ODOOadmin'
database = 'OdooSync'
cnxn = None

##Odoo
HOST = 'localhost'
PORT = '8069'
DB = 'dblarach'
USER = 'admin'
PASS = 'l@r@ch'
# log in the given database
url = "http://%s:%s/jsonrpc" % (HOST, PORT)
uid = 1 #self.call(self, url, "common", "login", DB, USER, PASS)

class schedule(models.Model):
	_name = 'schedule.tasks'
	
	cnxn = None
	print cnxn
	#Json RPC
	def _json_rpc(self, url, method, params):
		data = {
			"jsonrpc": "2.0",
			"method": method,
			"params": params,
			"id": random.randint(0, 1000000000),
		}
		req = urllib2.Request(url=url, data=json.dumps(data), headers={
		"Content-Type":"application/json",
		})
		
		reply = json.load(urllib2.urlopen(req))
		
		if reply.get("error"):
			raise Exception(reply["error"])
		return reply["result"]
	
	def call(self, url, service, method, *args):
		return self._json_rpc(url, "call", {"service": service, "method": method, "args": args})

	def search(obj, arg):
		result = self.call(self, url, "object", "execute", DB, uid, PASS, obj, 'search', args)
		return result


	#Conectando al origen
	def connectOrigin(self, obj):
		con_string = 'DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (dsn, user, password, database)
		self.Log('Revisando la conexión', '')		
		cn = None #cnxn
		if cn != None:
			self.Log(obj , 'Usando la conexión existente')
			return cn
		else:
			self.Log(obj, 'Intendo conectar al origen')
			try:			
				cn = pyodbc.connect(con_string)
				self.Log(obj, 'Conectado al origen')
				cnxn = cn
				return cn
			except pyodbc.Error as e:
		    		print e
				self.Log(obj +': Error de conexión', e)
				pass		

		return None
			
	######################################################################
	#############		Loggin in Odoo 
	######################################################################
	def Log(self, message, description):
		args = {'log': message, 'description': description, }
		self.call(url, "object", "execute", DB, uid, PASS, 'sap_integration.log', 'create', args)

	


	#Base for importation
	def toOdoo(self, toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
	
		self.Log('Procesando %s %s' % (toObj, current), '')
		x = self.call(url, "object", "execute", DB, uid, PASS, toObj, 'search', search)
				
		#self.Log(toObj, 'Odoo x)
		odooId=0

		if x == []: # Nuevo regisro
			self.Log('Creando ' + toObj,data)
			odooId = self.call(url, "object", "execute", DB, uid, PASS, toObj, 'create', data)
			result ='insert'			
			cursor.execute("update %s set odoo_id = %s where %s = '%s'" % (tableOrig, odooId, keyOrig, valueKeyRef)) 
			self.Log('Registro actualizado en el orígen', '')

		else:	# Registro existente
			self.Log('Actualizando ' + toObj,data)
			odooId = self.call(url, "object", "execute", DB, uid, PASS, toObj, 'write', x, data)
			result = 'update'	
			cursor.execute("update %s set odoo_id = %s where %s = '%s'" % (tableOrig, x[0], keyOrig, valueKeyRef)) 
			self.Log('Registro actualizado en el orígen', '')
			odooId =x[0]
		return odooId
	#######################################################################Series###########################################################3
	def Series(self,uid, *args):
		obj = 'Series'
		cnxc = self.connectOrigin(obj)
		if not cnxc:
			self.Log('error','No hay conexión al origen, revise la configuración')
			return
		cursor = cnxc.cursor()
		cursor.execute('exec getSeries')
		rows = cursor.fetchall()
		self.Log(obj, 'Cargando registros')
		for row in rows: # FirmCode, FirmName
			search = [('name', '=', row.SeriesName)]
			data = {'name': row.SeriesName, 'active': 1, 'prefix': row.BeginStr, 'padding': 0, 'number_next_actual': row.NextNumber, 'number_increment':1, 'implementation': 'standard', }
		
			self.toOdoo ('ir.sequence', row.SeriesName, search, data, cursor, 'NNM1', 'SeriesName', row.SeriesName)
			cnxc.commit()
		cnxc.close()
		self.Log(obj, 'Conexión cerrada')

	#######################################################################PaymentMethod###########################################################3
	def PaymentMethod(self,uid, *args):
		obj = 'PaymentMethod'
		cnxc = self.connectOrigin(obj)
		if not cnxc:
			self.Log('error','No hay conexión al origen, revise la configuración')
			return
		cursor = cnxc.cursor()
		cursor.execute('exec getPaymentMethod ')
		rows = cursor.fetchall()
		self.Log(obj, 'Cargando registros')
		for row in rows:
			search =  [('sap_id', '=', row.GroupNum)]
			data = 	{'sap_id': row.GroupNum, 'name': row.PymntGroup, 'note': row.PymntGroup, }
			self.toOdoo('account.payment.term', row.GroupNum, search, data, cursor, 'OCTG', 'GroupNum', row.GroupNum)
			cnxc.commit()
		cnxc.close()
		self.Log(obj, 'Conexión cerrada')

	#######################################################################CustomerCategories###########################################################3		
	def CustomerCategories(self,uid, *args):
		obj = 'CustomerCategories'
		cnxc = self.connectOrigin(obj)
		if not cnxc:
			self.Log('error','No hay conexión al origen, revise la configuración')
			return
		cursor = cnxn.cursor()
		cursor.execute('exec getCustomerCategories')
		rows = cursor.fetchall()
		self.Log(obj, 'Cargando registros')
		for row in rows:
			search =  [('sap_id', '=', row.GroupCode)]
			data = args = {'sap_id': row.GroupCode, 'name': row.GroupName, }
			self.toOdoo('res.partner.category', row.GroupCode, search, data, cursor, 'OCRG', 'GroupCode', row.GroupCode)
			cnxc.commit()
		cnxc.close()
		self.Log(obj, 'Conexión cerrada')

	#######################################################################Customers###########################################################3
	def customers(self,uid, *args):
		obj = 'Customers'
		cnxc = self.connectOrigin(obj)
		if not cnxc:
			self.Log('error','No hay conexión al origen, revise la configuración')
			return
		cursor = cnxc.cursor()
		cursor.execute('exec getCustomer')
		rows = cursor.fetchall()
		self.Log(obj, 'Cargando registros')
		for row in rows:
			search = [('sap_id', '=', row.CardCode)]
			data = {'sap_id': row.CardCode, 'name': row.name, 'display_name': row.name, 'customer':row.customer, 'supplier': row.supplier, 'property_payment_term': row.property_payment_term,  'discount': float(row.Discount), 'credit_limit': float(row.credit_limit), 'category_id': [(6,0,[row.category_id])], 'property_account_position' : row.property_account_position, 'active': row.active, 'country_id': row.country, 'city':row.City, 'property_product_pricelist': row.PriceListId }
		
			self.toOdoo ('res.partner', row.CardCode, search, data, cursor, 'OCRD', 'CardCode', row.CardCode)
			cnxc.commit()
		cnxc.close()
		self.Log(obj, 'Conexión cerrada')
	#######################################################################3ProductMaker###########################################################3
	def ProductMaker(self,uid, *args):
		obj = 'Product Makers'
		cnxc = self.connectOrigin(obj)
		if not cnxc:
			self.Log('error','No hay conexión al origen, revise la configuración')
			return
		cursor = cnxc.cursor()
		cursor.execute('exec getFabricantes')
		rows = cursor.fetchall()
	
		for row in rows: # FirmCode, FirmName
			search = [('sap_id', '=', row.FirmCode)]
			data = {'sap_id': row.FirmCode, 'name': row.FirmName, }
		
			self.toOdoo ('sap_integration.product.maker', row.FirmCode, search, data, cursor, 'OMRC', 'FirmCode', row.FirmCode)
			cnxc.commit()
		cnxc.close()
		self.Log(obj, 'Conexión cerrada')

	#######################################################################3ProductMaker###########################################################3
	def ProductCategory(self,uid, *args):
		obj = 'ProductCategory'
		cnxc = self.connectOrigin(obj)
		if not cnxc:
			self.Log('error','No hay conexión al origen, revise la configuración')
			return
		cursor = cnxc.cursor()
		cursor.execute('exec getProductCategory')
		rows = cursor.fetchall()
	
		for row in rows: ##ItmsGrpCod, ItmsGrpNam 
			search = [('sap_id', '=', row.ItmsGrpCod)]
			data = {'sap_id': row.ItmsGrpCod, 'name': row.ItmsGrpNam,  }
		
			self.toOdoo ('product.category', row.ItmsGrpCod, search, data, cursor, 'OITB', 'ItmsGrpCod', row.ItmsGrpCod)
			cnxc.commit()
		cnxc.close()
		self.Log(obj, 'Conexión cerrada')
	#######################################################################ProductUoMCategory###########################################################3

	def ProductUoMCategory(self,uid, *args):
		obj = 'ProductUoMCategory'
		cnxc = self.connectOrigin(obj)
		if not cnxc:
			self.Log('error','No hay conexión al origen, revise la configuración')
			return
		cursor = cnxc.cursor()
		cursor.execute('exec getUomCategory')
		rows = cursor.fetchall()
	
		for row in rows: # id, name
			search = [('sap_id', '=', row.id)]
			data = {'sap_id': row.id, 'name': row.name, }
		
			#toOdoo(toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
			self.toOdoo ('product.uom.categ', row.id, search, data, cursor, 'odoo_uomCategory', 'id', row.id)
			cnxc.commit()
		cnxc.close()
		self.Log(obj, 'Conexión cerrada')
	#######################################################################ProductUoM###########################################################3
	def ProductUoM(self,uid, *args):
		obj = 'ProductUoMCategory'
		cnxc = self.connectOrigin(obj)
		if not cnxc:
			self.Log('error','No hay conexión al origen, revise la configuración')
			return
		cursor = cnxc.cursor()
		cursor.execute('exec getUoM')
		rows = cursor.fetchall()
	
		for row in rows: # id, categoryId, name, factor, type, rounding
			search = [('sap_id', '=', row.id)]
			data = {'sap_id': row.id, 'name': row.name, 'category_id': row.categoryId, 'uom_type': row.type, 'factor': float(row.factor), 'roundind':float(row.rounding)}
		
			#toOdoo(toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
			self.toOdoo ('product.uom', row.id, search, data, cursor, 'odoo_uom', 'id', row.id)
			cnxc.commit()
		cnxc.close()
		self.Log(obj, 'Conexión cerrada')


	#######################################################################Items###########################################################3

	def Items(self,uid, *args):
		obj = 'ProductUoMCategory'
		cnxc = self.connectOrigin(obj)
		if not cnxc:
			self.Log('error','No hay conexión al origen, revise la configuración')
			return
		cursor = cnxc.cursor()
		cursor.execute('exec getItems')
		rows = cursor.fetchall()
	
		for row in rows: # ItemCode, categoryId, name, factor, type, rounding
			search = [('item_code', '=', row.ItemCode)]
			tax=[]		
			if row.Vatliable ==0:
				tax = []
			else:
				tax = [row.Vatliable]
			data = {'sap_id': row.ItemCode, 'item_code': row.ItemCode, 'name': row.Name, 'categ_id': row.ItmsGrpCod, 'taxes_id': [(6,0,tax)], 'purchase_ok': row.purchase_ok, 'sale_ok': row.sale_ok, 'discount': float(row.Discount), 'uom_id': row.uom_id, 'uom_po_id': row.uom_id, 'supplier_cat_num': row.SuppCatNum, 'property_product_maker': row.FirmCode, 'active':row.active, 'default_code': row.CodeBars, 'on_hand': float(row.OnHand), 'is_commited': float(row.IsCommited), 'on_order': float(row.OnOrder), 'product_uom_cat_id': row.uom_cat }
		
			#toOdoo(toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
			odoo_id = self.toOdoo ('product.template', row.ItemCode, search, data, cursor, 'OITM', 'ItemCode', row.ItemCode)
			#cnxc.commit()
			print 
			##Ahora creando el CodeBars principal
			# a.BcdEntry ,a.BcdCode, a.BcdName, a.ItemCode, c.odoo_id as ItemsId, a.UomEntry, b.PkgType, u.odoo_id as uom_cat, v.odoo_id as uom_id, v.name
			search = [('bar_code', '=', row.CodeBars)]
			data = {'sap_id': 0, 'item_id': odoo_id, 'bar_code': row.CodeBars, 'description': row.Name, 'uom_id': row.uom_id, 'item_code': row.ItemCode, }
		
			#toOdoo(toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
			self.toOdoo ('product.codebars', row.ItemCode, search, data, cursor, 'OBCD', 'BcdEntry', 0)
			cnxc.commit()	
		cnxc.close()
		self.Log(bj, 'Conexión cerrada')

	#######################################################################PriceList###########################################################3
	def PriceList(self,uid, *args):
		obj = 'ProductUoMCategory'
		cnxc = self.connectOrigin(obj)
		if not cnxc:
			self.Log('error','No hay conexión al origen, revise la configuración')
			return
		cursor = cnxc.cursor()
		cursor.execute('exec getPriceList')
		rows = cursor.fetchall()
	
		for row in rows: # ListNum, ListName, BASE_NUM, Factor
			search = [('sap_id', '=', row.ListNum)]
		
			data = {'sap_id': row.ListNum, 'name': row.ListName, 'active': 1, 'type': 'sale', 'currency_id': 45, 'based_in': row.BASE_NUM, 'factor': float(row.Factor), }
		
			#toOdoo(toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
			self.toOdoo ('product.pricelist', row.ListNum, search, data, cursor, 'OPLN', 'ListNum', row.ListNum)
			cnxc.commit()
		cnxc.close()
		self.Log(obj, 'Conexión cerrada')

	#######################################################################PriceListVersion###########################################################3
	def PriceListVersion(self,uid, *args):
		obj = 'PriceListVersion'
		cnxc = self.connectOrigin(obj)
		if not cnxc:
			self.Log('error','No hay conexión al origen, revise la configuración')
			return
		cursor = cnxc.cursor()
		cursor.execute('exec getPriceListVersion')
		rows = cursor.fetchall()
	
		for row in rows: # a.sap_id, a.ItemCode name,  b.odoo_id ListNumOdoo, d.odoo_id as ItemCodeOdoo, a.Price, a.Currency, a.Factor, isnull(c.LINENUM,0) LINENUM, c.FromDate, c.ToDate
			search = [('sap_id', '=', row.sap_id)]
		
			data = {'sap_id': row.sap_id, 'name': row.name, 'pricelist_id': row.ListNumOdoo, 'product_id': row.ItemCodeOdoo, 'price': float(row.Price), 'currency_id': row.Currency, 'factor': float(row.Factor), 'line_num': row.LINENUM, 'date_start': row.FromDate, 'date_end': row.ToDate }
		
			#toOdoo(toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
			self.toOdoo ('product.pricelist.version', row.sap_id, search, data, cursor, 'ITM1', 'sap_id', row.sap_id)
			cnxc.commit()
		cnxc.close()
		self.Log(obj, 'Conexión cerrada')

	#######################################################################PriceListDiscounts###########################################################3
	def PriceListDiscounts(self,uid, *args):
		obj = 'PriceListDiscounts'
		cnxc = self.connectOrigin(obj)
		if not cnxc:
			self.Log('error','No hay conexión al origen, revise la configuración')
			return		
		cursor = cnxc.cursor()
		cursor.execute('exec getPriceListDiscounts')
		rows = cursor.fetchall()
	
		for row in rows: # sap_id, ListVersionOdoo, SPP2LNum, Amount, Discount
			search = [('sap_id', '=', row.sap_id)]
		
			data = {'sap_id': row.sap_id, 'pricelist_version_id': row.ListVersionOdoo, 'sequence': row.SPP2LNum, 'amount': float(row.Amount), 'discount': float(row.Discount) }
		
			#toOdoo(toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
			self.toOdoo ('product.pricelist.discount', row.sap_id, search, data, cursor, 'SPP2', 'sap_id', row.sap_id)
			cnxc.commit()
		cnxc.close()
		self.Log(obj, 'Conexión cerrada')

	#######################################################################Items###########################################################3
	def BarCode(self,uid, *args):
		obj = 'BarCode'
		cnxc = self.connectOrigin(obj)
		if not cnxc:
			self.Log('error','No hay conexión al origen, revise la configuración')
			return
		cursor = cnxc.cursor()
		cursor.execute('exec getBarCode')
		rows = cursor.fetchall()
	
		for row in rows: # a.BcdEntry ,a.BcdCode, a.BcdName, a.ItemCode, c.odoo_id as ItemsId, a.UomEntry, b.PkgType, u.odoo_id as uom_cat, v.odoo_id as uom_id, v.name
			search = [('sap_id', '=', row.BcdEntry)]
		
			data = {'sap_id': row.BcdEntry, 'item_id': row.ItemsId, 'bar_code': row.BcdCode, 'description': row.BcdName, 'uom_id': row.uom_id, 'item_code': row.ItemCode, }
		
			#toOdoo(toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
			self.toOdoo ('product.codebars', row.BcdEntry, search, data, cursor, 'OBCD', 'BcdEntry', row.BcdEntry)
			cnxc.commit()
		cnxc.close()
		self.Log(obj, 'Conexión cerrada')
	#######################################################################Items###########################################################3

	#######################################################################Items###########################################################3
	#######################################################################Items###########################################################3

