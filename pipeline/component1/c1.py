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
    con.execute(f"""CREATE OR REPLACE TABLE validprot AS
        SELECT
            local_gap_compressed_percent_id,
            prot_pair_index,
            meso_protein_int_index,
            thermo_protein_int_index
        FROM protein_pairs
        USING SAMPLE {sample_size}""")
    print('Generating index filter')

    protein_index = con.execute("""SELECT meso_protein_int_index, thermo_protein_int_index FROM validprot""").df()

    meso_protein_list = [i for i in protein_index['meso_protein_int_index']]
    thermo_protein_list = [i for i in protein_index['thermo_protein_int_index']]

    m = ', '.join(map(str, meso_protein_list))
    t = ', '.join(map(str, thermo_protein_list))
    
    print('Finding relevant proteins')
    con.execute(f"""CREATE OR REPLACE TABLE relevant_meso AS 
            SELECT * FROM proteins WHERE protein_int_index IN ({m})""")
    con.execute(f"""CREATE OR REPLACE TABLE relevant_thermo AS 
            SELECT * FROM proteins WHERE protein_int_index IN ({t})""")
    
    print('Generating final dataset')
    valid_prot_df = con.execute("""
        SELECT
            validprot.local_gap_compressed_percent_id AS percent_id,
            proteins_m.protein_seq AS meso_seq,
            proteins_t.protein_seq AS thermo_seq,
            proteins_m.protein_desc AS meso_desc,
            proteins_t.protein_desc AS thermo_desc,
        FROM validprot
        JOIN relevant_meso AS proteins_m ON (validprot.meso_protein_int_index=proteins_m.protein_int_index)
        JOIN relevant_thermo AS proteins_t ON (validprot.thermo_protein_int_index=proteins_t.protein_int_index)
    """).df()
    
    print('Cleaning up...')
    con.execute("""DROP TABLE validprot""")
    con.execute("""DROP TABLE relevant_meso""") 
    con.execute("""DROP TABLE relevant_thermo""") 
    con.commit()
    con.close()
    print('Done.')
    
    et = time.time()
    elapsed_time = et - st
    print('Execution time:', elapsed_time, 'seconds')
    #print(valid_prot_df.head())
    return valid_prot_df, elapsed_time
