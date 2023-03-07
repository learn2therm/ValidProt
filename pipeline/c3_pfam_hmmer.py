'''
The script executes HMMER against pfam and generate output files

The packages you need to run this script are the following:
- biopython
- HMMER (http://hmmer.org/documentation.html)
- pandas

You also need to have:
- pfam db locally
- protein db
'''

# system dependecies
from pathlib import Path
import subprocess



# library dependencies
from collections import defaultdict
import pandas as pd



## biopython
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import SearchIO


# local dependencies/utils

## Paths
PFAM_PATH = Path("/Users/humoodalanzi/pfam/Pfam-A.hmm")
ID_DB_PATH = Path("/Users/humoodalanzi/pfam/proteins_id.zip")



def hmmer_wrapper(seq: pd.core.frame.DataFrame, input_filename: str, pfam_path: str, input_filename_with_ext: str, output_filename_with_ext: str, cpu: int = 4):
    """
    Executes HMMER against pfam and parses the results

    Parameters:
    ------------
    seq : pandas.core.frame.DataFrame
        a dataframe with string amino acid sequences in a 'seq' column (has to be processed in a certain way)
    input_filename : str
        A file name for the input of the transformed seq to FASTA
    pfam_path : str
        path of the HMMER/pfam db
    input_filename_with_ext : str
        A file name for the input FASTA has to include the ext. FASTA
    output_filename_with_ext : str
        output file name perferred extension is domtblout
    cpu : 4
        number of cpus for i/o
    
    Returns:
    ------------
    file : TextIOWrapper (Input fasta file)
        the input fasta file created from the list of SeqRecord objects
    file : TextIOWrapper (Output domtblout file)
        an output domtblout file of the HMMER/pfam results
        
    Raises
    -------
    AttributeError :
        in development
    """
    ### wrapper execution
    # User should define an amino acid sequence as Pandas series
    
    # generate meso and thermo files
    read_seq(seq, input_filename)

    # place files into HMMER/pfam
    run_hmmer(pfam_path, input_filename_with_ext, output_filename_with_ext, cpu)
    


# Create a list of SeqRecord objects
# Write the list of SeqRecord objects to a FASTA file
def read_seq(lists: pd.core.frame.DataFrame, inputname: str = "input"):
    """
    Returns a list of SeqRecord objects and creates a corresponding input Fasta of them

    Parameters:
    ------------
    list : pandas.core.frame.DataFrame
        a dataframe with string amino acid sequences in a 'protein_seq' column
    input name : str, default = 'input'
        a name for the input fasta file

    
    Returns:
    ------------
    file : TextIOWrapper
        the input fasta file created from the list of SeqRecord objects

    Raises
    -------
    ValueError : 
        if the input dataframe is empty
    AttributeError :
        if any of the sequences are invalid
    """
    # check if input is empty
    if lists.empty:
        raise ValueError("Input dataframe is empty")
    
    # check if sequences are valid
    for seq in lists['protein_seq']:
        try:
            Seq(seq)
        except:
            raise AttributeError("Invalid sequence")

    # function    
    records = []
    for index, seq in lists.itertuples():
        try:
            record = SeqRecord(Seq(seq), id=str(index))
            records.append(record)
        except AttributeError:
            raise AttributeError(f"Invalid sequence: {seq}")
    
    # raise error if seq not valid
    if not records:
        raise AttributeError("No valid sequences found in input")
    
    with open(f"{inputname}.fasta", "w") as file:
            SeqIO.write(records, file, "fasta")
    return file



def run_hmmer(DB_PATH: str, input_filename: str, output_filename: str, num_cpu: int = 4) -> None:
    """
    Runs HMMER search against the Pfam database using the hmmscan command
    
    Parameters:
    ------------
    DB_PATH : str
        the path of the HMMER/pfam database
    input_filename : str
        a name for the input fasta file (don't forget extension!)
    output_filename : str
        a name for the domtblout output file (don't forget extension!)
    num_cpu : int

    
    Returns:
    ------------
    file : TextIOWrapper (Output domtblout file)
        an output domtblout file of the HMMER/pfam results

    Raises
    -------
    AttributeError :
        in development
    """
    with open(output_filename, "w", encoding="utf-8") as file:
        subprocess.run(["hmmscan", "--cpu", str(num_cpu), "--domtblout", output_filename, DB_PATH, input_filename], stdout=file)
    return file


if __name__ == '__main__':
    ### Data prep and processing

    # reading the data
    protein_database = pd.read_csv(ID_DB_PATH, index_col=0)

    # separating the meso and thermo
    meso_seq_db = protein_database.loc[protein_database["identity"] == "m"]
    thermo_seq_db = protein_database.loc[protein_database["identity"] == "t"]

    ## processing meso to be suitable for HMMER
    meso_seq_pre = meso_seq_db[["protein_seq", "protein_int_index"]]
    meso_seq_list = meso_seq_pre.set_index("protein_int_index").iloc[:15]
    meso_seq_list.index.name = None


    ## processing meso to be suitable for HMMER
    thermo_seq_pre = thermo_seq_db[["protein_seq", "protein_int_index"]]
    thermo_seq_list = thermo_seq_pre.set_index("protein_int_index").iloc[:15]
    thermo_seq_list.index.name = None


    #### Execution
    hmmer_wrapper(meso_seq_list, "meso_input", PFAM_PATH, "meso_input.fasta", "meso_output.domtblout", 4)
    hmmer_wrapper(thermo_seq_list, "thermo_input", PFAM_PATH, "thermo_input.fasta", "thermo_output.domtblout", 4)
