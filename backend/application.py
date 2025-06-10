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
'''
logging.basicConfig(level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(), 
                              logging.FileHandler('app.log', encoding='utf-8')])
'''

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


class FaviconHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_status(204)  # No Content


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
class GetDrProjects(tornado.web.RequestHandler):
    def get(self, sTable):
        sSql = f'''select distinct(project) project from {sTable} order by project'''

        cur.execute(sSql)
        res = res2json()
        #response = cur.fetchall()
        #res = res_to_json(response, cur)
        self.finish(res)

        
@jwtauth
class GetTargets(tornado.web.RequestHandler):
    def get(self):
        sSql = f'''select target_id from hive.target_details
        where hive.target_details.terminated is null
        order by target_id'''
        cur.execute(sSql)
        res = res2json()
        self.finish(res)


@jwtauth
class GetAssayTypes(tornado.web.RequestHandler):
    def get(self):
        sSql = f'select distinct(assay_type) assay_type from assay.lcb_sp'
        sSql = f'select distinct(%s) assay_type from assay.lcb_sp'
        cur.execute(sSql, assay_type)
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


@jwtauth
class GetDrData(tornado.web.RequestHandler):
    def get(self, sProject, sTable):
        sSql = f'''select compound_id, compound_batch, target, graph
        from {sTable}
        where project = %s '''
        
        cur.execute(sSql, (sProject, ))

        response = cur.fetchall()
        res = res_to_json(response, cur)
        self.finish(json.dumps(res))
        
        #res = res2json()
        #self.finish(res)

    
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
        ret = cur.ping(sSql)
        if ret == 'error':
            self.set_status(400)

    def head(self):
        sSql = "SELECT * FROM glass.box_sequence"
        ret = cur.ping(sSql)
        if ret == 'error':
            self.set_status(400)


def implSaveDrRowToDb(self, row, targetTable):

    def nullifyNumeric(sString):
        if sString == '':
            return None
        else:
            return sString
        
    assayDB = getDatabase(self)

    try:
        sCompound = row['compound_id']
        sBatch = row['batch_id']
        sTarget = row['target']
        sModelSystem = row['model_system']
        sProject = row['project']
        sAssay_type = row['assay_type']
        sDetection_type = row['detection_type']
        sViability_measurement = row['viability_measurement']
        sCmax = row['Cmax']
        sYmax = nullifyNumeric(row['Y Max'])
        sMmin = nullifyNumeric(row['M Min'])
        sHill = row['Hill']
        sIC50 = nullifyNumeric(row['IC50'])
        sEC50 = nullifyNumeric(row['EC50'])
        sICmax = nullifyNumeric(row['I Cmax'])
        sECmax = nullifyNumeric(row['E Cmax'])
        sGraph = row['Graph']
        sExperiment_date = row['experiment_date']
        sOperator = row['operator']
        sEln = row['eln']
        sComment = row['comment']
        sConfirmed = row['Confirmed']
    except Exception as e:
        logging.error(str(e))
        logging.error(row)
        sStatus = 400
        return sStatus, 'Can not parse input'

    if targetTable == "assay_test.lcb_dr":
        tTable = targetTable
    else:
        logging.info("Wrong DR table")
        #tTable = f'{assayDB}.{targetTable}'
        pass

    sSql = f'''insert into {tTable}
    (compound_id,
    compound_batch,
    project,
    target,
    model_system,
    assay_type,
    detection_type,
    viability_measurement,
    CMAX,
    Y_MAX,
    M_MIN,
    Hill,
    IC50,
    EC50,
    I_CMAX,
    E_CMAX,
    GRAPH,
    TDATE,
    operator,
    eln_id,
    COMMENTS,
    CONFIRMED,
    CREATED_DATE)
    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
    '''

    sError = ''
    sStatus = 200
    
    try:
        sSql = sSql.encode('utf-8', 'replace').decode('utf-8')
        cur.execute(sSql, (sCompound, sBatch,
                           sProject, sTarget,
                           sModelSystem, sAssay_type,
                           sDetection_type, sViability_measurement,
                           sCmax, sYmax, sMmin, sHill, sIC50, sEC50, sICmax, sECmax, sGraph, 
                           sExperiment_date, sOperator, sEln, sComment, sConfirmed))
    except Exception as e:
        sError = f"{str(e).encode('utf-8', 'replace').decode('utf-8')}"
        logging.error(sError)
        self.set_status(400)
        sStatus = 400
    return sStatus, sError


