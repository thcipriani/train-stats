#!/usr/bin/env python3
"""
Collect snapshots of deployment-info.php for each train group.

Run every 5 minutes to keep timestamps accurate/up-to-date with prod.
Eventually, we'll process this data...
"""

import hashlib
import json
import sqlite3
import sys
import time

import trainstats
import utils

WIKIS = {
    'testwiki': 'test.wikipedia.org',
    'mediawikiwiki': 'www.mediawiki.org',
    'commonswiki': 'commons.wikimedia.org',
    'enwiki': 'en.wikipedia.org',
}
SESSION = utils.make_session()


class InvalidDeploymentInfo(Exception):
    pass


def setup_db(conn):
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS deploy_snapshot (
            id INTEGER PRIMARY KEY,
            wiki TEXT NOT NULL,
            version TEXT NOT NULL,
            checksum TEXT NOT NULL,
            fetched_at INTEGER NOT NULL,
            last_seen_at INTEGER NOT NULL,
            -- We'll use this later...
            processed_at INTEGER,
            UNIQUE(wiki, fetched_at)
        );
        CREATE INDEX IF NOT EXISTS deploy_snapshot_wiki_fetched
            ON deploy_snapshot(wiki, fetched_at);

        CREATE TABLE IF NOT EXISTS deploy_snapshot_checkout (
            id INTEGER PRIMARY KEY,
            snapshot_id INTEGER NOT NULL,
            repo TEXT NOT NULL,
            branch TEXT,
            commit_ref TEXT NOT NULL,
            UNIQUE(snapshot_id, repo),
            FOREIGN KEY(snapshot_id) REFERENCES deploy_snapshot(id)
        );
    ''')


def fetch(host):
    r = SESSION.get(f'https://{host}/w/deployment-info.php')
    r.raise_for_status()
    return r.json()


def parse(wiki, info):
    if info.get('dbname') != wiki:
        raise InvalidDeploymentInfo(
            f'expected dbname {wiki!r}, got {info.get("dbname")!r}')
    version = info.get('version')
    if not version:
        raise InvalidDeploymentInfo('missing version')
    raw_checkouts = info.get('checkouts')
    if not raw_checkouts:
        raise InvalidDeploymentInfo('missing or empty checkouts')

    checkouts = {}
    for checkout in raw_checkouts:
        repo = checkout.get('repo')
        commit_ref = checkout.get('commit_ref')
        if not repo or not commit_ref:
            raise InvalidDeploymentInfo(f'incomplete checkout: {checkout!r}')
        if repo in checkouts:
            raise InvalidDeploymentInfo(f'duplicate repo: {repo}')
        checkouts[repo] = (repo, checkout.get('branch'), commit_ref)

    return version, sorted(checkouts.values())


def checksum(version, checkouts):
    canonical = json.dumps([version, checkouts])
    return hashlib.sha256(canonical.encode('utf8')).hexdigest()


def record(conn, wiki, info, now):
    """
    Record deployment info for one wiki.

    Return the new snapshot_id, or None if the deployed state did not change.
    """
    version, checkouts = parse(wiki, info)
    digest = checksum(version, checkouts)

    with conn:
        latest = conn.execute('''
            SELECT id, checksum
            FROM deploy_snapshot
            WHERE wiki = ?
            ORDER BY fetched_at DESC
            LIMIT 1
        ''', (wiki,)).fetchone()

        if latest is not None and latest[1] == digest:
            conn.execute(
                'UPDATE deploy_snapshot SET last_seen_at = ? WHERE id = ?',
                (now, latest[0]))
            return None

        snapshot_id = conn.execute('''
            INSERT INTO deploy_snapshot(
                wiki, version, checksum, fetched_at, last_seen_at
            ) VALUES(?,?,?,?,?)
        ''', (
            wiki, version, digest, now, now
        )).lastrowid

        conn.executemany('''
            INSERT INTO deploy_snapshot_checkout(
                snapshot_id, repo, branch, commit_ref
            ) VALUES(?,?,?,?)
        ''', [(snapshot_id, *checkout) for checkout in checkouts])

    return snapshot_id


def collect(conn, wikis=WIKIS, fetch=fetch, clock=time.time):
    """
    Poll every wiki. A failure on one wiki does not stop the others.

    Return the number of wikis that failed.
    """
    failures = 0
    for wiki, host in wikis.items():
        try:
            info = fetch(host)
            snapshot_id = record(conn, wiki, info, int(clock()))
        except Exception as e:
            failures += 1
            print(f'{wiki}: ERROR: {e}', file=sys.stderr)
            continue
        if snapshot_id is None:
            print(f'{wiki}: unchanged')
        else:
            print(f'{wiki}: new snapshot {snapshot_id}')
    return failures


def main():
    conn = sqlite3.connect(trainstats.DB_PATH, timeout=30)
    conn.execute('PRAGMA foreign_keys = ON')
    setup_db(conn)
    failures = collect(conn)
    conn.close()
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
