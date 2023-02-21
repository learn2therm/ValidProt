import pandas as pd
import numpy as np
import time
import duckdb

def fetch_data(con: str, sample_size: int):

    st = time.time()

    print('Connecting to database...')
    con = duckdb.connect(con)

    et = time.time()
    elapsed_time = et - st
    print(f'Connection established! Execution time: {elapsed_time} seconds')

    print('Sampling dataset')
    validprot_str = f"""CREATE OR REPLACE TABLE validprot AS
        SELECT
            local_gap_compressed_percent_id,
            prot_pair_index,
            meso_protein_int_index,
            thermo_protein_int_index
        FROM protein_pairs
        USING SAMPLE {sample_size}"""
    
    con.execute(validprot_str)
    
    print('Generating index filter')
    get_idx_str = """SELECT meso_protein_int_index, thermo_protein_int_index FROM validprot"""
    protein_index = con.execute(get_idx_str).df()

    meso_protein_list = [i for i in protein_index['meso_protein_int_index']]
    thermo_protein_list = [i for i in protein_index['thermo_protein_int_index']]

    meso_idx_str = ', '.join(map(str, meso_protein_list))
    thermo_idx_str = ', '.join(map(str, thermo_protein_list))
    
    print('Finding relevant proteins')
    relevant_meso_str = f"""CREATE OR REPLACE TABLE relevant_meso AS 
            SELECT * FROM proteins WHERE protein_int_index IN ({meso_idx_str})"""
    relevant_thermo_str = f"""CREATE OR REPLACE TABLE relevant_thermo AS 
            SELECT * FROM proteins WHERE protein_int_index IN ({tthermo_idx_str})"""
    con.execute(relevant_meso_str)
    con.execute(relevant_thermo_str)
    
    print('Generating final dataset')
    valid_prot_df_str = """
        SELECT
            validprot.local_gap_compressed_percent_id AS percent_id,
            proteins_m.protein_seq AS meso_seq,
            proteins_t.protein_seq AS thermo_seq,
            proteins_m.protein_desc AS meso_desc,
            proteins_t.protein_desc AS thermo_desc,
        FROM validprot
        JOIN relevant_meso AS proteins_m ON (validprot.meso_protein_int_index=proteins_m.protein_int_index)
        JOIN relevant_thermo AS proteins_t ON (validprot.thermo_protein_int_index=proteins_t.protein_int_index)
    """
    valid_prot_df = con.execute(valid_prot_df_str).df()
    
    print('Cleaning up...')
    drop_tables = ['validprot', 'relevant_meso', 'relevant_thermo']
    for table in drop_tables:
        drop_str = f"""DROP TABLE {table}"""
        con.execute(drop_str)

    con.commit()
    con.close()
    print('Done.')
    
    et = time.time()
    elapsed_time = et - st
    print('Execution time:', elapsed_time, 'seconds')
    #print(valid_prot_df.head())
    return valid_prot_df, elapsed_time
