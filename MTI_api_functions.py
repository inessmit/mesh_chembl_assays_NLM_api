
# coding: utf-8

# In[2]:

import sqlalchemy as al
import os
import itertools
import logging


# Notes README
# * file hierarchy
# * talk about changes I made in the java files
# * take note of command/options used, as well as need for umls license and password insert into GenericBatchUser file.
# * explain about the failing jobs and errors
# 
# * example script

# In[ ]:




# In[14]:

def get_assay_descriptions(engine, condition = None):
    """Connect to engine and gets all assay descriptions from ChEMBL to iterable for use in make_input_files function.
    kwargs: engine -- str, database engine e.g. sqlalchemy engine"""
    connection = engine.connect()
    sql = "select assay_id, trim('.' from description) from chembl_21.assays where description is not null"
    if condition != None:
        sql = sql + ' and ' + condition
    result = engine.execute(sql).fetchall()
    connection.close()
    return(result)


# In[27]:

def make_input_files(db_result, nr_assays = 4000, nr_files = 100, path_to_inputfiles = './inputfiles'): 
    """Create text files containing assay_ids and ChEMBL assay descriptions for use as input to Medical Text Indexer.
    Place the inputfiles in numbered directories within the provided directory.
    If no directory is given, create the directory 'inputfiles' if it does not exist yet and remove all existing contents before filling it.
    kwargs: db_result -- iterable containing tuples with assay_ids and assay_descriptions from ChEMBL
        nr_assays -- int, number of assays (rows) to be put in one text file
        nr_files -- int, number of inputfiles to be put in one numbered subdirectory of the inputfiles directory"""

    # The number 4000 is arbitary, there are no limits from the NLM API side, apart from the note that it's more efficient to submit many lines per file than few. 
    
    def grouper(n, iterable):
        it = iter(iterable)
        while True:
            chunk = tuple(itertools.islice(it, n))
            if not chunk:
                return
            yield chunk

    #create inputfiles directory, empty old contents
    if not os.path.exists(path_to_inputfiles):
        os.makedirs(path_to_inputfiles)
    os.system('rm -rf ./inputfiles/*')
        
    # create inputfiles
    filenumber = 0
    for chunk in grouper(nr_assays, db_result):
        filenumber += 1

        directory = '000'+str(int(1+filenumber/nr_files)) 
        if not os.path.exists(path_to_inputfiles+'/'+directory):
            os.makedirs(path_to_inputfiles+'/'+directory)

        filepath = path_to_inputfiles+'/'+directory+'/input' + str(filenumber) + '.txt'
    
        file = open(filepath, 'w')
        for item in chunk:
            file.write('"'+str(item[0])+'"|'+item[1].replace('prostrate', 'prostate').replace('Prostrate', 'Prostate')+'\n') # typo in ChEMBL_21
        file.close()


# In[ ]:

# Need to define paths
# The scripts assume a path to the 'SKR_Web_API_V2_1' directory as downloaded from NCBI Medical Text Indexer website.
# The 'SKR_Web_API_V2_1' directory needs to contain the run.sh file.
# The 'examples' directory contains the java files (e.g. I have been using GenericBatchUser.java)

# path_to_MTI_dir = '/nfs/research2/jpo/shared/projects/HeCaToS/mesh_api/SKR_Web_API_V2_1/'
# path_to_files_dir = '/nfs/research2/jpo/shared/projects/HeCaToS/mesh_api/SKR_Web_API_V2_1/examples'


# In[ ]:

