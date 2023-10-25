import tornado.autoreload
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado import web
import util
import os
import application
from tornado.options import define, options
import logging
from tornado.log import enable_pretty_logging
import MySQLdb
from datetime import datetime, timedelta
import jwt
import json

# Secret stuff in config file
import config

tornado.log.enable_pretty_logging()
logging.getLogger().setLevel(logging.DEBUG)

root = os.path.dirname(__file__)
settings = {
    "cookie_secret": config.secret_key,
}

JWT_SECRET = config.secret_key
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 999999

class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        pass
        
    def post(self):
        self.write('some post')

    def get(self):
        self.write('some get')

    def options(self, *args):
        # no body
        # `*args` is for route with `path arguments` supports
        self.set_status(204)
        self.finish()

class login(tornado.web.RequestHandler):
    def post(self, *args):
        username = self.get_argument('username')
        password = self.get_argument('password')
        database = self.get_argument('database')
        try:
            db_connection2 = MySQLdb.connect(
                host="esox3",
                user=username,
                passwd=password
            )
            db_connection2.close()
        except Exception as ex:
            logging.error(str(ex))
            self.set_status(400)
            self.write({'message': 'Wrong username password'})
            self.finish()
            return
        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
        }
        jwt_token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)
        self.write({'token': jwt_token,
                    'database': database})
        logging.info(f'Login: {username} Database: {database}')

    def get(self):
        pass

class GetVersionData(tornado.web.RequestHandler):
    def post(self):
        pass

    def get(self):
        try:
            with open('./ver.dat', 'r') as f:
                self.write(json.load(f))
                return
        except Exception as e:
            logging.error(str(e))
            self.set_status(500)
            self.write({'message': 'ver.dat not available'})


class GetAssayLoaderBinary(tornado.web.RequestHandler):
    def post(self):
        pass

    def get(self, os_name):
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
        try:
            with open(bin_file, 'rb') as f:
                logging.info("sending bin file")
                self.set_status(200)
                self.write(f.read())
        except Exception as e:
            logging.error(f"Did not send bin file, error: {str(e)}")

           
def make_app():
    return tornado.web.Application([
        (r"/getDatabase", application.GetDatabase),
        (r"/login", login),
        (r"/pingDB", application.PingDB),
        (r"/getVersionData", GetVersionData),
        (r"/getSinglePointConfig", application.GetSinglePointConfig),
        (r"/getDoseResponseConfig", application.GetDoseResponseConfig),
        (r"/getAssayTypes", application.GetAssayTypes),
        (r"/getInstruments", application.GetInstruments),
        (r"/getInstrument/(?P<sInstrument>[^\/]+)", application.GetInstrument),
        (r"/getDetectionTypes", application.GetDetectionTypes),
        (r"/getOperators", application.GetOperators),
        (r"/getProjects", application.GetProjects),
        (r"/getTargets", application.GetTargets),
        (r"/getBatchCompound/(?P<sBatchCompound>[^\/]+)", application.GetBatchCompound),
        (r"/getPlate/(?P<sPlate>[^\/]+)", application.GetPlate),
        (r"/getAssayLoaderBinary/(?P<os_name>[^\/]+)", GetAssayLoaderBinary),
        (r"/dist/(.*)", tornado.web.StaticFileHandler, {"path": "dist/"}),
        (r"/uploadBinary", application.UploadBinary),
        (r"/uploadLauncher", application.UploadLauncher),
        (r"/getAssayLoaderLauncher/Windows/(.*)", web.StaticFileHandler, {"path": "dist/launchers/Windows/"}),
        (r"/getAssayLoaderLauncher/Linux/(.*)", web.StaticFileHandler, {"path": "dist/launchers/Linux/"}),
        (r"/getAssayLoaderLauncher/Darwin/(.*)", web.StaticFileHandler, {"path": "dist/launchers/Darwin/"}),
        (r"/(.*)", web.StaticFileHandler,  {"path": "dist", "default_filename": "index.html"}),
        (r'.*', util.BaseHandler),
    ], **settings)

if __name__ == "__main__":
    app = make_app()
    app.listen(8084, max_buffer_size=200000000)
    tornado.autoreload.start()
    
    for dir, _, files in os.walk('static'):
        [tornado.autoreload.watch(dir + '/' + f) \
         for f in files if not f.startswith('.')]

    tornado.ioloop.IOLoop.current().start()
