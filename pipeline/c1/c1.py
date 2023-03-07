'''
This package imports data to be used in the ValidProt model. Current support for DuckDB objects generated
'''

import pandas as pd
import numpy as np

import time
import duckdb
import c0

def fetch_data(path, form = 'duckdb', size: int = 1000, method = 'random'):
    '''
    Pulls data from DuckDB database or pandas DataFrame for input to ValidProt model.
    
    Args:
        path (str): Path to database or DataFrame input.
        form (str): Identifies import method for either DuckDB database or DataFrame.
        size (int): Sample size to be passed to ValidProt model.
        method (str): Specifies random, chunked, or sequential sampling.
        
    Returns:
        validprot_df (pandas.DataFrame): DataFrame formatted for ValidProt model.
        
    Raises:
    '''
    forms = ['csv','duckdb']
    
    if form not in forms:
        raise ValueError(f'Invalid argument passed to form. Expected one of: {forms}')
    
    if form == 'csv':
        
        if method == 'random':
            
            validprot_df = pd.read_csv(path).sample(size)
            
        elif method == 'numeric':
            
            validprot_df = pd.read_csv(path)
        
        
        
    if form == 'duckdb':
        
        con = c0.connect_db(path)
        
        if method == 'random':
            
            sample_cmd = f"""SELECT * 
                             FROM vp_final
                             USING SAMPLE {size}"""
            validprot_df = con.execute(sample_cmd).df()
        
        
    features = []
    
    return validprot_df

