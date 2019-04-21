import os
import sqlite3


DB_FILE = 'storage.db'


class SqlStorage(object):

    def __init__(self, dbname=None, dbpath=None):
        self.name = dbname if dbname else DB_FILE
        if dbpath:
            self.path = os.path.join(os.getcwd(), dbpath)
        else:
            self.path = os.path.join(os.getcwd(), self.name)

        self.con = sqlite3.connect(self.path)
        self.cur = self.con.cursor()

    def terminate(self):
        self.cur.close()
        self.con.close()
