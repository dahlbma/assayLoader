import MySQLdb 
from MySQLdb import OperationalError
import config
import logging

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')


def setup_logger(name, log_file, level=logging.INFO):
    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

scarabLogger = setup_logger('scara_logger', 'scarabSqlError.txt')

class DisconnectSafeCursor(object):
    db = None
    cursor = None
    conn = None
    scarabCursor = None
    scarabConn = None
    
    def __init__(self, db, cursor):
        self.db = db
        self.cursor = cursor
        self.scarabCursor = db.scarabCur

    def close(self):
        self.cursor.close()
        self.scarabCursor.close()

    def ping(self, *args, **kwargs):
        ret = ''
        try:
            self.db.conn.ping(True)
            self.db.scarabConn.ping(True)
        except OperationalError as e:
            scarabLogger.error(f"OperationalError: {str(e)}")
            if e.args[0] == 2006:  # MySQL server has gone away
                scarabLogger.error('Server gone away')
            ret = 'error'
        return ret
            

    def execute(self, *args, **kwargs):
        try:
            if args[0].lstrip().upper().startswith('SELECT'):
                return self.cursor.execute(*args, **kwargs)
            else:
                try:
                    #self.scarabCursor.execute(*args, **kwargs)
                    pass
                except Exception as e:
                    if '_test' in args[0]:
                        pass
                    else:
                        scarabLogger.error(str(e))
                        scarabLogger.error(args)
                return self.cursor.execute(*args, **kwargs)
        except MySQLdb.OperationalError:
            ## How can we reconnect in a safe way?
            #self.db.reconnect()
            #self.cursor = self.db.cursor()
            pass
            return self.cursor.execute(*args, **kwargs)
    
        
    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def description(self):
        return self.cursor.description


class DisconnectSafeConnection(object):
    connect_args = None
    connect_kwargs = None
    conn = None
    cur = None
    
    scarabConn = None
    scarabCur = None
    
    def __init__(self, *args, **kwargs):
        self.connect_args = args
        self.connect_kwargs = kwargs
        self.reconnect()

    def reconnect(self):
        self.conn = MySQLdb.connect(
            host=config.database['host'],
            user=config.database['user'],
            passwd=config.database['password'],
            database=config.database['db'],
            charset='utf8mb4',  # Use utf8mb4 charset
            use_unicode=True    # Use Unicode
        )
        self.conn.autocommit(True)


        self.scarabConn = MySQLdb.connect(
            host=config.scarabDatabase['host'],
            user=config.scarabDatabase['user'],
            passwd=config.scarabDatabase['password'],
            database=config.scarabDatabase['db'],
            charset='utf8mb4',  # Use utf8mb4 charset
            use_unicode=True    # Use Unicode

        )
        self.scarabConn.autocommit(True)
        self.scarabConn.query('SET GLOBAL connect_timeout=28800')
        self.scarabConn.query('SET GLOBAL interactive_timeout=28800')
        self.scarabConn.query('SET GLOBAL wait_timeout=28800')

        
  
    def cursor(self, *args, **kwargs):
        self.cur = self.conn.cursor(*args, **kwargs)
        self.scarabCur = self.scarabConn.cursor(*args, **kwargs)
        return DisconnectSafeCursor(self, self.cur)

    def commit(self):
        self.scarabConn.commit()
        self.conn.commit()

    def rollback(self):
        self.scarabConn.rollback()
        self.conn.rollback()

disconnectSafeConnect = DisconnectSafeConnection
