#!/usr/bin/env python3

import argparse
import csv
import json
import os
import re
import subprocess
import sys

import requests

from bs4 import BeautifulSoup

from datetime import date, datetime, timedelta
from distutils.version import LooseVersion
from statistics import mode
import sqlite3

import bugs
import gerrit
import git
import trainblockers
import utils

BASE_URL = 'https://www.mediawiki.org/wiki/'
FMT_URL = 'MediaWiki_{}/Changelog'

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'train.db')


class VersionDiff(object):
    def __init__(self):
        self.old_version = None
        self.new_version = None


class ChangelogItem(object):
    def __init__(self, link, text):
        self.link = link
        self.text = text

    def __str__(self):
        return f'CHANGELOGITEM({self.text}, {self.link})'


def extract_changeid(change_url):
    """
    Patch info:
    * extract changeid ('https://gerrit.wikimedia.org/r/#/q/6df84533,n,z')
    """
    return change_url.split('/')[-1].split(',')[0]


def get_patch_info(changelog_item):
    if not changelog_item.link.startswith(gerrit.URL):
        return None

    changes = gerrit.search(
        change_id=extract_changeid(changelog_item.link),
        changelog_item=changelog_item
    )

    if changes:
        return changes

    return None


def get_mw_url_for_version(version):
    # Get the url for 1.35.0-wmf.10
    major, minor = version.split('-')
    major = '.'.join(major.split('.')[:-1])
    url_version = os.path.join(major, minor)
    return os.path.join(BASE_URL, FMT_URL.format(url_version))


def get_patches_for_version(version):
    mw_url = get_mw_url_for_version(version)
    patches = []

    r = requests.get(mw_url)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, 'html.parser')
    list_items = soup.find_all('li')

    count = 0
    for li in list_items:
        link = li.find('a')
        if not link or not link['href']:
            continue
        if not link['href'].startswith(gerrit.URL):
            continue
        patches.append(ChangelogItem(
            link=link['href'],
            text=li.text
        ))
        count += 1
    return (patches, count)


def set_version(version_diff, wikiversions_line):
    if wikiversions_line['diff'] == '-':
        version_diff.old_version = LooseVersion(wikiversions_line['version'])
    else:
        version_diff.new_version = LooseVersion(wikiversions_line['version'])

    return version_diff


def wikiversion_info(version, change):
    wikiversion = LooseVersion(version)
    wikis = {}
    # Get the diff for the change
    diff = subprocess.check_output([
        'git', '-C', git.MWCONFIG_PATH, 'diff-tree', '-p', '-U0', change, 'wikiversions.json'
    ])

    committer = subprocess.check_output([
        'git', '-C', git.MWCONFIG_PATH, 'log', '-1', '--format=%cN', change
    ]).decode('utf8').strip()

    commit_date = int(subprocess.check_output([
        'git', '-C', git.MWCONFIG_PATH, 'log', '-1', '--format=%ct', change
    ]).decode('utf8').strip())

    # That's right. It's a regex for parsing a diff. Fight me.
    for line in diff.splitlines():
        line = line.decode('utf8')
        if not re.search(r'^(-|\+)\s+', line):
            continue
        regex = ''.join([
            r'(?P<diff>(-|\+))\s+',              # +/-
            r'"(?P<wiki>\w+)":\s+',              # "Wiki:"
            r'"php-(?P<version>[0-9\.wmf-]+)"', # "php-1.3x.0-wmf.x"
        ])
        line = re.search(regex, line).groupdict()

        # Get the wiki from the diff
        wiki = line['wiki']

        # Set the wiki to an empty VersionDiff
        version_diff = wikis.get(wiki, VersionDiff())

        # Set the versions that we're rolling back to and from
        wikis[wiki] = set_version(version_diff, line)

    rollback = False
    rollforward = False
    for w, v in wikis.items():
        try:
            # If the old version of wikiversions.json had the wikiversion we're investigating
            # AND
            # the new wikiversions.json has an OLDER wikiversion than the one we're investigating           #
            if wikiversion == v.old_version and v.new_version < wikiversion:
                rollback = True
            # TODO: this could be wrong if we roll back and forward for different wikis in the same commit
            if wikiversion == v.new_version and v.old_version < wikiversion:
                rollforward = True
        except TypeError:
            # This happens when you add or remove a wiki -- there won't be an
            # old_version or a new_version, respectively
            pass

    return {
        'rollback': rollback,
        'rollforward': rollforward,
        'wikis': wikis,
        'committer': committer,
        'commit_date': commit_date,
        'version': version,
        'sha1': change.decode('utf8'),
    }


