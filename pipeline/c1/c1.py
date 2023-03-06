import pandas as pd
import numpy as np

import time
import duckdb

def fetch_data(path, form = 'duckdb', size: int = 1000, sampling = 'random'):
    forms = ['csv','duckdb']
    
    if form not in forms:
        raise ValueError(f'Invalid argument passed to form. Expected one of: {forms}')
    
    if form == 'csv':
        
        if sampling == 'random':
            df = pd.read_csv(path).sample(size)
            
        
    if form == 'duckdb':
        pass
    
    return df

def get_features(data):
    return