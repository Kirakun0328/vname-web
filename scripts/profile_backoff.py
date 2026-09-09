"""Persist host cooldowns so a new process or runner cannot bypass a limit."""
import datetime
import email.utils
import json
import threading
from pathlib import Path
from urllib.parse import urlsplit

PATH = Path(__file__).with_name('profile-fetch-backoff.json')
LOCK = threading.RLock()
HOSTS = {}


class DeferredHost(Exception):
    pass


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def host_key(url):
    host = (urlsplit(url).hostname or '').lower().removeprefix('www.').removeprefix('m.')
    return 'youtube.com' if host == 'youtu.be' else host


def load():
    global HOSTS
    HOSTS = json.loads(PATH.read_text()) if PATH.exists() else {}


def save():
    with LOCK:
        tmp = PATH.with_suffix('.tmp')
        tmp.write_text(json.dumps(HOSTS, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        tmp.replace(PATH)


def blocked(url):
    with LOCK:
        until = HOSTS.get(host_key(url), {}).get('until')
        return bool(until and now() < datetime.datetime.fromisoformat(until))


def pause(url, code, retry_after=None):
    timestamp = now()
    until = timestamp + datetime.timedelta(seconds=3600 if code == 429 else 86400)
    if retry_after:
        try:
            parsed = (timestamp + datetime.timedelta(seconds=max(1, int(retry_after)))
                      if str(retry_after).strip().isdigit() else email.utils.parsedate_to_datetime(retry_after))
            if parsed > timestamp:
                until = parsed
        except (TypeError, ValueError, OverflowError):
            pass
    with LOCK:
        host = host_key(url)
        previous = HOSTS.get(host, {})
        if previous.get('until'):
            until = max(until, datetime.datetime.fromisoformat(previous['until']))
        HOSTS[host] = {**previous, 'until': until.isoformat(), 'observed_at': timestamp.isoformat(),
                      'reason': 'HTTP' + str(code), 'retry_after_provided': bool(retry_after)}
        save()


def recover_legacy_candidate(row):
    evidence = HOSTS.get(host_key(row.get('url', '')), {})
    if (row.get('verification_status') in {'unavailable:ValueError', 'unavailable:HTTP429'} and
            evidence.get('legacy_verification_batch') and
            row.get('verified_at') == evidence['legacy_verification_batch']):
        row.update(review_status='pending_primary_confirmation', verification_status='deferred_host_backoff')
        return True
    return False
