import json
from dateutil import parser
from datetime import date, datetime
import os
import re
import sys

import requests

URL ='https://gerrit.wikimedia.org/r'

def get_bug(patch):
    """
    Gets the bug footer from gerrit json
    """
    bugs = []
    rev = [*patch['revisions'].keys()][0]
    msg = patch['revisions'][rev]['commit']['message'].splitlines()
    bug_footers = [line for line in msg if line.startswith('Bug: ')]
    for bug in bug_footers:
        # "Bug: T200" -> ["200"]
        # OR "Bug: T200, T100" -> ["200", "100"]
        bug_id = bug.split(':')[-1]
        if ',' in bug_id:
            bug_ids = bug_id.split(',')
        else:
            bug_ids = [bug_id]

        # Remove links to specific comments on bugs
        for b in bug_ids:
            b = b.strip()[1:]
            if '#' in b:
                b = b.split('#')[0]
            if b.startswith('t') or b.startswith('T'):
                b = b[1:]
            try:
                b = int(b)
            except ValueError:
                continue  # Skip this one
            bugs.append(b)
    return bugs


def get_submitted(patch_json):
    if not patch_json.get('submitted'):
        return False
    return int(parser.parse(patch_json['submitted'], ignoretz=True).timestamp())

def get_owner(patch_json):
    owner = patch_json['owner']
    owner_name = owner.get('display_name', owner.get('name', ''))
    owner_email = owner.get('email')
    if owner_email is not None:
        owner_email = ' <{}>'.format(owner_email)
    else:
        owner_email = ''
    return '{}{}'.format(owner_name, owner_email)

def get_initiator(patch_json):
    """
    Since introducing spiderpig, this is how we find out who initiated
    the train.
    """
    # Code-Review+2\n\nInitiated by dancy@deploy1003
    initiated_by_regex = re.compile(r'Initiated by (?P<conductor>[^@]+)@')
    initiator = None
    for msg in patch_json.get('messages', []):
        m = initiated_by_regex.search(msg.get('message', ''))
        if m:
            initiator = m.group(1)
            break
    return initiator

def confirm_change_id(patches, change_id, changelog_item):
    """
    Find the right patch in the list of patches
    """
    subjects = []
    for patch in patches:
        # Match the sha1 from the changelog to the sha1 we just found
        sha1 = [*patch['revisions'].keys()][0]
        if not sha1.startswith(change_id):
            continue
        # This matches the bad way we do this in changelog generation
        patch_subj = patch['revisions'][sha1]['commit']['message'].splitlines()[0]
        subjects.append(patch_subj)
        # substring matches with, like ::static_method don't match so...
        if (re.sub(r'\W', '.', patch_subj) in
                re.sub(r'\W', '.', changelog_item)):
            patch_json = patch
            break

    try:
        cr = patch_json['current_revision']
        return [patch_json]
    except UnboundLocalError:
        txt = re.sub(r'\W', '.', changelog_item)
        print(f'Couldn\'t find the Gerrit change for: {txt} ({change_id})')
        print([re.sub(r'\W', '.', sub) for sub in subjects])
        # raise
        # Sometimes the changelog notes don't match the patches...
        #
        # For versions:
        #
        # * 1.27.0-wmf.22
        # * 1.28.0-wmf.1
        # * 1.28.0-wmf.13
        # * 1.28.0-wmf.18
        # * 1.28.0-wmf.2
        # * 1.28.0-wmf.21
        # * 1.28.0-wmf.4
        # * 1.29.0-wmf.1
        # * 1.29.0-wmf.15
        # * 1.29.0-wmf.4
        # * 1.29.0-wmf.6
        # * 1.29.0-wmf.7
        # * 1.30.0-wmf.4
        # * 1.30.0-wmf.6
        # * 1.30.0-wmf.9
        #
        # One of the problems was "transaction" vs "transacton".
        # Helpful editors fixing wiki typos ¯\_(ツ)_/¯
        return []

def search(change_id=None, branch=None, changelog_item=None):
    """
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
    if change_id is not None and branch is not None:
        raise RuntimeError('Do not pass both branch and change_id')

    fn = lambda x, y: x
    if change_id is not None and changelog_item is not None:
        fn = confirm_change_id

    if branch is not None:
        query = f'branch:{branch}+is:merged'

    if change_id is not None:
        query = change_id

    url = ''.join([
        URL,
        '/changes/?q=',
        query,
        '&o=CURRENT_REVISION',
        '&o=CURRENT_COMMIT',
        '&o=MESSAGES',
        '&o=CURRENT_FILES',
        '&o=DETAILED_ACCOUNTS',
    ])
    print(url, file=sys.stderr)
    r = requests.get(url)
    r.raise_for_status()

    patch_jsons = json.loads(r.text[5:])
    if not patch_jsons:
        return None
    if not isinstance(patch_jsons, list):
        patch_jsons = [patch_jsons]

    if changelog_item is not None:
        patch_jsons = fn(patch_jsons, change_id or branch, changelog_item.text)
    else:
        patch_jsons = fn(patch_jsons, change_id or branch)
    patches_stats = []

    for patch_json in patch_jsons:
        r = requests.get(
            os.path.join(
                URL,
                'changes',
                str(patch_json['_number']),
                'revisions',
                patch_json['current_revision'],
                'related'
            )
        )
        r.raise_for_status()
        related = json.loads(r.text[5:])
        patch_files = [*patch_json['revisions'][[*patch_json['revisions'].keys()][0]]['files'].keys()]
        try:
            patch_stats = {
                'owner': get_owner(patch_json),
                'created': int(parser.parse(patch_json['created'], ignoretz=True).timestamp()),
                'submitted': get_submitted(patch_json),
                'insertions': patch_json['insertions'],
                'project': patch_json['project'],
                'deletions': patch_json['deletions'],
                'loc': patch_json['insertions'] + patch_json['deletions'],
                'files': patch_files,
                # This, of course, includes itself as "related" if there is 1 or more related changes because: FUCK IF I KNOW WHY!!
                'patch_deps': max(0, len(related['changes']) - 1),
                'bug': get_bug(patch_json),
                'comments': len([
                    msg for msg in patch_json['messages']
                    if (
                        not msg.get('tag', 'None').startswith('autogenerated')
                        and msg.get('author', {}).get('_account_id', 75) != 75
                    )
                ]),
                'initiator': get_initiator(patch_json),
                'link': os.path.join(URL, str(patch_json['_number'])),
                'patchset': patch_json['_number'],
            }
        except:
            import pdb
            pdb.set_trace()
        time_in_review = patch_stats['submitted'] - patch_stats['created']
        patch_stats['time_in_review'] =  time_in_review
        patches_stats.append(patch_stats)

    return patches_stats
