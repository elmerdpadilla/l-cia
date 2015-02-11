# -*- coding: utf-8 -*-
import pyodbc
import schedule
import time
import json
import random
import urllib2
import logging
import logging.config
import collections



###Logging
#logging.basicConfig(filename='logging.log',level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
#logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
#logging.debug('This message should go to the log file')
#logging.info('So should this')
#logging.warning('And this, too')

logging.config.fileConfig('config/logging.cfg') #logfile config

##SQL Server
dsn = 'larachdatasource'
user = 'sa'
password = 'stmn'
database = 'appLarach'



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
DB = 'dbsigua'
dbTo = 'dbsiguacoffe'
USER = 'admin'
PASS = 'Sigua2014'
PassTo = 'admin'

# log in the given database
url = "http://%s:%s/jsonrpc" % (HOST, PORT)
uid = call(url, "common", "login", DB, USER, PASS)

def search(obj, arg):
	result = call(url, "object", "execute", DB, uid, PASS, obj, 'search', args)
	return result

######################################################################
#############		Loggin in Odoo 
######################################################################



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






def Categ():

	search = [('id', '>', 0)]
	categs = call(url, "object", "execute", DB, uid, PASS, "pos.category", 'search',search)
	
	for categ in categs:
		fields = ['id', 'name', 'parent_id', 'sequence',]
		data = call(url, "object", "execute", DB, uid, PASS, "pos.category", 'read',categ, fields)
		print "##"*50		
		print data['id']
		print data
		print data['parent_id'](0)
		args = [('id', '=',  data['id'])]
		x = call(url, "object", "execute", dbTo, uid, PassTo, 'pos.category', 'search', args)
		
		#args = { 'id': data['id'], 'name': data['name'], 'parent_id' : data['parent_id'](0), 'sequence' : data['sequence'], 'image_medium':data['image_medium'] }
		
		#if x == []: # Nuevo regisro	
		#	odooId = call(url, "object", "execute", dbTo, uid, PassTo, 'pos.category', 'create', args)
		#else:		# Registro existente
		#	odooId = call(url, "object", "execute", dbTo, uid, PassTo, 'pos.category', 'write', x, args)	
		#call(url, "object", "execute", dbTo, uid, PassTo, 'pos.category', 'create', args)
		
			


def Items():

	search = [('id', '>', 0)]
	products = call(url, "object", "execute", DB, uid, PASS, "product.template", 'search',search)
	#products = collections.OrderedDict(sorted(products.items()))
	
	
			
	#cursor = cnxc.cursor()
	#cursor.execute('exec getItems')
	products = sorted(products)
	print products
	for product in products: #range(1,104): #
		#fields = ['id', 'name',]
		data = {}
		data = call(url, "object", "execute", DB, uid, PASS, "product.template", 'read',product)
		print "##"*50		
		print data['id'], '-->   ', data['name']
		
		
		#args = [('name', '=',  data['name'])]
		#x = call(url, "object", "execute", dbTo, uid, PassTo, 'product.template', 'search', args)
		#print x
		args={}
		if  data['pos_categ_id']:
			args = { 'id': data['id'], 'name': data['name'], 'image_medium' : data['image_medium'], 'list_price' : data['list_price'], 'pos_categ_id' : data['pos_categ_id'][0], }
		else:
			args = { 'id': data['id'], 'name': data['name'], 'image_medium' : data['image_medium'], 'list_price' : data['list_price'], }
			
		#if x == []: # Nuevo regisro	
		odooId = call(url, "object", "execute", dbTo, uid, PassTo, 'product.template', 'create', args)
		#else:		# Registro existente
		#	odooId = call(url, "object", "execute", dbTo, uid, PassTo, 'product.template', 'write', x, args)	
			
	
	

def SearchNewData():
	try:
		#############################################################################3##Revisar si se puede hacer una sola conección
		#cnxn = pyodbc.connect(con_string)
		#Log('Conectado al orígen', '')
		#########ProcesaVendedores(cnxn)
		#CustomerCategories(cnxn)
		#PaymentMethod(cnxn)
		###Customers(cnxn) #using the next
		#cust(cnxn)		
		#Warehouses(cnxn)
		
		###		
		#ProductCategory(cnxn)
		#ProductMaker(cnxn)
		#ProductUoMCategory(cnxn)
		#ProductUoM(cnxn)
		#Categ()
		Items()
		#PriceList(cnxn)
		#PriceListVersion(cnxn)
		#PriceListDiscounts(cnxn)

		#BarCode(cnxn)

	except pyodbc.Error as e:
    		print e
		logging.warning(e)
		Log('Error de conección', e)
	#finally:
	#	print 'cierre inesperado'




schedule.every(5).seconds.do(SearchNewData)


while True:
	schedule.run_pending()
	time.sleep(1)



