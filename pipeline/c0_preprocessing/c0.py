import pandas as pd
import numpy as np
import time
import duckdb

# This package builds the ValidProt database from learn2therm.
# 
# Functions:
#     connect_df(): Establishes connection to DuckDB database using local or 
#                   remote input path. Reports time to connection.
#
#     validprot_build(): Constructs validprot database from learn2therm database.
#         
#     remove: fetch_data(): Samples learn2therm database to DataFrame with given number
#                   of entries. Currently pulls protein sequences, descriptions,
#                   optimal growth temperature, and local gap compressed % ID.
#                   Reports time taken to assemble DataFrame.

    
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


def build_validprot(con: duckdb.DuckDBPyConnection, min_ogt_diff: int = 20, min_16s: int = 1300, plots = False):
    '''
    Converts learn2therm DuckDB database into a DuckDB database for ValidProt by adding relevant tables. Takes up a lot of disk space.
    '''
    
    st = time.time()
    
    print('Constructing vp_taxa_pairs...')
    # Builds ValidProt taxa pair table using only paired taxa from learn2therm
    taxa_pairs_cmd = """CREATE OR REPLACE TABLE vp_taxa_pairs AS SELECT * FROM taxa_pairs WHERE is_pair = True"""
    con.execute(taxa_pairs_cmd)
    
    et = time.time()
    elapsed_time = et - st
    print(f'Finished constructing vp_taxa_pairs. Execution time: {elapsed_time} seconds')
    
    print('Constructing vp_taxa...')
    # Commands to identify all taxa that are implicated in learn2therm pairs.
    meso_cmd = """SELECT DISTINCT meso_index
    FROM taxa_pairs
    WHERE is_pair = True"""
    
    thermo_cmd = """SELECT DISTINCT thermo_index
    FROM taxa_pairs
    WHERE is_pair = True"""

    useful_thermo = con.execute(thermo_cmd).df()
    useful_meso = con.execute(meso_cmd).df()
    
    # Generates tuple object containing all relevant taxa
    useful_taxa = tuple([i for i in useful_meso['meso_index']] + [i for i in useful_thermo['thermo_index']])
    
    # Builds ValidProt taxa table using only paired taxa from learn2therm.
    taxa_cmd = f"""CREATE OR REPLACE TABLE vp_taxa AS SELECT * FROM taxa WHERE taxa_index IN {useful_taxa}"""
    con.execute(taxa_cmd)
    
    et2 = time.time()
    elapsed_time = et2 - et
    print(f'Finished constructing vp_taxa. Execution time: {elapsed_time} seconds')
    
    print('Filtering on ogt and 16S sequence parameters...')
    # Builds ValidProt table containing taxa pairs and their associated optimal growth temperatures (ogt). 
    # Excludes short 16S sequences and pairs with ogt spread below cutoff value from function input.
    ogt_pairs_cmd = f"""CREATE OR REPLACE TABLE vp_ogt_taxa_pairs AS SELECT vp_taxa_pairs.*,
                    taxa_m.ogt AS meso_ogt,
                    taxa_t.ogt AS thermo_ogt,
                    taxa_t.ogt - taxa_m.ogt AS ogt_diff,
                    taxa_m.len_16s AS meso_16s_len,
                    taxa_t.len_16s AS thermo_16s_len
                    FROM vp_taxa_pairs
                    JOIN vp_taxa AS taxa_m ON (vp_taxa_pairs.meso_index = taxa_m.taxa_index)
                    JOIN vp_taxa AS taxa_t ON (vp_taxa_pairs.thermo_index = taxa_t.taxa_index)
                    WHERE ogt_diff >= {min_ogt_diff}
                    AND meso_16s_len >= {min_16s}
                    AND thermo_16s_len >= {min_16s}"""
    con.execute(ogt_pairs_cmd)
    
    et3 = time.time()
    elapsed_time = et3 - et2
    print(f'Finished filtering. Execution time: {elapsed_time} seconds')

    print('Constructing vp_protein_pairs...')
    # Builds ValidProt table containing protein pairs 
    protein_pair_cmd = """CREATE OR REPLACE TABLE vp_protein_pairs AS SELECT protein_pairs.*,
                    otp.local_gap_compressed_percent_id AS local_gap_compressed_percent_id_16s,
                    otp.scaled_local_query_percent_id AS scaled_local_query_percent_id_16s,
                    otp.scaled_local_symmetric_percent_id AS scaled_local_symmetric_percent_id_16s,
                    otp.query_align_cov AS query_align_cov_16s,
                    otp.subject_align_cov AS subject_align_cov_16s,
                    otp.bit_score AS bit_score_16s,
                    otp.meso_ogt AS m_ogt,
                    otp.thermo_ogt AS t_ogt,
                    otp.ogt_diff AS ogt_difference
                    FROM protein_pairs 
                    INNER JOIN vp_ogt_taxa_pairs AS otp ON (protein_pairs.taxa_pair_index = otp.taxa_pair_index)"""
    con.execute(protein_pair_cmd)
    
    et4 = time.time()
    elapsed_time = et4 - et3
    print(f'Finished constructing vp_protein_pairs. Execution time: {elapsed_time} seconds')
    
    print('Constructing vp_proteins...')
    # Builds ValidProt table containing proteins that belong to taxa pairs from vp_taxa_pairs.
    prot_filt_cmd = """CREATE OR REPLACE TABLE vp_proteins AS SELECT *
                    FROM proteins
                    WHERE protein_int_index IN (SELECT DISTINCT meso_protein_int_index FROM protein_pairs) OR
                    protein_int_index IN (SELECT DISTINCT thermo_protein_int_index FROM protein_pairs)
                    """
    con.execute(prot_filt_cmd)
    et5 = time.time()
    elapsed_time = et5 - et4
    print(f'Finished constructing vp_proteins. Execution time: {elapsed_time} seconds')
    
    print('Constructing final dataset...')
    # Builds final ValidProt data table for downstream sampling.
    big_table_cmd = """CREATE OR REPLACE TABLE vp_final AS SELECT vp_protein_pairs.*,
                    proteins_m.protein_seq AS m_protein_seq,
                    proteins_t.protein_seq AS t_protein_seq,
                    proteins_m.protein_desc AS m_protein_desc,
                    proteins_t.protein_desc AS t_protein_desc,
                    proteins_m.protein_len AS m_protein_len,
                    proteins_t.protein_len AS t_protein_len
                    FROM vp_protein_pairs
                    JOIN vp_proteins AS proteins_m ON (vp_protein_pairs.meso_protein_int_index = proteins_m.protein_int_index)
                    JOIN vp_proteins AS proteins_t ON (vp_protein_pairs.thermo_protein_int_index = proteins_t.protein_int_index)"""

    con.execute(big_table_cmd)

    print('Finishing up...')
    con.commit()
    con.close()
    
    et_final = time.time()
    elapsed_time = et_final - et5
    print(f'Finished. Total execution time: {elapsed_time} seconds')
    return