def submit_job_array_for_inputdir(inputfiles_dir, inputfiles_subdir, email, path_to_MTI_dir='/nfs/research2/jpo/shared/projects/HeCaToS/mesh_api/SKR_Web_API_V2_1', path_to_files_dir='/nfs/research2/jpo/shared/projects/HeCaToS/mesh_api/SKR_Web_API_V2_1/examples'):
    """Submit a job array using bsub referring to the inputfiles in the given inputfiles directory to get the results from the Java-based Medical Text Indexer web services.
    kwargs: path_to_MTI_dir -- str, full path to the directory with MTI files in it, as downloaded from them, called 'SKR_Web_API_V2_1'
            path_to_files_dir -- str, full path to the directory within the MTI directory in which the java files are stored, this is called 'examples' in the downloaded 'SKR_Web_API_V2_1' directory.
            inputfiles_dir -- str, name of the directory that contains the numbered subdirectories which in turn contain the inputfiles. Must be located within path_to_files_dir.
            inputfiles_subdir -- str, name of a specific subdirectory of the inputfiles directory (as defined under 'inputfiles_dir') for which you want to submit an array. 
            email -- str email address mandatory for using NLM API
    """
    # This function expects a hierarchical file structure in which the parent directory 'SKR_Web_API_V2_1' contains the run.sh file.
    # Within 'SKR_Web_API_V2_1' there should be a subdirectory with the java files for e.g. GenericBatchUser.java
    # Within this subdirectory this function expects an 'inputfiles' directory that contains subdirectories with the inputfiles. There should be max. 1000 inputfiles in each subdirectory because this is the max size of an array for bsub.
    # This function will make the directories 'outputfiles' and 'errorfiles' if they don't yet exist.

    inputfiles = [int(file.strip('.txt').strip('input')) for file in os.listdir(path_to_files_dir+'/'+inputfiles_dir+'/'+inputfiles_subdir) if 'input' in file]

    if not os.path.exists(path_to_files_dir+'/errorfiles/'+inputfiles_subdir):
        os.makedirs(path_to_files_dir+'/errorfiles/'+inputfiles_subdir)
    if not os.path.exists(path_to_files_dir+'/outputfiles/'+inputfiles_subdir):
        os.makedirs(path_to_files_dir+'/outputfiles/'+inputfiles_subdir)

    errorfiles = path_to_files_dir+'/errorfiles/'+inputfiles_subdir+'/errors%J_%I'
    outputfiles = path_to_files_dir+'/outputfiles/'+inputfiles_subdir+'/output%I'
    script = path_to_MTI_dir+'/run.sh'
    inputfiles_spec = path_to_files_dir+'/'+inputfiles_dir+'/'+inputfiles_subdir+'/input\$LSB_JOBINDEX.txt'
    outputfiles_spec = path_to_files_dir+'/outputfiles/'+inputfiles_subdir+'/output\$LSB_JOBINDEX'

    # In the command below, one job is run at a time. It was recommended by NLM MTI support to run max 2-3 jobs at a time, otherwise things slow down.
    command = 'bsub -J "myArray[{0}-{1}]%1" -e "'+errorfiles+'" -o "'+outputfiles+'" "'+script+' GenericBatchUser --email '+email+' --singleLinePMID '+inputfiles_spec+' > '+outputfiles_spec+'"'
    formatted_command = command.format(min(inputfiles), max(inputfiles), inputfiles_subdir)
    os.system(formatted_command)


# In[ ]:

# I haven't tested this function

def redo_failed_jobs(inputfiles_dir, inputfiles_subdir, email, path_to_files_dir='/nfs/research2/jpo/shared/projects/HeCaToS/mesh_api/SKR_Web_API_V2_1/examples', path_to_MTI_dir = '/nfs/research2/jpo/shared/projects/HeCaToS/mesh_api/SKR_Web_API_V2_1'):
    """Detect which outputfiles in a subdirectory of outputfiles have failed (based on size of the file) and resubmit them in an array
    kwargs: path_to_MTI_dir -- str, full path to the directory with MTI files in it, as downloaded from them, called 'SKR_Web_API_V2_1'
            path_to_files_dir -- str, full path to the directory within the MTI directory in which the java files are stored, this is called 'examples' in the downloaded 'SKR_Web_API_V2_1' directory.
            inputfiles_dir -- str, name of the directory that contains the numbered subdirectories which in turn contain the inputfiles. Must be located within path_to_files_dir.
            inputfiles_subdir -- str, name of a specific subdirectory of the inputfiles directory (as defined under 'inputfiles_dir') for which you want to redo failed jobs.
            email -- str email address mandatory for using NLM API
    """
    
    logging.info('Starting to check missing files in {}'.format(inputfiles_subdir))
    
    missing_files = [file.strip('output') for file in os.listdir(path_to_files_dir+'/'+'outputfiles'+'/'+inputfiles_subdir) if os.path.getsize(path_to_files_dir+'/'+'outputfiles'+'/'+inputfiles_subdir+'/'+file) < 20000]
    missing_files_formatted = ','.join(missing_files)
    
    if len(missing_files) == 0:
        logging.info('No missing files detected in {}'.format(inputfiles_subdir))
        return
    else:
        logging.info('Missing file(s) detected, starting to rerun missing files for {}'.format(inputfiles_subdir))
        
    errorfiles = path_to_files_dir+'/errorfiles/{1}/errors%J_%I'
    outputfiles = path_to_files_dir+'/outputfiles/{1}/output%I'
    script = path_to_MTI_dir+'/run.sh'
    inputfiles_spec = path_to_files_dir+'/'+inputfiles_dir+'/{1}/input\$LSB_JOBINDEX.txt'
    outputfiles_spec = path_to_files_dir+'/outputfiles/{1}/output\$LSB_JOBINDEX'

    command = 'bsub -J "myArray[{0}]%1" -e "'+errorfiles+'" -o "'+outputfiles+'" "'+script+' GenericBatchUser --email '+email+' --singleLinePMID '+inputfiles_spec+' > '+outputfiles_spec+'"'
    formatted_command = command.format(missing_files_formatted, inputfiles_subdir)
    os.system(formatted_command)
    
    logging.info('Submitted missing files from {}'.format(inputfiles_subdir))


# In[1]:

