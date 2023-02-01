# %%
import json
from urllib.parse import urljoin
import requests
import urllib3
import ssl
import lxml.html
import pandas as pd

# %%
# PSP si neumi vyresit TLS na webu :/
# https://stackoverflow.com/questions/71603314/ssl-error-unsafe-legacy-renegotiation-disabled
class CustomHttpAdapter (requests.adapters.HTTPAdapter):
    # 'Transport adapter' that allows us to use custom ssl_context.

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)

def get_legacy_session():
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount('https://', CustomHttpAdapter(ctx))
    return session

# %%
base_url = 'https://www.psp.cz/sqw/hp.sqw?k=192'
r = get_legacy_session().get(base_url)
# %%
data = []
ht = lxml.html.fromstring(r.text)
for link in ht.cssselect('ul.person-list li span a'):
    person_url = urljoin(base_url, link.attrib['href'])
    rp = get_legacy_session().get(person_url)
    htp = lxml.html.fromstring(rp.text)
    name = htp.cssselect('h1')[0].text.replace('\xa0', ' ')
    mail = htp.cssselect('li.mail')[0].cssselect('a')[0].text

    party = ''
    try:
        bio = list(htp.cssselect('.figcaption')[0].cssselect('p')[0].itertext())
        party = bio[-1].split('na kandidátce: ')[1]
    except:
        pass

    data.append(
        {
            'poslanec': name,
            'url': person_url,
            'mail': mail,
            'partaj': party,
        }
    )

# %%
pd.DataFrame(data).to_csv('psp_maily.csv', index=False)

# %%
