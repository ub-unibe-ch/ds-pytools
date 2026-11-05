#!/usr/bin/env python
# coding: utf-8

# # Using the Crossref REST API

# ## Table of contents
# 
# - [🎓 About Crossref](#about-crossref)
# - [📚 Works endpoint](#works-endpoint)
#   - [Check existence and registration agency](#check-existence-and-registration-agency)
#   - [Get citations and references in other formats](#get-citations-and-references-in-other-formats)
#   - [Search works with queries](#search-works-with-queries)
#     - [Match references with `query.bibliographic`](#match-references-with-query-bibliographic)
#   - [Filter works](#filter-works)
#     - [Select fields and get random samples](#select-fields-and-get-random-samples)
#   - [Facets: summary statistics](#facets-summary-statistics)
#   - [Retrieve large result sets with cursors](#retrieve-large-result-sets-with-cursors)
#   - [Corrections, retractions and other updates](#corrections-retractions-and-other-updates)
#   - [Relations between works](#relations-between-works)
# - [💶 Funders endpoint](#funders-endpoint)
# - [🏢 Members endpoint](#members-endpoint)
# - [📰 Journals endpoint](#journals-endpoint)
# - [🔢 Prefixes endpoint](#prefixes-endpoint)
# - [🏷️ Types endpoint](#types-endpoint)
# - [📜 Licenses endpoint](#licenses-endpoint)
# - [⚠️ Error handling and rate limits](#error-handling-and-rate-limits)
# - [🧰 Using a client library: Habanero](#using-a-client-library-habanero)

# <a id="about-crossref"></a>
# ## 🎓 About Crossref

# [Crossref](https://www.crossref.org/) is the largest **DOI registration agency** for scholarly content. Its members - publishers, universities, societies, funders - register **Digital Object Identifiers (DOIs)** for their publications and deposit the corresponding **metadata** with Crossref: titles, authors, ORCIDs, affiliations, references, funding information, licenses, links to full texts, corrections and retractions and much more. Today Crossref holds metadata on more than 180 million records: journal articles, books and chapters, conference papers, preprints, datasets, dissertations, reports, standards, peer reviews and even research grants.
# 
# Crossref makes this metadata **openly available** via its [REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) - free of charge and without registration. Crossref regards bibliographic metadata as facts which can be reused without restriction (please note that abstracts may remain subject to the publishers' copyright).
# 
# **💻 Endpoints**
# 
# Similar to other APIs for scholarly data, the Crossref REST API consists of different endpoints representing different kinds of entities:
# * `/works` - the registered content items (articles, books, chapters, datasets ...) - the heart of the API
# * `/funders` - funding organizations, based on the [Open Funder Registry](https://www.crossref.org/services/funder-registry/)
# * `/members` - the Crossref members, i.e. the organizations that register DOIs (mostly publishers)
# * `/journals` - journals and other serials, identified by their ISSN
# * `/prefixes` - the DOI prefixes (like `10.1063`) owned by members
# * `/types` - the content types used by Crossref
# * `/licenses` - the license URLs attached to works
# 
# Most of these endpoints can be combined with `/works`, e.g. `/funders/{id}/works` lists all works funded by a certain funder. An interactive overview of all endpoints and parameters is available in the [Swagger documentation](https://api.crossref.org/swagger-ui/index.html).
# 
# **📦 Three types of responses**
# 
# * **Singleton**: the metadata record of a single object, e.g. `https://api.crossref.org/works/10.1063/1.1699114`
# * **List**: the result of a query or filter, containing multiple items, e.g. `https://api.crossref.org/funders?query=swiss`
# * **Headers only**: an HTTP `HEAD` request just tells you whether an object exists (status code 200) or not (404)
# 
# **☝️ Caveat**
# 
# All metadata in Crossref is **deposited by its members**. Its completeness and quality therefore varies a lot between publishers, journals and time periods: some deposit abstracts, references, affiliations and ORCIDs, others only the bare minimum. Citation counts in Crossref (`is-referenced-by-count`) only count citations from other Crossref records whose references were deposited. **Handle all derivative numbers with care** and crosscheck your findings with other data sources like [OpenAlex](https://openalex.org/), if possible. You will learn below how to check the metadata coverage of members and journals.
# 
# **😇 Be polite and show who you are**
# 
# Crossref offers three "pools" of API access:
# * **Public pool**: anonymous requests
# * **Polite pool**: requests which contain a contact e-mail address, either as `mailto` parameter or in the `User-Agent` header. They get **higher rate limits** and more reliable response times.
# * **Plus pool**: for subscribers of the paid service [Metadata Plus](https://www.crossref.org/services/metadata-plus/), using an API token.
# 
# The rate limits were adjusted in 2025/2026 and are now differentiated by request type: requests for **single records** allow more requests per second than requests returning **lists** of records (queries, filters). The current limits are always given in the response headers `x-rate-limit-limit`, `x-rate-limit-interval` and `x-concurrency-limit` - we will look at them below. If you exceed the limits you will get the status code `429` (too many requests). So: **always provide your e-mail address**, send requests one after another (not in parallel) and pause shortly within loops.

