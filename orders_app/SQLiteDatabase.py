#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#-------------------------------------------------------------------------------
# Name:         SQLiteDatabase.py
# Purpose:      A class module to handle the database connections to a SQLite
#               database. It caters for selection queries and insert/update
#               queries. The class itself is independant of any specific
#               database, but the test code in main() would need to be changed
#               for specific tests.
# Author:       Bill
# Created:      30/06/2019
# Amended:      31/08/2020 - Add a setter/getter for a 'values' tuple.
#                            Amend the Update method to take a parameterised
#                            query and a tuple of values.
#               09/10/2020 - Amend the select method to use a parameterised
#                            query as well.
#               16/05/2022 - Add new methods to return schema information for
#                            the selected database.
#               15/07/2022 - Add a new method to return the database data as a
#                            pandas dataframe, rather than as a list of lists.
#               16/07/2022 - Include a parameter substitution option in the
#                            new pandas dataframe method.
#               30/08/2022 - Add new method to return the database data as a
#                            JSON formatted dictionary.
#
# *** NOTE ***
# In order for this module to be availabe in any project (without needing to
# copy it) the main version is located in the N:/Utilities folder. Also
# need to set the environment variable PYTHONPATH to the path to the folder.
#
# The version in the N:/Net_Root/PythonCode/Database Test/ folder is the
# "working" version to be used for future amendments only.
#
# ------------------
# - Flask Websites -
# ------------------
# If the site is to be be deployed on a remote server, it will not be able to
# access the local copy (from PYTHONPATH), and so a copy of the module must be
# placed in the Flask "app" folder, as part of the site's package structure.
#
# THIS VERSION WILL NOT REQUIRE PANDAS OR JSON.
# The imports and methods will be changed accordingly, from the base version.
#
#-------------------------------------------------------------------------------

import os
import sqlite3

#-------------------------------------------------------------------------------

class SQLClass:
    """ A class to encapsulate connections to a SQLite database, it will allow
    the database to be queried, and will return the result set for display.
    """

    def __init__(self):
        """ Instantiate an SQLiteClass object, and perform any initialisation
        required. """

        self.__query = ''       # Input Property
        self.__values = ()      #   "      "
        self.__db = ''          #   "      "
        self.__results = ''     # Output property

#-------------------------------------------------------------------------------
# Public Setter and Getter methods for all the input and output values.
# NB - both required if properties are write or read/write. But only the
#      getter required if the property is read-only.
#-------------------------------------------------------------------------------

    @property
    def query(self):
        return self.__query

    @query.setter
    def query(self, value):
        self.__query = value

    @property
    def values(self):
        return self.__values

    @values.setter
    def values(self, value):
        self.__values = value

    @property
    def db(self):
        return self.__db

    @db.setter
    def db(self, value):
        self.__db = value

    @property
    def results(self):
        return self.__results

#-------------------------------------------------------------------------------
# PUBLIC CLASS METHODS
#-------------------------------------------------------------------------------

    def GetSQLData(self):
        """ Using the properties passed in to the class, connect to the
        appropriate database and return the requested dataset. """

        retDataset = self.__GetSQLiteData()
        return retDataset

#-------------------------------------------------------------------------------

    def UpdateSQLData(self):
        """ Update the database. """

        return self.__UpdateSQLiteData()

#-------------------------------------------------------------------------------

    def getTables(self):
        """ Return a list of tables from the requested database. """

        query = "Select tbl_name From sqlite_master Where type = ? "
        query += "Order By tbl_name;"
        self.query = query
        self.values = ('table',)
        return self.__GetSQLiteData()

#-------------------------------------------------------------------------------

    def getViews(self):
        """ Return a list of views from the requested database. """

        query = "Select tbl_name From sqlite_master Where type = ? "
        query += "Order By tbl_name;"
        self.query = query
        self.values = ('view',)
        return self.__GetSQLiteData()

#-------------------------------------------------------------------------------

    def getColumnList(self, table):
        """ Return a list of the column names for the requested table. The data
            types will be needed as well, to decide which values should be
            enclosed in quotes and which not. """

        self.query = f'pragma table_info({table});'
        self.values = tuple()
        return self.__GetSQLiteData()

#-------------------------------------------------------------------------------

    def getViewDefinition(self, view):
        """ Get the SQL definition of the requested database view. """

        query = "Select sql From sqlite_master Where type = ? And tbl_name = ?;"
        self.query = query
        self.values = ('view',view)
        return self.__GetSQLiteData()

#-------------------------------------------------------------------------------

    def getTableDefinition(self, table):
        """ Get the SQL definition of the requested database table. """

        query = "Select sql From sqlite_master Where type = ? And tbl_name = ?;"
        self.query = query
        self.values = ('table',table)
        return self.__GetSQLiteData()

#-------------------------------------------------------------------------------

    def getTableData(self, table, recs=0):
        """ Get the data from the requested table. If recs is greater than zero,
            return that number of records only. """

        query = "Select * From " + table
        if recs > 0: query += " Limit " + str(recs) + ";"
        else: query += ";"
        self.query = query
        self.values = ()
        return self.__GetSQLiteData()

#-------------------------------------------------------------------------------
# PRIVATE CLASS METHODS
#-------------------------------------------------------------------------------

    def __str__(self):
        """ Print brief details of what this class does.
        Usage : sql = SQLiteDatabase.SQLClass()
                print(sql)
        """

        desc = 'Class to execute an SQL query against a SQLite database'
        return desc

#-------------------------------------------------------------------------------

    def __repr__(self):
        """ Print brief details of what this class does.
        Usage : sql = SQLiteDatabase.SQLClass()
                print(repr(sql))
        """

        desc = 'SQLClass()'
        return desc

#-------------------------------------------------------------------------------

    def __GetSQLiteData(self):
        """ Retrieve the requested data from the SQLite database file. Return
            either the requested dataset or the generated error message. The
            query is parameterised (i.e. actual values replaced by question
            marks), with the values passed in a separate tuple, 'values'   """

        try:
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            cursor.execute(self.query, self.values)
            return self.__FormatOutput(cursor)
        except Exception as err:
            return '**ERROR**\n__GetSQLiteData : ' + str(err)
        finally:
            try:
                cursor.close()
                del cursor
                conn.close()
            except:
                pass

#-------------------------------------------------------------------------------

    def __UpdateSQLiteData(self):
        """ Update the SQLite database. Return either the count of recods
            updated for success, or the generated error message. The query is
            parameterised (i.e. actual values replaced by question marks), with
            the values passed in a separate tuple, 'values' """

        try:
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            cursor.execute(self.query, self.values)
            conn.commit()
            return cursor.lastrowid
        except Exception as err:
            return '**ERROR**\n__GetSQLiteData : ' + str(err)
        finally:
            try:
                cursor.close()
                del cursor
                conn.close()
            except:
                pass

#-------------------------------------------------------------------------------

    def __FormatOutput(self, cursor):
        """ Format the cursor data. Return the data as a list of records, each
            record consisting of a list of column values (as strings). The
            first list will contain the column names. For example,
            [[col. names],[record 1],[record 2],[record 3]]...  """

        # Store the column names from the cursor
        colnames = list(zip(*cursor.description))[0]

        # Get the recordset from the cursor and insert the column names
        # as the first entry in the list. The individual records need to be
        # lists so that they can be amended in the calling program if required.
        ret = [list(colnames)]
        for row in cursor.fetchall():
            record = []
            for idx in range(len(colnames)):
                record.append(str(row[idx]))
            ret.append(record)
        return ret

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
