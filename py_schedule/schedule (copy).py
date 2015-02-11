# -*- coding: utf-8 -*-
import pyodbc
import schedule
import time
import json
import random
import urllib2
import logging
import logging.config



###Logging
#logging.basicConfig(filename='logging.log',level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
#logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
#logging.debug('This message should go to the log file')
#logging.info('So should this')
#logging.warning('And this, too')

logging.config.fileConfig('config/logging.cfg') #logfile config

##SQL Server
dsn = 'larachdatasource'
user = 'odoosync'
password = 'ODOOadmin'
database = 'OdooSync'



def json_rpc(url, method, params):
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

def call(url, service, method, *args):
    return json_rpc(url, "call", {"service": service, "method": method, "args": args})


##Odoo
HOST = 'localhost'
PORT = '8069'
DB = 'larach'
USER = 'admin'
PASS = 'l@r@ch'
# log in the given database
url = "http://%s:%s/jsonrpc" % (HOST, PORT)
uid = call(url, "common", "login", DB, USER, PASS)

def search(obj, arg):
	result = call(url, "object", "execute", DB, uid, PASS, obj, 'search', args)
	return result

######################################################################
#############		Loggin in Odoo 
######################################################################
def Log(message, description):
	args = {'log': message, 'description': description, }
	call(url, "object", "execute", DB, uid, PASS, 'sap_integration.log', 'create', args)

# create a new idea
def newCustomer(args):
	#args = {
	#	'name' : 'fran',
	#}
	idcliente = call(url, "object", "execute", DB, uid, PASS, 'res.partner', 'create', args)
	print (idcliente)


def ProcesaVendedores(cnxn):
	print('Buscando vendedores')
	cursor = cnxn.cursor()
	cursor.execute('SELECT SlpCode, SlpName FROM OSLP with (nolock) where isnull(odoo_id,0) = 0')
	for row in cursor:
		#
		print 'Procesando el vendedor ', row.SlpName
		search
		args = {
			'name' : row.SlpName,
		}
		newCustomer(args)
		print 'fin ', row.SlpName
		
######################################################################
#############Payment Method 
######################################################################
def PaymentMethod(cnxn):
	Log('Buscando metodos de pago', '')
	cursor = cnxn.cursor()
	cursor.execute('exec getPaymentMethod ')
	rows = cursor.fetchall()
	
	for row in rows:
		#
		Log('Procesando metodo %s' % row.PymntGroup, '')
		args = [('sap_id', '=', row.GroupNum)]
		x = call(url, "object", "execute", DB, uid, PASS, 'account.payment.term', 'search', args)
		Log('Odoo Id', x)

		args = {'sap_id': row.GroupNum, 'name': row.PymntGroup, 'note': row.PymntGroup, }
		if x == []: # Nuevo regisro
			Log('Creando registro en Odoo',args)
			odooId = call(url, "object", "execute", DB, uid, PASS, 'account.payment.term', 'create', args)
			cursor.execute('update OCTG set odoo_id = %s where GroupNum = %s' % (odooId, row.GroupNum)) 
			cnxn.commit()
			Log('Registro actualizado en el orígen', '')
			
		else:		# Registro existente
			Log('Actualizando registro en Odoo',args)
			odooId = call(url, "object", "execute", DB, uid, PASS, 'account.payment.term', 'write', x, args)	
			cursor.execute('update OCTG set odoo_id = %s where GroupNum = %s' % (x[0], row.GroupNum)) 
			cnxn.commit()
			Log('Registro actualizado en el orígen', '')
			

