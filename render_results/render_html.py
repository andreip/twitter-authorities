#!/usr/bin/env python

# Response from
# http://stackoverflow.com/questions/6748559/generating-html-documents-in-python

import os

from django.template import Template, Context, loader
from django.conf import settings

from helpers.mongo import get_min_max_timestamp

# We have to do this to use django templates standalone - see
# http://stackoverflow.com/questions/98135/how-do-i-use-django-templates-without-the-rest-of-django
settings.configure()

# Configure template path to this cwd.
path = os.path.dirname(os.path.realpath(__file__))
settings.TEMPLATE_DIRS += (
    path,
)

def render_html(keys, top, query, db):
    '''Given input, form a dict to pass to render_authorities_page.

    keys: list of strings that represent the headers of
          features frop top.
    top: list of tuple, where:
         * first is the username string
         * second is a numpy array of features (floats)
    query: query name used to generate data

    Need to form a dict of the form:
    'features':
        'user1':
            'TS': 0.012,
            'SS': 0.1,
            ...
    'doc': // a docstring with documentation
    '''
    from constants import UM, UF
    res = {}
    res['features'] = map(
        lambda (i, user): { user[0]: { a:b for (a,b) in zip(keys,user[1]) } }
        , enumerate(top)
    )
    res['metrics_doc'] = UM.__doc__
    res['features_doc'] = UF.__doc__
    res['query'] = query
    # Add min,max timestamp for HTML generation.
    res['min_t'], res['max_t'] = get_min_max_timestamp(query, db)
    render_authorities_page(res, query)

def render_authorities_page(context_dict, query):
    t = loader.get_template('template.html')
    c = Context(context_dict)
    html_output = t.render(c)
    filename = query + '.html'
    with open(filename, 'w') as f:
        f.write(html_output)
    print 'Created HTML output file', filename