# def build_protein_table():
#     '''
#     '''
#     return

# def fetch_data(sample_size: int, con: duckdb.DuckDBPyConnection, E_cutoff: float = 0, ID_cutoff: float = 0):
#     '''Samples protein_pairs table, then creates a subset of relevant proteins
# and joins to output a sample DataFrame. Leaves behind no database objects.
# Relatively fast and less memory intensive than creating a new table.'''
    
#     st = time.time()
    
#     print('Sampling dataset')
    
#     validprot_str = f"""CREATE OR REPLACE TABLE validprot AS
#         SELECT
#             local_gap_compressed_percent_id,
#             scaled_local_query_percent_id,
#             scaled_local_symmetric_percent_id,
#             bit_score,
#             query_align_cov,
#             subject_align_cov,
#             prot_pair_index,
#             meso_protein_int_index,
#             thermo_protein_int_index
#         FROM protein_pairs
#         WHERE local_gap_compressed_percent_id >= {ID_cutoff} AND
#               local_E_value <= {E_cutoff}
#         USING SAMPLE {sample_size}"""
    
#     con.execute(validprot_str)
    
#     # Extract protein index values from validprot to Python DataFrame, then to list.
#     print('Generating index filter')
#     get_idx_str = """SELECT meso_protein_int_index, thermo_protein_int_index FROM validprot"""
#     protein_index = con.execute(get_idx_str).df()

#     meso_protein_list = [i for i in protein_index['meso_protein_int_index']]
#     thermo_protein_list = [i for i in protein_index['thermo_protein_int_index']]

#     # Generate single string as comma-separated list of protein indices.
#     meso_idx_str = ', '.join(map(str, meso_protein_list))
#     thermo_idx_str = ', '.join(map(str, thermo_protein_list))
    
#     # Create new tables from proteins containing only proteins mentioned in validprot.
#     print('Finding relevant proteins')
#     relevant_meso_str = f"""CREATE OR REPLACE TABLE relevant_meso AS 
#             SELECT * FROM proteins WHERE protein_int_index IN ({meso_idx_str})"""
#     relevant_thermo_str = f"""CREATE OR REPLACE TABLE relevant_thermo AS 
#             SELECT * FROM proteins WHERE protein_int_index IN ({thermo_idx_str})"""
#     con.execute(relevant_meso_str)
#     con.execute(relevant_thermo_str)
    
#     # Perform final join of sampled dataset to validprot_df, a DataFrame containing all
#     # useful features for downstream processing.
#     print('Generating final dataset')
#     validprot_df_str = """
#         SELECT
#             validprot.local_gap_compressed_percent_id AS percent_id,
#             proteins_m.protein_seq AS meso_seq,
#             proteins_t.protein_seq AS thermo_seq,
#             proteins_m.protein_desc AS meso_desc,
#             proteins_t.protein_desc AS thermo_desc,
#         FROM validprot
#         JOIN relevant_meso AS proteins_m ON (validprot.meso_protein_int_index=proteins_m.protein_int_index)
#         JOIN relevant_thermo AS proteins_t ON (validprot.thermo_protein_int_index=proteins_t.protein_int_index)
#     """
#     validprot_df = con.execute(validprot_df_str).df()
#     print(f'validprot shape: {validprot_df.shape}')
    
#     # Remove new tabled from database and commit changes so that connection will close properly.
#     print('Cleaning up...')
#     drop_tables = ['validprot', 'relevant_meso', 'relevant_thermo']
#     for table in drop_tables:
#         drop_str = f"""DROP TABLE {table}"""
#         con.execute(drop_str)
#     con.commit()
#     print('Done.')
    
#     et = time.time()
#     elapsed_time = et - st
#     print('Execution time:', elapsed_time, 'seconds')

#     return validprot_df, elapsed_time

# # def build_validprot_table(params):