# In[1]:


# Check Python version
import sys
print(sys.version)


# In[2]:


# Install necessary libraries if not already available
#!pip install requests pandas habanero


# In[3]:


# Import the necessary libraries
import json, os, re, time
import requests
import pandas as pd


# In[4]:


# IMPORTANT: Fill in your e-mail address to use the polite pool
# (or set it as environment variable CROSSREF_MAILTO)
email = os.environ.get('CROSSREF_MAILTO', 'your.name@example.org')


# We use a `requests.Session` for all requests: it reuses the connection to the server, which is faster, and allows us to set a descriptive `User-Agent` header once. Additionally, we pass our e-mail address as `mailto` parameter in every request.
# 
# We also tell the session to **automatically retry** a request a few times if the server answers with `429` (too many requests) or a server error (`5xx`), waiting a bit longer each time and respecting the `Retry-After` header of the server.

# In[5]:


base_url = 'https://api.crossref.org/'

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
session.headers.update({'User-Agent': f'ds-pytools Crossref tutorial (mailto:{email})'})

retry = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504], 
              allowed_methods=['GET', 'HEAD'], respect_retry_after_header=True)
session.mount('https://', HTTPAdapter(max_retries=retry))


# <a id="works-endpoint"></a>
# ## 📚 Works endpoint

# The `/works` endpoint gives access to the metadata of all registered content items. A single *Work* is retrieved by its **DOI**: `https://api.crossref.org/works/{doi}`. DOIs are case-insensitive and may contain characters like `/`, `(` or `;`; the `requests` library takes care of encoding them correctly.
# 
# As a first example we retrieve the famous paper by Metropolis et al. (1953), which introduced the Metropolis algorithm.

# In[6]:


doi = '10.1063/1.1699114'
#doi = '10.7554/elife.86663'               # open access article with license, full-text links and references
#doi = '10.1007/978-3-319-20319-5_4'       # book chapter

params = {'mailto': email}

r = session.get(base_url + 'works/' + doi, params=params)
print(r.status_code)
data = r.json()


# Each response of the API is a JSON object with the same envelope: a `status`, the `message-type` (e.g. `work` or `work-list`), the `message-version` and the actual content in `message`.

# In[7]:


# The response envelope
{key: data[key] for key in ['status', 'message-type', 'message-version']}


# In[8]:


# The work's metadata is found in "message" - an overview of the available fields
work = data['message']
list(work)


# Note that the available fields **depend on what the publisher deposited**: a field which is missing in one record may be present in another. Therefore it is good practice to access fields with `.get()`, which returns `None` (or a given default) instead of raising an error. Also note that some fields like `title` or `container-title` are **lists**, since a work can have several titles (e.g. in different languages).

# In[9]:


# Title, type, publisher and journal
print(work['title'])
print(work['type'])
print(work['publisher'])
print(work.get('container-title'), work.get('volume'), work.get('issue'), work.get('page'))


# In[10]:


# Authors with given and family name, sequence, affiliations and ORCID (if available)
work['author'][:2]


# In[11]:


# Print a readable author list
[f"{a.get('given', '')} {a.get('family', '')}" for a in work.get('author', [])]


# Crossref records contain several **dates**, each given as `date-parts` (year, month, day - as far as known):
# * `published-print` / `published-online`: the print and online publication dates
# * `published`: the earliest of both
# * `issued`: the earliest known publication date - the date to use for citations
# * `created`, `deposited`, `indexed`: when the DOI was registered, the metadata was last deposited and indexed by Crossref

# In[12]:


# Dates of the work
{key: work.get(key, {}).get('date-parts') for key in
 ['issued', 'published', 'published-print', 'published-online', 'created', 'deposited', 'indexed']}


# In[13]:


# Number of citations from other Crossref records and number of references of this work
print(work['is-referenced-by-count'])
print(work['references-count'])


# In[14]:


# The deposited references (if any) - some with DOI, some only as unstructured string
work.get('reference', [])[:2]


# In[15]:


# Member ID, DOI prefix and links to the work
print(work['member'], work['prefix'])
print(work['URL'])
print(work.get('resource'))


# Further information is available for many works - but not for all: `abstract`, `license`, `link` (links to the full text, e.g. for text and data mining), `funder` (with award numbers), `relation` (to other works) and `update-to`/`updated-by` (corrections and retractions, see below).
# 
# **Abstracts** are delivered in [JATS XML](https://jats.nlm.nih.gov/) format. A simple regular expression is enough to remove the tags for a quick look.

# In[16]:


# Abstract in JATS XML format - and as plain text
abstract = work.get('abstract', '')
print(abstract[:300])
print('---')
print(re.sub(r'<[^>]+>', ' ', abstract).split())