def create_db_tables(engine, annotation_table):
    """Create tables for storing mesh annotations per assay_id in my own Oracle area. Only needs to be done once.
    kwargs: engine -- str, database engine e.g. sqlalchemy engine
            annotation_table -- str, name of the table for storing the assay_id together with ids for descriptors and qualifiers"""
    engine.execute('''
    create table {}
    (
    assay_id int
    , descriptor_ui varchar2(50)
    , descriptor_text varchar(200)
    , umls_id varchar2(50)
    , score int
    , term_type varchar2(50)
    , misc varchar(1000)
    , paths varchar(50)
    , comments varchar2(400)
    )
     '''.format(annotation_table))
    
    engine.execute("COMMENT ON COLUMN {}.assay_id IS 'ChEMBL assay_id'".format(annotation_table))
    engine.execute("COMMENT ON COLUMN {}.descriptor_ui IS 'Unique identifier for the subject heading. Every identifier begins with the letter D (for descriptor). Unique IDs starting with C are supplementary concepts.'".format(annotation_table))
    engine.execute("COMMENT ON COLUMN {}.descriptor_text IS 'Preferred term for the concept. Preferred term for the concept, unique for the descriptor ID.'".format(annotation_table))
    engine.execute("COMMENT ON COLUMN {}.umls_id IS 'Concept Unique Identifier for the MeSH Term. A single e.g. descriptor record will have one or more concepts, one of which is the preferred concept of the record.'".format(annotation_table))
    engine.execute("COMMENT ON COLUMN {}.score IS 'Medical Text Indexer Score for this term'".format(annotation_table))
    engine.execute("COMMENT ON COLUMN {}.term_type IS 'Type of the term. MeSH Heading (MH), Heading Mapped to (HM), Entry Term (ET), Supplemental Concept(NM), MeSH SubHeading (SH), MeSH CheckTag (CT)'".format(annotation_table))
    engine.execute("COMMENT ON COLUMN {}.misc IS 'If via entry term, this explains the replacement. If not, blank'".format(annotation_table))
    engine.execute("COMMENT ON COLUMN {}.paths IS 'One or more designators showing which of the pathways recommended the term. MetaMap''s MMI (MM), PubMed Related Citations (RC)'".format(annotation_table))
    
    logging.info('database table called {} created'.format(annotation_table))


# In[ ]:

def insert_results_into_oracle(engine, annotation_table, outputfiles_path):
    """Insert results from output text files into oracle table. If no terms were suggested for the assay 'no terms suggested' is writtin in the comments column.
    kwargs: engine -- str, database engine e.g. sqlalchemy engine
            annotation_table -- str, name of the table for storing the pmid together with ids for descriptors and qualifiers
            outputfiles_path -- path to directory containing outputfiles
            """
    logging.info('Started inserting files from {}'.format(outputfiles_path))
    
    for outputfile in [file for file in os.listdir(outputfiles_path) if 'output' in file]:
        
        logging.info('started with file ' + outputfile)
        
        with open(outputfiles_path+'/'+outputfile, 'r') as f:
            result = f.readlines()

        for line in result:

            if '||||' in line:
                assay_id = line.split('"')[1]
                sql = '''insert into {}(assay_id, descriptor_ui, comments) values({}, 'not applicable', 'no terms suggested')'''.format(annotation_table, assay_id)
                engine.execute(sql)
                continue

            else:
                try:
                    fields = line.split('|')

                    try:
                        assay_id = int(str(fields[0]).strip('"'))
                        descriptor_text = fields[1].strip("*").replace("'", "''")
                        umls_id = fields[2]
                        score = fields[3]
                        term_type = fields[4].replace("'", "''")
                        misc = fields[5].replace("'", "''")
                        paths = fields[7].replace("'", "''")
                        descriptor_ui = fields[8].strip('\n') # haven't tested the stripping here

                        sql = """insert into {}(assay_id, descriptor_ui, descriptor_text, umls_id, score, term_type, misc, paths) 
                        values({}, '{}', '{}', '{}', {}, '{}', '{}', '{}')""".format(annotation_table, assay_id, descriptor_ui, descriptor_text, umls_id, score, term_type, misc, paths)

                        engine.execute(sql)

                    except IndexError:
                        logging.info('Problem at assay_id {}: Did not extract the fields correctly'.format(assay_id))
                        next

                except ValueError:
                    # This exception happens when '|' is not in the line. This happens at the end of the outputfile where there are some lines reporting on the lsf job.
                    # These lines can be ignored. However, there were some cases I got 'ERROR' returned on the line (no assay_id on the line) and these seemed to correspond to missing assay_ids.
                    if 'ERROR' in line:
                        logging.info("Problem at this line, contains the string 'ERROR'. Check assay_ids against the input files (or original sql statement) to check if any assay_ids are missing.")
                    next

        logging.info('finished with file ' + outputfile)
    logging.info('Finished inserting files from {}'.format(outputfiles_path))


# In[5]:

def create_indexes(engine, annotation_table):
    """Create indexes on the tables containing mesh annotations per assay_id.
    kwargs: engine -- str, database engine e.g. sqlalchemy engine
            annotation_table -- str, name of the table for storing the pmid together with ids for descriptors and qualifiers"""
    
    engine.execute("CREATE INDEX test_dui ON {}(descriptor_ui)".format(annotation_table))
    engine.execute("CREATE INDEX test_dtext ON {}(descriptor_text)".format(annotation_table))
    engine.execute("CREATE INDEX test_idx ON {}(assay_id, descriptor_ui, descriptor_text)".format(annotation_table))

    logging.info('Indexes on table {} created'.format(annotation_table))


# In[ ]:



