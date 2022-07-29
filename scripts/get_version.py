#!/usr/bin/env python3
import argparse
import os
import sqlite3

AP = argparse.ArgumentParser()
AP.add_argument('version', help='Train version, e.g., 1.39.0-wmf.21')
ARGS = AP.parse_args()

DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'train.db')
CONN = sqlite3.connect(DB)
CRS = CONN.cursor()

last_version = CRS.execute('select version from train where version = ?', (ARGS.version,)).fetchone()
if last_version:
    last_version = last_version[0]
print(last_version)
