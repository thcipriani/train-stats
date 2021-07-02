#!/usr/bin/env python3

import json
import subprocess

import utils
import git

from phabricator import Phabricator


def new_trainblockers(version):
    phab = Phabricator()
    return TrainBlockers(version, phab)


def group_at_time(time, version):
    group0 = 'mediawikiwiki'
    group1 = 'commonswiki'
    group2 = 'enwiki'

    rev = subprocess.check_output([
        'git', '-C', git.MWCONFIG_PATH, 'rev-list', '-1', '--before', time, r'@{u}'
    ]).decode('utf8').strip()
    wikiversions = json.loads(subprocess.check_output([
        'git', '-C', git.MWCONFIG_PATH, 'show', '{}:wikiversions.json'.format(rev)
    ]))
    if version in wikiversions[group2]:
        return 2
    if version in wikiversions[group1]:
        return 1
    if version in wikiversions[group0]:
        return 0
    return -1


class TrainBlocker(object):
    def __init__(self):
        self.task = None
        self.removed = False
        self.resolved = False
        self.blocker = None
        self.unblocker = None
        self.unblocked = None
        self.blocked = None
        self.group_blocked = None
        self.group_unblocked = None

    @property
    def id(self):
        if not self.task:
            return None
        return self.task['id']

    @property
    def url(self):
        if not self.task:
            return None
        return 'https://phabricator.wikimedia.org/T{}'.format(self.id)

    @property
    def status(self):
        if not self.task:
            return None
        return self.task['fields']['status']['value']


class TrainBlockers(object):
    def __init__(self, version, phab):
        self.version = version
        self.phab = phab
        self._blockers = {}

    def _get_blockers(self, task_id):
        return self.phab.maniphest.gettasktransactions(ids=[task_id])[str(task_id)]

    def _get_blocker(self, phid):
        blocker = self._blockers.get(phid)
        if blocker is None:
            self._blockers[phid] = blocker = TrainBlocker()
            blocker.task = self.phab.maniphest.search(
                constraints={'phids': [phid]}
            )['data'][0]

        return blocker

    def _parse_blockers(self, transactions):
        for transaction in transactions:
            # Closed a subtask
            if transaction['transactionType'] == 'unblock':
                phid = list(transaction['oldValue'].keys())[0]
                self._parse_unblock(phid, transaction, resolved=True)

            # Added/removed a subtask
            if (transaction['transactionType'] == 'core:edge' and
                transaction['meta']['edge:type'] == 3):
                if transaction['oldValue']:
                    for oval in transaction['oldValue']:
                        self._parse_unblock(oval, transaction, removed=True)
                if transaction['newValue']:
                    for nval in transaction['newValue']:
                        self._parse_block(nval, transaction)

    def _parse_unblock(self, phid, transaction, removed=False, resolved=False):
        blocker = self._get_blocker(phid)
        if removed:
            blocker.removed = removed
        if resolved:
            blocker.resolved = resolved
        blocker.unblocker = self.phab.user.search(
            constraints={'phids': [transaction['authorPHID']]}
        )['data'][0]['fields']['realName']
        blocker.unblocked = int(transaction['dateCreated'])
        blocker.group_unblocked = group_at_time(transaction['dateCreated'], self.version)

    def _parse_block(self, phid, transaction):
        blocker = self._get_blocker(phid)
        blocker.blocker = self.phab.user.search(
            constraints={'phids': [transaction['authorPHID']]}
        )['data'][0]['fields']['realName']
        blocker.blocked = int(transaction['dateCreated'])
        blocker.group_blocked = group_at_time(transaction['dateCreated'], self.version)

    @property
    def blocker_task(self):
        constraints = {
            'query': 'title:"{} deployment blockers"'.format(self.version)
        }
        task_id = self.phab.maniphest.search(
            constraints=constraints,
            queryKey='k5YunDeBIWUo'
        )['data'][0]['id']
        return task_id

    @property
    def blockers(self):
        if not self._blockers:
            self._parse_blockers(self._get_blockers(self.blocker_task))

        return [b for _, b in self._blockers.items()]



if __name__ == '__main__':
    args = utils.parse_args()

    for version in args.versions:
        tb = new_trainblockers(version)
        tb.blockers
        import pdb
        pdb.set_trace()