def get_conductor(version, changes):
    """
    if it's not a rollback and the new version is the version we're looking for
    the author is probably the conductor
    """
    conductors = []
    for change in changes:
        if change['rollforward']:
            # debug
            print('{}: {} ROLLFORWARD'.format(change['committer'], change['sha1']))
            conductors.append(change['committer'])
    return mode([c for c in conductors if c != 'jenkins-bot'])


def time_rolledback(version, changes):
    total_seconds = 0
    start = None
    for change in sorted(changes, key=lambda x: x['commit_date']):
        if change['rollback'] and start is None:
            start = change['commit_date']
            continue
        if start is not None and change['rollforward']:
            total_seconds += change['commit_date'] - start
            start = None

    return total_seconds


def count_rollbacks(version, changes):
    rollbacks = 0
    for change in changes:
        print('{}: {} MENTION'.format(version, change['sha1']))
        if change['rollback']:
            # debug
            print('{}: {} ROLLBACK'.format(version, change['sha1']))
            rollbacks += 1
    return rollbacks


def get_starttime(version, changes):
    starttime = float('inf')
    for change in changes:
        if change['rollforward']:
            if change['commit_date'] < starttime:
                starttime = change['commit_date']
    return starttime


def total_train_time(version, changes):
    roll_forwards = [x for x in changes if x['rollforward']]
    sorted_commits = sorted(roll_forwards, key=lambda x: x['commit_date'])
    return sorted_commits[-1]['commit_date'] - sorted_commits[0]['commit_date']

def group_times(version, changes):
    groups = [
        'mediawikiwiki',
        'commonswiki',
        'enwiki',
    ]
    times = {}
    for change in sorted(changes, key=lambda x: x['commit_date']):
        if change['rollforward']:
            for wiki in groups:
                if change['wikis'].get(wiki, VersionDiff()).new_version == version:
                    times[wiki] = datetime.fromtimestamp(change['commit_date'])

    return times


def train_delays(groups_times, start_time):
    # Monday = 1; Sunday = 7
    expected = {
        'mediawikiwiki': 2,   # Tuesday
        'commonswiki': 3,     # Wednesday
        'enwiki': 4,      # Thursday
    }
    # Initialized to preserve the order for return
    delays = { 'mediawikiwiki': 0, 'commonswiki': 0, 'enwiki': 0 }
    start_datetime = datetime.fromtimestamp(start_time)
    for wiki, exp in expected.items():
        # Modulo 7 to account for trains that finish the following week
        delay = (
            groups_times[wiki].isoweekday() - exp
        ) % 7
        # If it happens less than a day from the first one, then it's not "delayed"
        if (groups_times[wiki] - start_datetime).total_seconds() < 86400:
            delay = 0
        delays[wiki] = delay

    return delays.values()


def get_wikiversion_changes(version):
    # Oldest commit to wikiversions mentioning "version"
    oldest_cmd = [
        '/usr/bin/git',
        '-C', git.MWCONFIG_PATH,
        'log',
        '-G', f'\\b{version}\\b',  #-G vs --grep: -G searches body of commit
        '--reverse',
        '--format=%H',
        '--',
        'wikiversions.json'
    ]
    commits_with_version = subprocess.check_output(oldest_cmd)
    if not commits_with_version:
        return None
    oldest_commit_with_version = commits_with_version.splitlines()[0]
    all_changes_cmd = [
        '/usr/bin/git',
        '-C', git.MWCONFIG_PATH,
        'log',
        '--format=%H',
        f'{oldest_commit_with_version}..HEAD',
        '--',
        'wikiversions.json'
    ]
    all_changes_with_version = subprocess.check_output(oldest_cmd).splitlines()
    wikiversion_changes = []
    for change in all_changes_with_version:
        wikiversion_changes.append(wikiversion_info(version, change))
    return wikiversion_changes


