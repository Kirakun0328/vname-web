"""Pause third-party directory ingestion while permissions are reviewed.

A pause is not a finding of infringement. Existing provenance stays intact.
"""
from urllib.parse import urlsplit

PAUSED_HOSTS = frozenset({
    'vtuber-post.com', 'vdb.vtbs.moe', 'virtual-youtuber.userlocal.jp',
    'vstats.jp', 'liverfun.jp', 'aiv.nyagsicapp.com', 'aituberlist.net',
    'aituber.web.fc2.com', 'scholarvtuber.com', 'hololist.net',
})

def paused(url):
    host = (urlsplit(url or '').hostname or '').removeprefix('www.')
    return host in PAUSED_HOSTS

def check_fetch(url):
    if paused(url):
        raise ValueError('Third-party directory collection paused pending source review')