# In[17]:


# Licenses and full-text links (here for an open access article from eLife)
r = session.get(base_url + 'works/10.7554/elife.86663', params=params)
elife = r.json()['message']

print(elife.get('license'))
elife.get('link')


# <a id="check-existence-and-registration-agency"></a>
# ### Check existence and registration agency

# Not every DOI is registered with Crossref: there are other registration agencies, especially [DataCite](https://datacite.org/), which registers DOIs for research data, software and repository content (e.g. Zenodo). If a DOI is unknown to Crossref, you will get the status code `404`.
# 
# To check whether a DOI exists **without downloading its metadata**, use an HTTP `HEAD` request. And the special route `/works/{doi}/agency` tells you **which agency registered a DOI**.

# In[18]:


# HEAD request: 200 = exists in Crossref, 404 = unknown to Crossref
for d in ['10.1063/1.1699114', '10.5281/zenodo.3242074', '10.9999/does-not-exist']:
    r = session.head(base_url + 'works/' + d, params=params)
    print(d, r.status_code)


# In[19]:


# Find out the registration agency of a DOI
for d in ['10.1063/1.1699114', '10.5281/zenodo.3242074']:
    r = session.get(base_url + 'works/' + d + '/agency', params=params)
    print(d, r.json()['message']['agency'])


# <a id="get-citations-and-references-in-other-formats"></a>
# ### Get citations and references in other formats

# Crossref can deliver the metadata of a single work in other formats: **BibTeX** or **RIS** for reference managers, **CSL JSON** for citation processors, or a **formatted citation** in one of the many [citation styles](https://citationstyles.org/). The general way to do this is [content negotiation](https://www.crossref.org/documentation/retrieve-metadata/content-negotiation/) at `https://doi.org/{doi}` with a corresponding `Accept` header, which works for Crossref and DataCite DOIs:
# 
#     requests.get('https://doi.org/10.1063/1.1699114', headers={'Accept': 'application/x-bibtex'})
# 
# The Crossref REST API offers the same functionality for Crossref DOIs with the route `/works/{doi}/transform/{format}`.

# In[20]:


# BibTeX
r = session.get(base_url + 'works/' + doi + '/transform/application/x-bibtex', params=params)
r.encoding = 'utf-8'       # the server does not always declare the character encoding correctly
print(r.text)


# In[21]:


# RIS
r = session.get(base_url + 'works/' + doi + '/transform/application/x-research-info-systems', params=params)
r.encoding = 'utf-8'
print(r.text)


# In[22]:


# Formatted citation: choose the citation style in the Accept header, e.g. apa, harvard-cite-them-right, ieee, nature
for style in ['apa', 'ieee', 'nature']:
    r = session.get(base_url + 'works/' + doi + '/transform',
                    params=params, headers={'Accept': f'text/x-bibliography; style={style}'})
    r.encoding = 'utf-8'
    print(style, ':', r.text)


# <a id="search-works-with-queries"></a>
# ### Search works with queries

# Instead of retrieving a single work, you can **search** the `/works` endpoint. The result is a **list** of works, sorted by **relevance** (`score`). There are two kinds of queries:
# 
# * `query` searches all fields of the metadata records
# * **field queries** search only certain fields: `query.bibliographic` (all fields used for citations: title, authors, journal, year, volume, pages ...), `query.author`, `query.editor`, `query.affiliation`, `query.container-title`, `query.title`, `query.publisher-name`, `query.funder-name` and some more. They can be combined.
# 
# Please note: queries are **not** a precise boolean search - the terms are weighted and the results ranked by relevance. To select works exactly by certain criteria use **filters** (next section).

# In[23]:


url = base_url + 'works'
params = {'mailto': email,
          'query': 'gauge field theory',
          'rows': 10}

r = session.get(url, params=params)
data = r.json()


# In[24]:


# A list response contains some general information and the "items"
print(list(data['message']))
print('total results =', data['message']['total-results'])
print('items per page =', data['message']['items-per-page'])


# In[25]:


# The 10 most relevant results with score, DOI and title
for item in data['message']['items']:
    print(round(item['score'], 1), item['DOI'], item.get('title'))


# In[26]:


# Combine field queries: works by an author named "Thiel" with "Mülheim" in the affiliation
params = {'mailto': email,
          'query.author': 'Walter Thiel',
          'query.affiliation': 'Mülheim',
          'rows': 5}

r = session.get(url, params=params)
data = r.json()
print('total results =', data['message']['total-results'])

for item in data['message']['items']:
    print(item['DOI'], item.get('title'), [a.get('family') for a in item.get('author', [])])


# <a id="match-references-with-query-bibliographic"></a>
# #### Match references with `query.bibliographic`
# 
# A very useful application of `query.bibliographic` is **reference matching**: finding the DOI for a reference given as plain text, e.g. from a reference list. Look at the `score` and compare the top results - the first hit is not always the work you are looking for! In the example below the first result is a technical report with the same title, published by the same authors before the journal article.

