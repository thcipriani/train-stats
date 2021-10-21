#!/usr/bin/env python3

import argparse
import re


def mediawiki_version(version):
    """
    Credit: Mukunda Modell
    """
    try:
        return re.match("(\\d+\\.\\d+(\\.\\d+-)?wmf\\.?\\d+)", version).group(0)
    except AttributeError:
        raise argparse.ArgumentTypeError(
            'Invalid wmf version "%s" expected: #.##.#-wmf.#' % version
        )


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '-w',
        '--wmf-version',
        dest='versions',
        action='append',
        required=True,
        type=mediawiki_version,
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
    ap.add_argument(
        '--tylers-only-do-this',
        action='store_true',
        help='I am dummy'
    )
    return ap.parse_args()
