#!/usr/bin/env python
import urllib
import re
import pyquery
from flask import Flask, render_template, request
app = Flask(__name__)

from wtforms import Form, TextField 

from util import retrieve, get_redir, cache_this

class MovorForm(Form):
    """
    A couple of Movies and/or Actors to cross match
    """
    movor1 = TextField('Movie or Actor')
    movor2 = TextField('Movie or Actor')

AC_re = re.compile(r'/name/nm\d{1,9}/')
MV_re = re.compile(r'/title/tt\d{1,9}/')
TITLE_re = re.compile('<title>([^<]+) - IMDb<\/title>', re.I)

class Movor(object):
    @property
    def typ(self):
        return 'Actor' if self.is_ac else 'Movie'


class Namer(object):

    def __init__(self, m1, m2):
        self.m1 = m1.strip()
        self.m2 = m2.strip()

    def get_ctx(self):
        ms = filter(None, (self.m1, self.m2))
        n = len(ms)
        ctx = {'n': n,
               'm2':None,
            }
        if n == 2:
            ctx.update(self.get_cross(*ms))
            ctx['links'] = dict(ctx['m1'].links.items() + ctx['m2'].links.items())
        if n == 1:
            ctx['m1'] = self.get_credits(ms[0])
            #ctx['links'] = 
        return ctx

    @cache_this
    def get_credits(self, search):
        GOOG = 'http://www.google.com/search?btnI=1&q=site:imdb.com/name/+OR+site:imdb.com/title/+'
        url = get_redir(GOOG + urllib.quote(search))
        if url is None:
            return 
        m = Movor()
        m.is_ac = '/name/nm' in url
        page = retrieve(url)
        m.url = url
        m.title = (TITLE_re.findall(page) or ['Unknown'])[0]
        if m.is_ac:
            m.creds = set(MV_re.findall(page))
            m.own_cred = AC_re.findall(url)[0]
        else:
            m.creds = set(AC_re.findall(page))
            m.own_cred = MV_re.findall(url)[0]
        p = pyquery.PyQuery(page)
        atags = p.find('a')
        m.links = dict((c, atags.filter('[href*="%s"]' % c).text()) for c in m.creds)
        return m

    def get_cross(self, search1, search2):
        m1 = self.get_credits(search1)
        m2 = self.get_credits(search2)
        
        if m1.is_ac != m2.is_ac:
            # see if this actor was in this movie or visa versa
            # | is set union
            cross = (
                    (set((m1.own_cred,)) & m2.creds) |
                    (set((m2.own_cred,)) & m1.creds)
                   )
        else:
            # find common credits from these two moviews or two actors
            # & = set intersection
            cross = m1.creds & m2.creds
        return {'m1': m1, 'm2': m2, 'cross': cross}
    
@app.route('/')
def home():
    form = MovorForm(request.values)
    if form.validate():
        namer = Namer(form.movor1.data or '', form.movor2.data or '')
        ctx = namer.get_ctx()
    return render_template('namer.html', form=form, **ctx)


if __name__ == '__main__':
    import sys
    port = 80
    if sys.argv[1:] and sys.argv[1]:
        port = int(sys.argv[1])
    app.run(debug=0, port=port)
