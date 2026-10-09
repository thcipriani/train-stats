import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import deployinfo  # noqa: E402

CORE = 'https://gerrit.wikimedia.org/r/mediawiki/core'
CONFIG = 'https://gerrit.wikimedia.org/r/operations/mediawiki-config'
EXT = 'https://gerrit.wikimedia.org/r/mediawiki/extensions/AbuseFilter'


def info(wiki='enwiki', version='1.47.0-wmf.23', core='aaa', config='ccc',
         extra=()):
    checkouts = [
        {'repo': CONFIG, 'branch': 'master', 'commit_ref': config},
        {'repo': CORE, 'branch': f'wmf/{version}', 'commit_ref': core},
    ]
    checkouts.extend(extra)
    return {'dbname': wiki, 'version': version, 'checkouts': checkouts}


class DeployInfoTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.execute('PRAGMA foreign_keys = ON')
        deployinfo.setup_db(self.conn)

    def tearDown(self):
        self.conn.close()

    def snapshots(self):
        return self.conn.execute(
            'SELECT id, wiki, version, fetched_at, last_seen_at '
            'FROM deploy_snapshot ORDER BY id').fetchall()

    def checkouts(self, snapshot_id):
        return self.conn.execute(
            'SELECT repo, branch, commit_ref FROM deploy_snapshot_checkout '
            'WHERE snapshot_id = ? ORDER BY repo', (snapshot_id,)).fetchall()

    def test_first_poll_creates_snapshot_with_checkouts(self):
        sid = deployinfo.record(self.conn, 'enwiki', info(), now=100)
        self.assertIsNotNone(sid)
        self.assertEqual(
            self.snapshots(), [(sid, 'enwiki', '1.47.0-wmf.23', 100, 100)])
        self.assertEqual(self.checkouts(sid), [
            (CORE, 'wmf/1.47.0-wmf.23', 'aaa'),
            (CONFIG, 'master', 'ccc'),
        ])

    def test_unchanged_poll_updates_last_seen_only(self):
        sid = deployinfo.record(self.conn, 'enwiki', info(), now=100)
        self.assertIsNone(deployinfo.record(self.conn, 'enwiki', info(), now=400))
        self.assertEqual(
            self.snapshots(), [(sid, 'enwiki', '1.47.0-wmf.23', 100, 400)])

    def test_checkout_order_does_not_change_checksum(self):
        deployinfo.record(self.conn, 'enwiki', info(), now=100)
        reordered = info()
        reordered['checkouts'].reverse()
        self.assertIsNone(
            deployinfo.record(self.conn, 'enwiki', reordered, now=200))

    def test_changed_commit_creates_new_snapshot(self):
        deployinfo.record(self.conn, 'enwiki', info(), now=100)
        sid = deployinfo.record(self.conn, 'enwiki', info(core='bbb'), now=200)
        self.assertIsNotNone(sid)
        self.assertEqual(len(self.snapshots()), 2)
        self.assertIn((CORE, 'wmf/1.47.0-wmf.23', 'bbb'), self.checkouts(sid))

    def test_added_repo_creates_new_snapshot(self):
        deployinfo.record(self.conn, 'enwiki', info(), now=100)
        added = info(extra=[{'repo': EXT, 'branch': 'x', 'commit_ref': 'eee'}])
        self.assertIsNotNone(
            deployinfo.record(self.conn, 'enwiki', added, now=200))

    def test_rollback_to_earlier_state_creates_new_snapshot(self):
        deployinfo.record(self.conn, 'enwiki', info(), now=100)
        deployinfo.record(self.conn, 'enwiki', info(core='bbb'), now=200)
        self.assertIsNotNone(
            deployinfo.record(self.conn, 'enwiki', info(), now=300))
        self.assertEqual(len(self.snapshots()), 3)

    def test_wikis_are_tracked_separately(self):
        deployinfo.record(self.conn, 'enwiki', info(), now=100)
        self.assertIsNotNone(deployinfo.record(
            self.conn, 'testwiki', info(wiki='testwiki'), now=100))

    def test_missing_branch_is_stored_as_null(self):
        sid = deployinfo.record(self.conn, 'enwiki', info(
            extra=[{'repo': EXT, 'commit_ref': 'eee'}]), now=100)
        self.assertIn((EXT, None, 'eee'), self.checkouts(sid))

    def test_invalid_info_is_rejected_and_writes_nothing(self):
        bad = [
            info(wiki='testwiki'),
            {'dbname': 'enwiki', 'version': 'v', 'checkouts': []},
            {'dbname': 'enwiki', 'checkouts': info()['checkouts']},
            info(extra=[{'repo': EXT}]),
            info(extra=[{'repo': CORE, 'commit_ref': 'zzz'}]),
        ]
        for payload in bad:
            with self.subTest(payload=payload):
                with self.assertRaises(deployinfo.InvalidDeploymentInfo):
                    deployinfo.record(self.conn, 'enwiki', payload, now=100)
        self.assertEqual(self.snapshots(), [])

    def test_collect_continues_after_one_wiki_fails(self):
        def fake_fetch(host):
            if host == 'test.wikipedia.org':
                raise RuntimeError('boom')
            wiki = {h: w for w, h in deployinfo.WIKIS.items()}[host]
            return info(wiki=wiki)

        failures = deployinfo.collect(
            self.conn, fetch=fake_fetch, clock=lambda: 100)
        self.assertEqual(failures, 1)
        self.assertEqual(
            sorted(row[1] for row in self.snapshots()),
            ['commonswiki', 'enwiki', 'mediawikiwiki'])


if __name__ == '__main__':
    unittest.main()
