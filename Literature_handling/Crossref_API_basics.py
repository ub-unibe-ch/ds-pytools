#!/usr/bin/env python
# coding: utf-8

# # Crossref API basics 
# ##                                     using Crossref Commons and Habanero
# 
# Basic literature search in Crossref https://search.crossref.org using the Crossref-API. This is done using Crossref-Commons:
# 
# https://gitlab.com/crossref/crossref_commons_py
# 
# and the Habanero package:
# 
# https://habanero.readthedocs.io/en/latest/index.html
# 

# Required packages and installation (in addition to standard packages):
# 
#      pip install crossref-commons
#      
#      pip install habanero
#  

# #### Check python version and import general packages

# In[1]:


# Check python version for reproducibility and import general packages
import sys, os
print("Python version = ", sys.version)


# # 1. Crossref Commons
# 
# We start with the Crossref Commons packages and look at some basic functionality

# ### 1. 1 Crossref Common imports and setup
# 
# Import some Crossref Commons modules and set up your crossref user agent 

# In[2]:


# import required packages
import crossref_commons.retrieval
from crossref_commons.relations import get_related
from crossref_commons.iteration import iterate_publications_as_json


# Setting up the crossref user agent below is optional, but may help to get more reliable server responses

# In[3]:


# setup crossref user agent using environmental variables
os.environ['CR_API_AGENT'] = "polite user agent; including mailto:foo@bar.com"
os.environ.get('CR_API_AGENT')


# In[4]:


# setup crossref user agent using environmental variables
os.environ['CR_API_MAILTO'] = "foo@bar.com"
os.environ.get('CR_API_MAILTO')


# ### 1.2 Get reference details from DOI via CrossRef Commons
# 
# Use crossref to retrieve the details of a literature reference from its DOI. You can choose a DOI as input in the field below:

# In[5]:


# define DOI
doi_var = '10.1063/1.1699114'


# #### Retrieve bibliographic information in JSON format
# 
# We can retrieve the bibliographic information linked to this DOI in different formats. Here we choose the JSON format.

# In[6]:


# retrieve bibliographic information related to DOI
ref = crossref_commons.retrieval.get_publication_as_json( doi_var)


# In[7]:


# print result
print(ref)


# This is a lot of information! In order to access specific fields, we have a look at how the data is structured. The information is stored in a structure called 'dictionnary' which has 'keys' for each information field. We can easily find out which keys are used here:

# In[8]:


# get keys
ref.keys()


# Now we can get the information stored for each key.

# In[9]:


# get authors
ref['author']


# In[10]:


# get only first author
ref['author'][0]


# In[11]:


# get publication date
ref['published']


# This can now be repeated for other fields, depending on what information we need.

# ### 1.3 Iterate queries with filter options
# 
# Crossref allows to query specific information using different filter options. Crossref filters are described here:
# https://docs.ropensci.org/rcrossref/articles/crossref_filters.html

# #### Example 1): Filter for a specific funder defined by its funder ID and reference type 'journal-article'.

# In[12]:


# Define Filter
filter = {'funder': '10.13039/501100000038', 'type': 'journal-article'}


# Now we define a query for using this filter. We search for authors named 'muller' affiliated with a university.

# In[13]:


# Define query
queries = {'query.author': 'muller', 'query.affiliation': 'university'}


# In[14]:


# Now iterate over search results and print the DOI for each result
for p in iterate_publications_as_json(max_results=189, filter=filter, queries=queries):
  print(p['DOI'])


# #### Example 2): Filter for specific author defined by ORCID and journal articles
# 
# ORCID is a mechanism to unambiguosly identify an author. Authors can choose to create an ORCID which will then help to find their publications. In case you don't know the ORCID ID of the author your searching for (if it exists), you can directly search for the author name on the ORCID webpage: https://orcid.org.

# In[15]:


# Define another filter
filter = {'orcid': '0000-0003-4169-9324', 'type': 'journal-article'}


# In[16]:


# Define query; in this case we look for affiliations containing "Texas"
queries = {'query.affiliation': 'Texas', }


# In[17]:


# Do query and get results as DOI
for p in iterate_publications_as_json(max_results=189, filter=filter, queries=queries):
  print(p['DOI'])


# Theses were just some of the many query and filter options provided by Crossref Commons. For more options check the documentation page: https://gitlab.com/crossref/crossref_commons_py

