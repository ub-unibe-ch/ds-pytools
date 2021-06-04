# e-manuscripta: accessing metadata and fulltexts

The Python Jupyer notebook [e_manuscripta_metadata_fulltext.ipynb](https://github.com/ub-unibe-ch/ds-pytools/blob/main/web-tools/e-manuscripta-access/e_manuscripta_metadata_fulltext.ipynb) aims to help you with **accessing metadata and fulltexts of [e-manuscripta](https://www.e-manuscripta.ch/)**, the platform for manuscript material from Swiss libraries and archives. It uses the [OAI-PMH](https://www.openarchives.org/pmh/) interface of the e-manuscripta service for retrieving metadata in different formats, and the e-manuscripta website in addition for downloading fulltexts.

**No Python available** on your machine? Use the online Jupyter notebook with Binder: 

Also, a static version of the notebook is available via [Jupyter nbviewer](https://nbviewer.jupyter.org/github/ub-unibe-ch/ds-pytools/blob/main/web-tools/e-manuscripta-access/e_manuscripta_metadata_fulltext.ipynb).

The notebook consists of four parts:

0. Introduction
1. Metadata access with Polymatheia
2. Direct metadata access via OAI-PMH
3. Download fulltext files from e-rara website.

You may start from the beginning and walk trough the whole notebook or jump to the section that suits you. Also, it's a good idea to play around with the code in the cells and see what happens. Have fun!

Have any comments, questions and the like? Try kathi.woitas[at]ub.unibe.ch.

## 0. Introduction

The introduction first offers an overview of the scope and contents of the notebook. After a short illustration of the e-manuscripta platform finally there is a summary of main concepts of the OAI-PMH protocol.

## 1. Metadata access with Polymatheia

The chapter introduces the *Polymatheia* library, which allows very convenient requests to the OAI interface by wrapping otherwise more elaborate code. Also, it offers methods to handle the retrieved data. Working with Polymatheia is an easy solution for quick access without going deep into coding. You might see the [documentation](https://polymatheia.readthedocs.io/en/latest/) of the Polymatheia library.

The chapter makes use of the following OAI verbs:
- oai: 'ListSets'
- oai: 'ListMetadataFormats'
- oai: 'ListRecords'.

Then, it shows **how to access certain metadata elements** and how to **save and recover the retrieved data**.

## 2. Direct metadata access via OAI-PMH

The *Polymatheia* library doesn't offer methods for *all* OAI verbs. For instance, there is no *ListIdentifiers* and no *GetRecord* wrapper. That's where more manual coding is needed. On the other hand accessing the e-manuscripta OAI-PMH directly gives you more freedom how to interact with the interface, naturally. You can use the functions without deeper programming skills - nevertheless these might be helpful if you want to adapt those functions for yourself.

The chapter makes use of the follwing OAI verbs:
- oai: 'Identify'
- oai: 'GetRecord'
- oai: 'ListIdentifiers'.

Therefore, it defines the following functions:
- **load_xml(params)**:

    Accesses the OAI interface according to given parameters and scrapes its content.
    
    Parameters:
    All available native OAI verbs and parameter/value pairs.
    
- **download_record(ID, metadataPrefix='mods')**:

    Downloads a certain metadata record from OAI to a single XML file.
    Throws a notice if metadata file already exists and leaves the existing one.
    
    Parameters:
    ID = E-manuscripta ID of the desired record.
    metadataPrefix = Metadata format to be delivered. Default value is MODS.
    
- **set_size(Set)**:

    Accesses the OAI interface and retrieves the size of a given OAI set.
    
    Parameters:
    * Set: The 'setSpec' short cut of the desired OAI set.
    
- **retrieve_set_metadata(Set, foldername, metadataPrefix='mods')**:
   
    Downloads metadata records of a given set and in a given format from OAI to XML files
    in a designated folder.
    Therefore it
    * requests e-manuscripta OAI-PMH interface according to a set 
    * creates a folder for the records according to parameter foldername
    * retrieves the set's e-manuscripta IDs
    * retrieves metadata according to IDs and given metadata format (default: MODS)
    * saves metadata to single <e-manuscripta ID>.xml files in the folder.
    
    Parameters:
    Set = The 'setSpec' short cut of the desired OAI set.
    foldername = The name of the folder which will be created to hold the metadata files.
    metadataPrefix = Metadata format to be delivered. Default value is MODS.
 
## 3. Download fulltext files from e-manuscripta website

Downloading e-manuscripta fulltetxts in PDF format can be done from the e-manuscripta website. When retrieving all fulltext files of a given OAI set, the OAI-PMH interface will be used in addition.

The chapter defines the following functions:

- **download_fulltext(ID)**:
    
    Downloads the PDF file of a certain e-manuscripta document by its ID.
    Builds with e-manuscripta ID the fulltext URL and downloads the PDF file.
    
    Parameter:
    ID = E-manuscripta ID of the desired record.
    
- **tech_metadata(pdf_path)**:
    
    Reads the technical metadata of a PDF formatted file and prints a summary.
    
    Parameter:
    * pdf_path = The path of the PDF file to be read.

- **retrieve_set_fulltexts(Set, foldername)**:
    
    Downloads PDF fulltexts of a given DDC set from e-manuscripta website to files in a certain folder.
    Therefore it
    * creates the folder according to the parameter foldername
    * requests e-manuscripta OAI-PMH interface according to a OAI set 
    * retrieves the set's e-manuscripta IDs
    * downloads PDF fulltexts according to IDs from e-manuscripta website
    
    Parameters:
    Set = The desired OAI set.
    foldername = name of the folder in which the fulltexts will be stored.