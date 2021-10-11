#!/usr/bin/env bash
"""
Train summary email flask app
=============================

Dumps out the skeleton of a train summary email magically!
"""

from flask import Flask
from flask.templating import render_template

from phabricator import Phabricator
from sparklines import sparklines
import sqlite3

import trainstats
import trainblockers

def _sparklines(arr: list) -> str:
    return ''.join([x for x in sparklines(arr)])

class TrainsStats(object):
    def __init__(self, trains_stats):
        self._trains = {}
        self.patches = []
        self.rollbacks = []
        self.days_delay = []
        self.blocker_count = []
        for train_stats in trains_stats:
            ts = TrainStats(train_stats)
            self.patches.append(ts.patches)
            self.rollbacks.append(ts.patches)
            self.days_delay.append(ts.days_delay)
            self.blocker_count.append(ts.blocker_count)
            self._trains[ts.version] = ts

    @property
    def patch_sparklines(self):
        print(f'Patches: {self.patches[::-1]}')
        return _sparklines(self.patches[::-1])

    @property
    def rollbacks_sparklines(self):
        print(f'rollbacks: {self.rollbacks[::-1]}')
        return _sparklines(self.rollbacks[::-1])

    @property
    def days_delay_sparklines(self):
        print(f'delay: {self.days_delay[::-1]}')
        return _sparklines(self.days_delay[::-1])

    @property
    def blocker_count_sparklines(self):
        print(f'blockers: {self.blocker_count[::-1]}')
        return _sparklines(self.blocker_count[::-1])

    def __getitem__(self, item):
        return self._trains[item]


class TrainStats(object):
    def __init__(self, stats):
        self.id = stats[0]
        self.version = stats[1]
        self.patches = stats[2]
        self.rollbacks = stats[3]
        self.days_delay = stats[4]
        self.blocker_count = stats[5]

class TrainEmail(object):
    def __init__(self, version, crs):
        self.version = version
        self.crs = crs
        self.last_five_version_ids = None
        self.version = version
        phab = Phabricator()
        self.train_blocker  = trainblockers.TrainBlockers(self.version, phab)
        self.conductor = trainblockers.get_phab_user(
            self.train_blocker.blocker_task['fields']['ownerPHID'],
            phab
        )
        self.backup = trainblockers.get_phab_user(
            self.train_blocker.blocker_task['fields']['custom.train.backup'][0],
            phab
        )
        self.stats = TrainsStats(self.crs.execute('''
            SELECT
                id,
                version,
                patches,
                rollbacks,
                (group0_delay_days + group1_delay_days + group2_delay_days) as days_delay,
                (SELECT count(*) from blocker b WHERE b.train_id = train.id) as blocker_count
            FROM train
            WHERE start_time <= (
                SELECT start_time
                FROM train
                WHERE version = ?
            )
            ORDER BY start_time desc
            LIMIT 5
        ''', (self.version,)).fetchall())
        self.thanks = set()
        for row in self.crs.execute('''
            SELECT
                blocker,
                unblocker
            FROM train t
            JOIN blocker b ON b.train_id = t.id
            WHERE version = ?
        ''', (self.version,)).fetchall():
            if row[0] not in [self.conductor, self.backup]:
                self.thanks.add(row[0])
            if row[1] not in [self.conductor, self.backup]:
                self.thanks.add(row[1])


    @property
    def patches(self):
        return self.stats[self.version].patches

    @property
    def rollbacks(self):
        return self.stats[self.version].rollbacks

    @property
    def days_delay(self):
        return self.stats[self.version].days_delay

    @property
    def blocker_count(self):
        return self.stats[self.version].blocker_count

app = Flask(__name__)

def make_train_email(version, crs):
    te = TrainEmail(version, crs)
    return render_template(
        'email.html',
        train_email=te
    )

@app.route('/')
def main():
    # Last train by default
    conn = sqlite3.connect(trainstats.DB_PATH)
    crs = conn.cursor()
    version = crs.execute('''
        SELECT version
        FROM train
        ORDER BY start_time desc LIMIT 1
    '''
    ).fetchone()[0]
    return make_train_email(version, crs)
    print(version)
    te = TrainEmail(version)
    return (version, 200)

if __name__ == "__main__":
    app.run(debug=True)
