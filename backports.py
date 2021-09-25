#!/usr/bin/env python3
"""
Bugs
====

We track almost all the errors from our wikis in produciton on the Wikimedia
Production Error workboard[0] or as bug reports.

The most severe of these will result in backports.

To determine production errors we:

1. Get all backports for version
2. Find any that mention a "Bug"
3. See if that bug is a "error" or a "bug"

[0]: <https://phabricator.wikimedia.org/tag/wikimedia-production-error/>
"""

import json
import sys

import utils
import gerrit

from phabricator import Phabricator


def _get_projects(bug_list):
    projects = set()
    for phid, bug in bug_list.items():
        projects = projects.union(
            set(bug['task']['attachments']['projects']['projectPHIDs']))

    return list(projects)


def _get_users(bug_list):
    people = set()
    for phid, bug in bug_list.items():
        if bug['task']['fields'].get('closerPHID'):
            people.add(bug['task']['fields']['closerPHID'])
        people.add(bug['task']['fields']['authorPHID'])

    return list(people)


class Backports(object):
    def __init__(self, version, phab):
        self._backports = None
        self.tasks = []
        self.bugs = {}
        self.phab = phab
        self.users = {}
        self.projects = {}
        self.version = version

    def _phab_maniphest_search(self, bugs, after=None):
        query = {
            'constraints': {
                'ids': bugs,
            },
            'attachments': {
                'subscribers': True,
                'projects': True,
            },
        }
        if after is not None:
            print(after, file=sys.stderr)
            query['after'] = after
        out = self.phab.maniphest.search(**query)
        self.tasks += out['data']
        if out.get('cursor') and out['cursor'].get('after'):
            return self._phab_maniphest_search(bugs, out['cursor']['after'])
        else:
            return self.tasks

    def _phab_proj_search(self, projects, after=None):
        query = {
            'constraints': {
                'phids': projects,
            },
        }
        if after is not None:
            print(after, file=sys.stderr)
            query['after'] = after
        out = self.phab.project.search(**query)
        for datum in out['data']:
            self.projects[datum['phid']] = datum['fields']['name']
        if out.get('cursor') and out['cursor'].get('after'):
            return self._phab_proj_search(projects, out['cursor']['after'])
        else:
            return self.projects

    def _phab_user_search(self, users, after=None):
        query = {
            'constraints': {
                'phids': users,
            },
        }
        if after is not None:
            print(after, file=sys.stderr)
            query['after'] = after
        out = self.phab.user.search(**query)
        for datum in out['data']:
            user = datum['fields']
            self.users[datum['phid']] = user['realName'] or user['username']
        if out.get('cursor') and out['cursor'].get('after'):
            return self._phab_user_search(users, out['cursor']['after'])
        else:
            return self.users

    def _bug_phids(self):
        """
        (Pdb) self.projects[self.bugs[290226]['task']['attachments']['projects']['projectPHIDs'][2]]
        'Unplanned-Sprint-Work'
        (Pdb) self.users[self.bugs[290226]['task']['authorPHID']]
        *** KeyError: 'authorPHID'
            (Pdb) self.users[self.bugs[290226]['task']['fields']['authorPHID']]
            'Christoph Jauera (WMDE)'
            (Pdb) self.users[self.bugs[290226]['task']['fields']['closerPHID']]
        """
        for task_id, task in self.bugs.items():
            task['phab'] = {}
            task['phab']['projects'] = []
            task['phab']['closer'] = None
            task['phab']['author'] = None
            closer = task['task']['fields'].get('closerPHID', False)
            for proj in task['task']['attachments']['projects']['projectPHIDs']:
                task['phab']['projects'].append(self.projects[proj])

            if closer:
                task['phab']['closer'] = self.users[closer]

            task['phab']['url'] = f'https://phabricator.wikimedia.org/T{task["task"]["id"]}'
            task['phab']['title'] = task['task']['fields']['name']
            task['phab']['created'] = task['task']['fields']['dateCreated']
            task['phab']['closed'] = task['task']['fields']['dateClosed']
            task['phab']['status'] = task['task']['fields']['status']['value']
            task['phab']['priority'] = task['task']['fields']['priority']['value']
            task['phab']['author'] = self.users[task['task']['fields']['authorPHID']]

    def search(self):
        bugs = [*self.backports.keys()]
        self._phab_maniphest_search(bugs)
        for task in self.tasks:
            if task['fields']['subtype'] in ['error', 'bug']:
                self.bugs[task['id']] = {
                    'patch': self._backports[task['id']],
                    'task': task,
                }

        self._phab_proj_search(_get_projects(self.bugs))
        self._phab_user_search(_get_users(self.bugs))
        self._bug_phids()
        return self.bugs

    @property
    def backports(self):
        """
        Query gerrit for all changes to the branch
        """

        if self._backports is None:
            self._backports = {}
            backports = gerrit.search(branch=self.version)
            for backport in backports:
                    if backport.get('bug') is None:
                        continue
                    for bug in backport['bug']:
                        self._backports[bug] = backport

        return self._backports


if __name__ == '__main__':
    args = utils.parse_args()
    for version in args.versions:
        if not version.startswith('wmf/'):
            version = f'wmf/{version}'
        pe = Backports(version, Phabricator())
        print(json.dumps(pe.search()))
