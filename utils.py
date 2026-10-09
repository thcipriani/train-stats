#!/usr/bin/env python3

import argparse
import os
import re
import sys
from pathlib import Path

from phabricator import Phabricator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = 'train-stats/0.0.1 (https://github.com/thcipriani/train-stats)'

# (connect timeout, read timeout) in seconds.
# The read timeout is what prevents hanging forever on a silent server.
DEFAULT_TIMEOUT = (3.05, 30)
class TimeoutAdapter(HTTPAdapter):
    """
    HTTPAdapter that applies a default timeout to every request unless
    one is explicitly passed, so no code path can accidentally block forever.
    """
    def __init__(self, *args, timeout=DEFAULT_TIMEOUT, **kwargs):
        self._timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        if kwargs.get('timeout') is None:
            kwargs['timeout'] = self._timeout
        return super().send(request, **kwargs)


def make_session():
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})
    retries = Retry(
        total=3,
        backoff_factor=1,               # 0s, 2s, 4s between retries
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=('GET',),       # we only GET; safe to retry
        respect_retry_after_header=True,
    )
    adapter = TimeoutAdapter(timeout=DEFAULT_TIMEOUT, max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


def init_phab():
    arcrc = Path.home() / '.arcrc'
    if arcrc.exists():
        return Phabricator()
    host = os.environ.get('WMF_PHAB_HOST', 'https://phabricator.wikimedia.org/api/')
    token = os.environ.get('WMF_PHAB_TOKEN') or ''
    if not token:
        print('Cannot find WMF_PHAB_TOKEN and no ~/.arcrc present. Giving up.')
        sys.exit(1)
    return Phabricator(host=host, token=token)


def mediawiki_version(version):
    """
    Credit: Mukunda Modell
    """
    try:
        return re.match("(\\d+\\.\\d+(\\.\\d+-)?wmf\\.?\\d+)", version).group(0)
    except AttributeError:
        raise argparse.ArgumentTypeError(
            'Invalid wmf version "%s" expected: #.##.#-wmf.#' % version
        )


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '-w',
        '--wmf-version',
        dest='versions',
        action='append',
        required=True,
        type=mediawiki_version,
        help='wmf version'
    )
    ap.add_argument(
        '--show-rollbacks',
        action='store_true',
        help='Show rollbacks'
    )
    ap.add_argument(
        '--only-start-time',
        action='store_true',
        help='only insert train start time'
    )
    ap.add_argument(
        '--only-blockers',
        action='store_true',
        help='only insert blockers'
    )
    ap.add_argument(
        '--only-patches',
        action='store_true',
        help='update only'
    )
    ap.add_argument(
        '--only-bugs',
        action='store_true',
        help='only insert train bugs'
    )
    ap.add_argument(
        '--tylers-only-do-this',
        action='store_true',
        help='I am dummy'
    )
    return ap.parse_args()