@jwtauth
class SaveDrRowToDb(tornado.web.RequestHandler):
    
    def post(self, *args, **kwargs):
        data = json.loads(self.request.body)
        saRows = data.get('rows')
        targetTable = data.get("targetTable")
        if targetTable == 'DR Sandbox table':
            targetTable = 'assay_test.lcb_dr'
        elif targetTable == 'Primary screen':
            targetTable = 'assay_test.lcb_dr'
        else:
            self.set_status(400)
            self.finish()
            return

        saError = []
        iRowIndex = 0
        for row in saRows:
            status, sMessage = implSaveDrRowToDb(self, row, targetTable)
            if status != 200:
                saError.append(row)
            iRowIndex += 1
                
        self.set_header("Content-Type", "application/json")
        if len(saError) != 0:
            self.set_status(400)
        if len(saError) > 0:
            logging.info(f'Error {saError}')
            
        self.finish(json.dumps(saError))

        
def implSaveSpRowToDb(self, row, targetTable):

    def nullifyNumeric(sString):
        if sString == '':
            return None
        else:
            return sString
        
    assayDB = getDatabase(self)

    sCompound = row['compound_id']
    sBatch = row['batch_id']
    sTarget = row['target']
    sModelSystem = row['model_system']
    sProject = row['project']
    sPlate = row['plate']
    sWell = row['well']
    sAssay_type = row['assay_type']
    sDetection_type = row['detection_type']
    sSiability_measurement = row['viability_measurement']
    sConcentration = nullifyNumeric(row['concentration'])
    sInhibition = nullifyNumeric(row['inhibition'])
    sActivation = nullifyNumeric(row['activation'])
    sHit = row['hit']
    sHit_threshold = nullifyNumeric(row['hit_threshold'])
    sExperiment_date = row['experiment_date']
    sOperator = row['operator']
    sEln = row['eln']
    sComment = row['comment']
        
    #sSql = f'''insert into {assayDB}.lcb_sp
    # Replace the next with the line above when we go live

    if targetTable == "assay_test.lcb_sp":
        tTable = targetTable
    else:
        tTable = f'{assayDB}.{targetTable}'

    sSql = f'''insert into {tTable}
    (compound_id,
    compound_batch,
    project,
    target,
    model_system,
    PLATE_ID,
    WELL_ID,
    assay_type,
    detection_type,
    viability_measurement,
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
    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
    '''

    sError = ''
    sStatus = 200
    
    try:
        sSql = sSql.encode('utf-8', 'replace').decode('utf-8')
        cur.execute(sSql, (sCompound, sBatch, sProject, sTarget, sModelSystem, sPlate,  sWell, sAssay_type, sDetection_type, sSiability_measurement, sInhibition, sActivation, sHit, sHit_threshold, sConcentration, sExperiment_date, sOperator, sEln, sComment,))
    except Exception as e:
        sError = f"{str(e).encode('utf-8', 'replace').decode('utf-8')}"
        logging.error(sError)
        self.set_status(400)
        sStatus = 400
    return sStatus, sError


@jwtauth
class SaveSpRowToDb(tornado.web.RequestHandler):
    
    def post(self, *args, **kwargs):
        data = json.loads(self.request.body)
        saRows = data.get('rows')
        targetTable = data.get("targetTable")

        if targetTable == 'Sandbox table':
            targetTable = 'assay_test.lcb_sp'
        elif targetTable == 'Primary screen':
            targetTable = 'lcb_sp'
        elif targetTable == 'Confirmation screen':
            targetTable = 'lcb_sp_confirming'
        elif targetTable == 'Counter screen':
            targetTable = 'lcb_sp_counter'
        else:
            self.set_status(400)
            self.finish()
            return
            
        saError = []
        iRowIndex = 0
        for row in saRows:
            status, sMessage = implSaveSpRowToDb(self, row, targetTable)
            if status != 200:
                saError.append(row)
            iRowIndex += 1
                
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
        where instrument_name = %s '''

        cur.execute(sSql, (sInstrument, ))
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
        from cool.config where config_id = %s
        '''
        
        cur.execute(sSql, (sPlate, ))
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
