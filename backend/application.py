import tornado.gen
import json
import logging
import ast
import datetime
import time
import os, random, string
import re
import util
import codecs
from auth import jwtauth
from rdkit import Chem
from rdkit.Chem import Draw
import mydb
import config
import pandas as pd
from os.path import exists

db = mydb.disconnectSafeConnect()
cur = db.cursor()

def res2json():
    result = [list(i) for i in cur.fetchall()]
    return json.dumps(result)

def res_to_json(response, cursor):
    columns = cursor.description()
    to_js = [{columns[index][0]:column for index, column in enumerate(value)} for value in response]
    return to_js

def getDatabase(parent):
    data = parent.request.headers['Token']
    jsonData = json.loads(data)
    database = jsonData['database']
    if database == 'Live':
        return 'assay'
    else:
        return 'assay_test'


class GetDatabase(tornado.web.RequestHandler):
    def get(self):
        sRes = json.dumps([['Live'], ['Test']])
        self.finish(sRes)


@jwtauth
class GetSinglePointConfig(tornado.web.RequestHandler):
    def get(self):
        sJson = '''{
	"DWell": {
	    "upload": true,
	    "db_col": "well",
        "verify_id": false
	},
	"rawIntensity": {
		"upload": false,
		"db_col": "",
        "verify_id": false
	},
	"screen_id": {
		"upload": false,
		"db_col": "",
        "verify_id": false
	},
	"Plate": {
		"upload": true,
		"db_col": "plate_id",
        "verify_id": false
	},
	"ProductName": {
		"upload": true,
		"db_col": "compound_batch",
        "verify_id": true,
        "verify_name": "batch"
	},
	"Concentration": {
		"upload": true,
		"db_col": "concentration",
        "verify_id": false
	},
	"DCol": {
		"upload": false,
		"db_col": "",
        "verify_id": false
	},
	"Column": {
		"upload": false,
		"db_col": "",
        "verify_id": false
	},
	"DRow": {
		"upload": false,
		"db_col": "",
        "verify_id": false
	},
	"Row": {
		"upload": false,
		"db_col": "",
        "verify_id": false
	},
	"readout": {
		"upload": false,
		"db_col": "",
        "verify_id": false
	},
	"Content": {
		"upload": false,
		"db_col": "",
        "verify_id": false
	},
	"inhibition_percent": {
		"upload": true,
		"db_col": "inhibition",
        "verify_id": false
	}
}
        '''
        self.finish(sJson)


@jwtauth
class GetDoseResponseConfig(tornado.web.RequestHandler):
    def get(self):
        sRes = json.dumps([['Live'], ['Test']])
        self.finish(sRes)


@jwtauth
class GetProjects(tornado.web.RequestHandler):
    def get(self):
        assayDB = getDatabase(self)
        sSql = f'select project_name project from hive.project_details where terminated_date is null'
        cur.execute(sSql)
        res = res2json()
        self.finish(res)


@jwtauth
class GetTargets(tornado.web.RequestHandler):
    def get(self):
        assayDB = getDatabase(self)
        sSql = f'select distinct(target) target from {assayDB}.lcb_sp'
        cur.execute(sSql)
        res = res2json()
        self.finish(res)


@jwtauth
class GetAssayTypes(tornado.web.RequestHandler):
    def get(self):
        assayDB = getDatabase(self)
        sSql = f'select distinct(assay_type) assay_type from {assayDB}.lcb_sp'
        cur.execute(sSql)
        res = res2json()
        self.finish(res)


@jwtauth
class GetDetectionTypes(tornado.web.RequestHandler):
    def get(self):
        assayDB = getDatabase(self)
        sSql = f'select distinct(detection_type) detection_type from {assayDB}.lcb_sp'
        cur.execute(sSql)
        res = res2json()
        self.finish(res)


@jwtauth
class GetOperators(tornado.web.RequestHandler):
    def get(self):
        assayDB = getDatabase(self)
        sSql = f'''select userid from hive.user_details where organization = 'screen' '''
        cur.execute(sSql)
        res = res2json()
        self.finish(res)


