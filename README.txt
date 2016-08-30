This project uses the Medical Text Indexer (MTI) Java-based API provided by the National Library (NLM) to annotate ChEMBL assays descriptions with MeSH terms.

To use the API, you need to download the directory from https://ii.nlm.nih.gov/MTI/.
This requires a UMLS Terminology Services license (this is free) which you can get here: https://uts.nlm.nih.gov//license.html
Publications on the MTI: https://ii.nlm.nih.gov/Publications/index.shtml#MTI

The file hierarchy expected is as follows:
SKR_Web_API_V2_1/
    run.sh
    examples/
        GenericBatchUser.java
        logs/
        inputfiles/
            0001/
                input1.txt
                input2.txt
                input3.txt
            0002/
                input4.txt
                input5.txt
                input5.txt
    
In order to submit the jobs to the NLM API I used the GenericBatchUser.java file from the examples directory provided.
One change to this script needs to be made on line 140, changing 'singleLineDelimitedInput = true' to 'singleLineDelimitedInputWithId = true'.

See the example notebooks A, B and C on how to use the functions in the MTI_api_functions.py module.

Also the environment needs to have a working version of Java, specify a path to this java in the run.sh file in the SKR_Web_API_V2_1 directory.
For the EBI cluster I used java from here /nfs/research2/software/prefix/usr/bin/java

The conda environment I used is as follows, using python 3.4:

# packages in environment
#
cssselect                 0.9.1                     <pip>
cx-oracle                 5.2                       <pip>
eutils                    0.0.9                     <pip>
fontconfig                2.11.1                        4
freetype                  2.5.2                         2
ipython                   3.2.1                    py34_0
libpng                    1.6.17                        0
libxml2                   2.9.2                         0
libxslt                   1.1.28                        0
lxml                      3.4.4                    py34_0
matplotlib                1.4.3                np19py34_2
metapub                   0.3.17.2                  <pip>
numpy                     1.9.2                    py34_0
openssl                   1.0.2g                        0
pandas                    0.16.2               np19py34_0
pip                       8.1.1                    py34_1
pyparsing                 2.0.3                    py34_0
pyqt                      4.11.3                   py34_1
python                    3.4.4                         0
python-dateutil           2.4.2                    py34_0
pytz                      2015.4                   py34_0
qt                        4.8.6                         3
readline                  6.2                           2
requests                  2.7.0                     <pip>
setuptools                20.3                     py34_0
sip                       4.16.5                   py34_0
six                       1.9.0                    py34_0
sqlalchemy                1.0.12                   py34_0
sqlite                    3.9.2                         0
system                    5.8                           2
tabulate                  0.7.5                     <pip>
tk                        8.5.18                        0
wheel                     0.29.0                   py34_0
xz                        5.0.5                         1
zlib                      1.2.8                         0