# In[27]:


reference = 'Metropolis N, Rosenbluth AW, Rosenbluth MN, Teller AH, Teller E (1953) Equation of state calculations by fast computing machines. J Chem Phys 21:1087'

params = {'mailto': email,
          'query.bibliographic': reference,
          'rows': 3}

r = session.get(url, params=params)
for item in r.json()['message']['items']:
    print(round(item['score'], 1), item['DOI'], item['type'], item.get('container-title'), item.get('title'))


# <a id="filter-works"></a>
# ### Filter works

# **Filters** select works exactly by certain criteria. They are given in the `filter` parameter as `name:value` pairs, separated by commas. There are more than 100 filters for works, e.g.:
# 
# | Filter | Description |
# |---|---|
# | `type:journal-article` | content type (see `/types` endpoint below) |
# | `from-pub-date:2024-01-01`, `until-pub-date:2024-12-31` | publication date range (also `-created-`, `-deposit-`, `-update-`, `-index-`, `-online-pub-`, `-print-pub-` dates) |
# | `funder:10.13039/501100001711` | funded by a certain funder (Funder ID) |
# | `orcid:0000-0001-6780-0350` | contributions of an author (ORCID) |
# | `ror-id:02k7v4d05` | affiliation with an institution ([ROR](https://ror.org/) ID) |
# | `issn:0028-0836`, `member:311`, `prefix:10.1063` | journal, member, DOI prefix |
# | `has-abstract:true`, `has-references:true`, `has-orcid:true`, `has-funder:true`, `has-license:true`, `has-full-text:true` | availability of certain metadata |
# | `license.url:...`, `license.delay:0` | license URL, embargo in days |
# | `update-type:retraction`, `updates:{doi}`, `is-update:true` | corrections, retractions etc. |
# | `relation.type:is-preprint-of` | relations between works |
# | `award.number:...`, `clinical-trial-number:...` | grant and clinical trial numbers |
# 
# The complete list is in the [filter documentation](https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-filters/). A useful trick: if you use an invalid filter name, the error message lists all valid filters (see "Error handling" at the end).
# 
# Different filters are combined with **AND**; the same filter repeated with different values is combined with **OR**.

# In[28]:


# Journal articles funded by the Swiss National Science Foundation (SNSF), published in 2025
params = {'mailto': email,
          'filter': 'funder:10.13039/501100001711,type:journal-article,from-pub-date:2025-01-01,until-pub-date:2025-12-31',
          'rows': 5}

r = session.get(url, params=params)
data = r.json()
print('total results =', data['message']['total-results'])

for item in data['message']['items']:
    print(item['DOI'], item.get('container-title'), item.get('title'))


# In[29]:


# The same filter with different values means OR: books or monographs
for f in ['type:book', 'type:monograph', 'type:book,type:monograph']:
    r = session.get(url, params={'mailto': email, 'filter': f, 'rows': 0})
    print(f, r.json()['message']['total-results'])


# Note the parameter `rows=0` in the last cell: it returns **no items, only the number of results** - a fast and cheap way to count.
# 
# Filters and queries can be combined, of course. In the next example we look for works of a certain author identified by ORCID and sort them by the number of citations, using the parameters `sort` and `order`. Possible sort fields are `relevance` (default for queries), `score`, `published`, `issued`, `created`, `updated`, `deposited`, `indexed`, `is-referenced-by-count` and `references-count`.

# In[30]:


# The most cited works of Walter Thiel (ORCID 0000-0001-6780-0350)
params = {'mailto': email,
          'filter': 'orcid:0000-0001-6780-0350',
          'sort': 'is-referenced-by-count',
          'order': 'desc',
          'rows': 5}

r = session.get(url, params=params)
data = r.json()
print('total results =', data['message']['total-results'])

for item in data['message']['items']:
    print(item['is-referenced-by-count'], item['issued']['date-parts'], item.get('container-title'), item.get('title'))


# <a id="select-fields-and-get-random-samples"></a>
# #### Select fields and get random samples
# 
# Full metadata records can be large - especially due to reference lists. With the `select` parameter you can choose the fields you need, which makes responses much smaller and faster. The `sample` parameter returns a **random sample** of up to 100 works - useful for statistical analyses of metadata quality.

# In[31]:


# A random sample of 5 works with only some selected fields
params = {'mailto': email,
          'sample': 5,
          'select': 'DOI,type,issued,title,publisher'}

r = session.get(url, params=params)
r.json()['message']['items']


# In[32]:


# Combine filter, sample and select: a random sample of 20 journal articles published in 2025.
# How many of them have an abstract, references or ORCIDs?
params = {'mailto': email,
          'filter': 'type:journal-article,from-pub-date:2025-01-01,until-pub-date:2025-12-31',
          'sample': 20,
          'select': 'DOI,abstract,reference,author'}

