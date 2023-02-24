import pandas as pd
import numpy as np
import time
import duckdb

# This package generates DataFrame objects sampling the learn2therm relational
# database using DuckDB.
# 
# Functions:
#     connect_df(): Establishes connection to DuckDB database using local or 
#                   remote input path. Reports time to connection.
#         
#     fetch_data(): Samples learn2therm database to DataFrame with given number
#                   of entries. Currently pulls protein sequences, descriptions,
#                   optimal growth temperature, and local gap compressed % ID.
#                   Reports time taken to assemble DataFrame.
#
#     build_validprot_table(): Constructs new table within learn2therm database 
#                              for later sampling.

def connect_db(path: str):
    '''Runs duckdb.connect() function on database path with timing. Returns a 
duckdb.DuckDBPyConnection object'''
    
    st = time.time()

    print('Connecting to database...')
    con = duckdb.connect(path)

    et = time.time()
    elapsed_time = et - st
    print(f'Connection established! Execution time: {elapsed_time} seconds')
    return con
        
def fetch_data(sample_size: int, con: duckdb.DuckDBPyConnection, E_cutoff: float = 0, ID_cutoff: float = 0):
    '''Samples protein_pairs table, then creates a subset of relevant proteins
and joins to output a sample DataFrame. Leaves behind no database objects.
Relatively fast and less memory intensive than creating a new table.'''
    
    st = time.time()
    
    print('Sampling dataset')
    
    validprot_str = f"""CREATE OR REPLACE TABLE validprot AS
        SELECT
            local_gap_compressed_percent_id,
            scaled_local_query_percent_id,
            scaled_local_symmetric_percent_id,
            bit_score,
            query_align_cov,
            subject_align_cov,
            prot_pair_index,
            meso_protein_int_index,
            thermo_protein_int_index
        FROM protein_pairs
        WHERE local_gap_compressed_percent_id >= {ID_cutoff} AND
              local_E_value <= {E_cutoff}
        USING SAMPLE {sample_size}"""
    
    con.execute(validprot_str)
    
    # Extract protein index values from validprot to Python DataFrame, then to list.
    print('Generating index filter')
    get_idx_str = """SELECT meso_protein_int_index, thermo_protein_int_index FROM validprot"""
    protein_index = con.execute(get_idx_str).df()

    meso_protein_list = [i for i in protein_index['meso_protein_int_index']]
    thermo_protein_list = [i for i in protein_index['thermo_protein_int_index']]

    # Generate single string as comma-separated list of protein indices.
    meso_idx_str = ', '.join(map(str, meso_protein_list))
    thermo_idx_str = ', '.join(map(str, thermo_protein_list))
    
    # Create new tables from proteins containing only proteins mentioned in validprot.
    print('Finding relevant proteins')
    relevant_meso_str = f"""CREATE OR REPLACE TABLE relevant_meso AS 
            SELECT * FROM proteins WHERE protein_int_index IN ({meso_idx_str})"""
    relevant_thermo_str = f"""CREATE OR REPLACE TABLE relevant_thermo AS 
            SELECT * FROM proteins WHERE protein_int_index IN ({thermo_idx_str})"""
    con.execute(relevant_meso_str)
    con.execute(relevant_thermo_str)
    
    # Perform final join of sampled dataset to validprot_df, a DataFrame containing all
    # useful features for downstream processing.
    print('Generating final dataset')
    validprot_df_str = """
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
    validprot_df = con.execute(validprot_df_str).df()
    print(f'validprot shape: {validprot_df.shape}')
    
    # Remove new tabled from database and commit changes so that connection will close properly.
    print('Cleaning up...')
    drop_tables = ['validprot', 'relevant_meso', 'relevant_thermo']
    for table in drop_tables:
        drop_str = f"""DROP TABLE {table}"""
        con.execute(drop_str)
    con.commit()
    print('Done.')
    
    et = time.time()
    elapsed_time = et - st
    print('Execution time:', elapsed_time, 'seconds')

    return validprot_df, elapsed_time

# def build_validprot_table(params):
