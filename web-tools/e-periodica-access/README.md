# e-periodica: accessing metadata and fulltexts

The Python Jupyer notebook [e_periodica_metadata_fulltext.ipynb](https://github.com/ub-unibe-ch/ds-pytools/blob/main/web-tools/e-periodica-access/e_periodica_metadata_fulltext.ipynb) aims to help you with **accessing metadata and fulltexts of [e-periodica](https://www.e-periodica.ch/)**, the platform for digitized and digital journals from Switzerland. It uses the [OAI-PMH](https://www.openarchives.org/pmh/) interface of the e-periodica service for retrieving metadata in different formats, and the e-periodica website in addition for downloading fulltexts.

**No Python available** on your machine? Use the online Jupyter notebook with Binder: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/k-woitas/e-periodica-access/HEAD?filepath=e_periodica_metadata_fulltext.ipynb)

Also, a **static version** of the notebook is available via [Jupyter nbviewer](https://nbviewer.jupyter.org/github/ub-unibe-ch/ds-pytools/blob/main/web-tools/e-periodica-access/e_periodica_metadata_fulltext.ipynb?flush_cache=true).

The notebook consists of four parts:

0. Introduction
1. Metadata access with Polymatheia
2. Direct metadata access via OAI-PMH
3. Download fulltext files from e-periodica website.

You may start from the beginning and walk trough the whole notebook or jump to the section that suits you. Also, it's a good idea to play around with the code in the cells and see what happens. Have fun!

Have any comments, questions and the like? Try kathi.woitas[at]unibe.ch.

## 0. Introduction

The introduction first offers an overview of the scope and contents of the notebook. After a short illustration of the e-periodica platform finally there is a summary of main concepts of the OAI-PMH protocol.

## 1. Metadata access with Polymatheia

The chapter introduces the *Polymatheia* library, which allows very convenient requests to the OAI interface by wrapping otherwise more elaborate code. Also, it offers methods to handle the retrieved data. Working with Polymatheia is an easy solution for quick access without going deep into coding. You might see the [documentation](https://polymatheia.readthedocs.io/en/latest/) of the Polymatheia library.

The chapter makes use of the following OAI verbs:
- oai: 'ListSets'
- oai: 'ListMetadataFormats'
- oai: 'ListRecords'.

Then, it shows **how to access certain metadata elements** and how to **save and recover the retrieved data**.

## 2. Direct metadata access via OAI-PMH

The *Polymatheia* library doesn't offer methods for *all* OAI verbs. For instance, there is no *ListIdentifiers* and no *GetRecord* wrapper. That's where more manual coding is needed. On the other hand accessing the e-periodica OAI-PMH directly gives you more freedom how to interact with the interface, naturally. You can use the functions without deeper programming skills - nevertheless these might be helpful if you want to adapt those functions for yourself.

The chapter makes use of the follwing OAI verbs:
- oai: 'Identify'
- oai: 'GetRecord'
- oai: 'ListIdentifiers'.

Therefore, it defines the following functions:
- **load_xml(params)**:

    Accesses the OAI interface according to given parameters and scrapes its content.
    
    Parameters:
    * All available native OAI verbs and parameter/value pairs.
    
- **download_record(ID, filename)**:

    Downloads a certain metadata record from OAI to a single XML file.
    Throws a notice if metadata file already exists and leaves the existing one.
    
    Parameters:
    * ID = E-periodica ID of the desired record.
    * filename = File name to choose for the downloaded record.
    
- **retrieve_set_metadata(Set, foldername, max_records=50)**:
   
    Downloads metadata records of a given set from OAI to XML files in a certain folder structure.
    Therefore it
    * creates a folder to hold the records
    * requests e-periodica OAI-PMH interface according to a set 
    * retrieves the set's e-periodica IDs
    * downloads Dublin Core metadata records according to IDs
    * writes them into single serially numbered XML files in the folder.
    
    Parameters:
    * Set = The desired OAI set.
    * foldername = name of the folder in which the records will be stored.
    * max_records = (Maximum) Number of records to retrieve. Default value is 50.
 
## 3. Download fulltext files from e-manuscripta website

Downloading e-periodica fulltetxts in PDF format can be done from the e-periodica website. When retrieving fulltext files of a given OAI set, the OAI-PMH interface will be used in addition.

The chapter defines the following functions:

- **download_fulltext(ID, filename)**:
    
    Downloads the PDF file of a certain e-periodica document by its ID.
    Builds with e-periodica ID the fulltext URL, and saves the PDF file on local disk.
    
    Parameters:
    * ID = E-periodica ID of the desired fulltext/PDF file.
    * filename = The file name to choose for the retrieved PDF file.
    
- **tech_metadata(pdf_path)**:
    
    Reads the technical metadata of a PDF formatted file and prints a summary.
    
    Parameter:
    * pdf_path = The path of the PDF file to be read.
    
- **read_pdf(pdf_path)**:
    
    Extracts the raw text of a PDF formatted file and prints it.
    Omits the first page of the PDF file, which is a cover sheet and not part of the article's genuine text.
    Uses *pdfplumber* library.
    
    Parameters:
    * pdf_path = The path of the PDF file to be read. 
    
- **pdf_to_txt(pdf_path)**:
   
    Extracts the raw text of a PDF formatted file and writes it into a TXT file of the same name (with
    '.txt' file extension respectively).
    Omits the first page of the PDF file, which is a cover sheet and not part of the article's genuine text.
    Uses *pdfplumber* library.
    
    Parameters:
    * pdf_path = The path of the PDF file to be read.   

- **read_pdf_tika(pdf_path)**:
    
    Extracts the raw text of a PDF formatted file with [Apache Tika](https://tika.apache.org/) and prints it.
    
    Parameters:
    * pdf_path = The path of the PDF file to be read.   
    
- **pdf_to_txt_tika(pdf_path)**:
    
    Extracts the raw text of a PDF formatted file with [Apache Tika](https://tika.apache.org/) and writes it into a
    TXT file of the same name (with '.txt' file extension respectively).
    
    Parameters:
    * pdf_path = The path of the PDF file to be read.   

- **retrieve_set_fulltexts(Set, foldername, max_fulltext=20)**:
    
    Downloads PDF fulltexts of a given DDC set from e-periodica website to files in a certain folder.
    Therefore it
    * creates the folder according to the parameter foldername
    * requests e-periodica OAI-PMH interface according to a OAI set 
    * retrieves the set's e-periodica IDs
    * downloads PDF fulltexts according to IDs from e-periodica website.
    
    Parameters:
    * Set = The desired OAI set.
    * foldername = name of the folder in which the fulltexts will be stored.
    * max_fulltext = (Maximum) Number of fulltexts to retrieve. Default value is 20.