######################################################################
#############Categorías ---> tags
######################################################################
def CustomerCategories(cnxn):
	Log('Buscando categorías de Clientes', '')
	cursor = cnxn.cursor()
	cursor.execute('exec getCustomerCategories')
	rows = cursor.fetchall()
	
	for row in rows:
		#
		Log('Procesando categoria %s' % row.GroupName, '')
		args = [('sap_id', '=', row.GroupCode)]
		x = call(url, "object", "execute", DB, uid, PASS, 'res.partner.category', 'search', args)
		Log('Odoo Id', x)

		args = {'sap_id': row.GroupCode, 'name': row.GroupName, }
		if x == []: # Nuevo regisro
			Log('Creando registro en Odoo',args)
			odooId = call(url, "object", "execute", DB, uid, PASS, 'res.partner.category', 'create', args)
			cursor.execute('update OCRG set odoo_id = %s where GroupCode = %s' % (odooId, row.GroupCode)) 
			cnxn.commit()
			Log('Registro actualizado en el orígen', '')
			
		else:		# Registro existente
			Log('Actualizando registro en Odoo',args)
			odooId = call(url, "object", "execute", DB, uid, PASS, 'res.partner.category', 'write', x, args)	
			cursor.execute('update OCRG set odoo_id = %s where GroupCode = %s' % (x[0], row.GroupCode)) 
			cnxn.commit()
			Log('Registro actualizado en el orígen', '')

######################################################################
#############Customers 
######################################################################
def Customers(cnxn):
	Log('Buscando Clientes', '')
	cursor = cnxn.cursor()
	cursor.execute('exec getCustomer')
	rows = cursor.fetchall()
	
	for row in rows:
		#
		Log('Procesando cliente %s' % row.CardCode, '')
		args = [('sap_id', '=', row.CardCode)]
		x = call(url, "object", "execute", DB, uid, PASS, 'res.partner', 'search', args)
		Log('Odoo Id', x)
		args = {'sap_id': row.CardCode, 'name': row.name, 'display_name': row.name, 'customer':row.customer, 'supplier': row.supplier, 'property_payment_term': row.property_payment_term,  'discount': float(row.Discount), 'credit_limit': float(row.credit_limit), 'category_id': [(6,0,[row.category_id])], 'property_account_position' : row.property_account_position, 'active': row.active, 'country_id': row.country, 'city':row.City}
		if x == []: # Nuevo regisro
			Log('Creando registro en Odoo',args)
			odooId = call(url, "object", "execute", DB, uid, PASS, 'res.partner', 'create', args)
			cursor.execute("update OCRD set odoo_id = %s where CardCode = '%s'" % (odooId, row.CardCode)) 
			cnxn.commit()
			Log('Registro actualizado en el orígen', '')
			
		else:		# Registro existente
			Log('Actualizando registro en Odoo',args)
			odooId = call(url, "object", "execute", DB, uid, PASS, 'res.partner', 'write', x, args)	
			cursor.execute("update OCRD set odoo_id = %s where CardCode = '%s'" % (x[0], row.CardCode)) 
			cnxn.commit()
			Log('Registro actualizado en el orígen', '')



##################################################################################################################################################################################################################