r = session.get(url, params=params)
items = r.json()['message']['items']

print('with abstract:  ', sum('abstract' in i for i in items))
print('with references:', sum('reference' in i for i in items))
print('with ORCIDs:    ', sum(any('ORCID' in a for a in i.get('author', [])) for i in items))


# <a id="facets-summary-statistics"></a>
# ### Facets: summary statistics

# **Facets** give you summary statistics of a result set without downloading the records - similar to the `group_by` parameter of OpenAlex. Use the parameter `facet` with the name of the facet and the maximum number of values (up to 1000, `*` for the maximum). Available facets are e.g. `type-name`, `published` (year), `publisher-name`, `container-title`, `funder-name`, `affiliation`, `ror-id`, `license`, `orcid`, `issn`, `update-type`, `relation-type` and `category-name`. Several facets can be requested at once, separated by commas.
# 
# Note that facet counts are approximate. Combined with `rows=0`, facets are a very efficient tool for bibliometric overviews.

# In[33]:


# All works in Crossref by content type
params = {'mailto': email,
          'facet': 'type-name:*',
          'rows': 0}

r = session.get(url, params=params)
data = r.json()
print('total results =', data['message']['total-results'])
data['message']['facets']['type-name']['values']


# In the next example we combine a **filter** for works affiliated with the *University of Bern* (ROR ID `02k7v4d05`) with several facets. Please note that only works with ROR IDs in their affiliation metadata are found - a quite recent and not yet common practice of publishers. So this is by far not the complete output of the University of Bern!

# In[34]:


params = {'mailto': email,
          'filter': 'ror-id:02k7v4d05',
          'facet': 'published:*,publisher-name:10,type-name:*',
          'rows': 0}

r = session.get(url, params=params)
data = r.json()
print('total results =', data['message']['total-results'])
facets = data['message']['facets']


# In[35]:


# Publications per year, sorted by year
sorted(facets['published']['values'].items(), reverse=True)[:10]


# In[36]:


# The 10 most frequent publishers and the content types
print(facets['publisher-name']['values'])
print(facets['type-name']['values'])


# <a id="retrieve-large-result-sets-with-cursors"></a>
# ### Retrieve large result sets with cursors

# A single request returns at most **1000 items** (`rows`). To get more results, there are two options:
# * `offset`: skip the first *n* results - limited to 10,000 results in total
# * `cursor`: **deep paging** without limits. Start with `cursor=*`; every response contains a `next-cursor` value which you pass on in the next request. Stop when a page contains fewer items than requested. Cursors expire after 5 minutes.
# 
# Crossref recommends using cursors. In the example we retrieve all works affiliated with the University of Bern (via ROR ID) published since 2024, selecting only a few fields, and put them into a pandas dataframe. Note the short pause within the loop to respect the rate limits.

# In[37]:


results = []
cursor = '*'
rows = 200

while True:
    params = {'mailto': email,
              'filter': 'ror-id:02k7v4d05,from-pub-date:2024-01-01',
              'select': 'DOI,type,issued,title,container-title,publisher,is-referenced-by-count',
              'rows': rows,
              'cursor': cursor}
    r = session.get(url, params=params)
    message = r.json()['message']
    results.extend(message['items'])
    print(len(results), 'of', message['total-results'])
    if len(message['items']) < rows:
        break
    cursor = message['next-cursor']
    time.sleep(0.5)


# In[38]:


# Transform the selected fields into a dataframe
df = pd.DataFrame({
    'doi': [i['DOI'] for i in results],
    'type': [i['type'] for i in results],
    'year': [i['issued']['date-parts'][0][0] for i in results],
    'title': [i.get('title', [None])[0] for i in results],
    'container': [(i.get('container-title') or [None])[0] for i in results],
    'publisher': [i.get('publisher') for i in results],
    'cited_by': [i.get('is-referenced-by-count') for i in results]})
df.head(10)


# In[39]:


# Number of works per year and type
df.groupby(['year', 'type']).size()


# In[40]:


# The 5 most cited works in this set
df.sort_values('cited_by', ascending=False).head(5)


# <a id="corrections-retractions-and-other-updates"></a>
# ### Corrections, retractions and other updates

# Publications can be **updated** after publication by corrections, errata, retractions, expressions of concern etc. Crossref records these updates in two directions:
# * the **update notice** (e.g. a retraction notice) has the field `update-to`, pointing to the original work
# * the **updated work** has the field `updated-by`, pointing to the notice
# 
# Crossref acquired the [Retraction Watch](https://retractionwatch.com/) database in 2023 and integrates its data into the API, so retractions are covered even if the publisher did not deposit them. The `source` attribute tells you whether an update was asserted by the `publisher` or by `retraction-watch`. This is especially valuable to **check reference lists for retracted works**.

# In[41]:


# How many updates of which kind are there?
params = {'mailto': email,
          'facet': 'update-type:10',
          'rows': 0}

