#!/usr/bin/env python3
"""
Train summary email flask app
=============================

Dumps out the skeleton of a train summary email magically!
"""

import argparse

from flask import Flask
from flask.templating import render_template

from phabricator import Phabricator, APIError
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
            self.rollbacks.append(ts.rollbacks)
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
        try:
            self.conductor = trainblockers.get_phab_user(
                self.train_blocker.blocker_task['fields']['ownerPHID'],
                phab
            )
        except APIError:
            self.conductor = 'Release Engineer Team'

        backups = self.train_blocker.blocker_task['fields']['custom.train.backup']
        if backups:
            self.backup = trainblockers.get_phab_user(backups[0], phab)
        else:
            self.backup = 'Nobody .·´¯`(>▂<)´¯`·.'
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
            if row[0] not in [self.conductor, self.backup, 'null']:
                self.thanks.add(row[0])
            if row[1] not in [self.conductor, self.backup, 'null']:
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

def get_crs(db_path):
    conn = sqlite3.connect(db_path)
    return conn.cursor()

def make_train_email(version, crs):
    te = TrainEmail(version, crs)
    return render_template(
        'email.html',
        train_email=te
    )


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/version/<path:version>')
def version(version):
    crs = get_crs(trainstats.DB_PATH)
    try:
        return make_train_email(version, crs)
    except argparse.ArgumentTypeError as e:
        return page_not_found(e)


@app.route('/')
def main():
    # Last train by default
    crs = get_crs(trainstats.DB_PATH)
    version = crs.execute('''
        SELECT version
        FROM train
        ORDER BY start_time desc LIMIT 1
    '''
    ).fetchone()[0]
    return make_train_email(version, crs)

if __name__ == "__main__":
    app.run()