# # 2. Habanero
# 
# In this second part we use the Habanero package to access the CrossRef API. Again we will just do some simple examples to show basic Habanero functionality

# ### 2.1 Habanero imports and setup
# 
# Import Habanero modules and set server communication variables

# #### Import Modules

# In[18]:


from habanero import Crossref


# In[19]:


from habanero import counts


# #### Server communication variables: set up user agent
# 
# This is again optional (see above).

# In[20]:


cr = Crossref()
# set a different base url
Crossref(base_url = "http://some.other.url")
# set an api key
Crossref(api_key = "123456")
# set a mailto address to get into the "polite pool"
Crossref(mailto = "foo@bar.com")
# set an additional user-agent string
Crossref(ua_string = "foo bar")


# ### 2.2  Citation counts
# 
# Get the number of citations for a given paper defined by its DOI from the CrossRef database.

# In[21]:


# define DOI of paper
doi_var = '10.1371/journal.pone.0042793'


# In[22]:


# get citation counts
print("number of citations = ", counts.citation_count(doi = doi_var))


# ### 2.3 Queries
# 
# Different query options can be found here: https://habanero.readthedocs.io/en/latest/modules/crossref.html Below two example queries are used to test some of the options.

# #### Example A: Query for a specific topic defined by keywords

# In[23]:


# define search topic
search_topic = "Gauge field theory"


# Now we do the querry for the defined seach topic, we limit the number of results we get to the 10 first results using the "limit" variable, and we filter for journal articles by defining 'type' as 'journal-article'.

# In[24]:


# do query 
test_query = cr.works(query = search_topic, limit=10, filter = {'type': 'journal-article'})


# In[25]:


# store main query result
query_result = test_query['message']


# In[26]:


# the query result is provided as a dictionary structure with different keys
query_result.keys()


# We had our query limited to the 10 first result, which is what we get as a result. However, we also got the informations how many results there are in total for this query in the database.

# In[27]:


# find out the total number of results in the database 
print("total results = ", query_result['total-results'])


# Now we look at our 10 results, again by using the keys of the dictionnary data structure.

# In[28]:


# the information we need is stored in the key "items", again in a dictionnary structure with keys:
query_result['items'][0].keys()


# We can look at each of the keys and list items separately. Here two examples:

# In[29]:


# look at the DOI of the first item
query_result['items'][0]['DOI']


# In[30]:


# look at the journal title of the third item
query_result['items'][2]['container-title']


# We can also make a list of all the 10 results, selecting some information fields to be displayed. Here we make a list of the 10 result with publisher, DOI, author list and title.

# In[31]:


# Display list with selected fields
for n, item in enumerate(query_result['items']):
    print(n, '\t Publisher =',  item['publisher'], ',\tDOI =', item['DOI'])
    print(item['author'])
    print(item['title'])
    print('---------------------------------------------------------------------------------------------------')


# #### Example B: Query for publications of a given author defined by name and ORCID
# 
# In the second query example, we look for the publication of a specific researcher which we define by his name and ORCID. In case you don't know the ORCID ID of the author your searching for (if it exists), you can directly search for the author name on the ORCID webpage: https://orcid.org.

# In[32]:


#Define author by Name and ORCID
author_name = "Walter Thiel"
author_orcid = "0000-0001-6780-0350"


# Now we do the query for the defined author. Instead of sorting by relevance (default), we have the results sorted by the number of times they are references. The query is limited to the first 5 items.

# In[33]:


# do query
test_query2 = cr.works(query_author = author_name, sort="is-referenced-by-count", limit=5, filter = {'orcid': author_orcid})


# In[34]:


# store result in query2_result variable and get total number of results
query2_result = test_query2['message']
print("total results = ", query2_result['total-results'])


# We can again display the results as a list. Here we choose to display the results with  publication date, author, title, journal name, volume, and issue information. In contrast to the list above, we only list authors given and family names, not the entire author field. This makes the list more readable.

# In[35]:


# display results as a list
for n, item in enumerate(query2_result['items']):
    print(n, '\t', 'publication date =', item['published']['date-parts'])
    authors = [[item['author'][x]['given']+" "+item['author'][x]['family']] for x in range(len(item['author']))]
    print(authors)
    print(item['title'])
    print(item['container-title'], " volume =", item['volume'], ", issue =", item['issue'])
    print('---------------------------------------------------------------------------------------------------')


# In[ ]:




