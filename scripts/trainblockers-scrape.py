#!/usr/bin/env python3
"""
I eventually settled on a much better method of doing this
but I'll keep this for a reference
"""

import sys

import requests

from bs4 import BeautifulSoup
from phabricator import Phabricator

import utils


def get_train_timeline(train_task):
    print('Fetching {}'.format(train_task))
    r = requests.get(train_task)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, 'html.parser')
    updates = soup.find_all('div', class_='phui-timeline-title')
    return [update.text.lower() for update in updates]


def get_train_blockers(updates):
    added = 0
    removed = 0
    closed = 0
    reopened = 0

    for update in updates:
        if 'added a subtask' in update:
            added += 1
        if 'closed subtask' in update:
            closed += 1
        if 'reopened subtask' in update:
            reopened += 1
        if 'removed a subtask' in update:
            removed += 1
    print(
        'Added\t{}\nRemoved\t{}\nReopened\t{}\nClosed\t{}\n'.format(
            added, removed, reopened, closed
        )
    )
    return (added, removed, reopened, closed)


def get_task(version):
    p = Phabricator()
    constraints = {
        'query': 'title:"{} deployment blockers"'.format(version)
    }
    phid = p.maniphest.search(constraints=constraints)['data'][0]['id']
    return 'https://phabricator.wikimedia.org/T{}'.format(phid)


if __name__ == '__main__':
    args = utils.parse_args()
    for version in args.versions:
        added, removed, reopened, closed = get_train_blockers(
            get_train_timeline(
                get_task(version)
            )
        )
