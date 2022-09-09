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
NR_OF_VIALS_IN_BOX = 200

def res2json():
    result = [list(i) for i in cur.fetchall()]
    return json.dumps(result)


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
		"db_col": "well"
	},
	"rawIntensity": {
		"upload": false,
		"db_col": ""
	},
	"screen_id": {
		"upload": false,
		"db_col": ""
	},
	"Plate": {
		"upload": true,
		"db_col": "plate_id"
	},
	"ProductName": {
		"upload": true,
		"db_col": "batch_id"
	},
	"Concentration": {
		"upload": true,
		"db_col": "concentration"
	},
	"DCol": {
		"upload": false,
		"db_col": ""
	},
	"Column": {
		"upload": false,
		"db_col": ""
	},
	"DRow": {
		"upload": false,
		"db_col": ""
	},
	"Row": {
		"upload": false,
		"db_col": ""
	},
	"readout": {
		"upload": false,
		"db_col": ""
	},
	"Content": {
		"upload": false,
		"db_col": ""
	},
	"inhibition_percent": {
		"upload": true,
		"db_col": "inhibition"
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
        sSql = f'select distinct(project) project from {assayDB}.lcb_sp'
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
        sSql = f'select distinct(operator) detection_type from {assayDB}.lcb_sp'
        cur.execute(sSql)
        res = res2json()
        self.finish(res)


def res_to_json(response, cursor):
    columns = cursor.description()
    to_js = [{columns[index][0]:column for index,
              column in enumerate(value)} for value in response]
    return to_js


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
