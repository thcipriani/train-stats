#!/usr/bin/env python3

import argparse
import csv
import json
import os
import re
import subprocess

import requests

from bs4 import BeautifulSoup

from distutils.version import LooseVersion
from dateutil import parser

BASE_URL = 'https://www.mediawiki.org/wiki/'
FMT_URL = 'MediaWiki_{}/Changelog'
GERRIT = 'https://gerrit.wikimedia.org/r'

MWCONFIG_PATH = './submodules/operations/mediawiki-config'


class VersionDiff:
    def __init__(self):
        self.old_version = None
        self.new_version = None


def get_patch_info(patch_url):
    """
    Patch info:
    * extract changeid ('https://gerrit.wikimedia.org/r/#/q/6df84533,n,z')
    * Curl gerrit for change info
    * remove first 6 bytes
    * convert to json
    * extract:
        * created
        * submitted
        * insertions
        * deletions
        * total_comment_count
    """
    if not patch_url.startswith(GERRIT):
        return {}
    change_id = patch_url.split('/')[-1].split(',')[0]
    r = requests.get(os.path.join(GERRIT, 'changes', '?q={}&o=CURRENT_REVISION&o=CURRENT_COMMIT'.format(change_id)))
    r.raise_for_status()
    patch_jsons = json.loads(r.text[5:])
    if not patch_jsons:
        return None
    if not isinstance(patch_jsons, list):
        patch_jsons = [patch_jsons]
    for patch in patch_jsons:
        if [*patch['revisions'].keys()][0].startswith(change_id):
            patch_json = patch
            break
    patch_stats = {
        'created': parser.parse(patch_json['created'], ignoretz=True),
        'submitted': parser.parse(patch_json['submitted'], ignoretz=True),
        'insertions': patch_json['insertions'],
        'deletions': patch_json['deletions'],
        'total_comment_count': patch_json['total_comment_count'],
    }
    time_in_review = patch_stats['submitted'] - patch_stats['created']
    patch_stats['time_in_review'] =  time_in_review.total_seconds()
    return patch_stats


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
    links = soup.find_all('a', href=True)

    count = 0
    for link in links:
        if not link['href'].startswith('https://gerrit.wikimedia.org/r/'):
            continue
        patches.append(link['href'])
        count += 1
    return (patches, count)


def set_version(version_diff, wikiversions_line):
    if wikiversions_line['diff'] == '-':
        version_diff.old_version = LooseVersion(wikiversions_line['version'])
    else:
        version_diff.new_version = LooseVersion(wikiversions_line['version'])

    return version_diff


def is_rollback(wikiversion, change):
    wikiversion = LooseVersion(wikiversion)
    wikis = {}
    # Get the diff for the change
    diff = subprocess.check_output([
        'git', '-C', MWCONFIG_PATH, 'diff-tree', '-p', '-U0', change, 'wikiversions.json'
    ])

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
    for wiki, version in wikis.items():
        try:
            # If the old version of wikiversions.json had the wikiversion we're investigating
            # AND
            # the new wikiversions.json has an OLDER wikiversion than the one we're investigating           #
            if wikiversion == version.old_version and version.new_version < wikiversion:
                rollback = True
        except AttributeError:
            # This happens when you add or remove a wiki -- there won't be an
            # old_version or a new_version, respectively
            pass

    return rollback


def count_rollbacks(version, changes):
    rollbacks = 0
    for change in changes:
        print('{}: {} MENTION'.format(version, change.decode('utf8')))
        if is_rollback(version, change):
            # debug
            print('{}: {} ROLLBACK'.format(version, change.decode('utf8')))
            rollbacks += 1
    return rollbacks

def get_rollbacks_for_version(version):
    # Oldest commit to wikiversions mentioning "version"
    oldest_cmd = [
        '/usr/bin/git',
        '-C', MWCONFIG_PATH,
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
        '-C', MWCONFIG_PATH,
        'log',
        '--format=%H',
        f'{oldest_commit_with_version}..HEAD',
        '--',
        'wikiversions.json'
    ]
    all_changes_with_version = subprocess.check_output(oldest_cmd).splitlines()
    return count_rollbacks(version, all_changes_with_version)


def get_version_info(version):
    rollbacks = get_rollbacks_for_version(version)
    if rollbacks is None:
        raise RuntimeError(f'{version} was never deployed!')
    patches, version = get_patches_for_version(version)
    return (patches, rollbacks, version)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '-w',
        '--wmf-version',
        dest='versions',
        action='append',
        required=True,
        help='wmf version'
    )
    args = ap.parse_args()

    patches_for_version = {}
    for version in args.versions:
        patches, rollbacks, count = get_version_info(version)
        patches_for_version[version] = patches

        with open(f'data/{version}.csv', 'w', newline='') as csvfile:
            fieldnames = [
                'created',
                'submitted',
                'insertions',
                'deletions',
                'total_comment_count',
                'time_in_review',
                'version',
                'patches',
                'rollbacks',
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for patch in patches_for_version[version]:
                print(patch)
                info = get_patch_info(patch)
                if info is None:
                    continue
                info['version'] = version
                info['patches'] = count
                info['rollbacks'] = rollbacks
                writer.writerow(info)
                print(info)