r = session.get(url, params=params)
r.json()['message']['facets']['update-type']['values']


# In[42]:


# A retracted work and its retraction notice
r = session.get(base_url + 'works/10.1177/1758835919874651', params={'mailto': email})
retracted = r.json()['message']

print(retracted['title'])
retracted.get('updated-by')


# In[43]:


# Find all update notices for a given DOI with the "updates" filter
params = {'mailto': email,
          'filter': 'updates:10.1177/1758835919874651'}

r = session.get(url, params=params)
for item in r.json()['message']['items']:
    print(item['DOI'], item.get('title'), [(u['type'], u['source']) for u in item['update-to']])


# In[44]:


# A simple check: are there retracted works among a list of DOIs (e.g. from your reference list)?
dois = ['10.1063/1.1699114', '10.1177/1758835919874651', '10.7554/elife.86663']

for d in dois:
    r = session.get(base_url + 'works/' + d, params={'mailto': email})
    updates = [u['type'] for u in r.json()['message'].get('updated-by', [])]
    print(d, '- RETRACTED' if 'retraction' in updates else '- ok', updates)
    time.sleep(0.2)


# <a id="relations-between-works"></a>
# ### Relations between works

# The field `relation` connects works with each other, e.g. a preprint with its published version (`is-preprint-of` / `has-preprint`), a peer review with the reviewed article (`is-review-of`), translations, versions, supplements or comments. Relations can also point to non-DOI identifiers. Let's look at the most frequent relation types and an example.

# In[45]:


params = {'mailto': email,
          'facet': 'relation-type:15',
          'rows': 0}

r = session.get(url, params=params)
r.json()['message']['facets']['relation-type']['values']


# In[46]:


# Preprints with a link to their published version
params = {'mailto': email,
          'filter': 'relation.type:is-preprint-of,from-pub-date:2025-01-01',
          'select': 'DOI,type,title,relation',
          'rows': 3}

r = session.get(url, params=params)
r.json()['message']['items']


# <a id="funders-endpoint"></a>
# ## 💶 Funders endpoint

# Funders are identified by their **Funder ID** from the [Open Funder Registry](https://www.crossref.org/services/funder-registry/) - a DOI with the prefix `10.13039`, e.g. `10.13039/501100001711` for the Swiss National Science Foundation (SNSF). In the `/funders` endpoint, only the second part (`501100001711`) is used. Funders can be searched with `query` and filtered by `location`. (Please note that Crossref is gradually moving from Funder IDs to [ROR IDs](https://ror.org/) for funders.)

# In[47]:


# Search for funders
params = {'mailto': email,
          'query': 'swiss national science foundation'}

r = session.get(base_url + 'funders', params=params)
[[i['id'], i['name'], i['location']] for i in r.json()['message']['items']]


# In[48]:


# How many funders are located in Switzerland?
params = {'mailto': email,
          'filter': 'location:Switzerland',
          'rows': 10}

r = session.get(base_url + 'funders', params=params)
data = r.json()
print('total results =', data['message']['total-results'])
[i['name'] for i in data['message']['items']]


# In[49]:


# A single funder: names, hierarchy and number of funded works
r = session.get(base_url + 'funders/501100001711', params={'mailto': email})
funder = r.json()['message']

print(list(funder))
print(funder['name'])
print(funder['alt-names'])
print(funder['work-count'], funder['descendant-work-count'])


# In[50]:


# Sub-units of the funder (e.g. National Centres of Competence in Research)
list(funder['hierarchy-names'].values())


# In[51]:


# Works funded by the SNSF: published per year and by type, using facets
params = {'mailto': email,
          'facet': 'published:*,type-name:*',
          'rows': 0}

r = session.get(base_url + 'funders/501100001711/works', params=params)
facets = r.json()['message']['facets']
print(sorted(facets['published']['values'].items(), reverse=True)[:10])
facets['type-name']['values']


# <a id="members-endpoint"></a>
# ## 🏢 Members endpoint

# **Members** are the organizations registering DOIs with Crossref - mostly publishers, but also universities, libraries, societies and funders. Each member has a numeric ID, one or more DOI prefixes, and statistics about its registered content. Especially interesting: the `coverage` information, telling you **how complete the deposited metadata** of a member is (share of records with abstracts, references, ORCIDs, licenses, funders, affiliations ...).

# In[52]:


# Search for members
params = {'mailto': email,
          'query': 'university of bern'}

r = session.get(base_url + 'members', params=params)
[[i['id'], i['primary-name'], i['counts']['total-dois']] for i in r.json()['message']['items']]


# In[53]:


# A single member: Wiley (member ID 311)
r = session.get(base_url + 'members/311', params={'mailto': email})
member = r.json()['message']

print(list(member))
print(member['primary-name'], '-', member['location'])
print(member['counts'])
print(len(member['prefixes']), 'prefixes, e.g.', member['prefixes'][:5])


