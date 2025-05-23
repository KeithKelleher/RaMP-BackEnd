# RaMP Creation Package #

This repository contains the source code that was used to create RaMP - a Relation database of Metabolic 
Pathways (https://www.ncbi.nlm.nih.gov/pubmed/29470400). RaMP is a conglomerate of several open source databases, 
which include reactions, pathways, and annotations for genes and metabolites. 
The database also includes chemical properties and chemical class annotations from HMDB, ChEBI and LIPIDMAPS.  

#### Note that the files here are NOT RaMP but merely the scripts used to create RaMP. ####

These scripts are used to build the RaMP database from scratch. 
You can download SQLite databases for the current and previous versions of RaMP in the repo for the RaMP R Package: https://github.com/ncats/RaMP-DB/tree/main/db

### The Basics ###
Here is the overall workflow for getting the mySQL database up and running:

  1. git clone this repository
  2. Run main.py successfully - the purpose is to create a file for each table in the RaMP DB Schema in the /misc/sql folder.
  3. Run ad_hoc_cross_check_met_harmony.py to check for bad mergers based on inconsistent molecular weights
  4. update the optionalVersionOveride = "2.6.2", and optionalVersionNote in mainSqliteDBLoad.py
  5. Run mainSqliteDBLoad.py to create and populate the new SQLite database. It will be saved to "src/schema"
  6. You can now query the database!

### Environment set-up ###
* Create and activate a python virtual environment 
  * python -m venv .venv
  * source .venv/bin/activate 
* install dependencies
  * pip install -r requirements.txt

#### Building the database ####
*main.py*

The main script to build the database is 'main.py'. This script calls the other classes and necessary code to 
build the database. 

The first time 'main.py' is run, the raw data files will download, and may take a long time. Note that the 
WikiPathways and PFOCR resources update monthly and change the name of their files to add the date.  The 
config/external_resource_config.txt needs to be updated with the correct new version name.

The output of running 'main.py' are intermediate files that are created in data-source specific files in 
misc/output. The EntityBuilder will automatically run afterwards to build the final files for database 
loading. The entity harmonization process enforces entity curation patches, aggregates duplicate gene and 
compound entities from different data sources and builds entity relationships. This step will refer to a text 
file that contains manual curation results that captures known problems in entity mappings held in certain 
data sources. The compound curation list prevents incorrect mappings between compounds from being introduced 
to the RaMP database. 

*importing sql tables*

Import the sql files into the database using mainSqliteDBLoad.py.

#### Overview of folders in this repo ####
The repo contains the following folders

    **src**: contains classes used by main.py (most of the code)

    **main**: contains main.py -- uses the classes in src (code)

    **tests**: unit testing

    **misc/data**: folders for files from hmdb, wikipathways, kegg, and reactome stored here

    **misc/sql**: .sql files output from running main.py. These .sql files make up the mySQL RaMP database

    **misc/output**: any output file that is not a .sql file -- some functions have other outputs, such as venndiagrams or lists of converted genes (can help with debugging)

*Note: when running main.py, the data, output, and sql folders contain lots of data which is not included with this repo due to size restrictions.*

#### Updates ####
Update to Sqlite DB version 3.0.7 (03/10/2025):
1. New data sources
   * PFOCR - v20240901 (2024-09-01)
   * RefMet IDs - v20250305 (2025-03-05)
2. Updated data sources 
   * Reactome - v89 (2024-06)
   * WikiPathways - v20240810 (2024-08-10)
   * ChEBI - Release 236 (2024-07-27)
   * Lipid Maps - Release (2024-08-19)
   * Rhea - Release 134 (2024-07-24)
3. Re-harmonized and re-built database
   * with updated curation_mapping_issues_list.txt


Update to Sqlite DB version 2.6.2 (09/01/2024):
1. Updated data sources
2. Updated parsing code for WikiPathways data
3. Fixed QC checks for inconsistent molecular weights, and updated curations in "curation_mapping_issues_list.txt"
4. Added a field for the single best common name for genes and metabolites


The first update to the RaMP (01/24/2019):

1. The major change is to adapt to the recent HMDB updates which changed the hierarchy of Ontology.
2. Exclusion of KEGG database.
3. Handled few compound mismatch that had occurred in the old version.

### Contact ###
* Keith Kelleher (keith.kelleher@nih.gov)
* Ewy Mathé (ewy.mathe@nih.gov)

John Braisted, Elizabeth Baskin, Senyang Hu, and Bofei Zhang were also involved in developing this code.