@jwtauth
class GetPlate(tornado.web.RequestHandler):
    def get(self, sPlate):
        sSql = f'''select p.plate_id PLATE,
        c.well WELL,
        IF(c.notebook_ref='CTRL', 'POS', c.notebook_ref) DRUG_NAME,
        c.CONC CONCENTRATION
        from cool.config c, cool.plate p
        where p.plate_id = '{sPlate}' and p.config_id = c.config_id
        '''
        cur.execute(sSql)
        tRes = cur.fetchall()
        if len(tRes) > 0:
            try:
                self.finish(json.dumps(res_to_json(tRes, cur), indent=4))
            except Exception as e:
                print(str(e))
        else:
            sError = f"Plate not found {sPlate}"
            logging.error(sError)
            self.set_status(400)
            self.finish(sError)


@jwtauth
class GetBatchCompound(tornado.web.RequestHandler):
    def get(self, sBatchCompound):
        if sBatchCompound == 'batch':
            #sSql = f'select notebook_ref detection_type from bcpvs.batch'
            sSql = f'select notebook_ref from bcpvs.batch'
        elif sBatchCompound == 'compound':
            sSql = f'select compound_id from bcpvs.compound'
        else:
            self.finish()
            return

        cur.execute(sSql)
        res = res2json()
        self.finish(res)


class PingDB(tornado.web.RequestHandler):
    def get(self):
        sSql = "SELECT * FROM glass.box_sequence"
        cur.execute(sSql)
        
    def head(self):
        sSql = "SELECT * FROM glass.box_sequence"
        cur.execute(sSql)
        res = cur.fetchall()
        self.finish()
        

@jwtauth
class UploadBinary(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        os_name = self.get_argument("os_name")

        try:
            # self.request.files['file'][0]:
            # {'body': 'Label Automator ___', 'content_type': u'text/plain', 'filename': u'k.txt'}
            file1 = self.request.files['file'][0]
        except:
            logging.error("Error cant find file1 in the argument list")
            return

        bin_file = ""
        if os_name == 'Windows':
            bin_file = f'dist/{os_name}/ce.exe'
        elif os_name == 'Linux':
            bin_file = f'dist/{os_name}/ce'
        elif os_name == 'Darwin':
            bin_file = f'dist/{os_name}/ce'
        else:
            # unsupported OS
            self.set_status(500)
            self.write({'message': 'OS not supported'})
            return
        
        output_file = open(bin_file, 'wb')
        output_file.write(file1['body'])
        output_file.close()


@jwtauth
class UploadLauncher(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        os_name = self.get_argument("os_name")

        try:
            # self.request.files['file'][0]:
            # {'body': 'Label Automator ___', 'content_type': u'text/plain', 'filename': u'k.txt'}
            file1 = self.request.files['file'][0]
        except:
            logging.error("Error cant find file1 in the argument list")
            return

        bin_file = ""
        if os_name == 'Windows':
            bin_file = f'dist/launchers/{os_name}/assayLoader.exe'
        elif os_name == 'Linux':
            bin_file = f'dist/launchers/{os_name}/assayLoader'
        elif os_name == 'Darwin':
            bin_file = f'dist/launchers/{os_name}/assayLoader'
        else:
            # unsupported OS
            self.set_status(500)
            self.write({'message': 'OS not supported'})
            return
        
        output_file = open(bin_file, 'wb')
        output_file.write(file1['body'])
        output_file.close()


@jwtauth
class GetInstruments(tornado.web.RequestHandler):
    def get(self):
        sSql = f'select instrument_name from assayloader.instrument'
        cur.execute(sSql)
        res = res2json()
        self.finish(res)

@jwtauth
class GetInstrument(tornado.web.RequestHandler):
    def get(self, sInstrument):
        sSql = f'''select pre_data,
        post_data,
        well_col,
        plate_col,
        data_col from assayloader.instrument
        where instrument_name = '{sInstrument}' '''
        cur.execute(sSql)
        tRes = cur.fetchall()
        res = res_to_json(tRes, cur)

        
        self.finish(json.dumps(res))