def setup_db():
    """
    setup the database file if it doesn't exist
    """
    conn = sqlite3.connect(DB_PATH)
    # If the db didn't exist at the start of the function, do the setup
    crs = conn.cursor()

    crs.execute('''
        CREATE TABLE IF NOT EXISTS train (
            id INTEGER PRIMARY KEY,
            version TEXT UNIQUE NOT NULL,
            conductor TEXT NOT NULL,
            patches INTEGER NOT NULL,
            rollbacks INTEGER NOT NULL,
            rollbacks_time INTEGER NOT NULL,
            group1 INTEGER NOT NULL,
            group2 INTEGER NOT NULL,
            group0_delay_days INTEGER NOT NULL,
            group1_delay_days INTEGER NOT NULL,
            group2_delay_days INTEGER NOT NULL,
            total_time INTEGER NOT NULL,
            start_time INTEGER NOT NULL
        );
    ''')
    crs.execute('''
        CREATE TABLE IF NOT EXISTS patch (
            id INTEGER PRIMARY KEY,
            train_id INTEGER NOT NULL,
            owner TEXT NOT NULL,
            created INTEGER NOT NULL,
            submitted INTEGER NOT NULL,
            insertions INTEGER NOT NULL,
            deletions INTEGER NOT NULL,
            loc INTEGER NOT NULL,
            patch_deps INTEGER NOT NULL,
            comments INTEGER NOT NULL,
            link TEXT UNIQUE NOT NULL,
            time_in_review INTEGER NOT NULL,
            FOREIGN KEY(train_id) REFERENCES train(id)
        );
    ''')
    crs.execute('''
        CREATE TABLE IF NOT EXISTS file (
            id INTEGER PRIMARY KEY,
            patch_id INTEGER NOT NULL,
            filename INTEGER NOT NULL,
            FOREIGN KEY(patch_id) REFERENCES patch(id)
        );
    ''')
    crs.execute('''
        CREATE TABLE IF NOT EXISTS bug (
            id INTEGER PRIMARY KEY,
            link TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            author TEXT,
            created INTEGER NOT NULL,
            closed INTEGER,
            status TEXT NOT NULL,
            priority INTEGER NOT NULL
        )
    ''')
    # Trains can have many bugs
    # A bug may be fixed in several trains
    crs.execute('''
        CREATE TABLE IF NOT EXISTS bug_train (
            id INTEGER PRIMARY KEY,
            train_id INTEGER NOT NULL,
            bug_id INTEGER NOT NULL,
            FOREIGN KEY(train_id) REFERENCES train(id),
            FOREIGN KEY(bug_id) REFERENCES bug(id)
        )
    ''')
    crs.execute('''
        CREATE TABLE IF NOT EXISTS bug_project (
            id INTEGER PRIMARY KEY,
            bug_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY(bug_id) REFERENCES bug(id)
        )
    ''')
    crs.execute('''
        CREATE TABLE IF NOT EXISTS bug_patch (
            id INTEGER PRIMARY KEY,
            train_id INTEGER NOT NULL,
            created INTEGER NOT NULL,
            submitted INTEGER NOT NULL,
            insertions INTEGER NOT NULL,
            deletions INTEGER NOT NULL,
            loc INTEGER NOT NULL,
            patch_deps INTEGER NOT NULL,
            comments INTEGER NOT NULL,
            link TEXT UNIQUE NOT NULL,
            time_in_review INTEGER NOT NULL
        )
    ''')
    # Bugs can have many patches
    # Patches can have many bugs
    crs.execute('''
        CREATE TABLE IF NOT EXISTS bug_bug_patch (
            id INTEGER PRIMARY KEY,
            bug_id INTEGER NOT NULL,
            bug_patch_id INTEGER NOT NULL,
            FOREIGN KEY(bug_id) REFERENCES bug(id),
            FOREIGN KEY(bug_patch_id) REFERENCES bug_patch(id)
        )
    ''')
    crs.execute('''
        CREATE TABLE IF NOT EXISTS bug_file (
            id INTEGER PRIMARY KEY,
            bug_patch_id INTEGER NOT NULL,
            filename INTEGER NOT NULL,
            UNIQUE(bug_patch_id,filename),
            FOREIGN KEY(bug_patch_id) REFERENCES bug_patch(id)
        )
    ''')
    crs.execute('''
        CREATE TABLE IF NOT EXISTS blocker (
            id INTEGER PRIMARY KEY,
            train_id INTEGER NOT NULL,
            blocked INTEGER NOT NULL,
            unblocked INTEGER,
            blocker TEXT NOT NULL,
            unblocker TEXT,
            removed INTEGER NOT NULL,
            resolved INTEGER NOT NULL,
            task INTEGER NOT NULL,
            url TEXT NOT NULL,
            status TEXT NOT NULL,
            group_blocked INTEGER NOT NULL,
            group_unblocked INTEGER,
            CHECK (removed IN (0, 1))
            CHECK (resolved IN (0, 1))
            UNIQUE(train_id,blocked,task)
            FOREIGN KEY(train_id) REFERENCES train(id)
        );
    ''')
    # Needed to count patches as sub-query
    crs.execute('CREATE INDEX IF NOT EXISTS file_patch_id ON file(patch_id);')
    conn.commit()
    return conn


