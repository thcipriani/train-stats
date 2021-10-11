#!/usr/bin/env python3

import json
import subprocess

import utils
import git

from phabricator import Phabricator
from phabricator import APIError


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


def get_phab_users(authorPHIDs, phab):
    return phab.user.search(
        constraints={'phids': authorPHIDs}
    )['data']


def get_phab_user(authorPHID, phab):
    user = get_phab_users([authorPHID], phab)[0]['fields']

    # TIL this syntax works in python and doesn't return a bool
    return user['realName'] or user['username']


class TrainBlocker(object):
    def __init__(self):
        self.task = None
        self.removed = False
        self.resolved = False
        self.blocker_name = None
        self.unblocker_name = None
        self.unblocked_date = None
        self.blocked_date = None
        self.group_blocked_at = None
        self.group_unblocked_at = None
        self.version = None
        self.phab = None

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

    @property
    def unblocked(self):
        """
        Phuck you phabricator you stupid fucking piece of shit software
        your fucking api is fucking horrible you stupid piece of shit!!!
        """
        if not self.unblocked_date:
            self.unblocked_date = self.task['fields'].get('dateClosed', 0)

        return self.unblocked_date

    @property
    def group_unblocked(self):
        if not self.group_unblocked_at:
            self.group_unblocked_at = group_at_time(
                str(self.unblocked), self.version)

        return self.group_unblocked_at

    @property
    def unblocker(self):
        """
        See comment for 'blocked'
        """
        if not self.unblocker_name:
            try:
                self.unblocker_name = get_phab_user(
                    self.task['fields']['closerPHID'], self.phab)
                if self.unblocker_name is None:
                    self.unblocker_name = 'null'
            except APIError:
                self.unblocker_name = 'null'

        return self.unblocker_name

    @property
    def blocked(self):
        """
        This is necessary since a task created via the "Create subtask link"
        is never "added" to the parent task. See::
        https://phabricator.wikimedia.org/T286091
        """
        if not self.blocked_date:
            self.blocked_date = self.task['fields']['dateCreated']

        return self.blocked_date

    @property
    def group_blocked(self):
        """
        See comment for 'blocked'
        """
        if not self.group_blocked_at:
            self.group_blocked_at = group_at_time(
                str(self.blocked), self.version)

        return self.group_blocked_at

    @property
    def blocker(self):
        """
        See comment for 'blocked'
        """
        if not self.blocker_name:
            self.blocker_name = get_phab_user(
                self.task['fields']['authorPHID'], self.phab)
        return self.blocker_name


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
            blocker.version = self.version
            blocker.phab = self.phab
            blocker.task = self.phab.maniphest.search(
                constraints={'phids': [phid]}
            )['data'][0]

        return blocker

    def _parse_blockers(self, transactions):
        for transaction in transactions:
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
        blocker.unblocker_name = get_phab_user(transaction['authorPHID'], self.phab)
        blocker.unblocked_date = int(transaction['dateCreated'])
        blocker.group_unblocked_at = group_at_time(transaction['dateCreated'], self.version)

    def _parse_block(self, phid, transaction):
        blocker = self._get_blocker(phid)
        blocker.blocker_name = get_phab_user(transaction['authorPHID'], self.phab)
        blocker.blocked_date = int(transaction['dateCreated'])
        blocker.group_blocked_at = group_at_time(transaction['dateCreated'], self.version)

    @property
    def blocker_task(self):
        constraints = {
            'query': 'title:"{} deployment blockers"'.format(self.version)
        }
        try:
            task = self.phab.maniphest.search(
                constraints=constraints,
                queryKey='k5YunDeBIWUo'
            )['data'][0]
        except IndexError:
            # This might be pre 1.31.0 which means it's not a
            # "release" task type, try a different queryKey
            task = self.phab.maniphest.search(
                constraints=constraints,
                queryKey='guO.3LPHn1Ao'
            )['data'][0]
        return task

    @property
    def blockers(self):
        if not self._blockers:
            self._parse_blockers(self._get_blockers(self.blocker_task['id']))

        return [b for _, b in self._blockers.items()]



if __name__ == '__main__':
    args = utils.parse_args()

    for version in args.versions:
        tb = new_trainblockers(version)
        print([x.unblocker for x in tb.blockers])
        import pdb
        pdb.set_trace()
