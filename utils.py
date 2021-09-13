#!/usr/bin/env python3

import argparse


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '-w',
        '--wmf-version',
        dest='versions',
        action='append',
        required=True,
        help='wmf version'
    )
    ap.add_argument(
        '--show-rollbacks',
        action='store_true',
        help='Show rollbacks'
    )
    ap.add_argument(
        '--only-start-time',
        action='store_true',
        help='only insert train start time'
    )
    ap.add_argument(
        '--only-blockers',
        action='store_true',
        help='only insert blockers'
    )
    ap.add_argument(
        '--only-patches',
        action='store_true',
        help='update only'
    )
    ap.add_argument(
        '--only-bugs',
        action='store_true',
        help='only insert train bugs'
    )
    return ap.parse_args()
