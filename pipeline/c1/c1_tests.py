import pandas as pd
import numpy as np
import time

import unittest
import duckdb

import os
import sys

import c0
import c1

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