if __name__ == '__main__':
    args = utils.parse_args()
    conn = setup_db()
    crs = conn.cursor()

    patches_for_version = {}
    for version in args.versions:
        wikiversion_changes = get_wikiversion_changes(version)
        if wikiversion_changes is None:
            raise RuntimeError(f'{version} was never deployed!')

        start_time = get_starttime(version, wikiversion_changes)

        if args.only_start_time:
            print(f'START TIME: {start_time}')
            crs.execute('''
                UPDATE train
                SET start_time = ?
                WHERE version = ?''', (
                    start_time,
                    version
                )
            )
            conn.commit()
            sys.exit(0)

        rollbacks = count_rollbacks(version, wikiversion_changes)
        conductor = get_conductor(version, wikiversion_changes)
        rollbacks_time = time_rolledback(version, wikiversion_changes)
        groups_times = group_times(version, wikiversion_changes)
        group0, group1, group2 = train_delays(groups_times, start_time)
        train_total_time = total_train_time(version, wikiversion_changes)

        patches, patch_count = get_patches_for_version(version)

        # Don't touch data, just print and exit
        if args.show_rollbacks:
            print(f'START TIME: {start_time}')
            print(f'CONDUCTOR: {conductor}')
            print(f'ROLLBACKS COUNT: {rollbacks}')
            print(f'TIME ROLLEDBACK (seconds): {rollbacks_time}')
            print(f'DELAYS (days)\n----\n\tGROUP0: {group0}\n\tGROUP1: {group1}\n\tGROUP2: {group2}')
            print(f'TIME TOTAL (seconds): {train_total_time}')
            sys.exit(0)

        # We actually want to update the train table, not just patches or
        # blockers
        if not args.only_patches and not args.only_blockers and not args.only_bugs:
            crs.execute('''
                INSERT INTO train(
                    start_time,
                    version,
                    conductor,
                    patches,
                    rollbacks,
                    rollbacks_time,
                    group1,
                    group2,
                    group0_delay_days,
                    group1_delay_days,
                    group2_delay_days,
                    total_time)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''', (
                    start_time,
                    version,
                    conductor,
                    patch_count,
                    rollbacks,
                    rollbacks_time,
                    groups_times['commonswiki'].timestamp(),
                    groups_times['enwiki'].timestamp(),
                    group0,
                    group1,
                    group2,
                    train_total_time
                )
            )
            conn.commit()

        train_id = crs.execute(
            'SELECT id FROM train WHERE version = ?', (version,)
        ).fetchone()[0]

        # Blockers
        if not args.only_patches and not args.only_bugs:
            tb = trainblockers.new_trainblockers(version)
            print('\t'.join([
                'train_id',
                'blocked',
                'unblocked',
                'blocker',
                'unblocker',
                'removed',
                'resolved',
                'task',
                'url',
                'status',
                'group_blocked',
                'group_unblocked'
            ]))

            for blocker in tb.blockers:
                print('\t'.join([str(fuck) for fuck in [
                    train_id,
                    blocker.blocked,
                    blocker.unblocked,
                    blocker.blocker,
                    blocker.unblocker,
                    blocker.removed,
                    blocker.resolved,
                    blocker.id,
                    blocker.url,
                    blocker.status,
                    blocker.group_blocked,
                    blocker.group_unblocked,
                ]]))
                crs.execute('''
                    INSERT INTO blocker(
                        train_id,
                        blocked,
                        unblocked,
                        blocker,
                        unblocker,
                        removed,
                        resolved,
                        task,
                        url,
                        status,
                        group_blocked,
                        group_unblocked)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''', (
                        train_id,
                        blocker.blocked,
                        blocker.unblocked,
                        blocker.blocker,
                        blocker.unblocker,
                        blocker.removed,
                        blocker.resolved,
                        blocker.id,
                        blocker.url,
                        blocker.status,
                        blocker.group_blocked,
                        blocker.group_unblocked,
                    )
                )
            conn.commit()

        # Patches
        if not args.only_blockers and not args.only_bugs:
            patches_for_version[version] = patches
            for patch in patches_for_version[version]:
                print(patch)
                patch_data = get_patch_info(patch)
                if patch_data is None:
                    continue
                patch_data = patch_data[0]
                if patch_data is None:
                    continue
                try:
                    crs.execute('''
                        INSERT INTO patch(
                            train_id,
                            created,
                            submitted,
                            insertions,
                            deletions,
                            loc,
                            patch_deps,
                            comments,
                            link,
                            time_in_review,
                            project,
                            owner
                        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''', (
                            train_id,
                            patch_data['created'],
                            patch_data['submitted'],
                            patch_data['insertions'],
                            patch_data['deletions'],
                            patch_data['loc'],
                            patch_data['patch_deps'],
                            patch_data['comments'],
                            patch_data['link'],
                            patch_data['time_in_review'],
                            patch_data['project'],
                            patch_data['owner']
                        )
                    )
                # 8: sha1 is not unique
                # ChangeId is not unique
                # The "id" is also not unique:
                #     https://gerrit.wikimedia.org/r/q/mediawiki%2Fcore~master~I6b543c508260f5889f1236dd43022a6a0fe963a9
                # Oddly "_number" seems unique and that's about it :(
                except sqlite3.IntegrityError:
                    print(patch_data)
                    raise

                patch_id = crs.execute(
                    'SELECT id FROM patch WHERE link = ?', (patch_data['link'],)
                ).fetchone()[0]

                for filename in patch_data['files']:
                    crs.execute('''
                        INSERT INTO file(
                            patch_id,
                            filename
                        ) VALUES(?,?)''', (
                            patch_id,
                            filename
                        )
                    )
            conn.commit()

        if not args.only_blockers and not args.only_patches:
            wmf_version = version
            if not wmf_version.startswith('wmf/'):
                wmf_version = f'wmf/{wmf_version}'
            train_bugs = bugs.get_all(wmf_version)

            for bug_id, bug in train_bugs.items():
                print(f'BACKPORT: {bug["phab"]["url"]} ({bug["patch"]["link"]})')

                already_seen = False
                try:
                    crs.execute('''
                        INSERT INTO bug(
                            link,
                            title,
                            author,
                            created,
                            closed,
                            status,
                            priority
                        ) VALUES(?,?,?,?,?,?,?)''', (
                            bug['phab']['url'],
                            bug['phab']['title'],
                            bug['phab']['author'],
                            bug['phab']['created'],
                            bug['phab']['closed'],
                            bug['phab']['status'],
                            bug['phab']['priority']
                        )
                    )
                except sqlite3.IntegrityError:
                    print(f'Bug affected more than 1 train: {bug["phab"]["url"]}')
                    already_seen = True

                bug_id = crs.execute(
                    'SELECT id FROM bug WHERE link = ?', (bug['phab']['url'],)
                ).fetchone()[0]

                crs.execute('''
                    INSERT INTO bug_train(
                        train_id,
                        bug_id
                    ) VALUES(?,?)''', (
                        train_id,
                        bug_id
                    )
                )

                for bug_project in bug['phab']['projects']:
                    crs.execute('''
                        INSERT INTO bug_project(
                            bug_id,
                            name
                        ) VALUES(?,?)''', (
                            bug_id,
                            bug_project
                        )
                    )

                try:
                    crs.execute('''
                        INSERT INTO bug_patch(
                            train_id,
                            created,
                            submitted,
                            insertions,
                            deletions,
                            loc,
                            patch_deps,
                            comments,
                            link,
                            time_in_review,
                            project
                        ) VALUES(?,?,?,?,?,?,?,?,?,?,?)''', (
                            train_id,
                            bug['patch']['created'],
                            bug['patch']['submitted'],
                            bug['patch']['insertions'],
                            bug['patch']['deletions'],
                            bug['patch']['loc'],
                            bug['patch']['patch_deps'],
                            bug['patch']['comments'],
                            bug['patch']['link'],
                            bug['patch']['time_in_review'],
                            bug['patch']['project']
                        )
                    )
                except sqlite3.IntegrityError:
                    print(f'Patch fixed > 1 bug: {bug["patch"]["link"]}')
                    already_seen = True


                bug_patch_id = crs.execute(
                    'SELECT id FROM bug_patch WHERE link = ?', (bug['patch']['link'],)
                ).fetchone()[0]

                crs.execute('''
                    INSERT INTO bug_bug_patch(
                        bug_id,
                        bug_patch_id
                    ) VALUES(?,?)''', (
                        bug_id,
                        bug_patch_id
                    )
                )

                for filename in bug['patch']['files']:
                    try:
                        crs.execute('''
                            INSERT INTO bug_file(
                                bug_patch_id,
                                filename
                            ) VALUES(?,?)''', (
                                bug_patch_id,
                                filename
                            )
                        )
                    except sqlite3.IntegrityError:
                        if not already_seen:
                            print(json.dumps(bug))
                            raise

            conn.commit()
