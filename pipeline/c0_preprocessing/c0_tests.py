'''
Unit testing script for ValidProt c0.
'''

import unittest

import os

import c0

def get_db_path(filename = 'validprot_testing'):
    '''
    Gets path to unit test dataset for testing functions.

    Args:
        filename (str): Name of the unit test database file. Generally should not be
        altered. validprot_testing should allow complete and efficient unit tests for
        the full learn2therm database, but is only 1.5 MB and will run through tests
        very quickly on most systems.

    Returns:
        db_path (str): Full path to unit test database file.

    Raises:
        ValueError: filename not found in current directory.
    '''

    # Get path for test dataset import
    db_path = os.path.abspath(os.path.join('.', filename))

    if os.path.exists(db_path) is False:
        raise ValueError(f'Could not find {filename} in current directory')

    return db_path



class TestConnection(unittest.TestCase):
    '''
    Tests for the connect_df function.
    '''

    def test_smoke(self):
        '''
        Smoke test to ensure connection can be made to database without error
        '''

        db_path = get_db_path()
        c0.connect_db(db_path)


    def test_not_empty(self):
        '''
        Test to make sure supplied database path is not an empty database.
        '''

        db_path = get_db_path()
        con = c0.connect_db(db_path)

        # Gets table names from database
        tables = con.execute("""SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE='BASE TABLE'""").df()

        # Make sure tables exist in database
        assert tables.shape[0] > 0


class TestBuildValidProt(unittest.TestCase):
    '''
    Tests for the validprot_build function.
    '''

    def test_smoke(self):
        '''
        Smoke test to ensure database is assembled without error.
        '''

        db_path = get_db_path()
        con = c0.connect_db(db_path)

        c0.build_validprot(con)


class TestSankey(unittest.TestCase):
    '''
    Tests for sankey_plots function.
    '''

    def test_smoke(self):
        '''
        Smoke test to ensure Sankey plots are made without error.
        '''

        db_path = get_db_path()
        con = c0.connect_db(db_path)

        min_ogt_diff = 20

        c0.sankey_plots(con, min_ogt_diff)