def toOdoo(toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
	
	#
	#Log('Procesando %s %s' % (toObj, current), '')
	
	x = call(url, "object", "execute", DB, uid, PASS, toObj, 'search', search)
	#Log('Odoo Id', x)
	odooId=0
	
	if x == []: # Nuevo regisro
		#Log('Creando registro en Odoo',data)
		odooId = call(url, "object", "execute", DB, uid, PASS, toObj, 'create', data)
		result ='insert'			
		cursor.execute("update %s set odoo_id = %s where %s = '%s'" % (tableOrig, odooId, keyOrig, valueKeyRef)) 
		#Log('Registro actualizado en el orígen', '')
		
	else:		# Registro existente
		#Log('Actualizando registro en Odoo',data)
		odooId = call(url, "object", "execute", DB, uid, PASS, toObj, 'write', x, data)
		result = 'update'	
		cursor.execute("update %s set odoo_id = %s where %s = '%s'" % (tableOrig, x[0], keyOrig, valueKeyRef)) 
		#Log('Registro actualizado en el orígen', '')
		odooId =x[0]
	return odooId

def Series(cnxc):
	cursor = cnxc.cursor()
	cursor.execute('exec getSeries')
	rows = cursor.fetchall()
	
	for row in rows: # FirmCode, FirmName
		search = [('name', '=', row.SeriesName)]
		data = {'name': row.SeriesName, 'active': 1, 'prefix': row.BeginStr, 'padding': 0, 'number_next_actual': row.NextNumber, 'number_increment':1, 'implementation': 'standard', }
		
		toOdoo ('ir.sequence', row.SeriesName, search, data, cursor, 'NNM1', 'SeriesName', row.SeriesName)
		cnxc.commit()



def cust(cnxc):
	cursor = cnxc.cursor()
	cursor.execute('exec getCustomer')
	rows = cursor.fetchall()
	
	for row in rows:
		search = [('sap_id', '=', row.CardCode)]
		data = {'sap_id': row.CardCode, 'name': row.name, 'display_name': row.name, 'customer':row.customer, 'supplier': row.supplier, 'property_payment_term': row.property_payment_term,  'discount': float(row.Discount), 'credit_limit': float(row.credit_limit), 'category_id': [(6,0,[row.category_id])], 'property_account_position' : row.property_account_position, 'active': row.active, 'country_id': row.country, 'city':row.City, 'property_product_pricelist': row.PriceListId }
		
		toOdoo ('res.partner', row.CardCode, search, data, cursor, 'OCRD', 'CardCode', row.CardCode)
		cnxc.commit()

def ProductMaker(cnxc):
	cursor = cnxc.cursor()
	cursor.execute('exec getFabricantes')
	rows = cursor.fetchall()
	
	for row in rows: # FirmCode, FirmName
		search = [('sap_id', '=', row.FirmCode)]
		data = {'sap_id': row.FirmCode, 'name': row.FirmName, }
		
		toOdoo ('sap_integration.product.maker', row.FirmCode, search, data, cursor, 'OMRC', 'FirmCode', row.FirmCode)
		cnxc.commit()

def ProductUoMCategory(cnxc):
	cursor = cnxc.cursor()
	cursor.execute('exec getUomCategory')
	rows = cursor.fetchall()
	
	for row in rows: # id, name
		search = [('sap_id', '=', row.id)]
		data = {'sap_id': row.id, 'name': row.name, }
		
		#toOdoo(toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
		toOdoo ('product.uom.categ', row.id, search, data, cursor, 'odoo_uomCategory', 'id', row.id)
		cnxc.commit()
	
def ProductUoM(cnxc):
	cursor = cnxc.cursor()
	cursor.execute('exec getUoM')
	rows = cursor.fetchall()
	
	for row in rows: # id, categoryId, name, factor, type, rounding
		search = [('sap_id', '=', row.id)]
		data = {'sap_id': row.id, 'name': row.name, 'category_id': row.categoryId, 'uom_type': row.type, 'factor': float(row.factor), 'roundind':float(row.rounding)}
		
		#toOdoo(toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
		toOdoo ('product.uom', row.id, search, data, cursor, 'odoo_uom', 'id', row.id)
		cnxc.commit()

def Items(cnxc):
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
		odoo_id = toOdoo ('product.template', row.ItemCode, search, data, cursor, 'OITM', 'ItemCode', row.ItemCode)
		#cnxc.commit()
		print 
		##Ahora creando el CodeBars principal
		# a.BcdEntry ,a.BcdCode, a.BcdName, a.ItemCode, c.odoo_id as ItemsId, a.UomEntry, b.PkgType, u.odoo_id as uom_cat, v.odoo_id as uom_id, v.name
		search = [('bar_code', '=', row.CodeBars)]
		data = {'sap_id': 0, 'item_id': odoo_id, 'bar_code': row.CodeBars, 'description': row.Name, 'uom_id': row.uom_id, 'item_code': row.ItemCode, }
		
		#toOdoo(toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
		toOdoo ('product.codebars', row.ItemCode, search, data, cursor, 'OBCD', 'BcdEntry', 0)
		cnxc.commit()	


def PriceList(cnxc):
	cursor = cnxc.cursor()
	cursor.execute('exec getPriceList')
	rows = cursor.fetchall()
	
	for row in rows: # ListNum, ListName, BASE_NUM, Factor
		search = [('sap_id', '=', row.ListNum)]
		
		data = {'sap_id': row.ListNum, 'name': row.ListName, 'active': 1, 'type': 'sale', 'currency_id': 45, 'based_in': row.BASE_NUM, 'factor': float(row.Factor), }
		
		#toOdoo(toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
		toOdoo ('product.pricelist', row.ListNum, search, data, cursor, 'OPLN', 'ListNum', row.ListNum)
		cnxc.commit()


def PriceListVersion(cnxc):
	cursor = cnxc.cursor()
	cursor.execute('exec getPriceListVersion')
	rows = cursor.fetchall()
	
	for row in rows: # a.sap_id, a.ItemCode name,  b.odoo_id ListNumOdoo, d.odoo_id as ItemCodeOdoo, a.Price, a.Currency, a.Factor, isnull(c.LINENUM,0) LINENUM, c.FromDate, c.ToDate
		search = [('sap_id', '=', row.sap_id)]
		
		data = {'sap_id': row.sap_id, 'name': row.name, 'pricelist_id': row.ListNumOdoo, 'product_id': row.ItemCodeOdoo, 'price': float(row.Price), 'currency_id': row.Currency, 'factor': float(row.Factor), 'line_num': row.LINENUM, 'date_start': row.FromDate, 'date_end': row.ToDate }
		
		#toOdoo(toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
		toOdoo ('product.pricelist.version', row.sap_id, search, data, cursor, 'ITM1', 'sap_id', row.sap_id)
		cnxc.commit()

def PriceListDiscounts(cnxc):
	cursor = cnxc.cursor()
	cursor.execute('exec getPriceListDiscounts')
	rows = cursor.fetchall()
	
	for row in rows: # sap_id, ListVersionOdoo, SPP2LNum, Amount, Discount
		search = [('sap_id', '=', row.sap_id)]
		
		data = {'sap_id': row.sap_id, 'pricelist_version_id': row.ListVersionOdoo, 'sequence': row.SPP2LNum, 'amount': float(row.Amount), 'discount': float(row.Discount) }
		
		#toOdoo(toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
		toOdoo ('product.pricelist.discount', row.sap_id, search, data, cursor, 'SPP2', 'sap_id', row.sap_id)
		cnxc.commit()


def BarCode(cnxc):
	cursor = cnxc.cursor()
	cursor.execute('exec getBarCode')
	rows = cursor.fetchall()
	
	for row in rows: # a.BcdEntry ,a.BcdCode, a.BcdName, a.ItemCode, c.odoo_id as ItemsId, a.UomEntry, b.PkgType, u.odoo_id as uom_cat, v.odoo_id as uom_id, v.name
		search = [('sap_id', '=', row.BcdEntry)]
		
		data = {'sap_id': row.BcdEntry, 'item_id': row.ItemsId, 'bar_code': row.BcdCode, 'description': row.BcdName, 'uom_id': row.uom_id, 'item_code': row.ItemCode, }
		
		#toOdoo(toObj, current, search, data, cursor, tableOrig, keyOrig, valueKeyRef):
		toOdoo ('product.codebars', row.BcdEntry, search, data, cursor, 'OBCD', 'BcdEntry', row.BcdEntry)
		cnxc.commit()


######################################################################
#############Warehouses
######################################################################
def Warehouses(cnxn):
	Log('Buscando Almacenes', '')
	cursor = cnxn.cursor()
	cursor.execute('exec getWarehouses')
	rows = cursor.fetchall()
	
	for row in rows:
		#
		Log('Procesando Warehouse %s' % row.WhsName, '')
		args = [('code', '=', row.WhsCode)]
		x = call(url, "object", "execute", DB, uid, PASS, 'stock.warehouse', 'search', args)
		Log('Odoo Id', x)

		args = {'code': row.WhsCode, 'name': row.WhsName, }
		if x == []: # Nuevo regisro
			Log('Creando registro en Odoo',args)
			odooId = call(url, "object", "execute", DB, uid, PASS, 'stock.warehouse', 'create', args)
			cursor.execute("update OWHS set odoo_id = %s where WhsCode = '%s'" % (odooId, row.WhsCode)) 
			cnxn.commit()
			Log('Registro actualizado en el orígen', '')
			
		else:		# Registro existente
			Log('Actualizando registro en Odoo',args)
			odooId = call(url, "object", "execute", DB, uid, PASS, 'stock.warehouse', 'write', x, args)	
			cursor.execute("update OWHS set odoo_id = %s where GroupCode = '%s'" % (x[0], row.WhsCode)) 
			cnxn.commit()
			Log('Registro actualizado en el orígen', '')

######################################################################
#############ProductCategory
######################################################################
def ProductCategory(cnxn):
	obj = 'product.category'	
	
	Log('Buscando ProductCategory', '')
	cursor = cnxn.cursor()
	cursor.execute('exec getProductCategory')
	rows = cursor.fetchall()

	for row in rows: ##ItmsGrpCod, ItmsGrpNam 
		#
		Log('Procesando ProductCategory %s' % row.ItmsGrpNam, '')
		args = [('sap_id', '=', row.ItmsGrpCod)]
		x = call(url, "object", "execute", DB, uid, PASS, obj, 'search', args)
		Log('Odoo Id', x)

		args = {'sap_id': row.ItmsGrpCod, 'name': row.ItmsGrpNam,  }
		
		if x == []: # Nuevo regisro
			Log('Creando registro en Odoo',args)
			odooId = call(url, "object", "execute", DB, uid, PASS, obj, 'create', args)
			cursor.execute("update OITB set odoo_id = %s where ItmsGrpCod = '%s'" % (odooId, row.ItmsGrpCod)) 
			cnxn.commit()
			Log('Registro actualizado en el orígen', '')
			
		else:		# Registro existente
			Log('Actualizando registro en Odoo',args)
			odooId = call(url, "object", "execute", DB, uid, PASS, obj, 'write', x, args)	
			cursor.execute("update OITB set odoo_id = %s where ItmsGrpCod = '%s'" % (x[0], row.ItmsGrpCod)) 
			cnxn.commit()
			Log('Registro actualizado en el orígen', '')







def SearchNewData():
	con_string = 'DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (dsn, user, password, database)
	Log('Conectando al orígen', '')
	

	try:
		#############################################################################3##Revisar si se puede hacer una sola conección
		cnxn = pyodbc.connect(con_string)
		Log('Conectado al orígen', '')
		Series(cnxn)
		#########ProcesaVendedores(cnxn)
		CustomerCategories(cnxn)
		PaymentMethod(cnxn)
		###Customers(cnxn) #using the next
		cust(cnxn)		
		Warehouses(cnxn)
		
		###		
		#ProductCategory(cnxn)
		#ProductMaker(cnxn)
		#ProductUoMCategory(cnxn)
		#ProductUoM(cnxn)
		Items(cnxn)
		#PriceList(cnxn)
		#PriceListVersion(cnxn)
		#PriceListDiscounts(cnxn)

		BarCode(cnxn)

	except pyodbc.Error as e:
    		print e
		logging.warning(e)
		Log('Error de conección', e)
		pass
	#finally:
	#	print 'cierre inesperado'




schedule.every(5).seconds.do(SearchNewData)


while True:
	schedule.run_pending()
	time.sleep(1)