# The `coverage` attributes are given separately for **current** content (published in the current and the two previous years) and **backfile** content (older). Let's compare the metadata coverage of two members in a dataframe.

# In[54]:


coverage = {}
for member_id in [311, 22676]:     # Wiley and University of Bern
    r = session.get(base_url + f'members/{member_id}', params={'mailto': email})
    m = r.json()['message']
    coverage[m['primary-name']] = {k.replace('-current', ''): round(v, 2) for k, v in m['coverage'].items()
                                   if k.endswith('-current')}
    time.sleep(0.5)

pd.DataFrame(coverage)


# In[55]:


# Works of a member can be accessed via /members/{id}/works - here: the content types of the University of Bern's DOIs
params = {'mailto': email,
          'facet': 'type-name:*',
          'rows': 0}

r = session.get(base_url + 'members/22676/works', params=params)
data = r.json()
print('total results =', data['message']['total-results'])
data['message']['facets']['type-name']['values']


# <a id="journals-endpoint"></a>
# ## 📰 Journals endpoint

# Journals are identified by their [ISSN](https://www.issn.org/) (print or electronic). The `/journals` endpoint provides information on the publisher, subjects, the number of DOIs per year and - again - the metadata coverage. Journals can be searched by title with `query`.

# In[56]:


# Search for journals
params = {'mailto': email,
          'query': 'digital humanities',
          'rows': 10}

r = session.get(base_url + 'journals', params=params)
[[i['title'], i['publisher'], i['ISSN']] for i in r.json()['message']['items']]


# In[57]:


# A single journal: Nature
r = session.get(base_url + 'journals/0028-0836', params={'mailto': email})
journal = r.json()['message']

print(list(journal))
print(journal['title'], '-', journal['publisher'])
print(journal['issn-type'])
print(journal['counts'])


# In[58]:


# Metadata coverage of the journal's current content
journal['coverage-type']['current']


# In[59]:


# Number of DOIs per publication year as dataframe
df_years = pd.DataFrame(journal['breakdowns']['dois-by-issued-year'], columns=['year', 'dois']).sort_values('year')
df_years.tail(10)


# In[60]:


# The 5 most cited Nature articles published since 2020
params = {'mailto': email,
          'filter': 'from-pub-date:2020-01-01,type:journal-article',
          'sort': 'is-referenced-by-count',
          'select': 'DOI,title,issued,is-referenced-by-count',
          'rows': 5}

r = session.get(base_url + 'journals/0028-0836/works', params=params)
[[i['is-referenced-by-count'], i['DOI'], i['title']] for i in r.json()['message']['items']]


# <a id="prefixes-endpoint"></a>
# ## 🔢 Prefixes endpoint

# Every DOI starts with a **prefix** (the part before the first `/`), which belongs to a Crossref member. The `/prefixes` endpoint tells you the owner of a prefix, and `/prefixes/{prefix}/works` gives access to all works registered with it.

# In[61]:


r = session.get(base_url + 'prefixes/10.1063', params={'mailto': email})
r.json()['message']


# In[62]:


# Number of works registered with this prefix, by type
params = {'mailto': email,
          'facet': 'type-name:*',
          'rows': 0}

r = session.get(base_url + 'prefixes/10.1063/works', params=params)
data = r.json()
print('total results =', data['message']['total-results'])
data['message']['facets']['type-name']['values']


# <a id="types-endpoint"></a>
# ## 🏷️ Types endpoint

# The `/types` endpoint lists all **content types** used by Crossref. Their `id` is used in the `type` filter, e.g. `type:posted-content` for preprints. Note that OpenAlex uses its own list of types, so types are not directly comparable between both sources.

# In[63]:


r = session.get(base_url + 'types', params={'mailto': email})
[[i['id'], i['label']] for i in r.json()['message']['items']]


# In[64]:


# Number of dissertations registered with Crossref, by publisher
params = {'mailto': email,
          'facet': 'publisher-name:10',
          'rows': 0}

r = session.get(base_url + 'types/dissertation/works', params=params)
data = r.json()
print('total results =', data['message']['total-results'])
data['message']['facets']['publisher-name']['values']


# <a id="licenses-endpoint"></a>
# ## 📜 Licenses endpoint

# Many members deposit **license information** for their works - e.g. Creative Commons licenses for open access publications or text and data mining licenses. The `/licenses` endpoint lists the license URLs with the number of works using them. As the URLs are deposited by the members, you will find many variants of the same license (`http`/`https`, with or without `legalcode`, different spellings ...). So, when filtering works by `license.url`, consider the different variants.

# In[65]:


params = {'mailto': email,
          'query': 'creativecommons.org/licenses/by/4.0',
          'rows': 10}

r = session.get(base_url + 'licenses', params=params)
data = r.json()
print('total results =', data['message']['total-results'])
data['message']['items']


# In[66]:


# The most frequent licenses of works published in 2025, via facet
params = {'mailto': email,
          'filter': 'from-pub-date:2025-01-01,until-pub-date:2025-12-31',
          'facet': 'license:10',
          'rows': 0}

