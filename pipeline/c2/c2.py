import pandas as pd
import numpy as np

import time
import duckdb

def validprot_sample(df, stat_samp = None, size):
    
    if stat_samp == None:
        
        sample_df = df.sample(size)
        return sample_df
   
    if stat_samp = representative:
        
        sample_df = df.sample(size)
    
    sample_df = pd.DataFrame()
    
    return sample_df

def explain_set(df, exclude):
    return