import string
from functools import wraps
import urllib

from werkzeug.contrib.cache import MemcachedCache
cache = MemcachedCache(['127.0.0.1:11922'])


class MyFancyOpener(urllib.FancyURLopener):
    version = 'Mozilla/4.0 (compatible; name-that-actor-or-movie)'
class MyOpener(urllib.URLopener):
    version = 'Mozilla/4.0 (compatible; name-that-actor-or-movie)'

def retrieve(url, data=None, opener=MyFancyOpener()):
    print 'GET' if not data else 'POST',
    print url
    try:
        return opener.open(url, *(data or ())).read()
    except IOError:
        return 'Timeout Error'

def get_headers(url, data=None):
    try:
        MyOpener().open(url, *(data or ()))
    except IOError, e:
        err, code, status, httpmsg = e.args
        
        return dict(h.split(':',1) for h in httpmsg.headers)
        
def get_redir(url, data=None):
    hds = get_headers(url, data)
    if not hds:
        return None
    return hds.get('Location')


def cache_this(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        search = args[-1].replace(' ', '-')
        search = ''.join(ch for ch in search if ch in string.letters)
        name = func.func_name + '-' + search
        res = cache.get(name)
        if res is None:
            #print 'cache: miss', name
            res = func(*args, **kwargs)
            cache.set(name, res)
        else:
            #print 'cache hit:', name
            pass
        return res
    return wrapper