r = session.get(url, params=params)
r.json()['message']['facets']['license']['values']


# <a id="error-handling-and-rate-limits"></a>
# ## ⚠️ Error handling and rate limits

# Always check the **status code** of a response before processing it:
# * `200`: success
# * `400`: invalid request, e.g. a wrong filter or parameter name - the response explains the error
# * `404`: the requested object does not exist (e.g. a DOI not registered with Crossref)
# * `429`: too many requests - slow down (see the `Retry-After` header)
# * `5xx`: server error - try again later, see the [status page](https://status.crossref.org/)
# 
# The error message of an invalid parameter is quite helpful, since it lists all valid values.

# In[67]:


# An invalid filter name returns status 400 and a list of all valid filters
r = session.get(url, params={'mailto': email, 'filter': 'foo:bar', 'rows': 0})
print(r.status_code)
print(r.json()['message'][0]['message'][:600], '...')


# In[68]:


# The same works for facets, sort fields, field queries and select fields
r = session.get(url, params={'mailto': email, 'facet': 'foo:5', 'rows': 0})
print(r.json()['message'][0]['message'])


# In[69]:


# The current rate limits are given in the response headers - compare single records and lists
for path, p in [('works/10.1063/1.1699114', {}), ('works', {'query': 'test', 'rows': 0})]:
    r = session.get(base_url + path, params={'mailto': email, **p})
    print(path, {k: v for k, v in r.headers.items() if k.lower().startswith(('x-rate-limit', 'x-concurrency', 'x-api-pool'))})


# The automatic retries of our session (see setup at the beginning) already handle `429` and server errors. If you do not use such a session, a small helper function does the same job: it pauses and retries if the server answers with `429` or a server error.

# In[70]:


def get_crossref(path, params=None, retries=3):
    """Request the Crossref REST API, retrying on rate limit and server errors."""
    params = {'mailto': email, **(params or {})}
    for attempt in range(retries):
        r = session.get(base_url + path, params=params)
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(int(r.headers.get('Retry-After', 2 ** attempt)))
            continue
        r.raise_for_status()
        return r.json()['message']
    r.raise_for_status()

get_crossref('works', {'query.bibliographic': 'Einstein 1905 Zur Elektrodynamik bewegter Körper', 'rows': 1,
                       'select': 'DOI,title,score'})


# <a id="using-a-client-library-habanero"></a>
# ## 🧰 Using a client library: Habanero

# Instead of writing all requests yourself, you can use a client library. For Python, [Habanero](https://habanero.readthedocs.io/) is well maintained and covers all endpoints of the REST API. It handles parameters, cursors and errors for you. (The formerly used library [crossref-commons](https://gitlab.com/crossref/crossref_commons_py) is no longer maintained.)
# 
#     pip install habanero

# In[71]:


from habanero import Crossref

# Set your e-mail address to use the polite pool, and a user agent string
cr = Crossref(mailto=email, ua_string='ds-pytools Crossref tutorial')
cr


# In[72]:


# Single work by DOI
cr.works(ids='10.1063/1.1699114')['message']['title']


# In[73]:


# Query with filter, sorting, selection and limit - the parameters are the same as in the REST API
res = cr.works(query='gauge field theory', filter={'type': 'journal-article', 'from_pub_date': '2020'},
               sort='is-referenced-by-count', select=['DOI', 'title', 'is-referenced-by-count'], limit=5)
[[i['is-referenced-by-count'], i['DOI'], i['title']] for i in res['message']['items']]


# In[74]:


# Deep paging with cursor: Habanero collects the pages for you (here: max. 300 items)
res = cr.works(filter={'ror_id': '02k7v4d05', 'from_pub_date': '2024'}, select=['DOI'],
               cursor='*', cursor_max=300, limit=100)
print(len(res), 'pages')
print(sum(len(page['message']['items']) for page in res), 'items')


# In[75]:


# Other endpoints: funders, members, journals, prefixes, types, licenses
print(cr.funders(query='swiss national science foundation')['message']['items'][0]['name'])
print(cr.members(ids=311)['message']['primary-name'])
print(cr.journals(ids='0028-0836')['message']['title'])
print(cr.prefixes(ids='10.1063')['message']['name'])


# In[76]:


# Works of a funder, member, journal etc. with works=True
res = cr.funders(ids='501100001711', works=True, limit=3, select=['DOI', 'title'])
res['message']['items']


# Habanero also provides content negotiation via `https://doi.org` (`from habanero import cn`):
# 
#     from habanero import cn
#     cn.content_negotiation(ids='10.1063/1.1699114', format='bibentry')               # BibTeX
#     cn.content_negotiation(ids='10.1063/1.1699114', format='text', style='apa')      # formatted citation
# 
# More examples are in the [Habanero documentation](https://habanero.readthedocs.io/en/latest/).
