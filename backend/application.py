import tornado.gen
from tornado.escape import json_decode, json_encode
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
        sSql = f'''select project_name project from hive.project_details
                   where terminated_date is null'''
        cur.execute(sSql)
        res = res2json()
        self.finish(res)


@jwtauth
class GetTargets(tornado.web.RequestHandler):
    def get(self):
        sSql = f'select target_id from hive.target_details order by target_id'
        cur.execute(sSql)
        res = res2json()
        self.finish(res)


@jwtauth
class GetAssayTypes(tornado.web.RequestHandler):
    def get(self):
        sSql = f'select distinct(assay_type) assay_type from assay.lcb_sp'
        cur.execute(sSql)
        res = res2json()
        self.finish(res)


@jwtauth
class GetDetectionTypes(tornado.web.RequestHandler):
    def get(self):
        sSql = f'select distinct(detection_type) detection_type from assay.lcb_sp'
        cur.execute(sSql)
        res = res2json()
        self.finish(res)


@jwtauth
class GetOperators(tornado.web.RequestHandler):
    def get(self):
        sSql = f'''select userid from hive.user_details where organization = 'screen' '''
        cur.execute(sSql)
        res = res2json()
        self.finish(res)

"""
@jwtauth
class GetPlate(tornado.web.RequestHandler):
    def get(self, sPlate):
        sSql = f'''select p.plate_id PLATE,
        c.well WELL,
        IF(c.notebook_ref='CTRL', 'POS', c.notebook_ref) DRUG_NAME,
        c.CONC CONCENTRATION, volume
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
"""

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


def implSaveSpRowToDb(self, row, targetTable):
    return 1, 2
    def nullifyNumeric(sString):
        if sString == '':
            return 'NULL'
        else:
            return sString
        
    assayDB = getDatabase(self)
    arg_dict = {}
    file_dict = {}
    try:
        tornado.httputil.parse_body_arguments(self.request.headers["Content-Type"],
                                              self.request.body,
                                              arg_dict,
                                              file_dict)
    except:
        self.set_status(400)
        self.finish('Decode failed')
        return

    sCompound = arg_dict['compound_id'][0].decode('utf-8')
    sBatch = arg_dict['batch_id'][0].decode('utf-8')
    sTarget = arg_dict['target'][0].decode('utf-8')
    sProject = arg_dict['project'][0].decode('utf-8')
    sPlate = arg_dict['plate'][0].decode('utf-8')
    sWell = arg_dict['well'][0].decode('utf-8')
    sAssay_type = arg_dict['assay_type'][0].decode('utf-8')
    sDetection_type = arg_dict['detection_type'][0].decode('utf-8')
    sConcentration = nullifyNumeric(arg_dict['concentration'][0].decode('utf-8'))
    sInhibition = nullifyNumeric(arg_dict['inhibition'][0].decode('utf-8'))
    sActivation = nullifyNumeric(arg_dict['activation'][0].decode('utf-8'))
    sHit = arg_dict['hit'][0].decode('utf-8')
    sHit_threshold = nullifyNumeric(arg_dict['hit_threshold'][0].decode('utf-8'))
    sExperiment_date = arg_dict['experiment_date'][0].decode('utf-8')
    sOperator = arg_dict['operator'][0].decode('utf-8')
    sEln = arg_dict['eln'][0].decode('utf-8')
    sComment = arg_dict['comment'][0].decode('utf-8')
        
    #sSql = f'''insert into {assayDB}.lcb_sp
    # Replace the next with the line above when we go live
    sSql = f'''insert into assay_test.lcb_sp
    (compound_id,
    compound_batch,
    project,
    target,
    PLATE_ID,
    WELL_ID,
    assay_type,
    detection_type,
    INHIBITION,
    ACTIVATION,
    HIT,
    HIT_THRESHOLD,
    CONC,
    TDATE,
    operator,
    eln_id,
    COMMENTS,
    CREATED_DATE)
    values (
    '{sCompound}',
    '{sBatch}',
    '{sProject}',
    '{sTarget}',
    '{sPlate}',
    '{sWell}',
    '{sAssay_type}',
    '{sDetection_type}',
    {sInhibition},
    {sActivation},
    '{sHit}',
    {sHit_threshold},
    {sConcentration},
    '{sExperiment_date}',
    '{sOperator}',
    '{sEln}',
    '{sComment}',
    now())
    '''

    try:
        #cur.execute(sSql)
        pass
    except Exception as e:
        sError = f"{str(e)}"
        logging.error(sError)
        self.set_status(400)
        self.finish(sError)


@jwtauth
class SaveSpRowToDb(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        data = json.loads(self.request.body)
        saRows = data.get('rows')
        logging.info(f"Type of saRows: {type(saRows[0])}")
        return
        saRows = ast.literal_eval(saRows)

        targetTable = data.get("targetTable")
        logging.info(targetTable)

        saError = []
        for row in saRows:
            logging.info(f'Error {row[0]}')
            status, sMessage = implUploadWellInformation(self, row, targetTable)
            if status != 200:
                saError.append(row)
                
        self.set_header("Content-Type", "application/json")
        if len(saError) != 0:
            self.set_status(400)
        if len(saError) > 0:
            logging.info(f'Error {saError}')
            
        self.finish(json.dumps(saError))

        
    def get(self):
        pass


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
            bin_file = f'dist/{os_name}/al.exe'
        elif os_name == 'Linux':
            bin_file = f'dist/{os_name}/al'
        elif os_name == 'Darwin':
            bin_file = f'dist/{os_name}/al'
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
        sSql = f'select instrument_name from assayloader.instrument order by pkey asc'
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


@jwtauth
class PrintPlateLabel(tornado.web.RequestHandler):
    def get(self, sPlate):
        sPlate = sPlate.upper()
        s = f'''
^XA
^MMT
^PW400
^LL0064
^LS0
^BY2,3,43^FT47,48^BCN,,Y,N
^FD>:P>{sPlate}^FS
^FT277,48^A0N,22,25^FH\^FD^FS
^PQ1,0,1,Y^XZ
'''
        f = open('/tmp/file.txt','w')
        f.write(s)
        f.close()
        os.system("lp -h homer.scilifelab.se:631 -d CBCS-GK420t_plates  /tmp/file.txt")


@jwtauth
class GetPlate(tornado.web.RequestHandler):
    def get(self, sPlate):
        # Platt ID	Well	Compound ID	Batch nr	Form	Conc (mM)	volume


        sSql = f'''select
        config_id plate,
        well,
        compound_id,
        notebook_ref batch_id,
        conc,
        volume
        from cool.config where config_id = '{sPlate}'
        '''
        cur.execute(sSql)
        res = res2json()
        
        if len(res) > 4:
            try:
                self.finish(res)
            except Exception as e:
                print(str(e))
        else:
            sError = f"Plate not found {sPlate}"
            logging.error(sError)
            self.set_status(400)
            self.finish(sError)
