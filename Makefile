SHELL=/bin/bash

README.md:
	jupyter nbconvert README.ipynb --to markdown --output README.md

dumbs:
	for i in {1..23}; do python3 trainstats.py --tylers-only-do-this -w 1.37.0-wmf.$$i; done
	for i in {1..38}; do python3 trainstats.py --tylers-only-do-this -w 1.36.0-wmf.$$i; done
	for i in {1..41}; do python3 trainstats.py --tylers-only-do-this -w 1.35.0-wmf.$$i; done
	for i in {1..25}; do python3 trainstats.py --tylers-only-do-this -w 1.34.0-wmf.$$i; done
	for i in {1..25}; do python3 trainstats.py --tylers-only-do-this -w 1.33.0-wmf.$$i; done
	for i in {1..26}; do python3 trainstats.py --tylers-only-do-this -w 1.32.0-wmf.$$i; done
	for i in {1..30}; do python3 trainstats.py --tylers-only-do-this -w 1.31.0-wmf.$$i; done
	for i in {2..19}; do python3 trainstats.py --tylers-only-do-this -w 1.30.0-wmf.$$i; done
	for i in {1..21}; do python3 trainstats.py --tylers-only-do-this -w 1.29.0-wmf.$$i; done
	for i in {1..23}; do python3 trainstats.py --tylers-only-do-this -w 1.28.0-wmf.$$i; done
	for i in {16..23}; do python3 trainstats.py --tylers-only-do-this -w 1.27.0-wmf.$$i; done

bugs:
	for i in {1..15}; do python3 trainstats.py --only-bugs -w 1.37.0-wmf.$$i; done
	for i in {1..38}; do python3 trainstats.py --only-bugs -w 1.36.0-wmf.$$i; done
	for i in {1..41}; do python3 trainstats.py --only-bugs -w 1.35.0-wmf.$$i; done
	for i in {1..25}; do python3 trainstats.py --only-bugs -w 1.34.0-wmf.$$i; done
	for i in {1..25}; do python3 trainstats.py --only-bugs -w 1.33.0-wmf.$$i; done
	for i in {1..26}; do python3 trainstats.py --only-bugs -w 1.32.0-wmf.$$i; done
	for i in {1..30}; do python3 trainstats.py --only-bugs -w 1.31.0-wmf.$$i; done
	for i in {2..19}; do python3 trainstats.py --only-bugs -w 1.30.0-wmf.$$i; done
	for i in {1..21}; do python3 trainstats.py --only-bugs -w 1.29.0-wmf.$$i; done
	for i in {1..23}; do python3 trainstats.py --only-bugs -w 1.28.0-wmf.$$i; done
	for i in {16..23}; do python3 trainstats.py --only-bugs -w 1.27.0-wmf.$$i; done

older:
	for i in {16..23}; do python3 stats-per-train.py -w 1.27.0-wmf.$$i; done
	for i in {1..23}; do python3 stats-per-train.py -w 1.28.0-wmf.$$i; done
	for i in {1..21}; do python3 stats-per-train.py -w 1.29.0-wmf.$$i; done
	for i in {2..19}; do python3 stats-per-train.py -w 1.30.0-wmf.$$i; done

start:
	for i in {1..15}; do python3 stats-per-train.py --only-start-time -w 1.37.0-wmf.$$i; done
	for i in {1..38}; do python3 stats-per-train.py --only-start-time -w 1.36.0-wmf.$$i; done
	for i in {1..41}; do python3 stats-per-train.py --only-start-time -w 1.35.0-wmf.$$i; done
	for i in {1..25}; do python3 stats-per-train.py --only-start-time -w 1.34.0-wmf.$$i; done
	for i in {1..25}; do python3 stats-per-train.py --only-start-time -w 1.33.0-wmf.$$i; done
	for i in {1..26}; do python3 stats-per-train.py --only-start-time -w 1.32.0-wmf.$$i; done
	for i in {1..30}; do python3 stats-per-train.py --only-start-time -w 1.31.0-wmf.$$i; done

blockers:
	for i in {5..6}; do python3 stats-per-train.py --only-blockers -w 1.37.0-wmf.$$i; done
	for i in {1..38}; do python3 stats-per-train.py --only-blockers -w 1.36.0-wmf.$$i; done
	for i in {1..41}; do python3 stats-per-train.py --only-blockers -w 1.35.0-wmf.$$i; done
	for i in {1..25}; do python3 stats-per-train.py --only-blockers -w 1.34.0-wmf.$$i; done
	for i in {1..25}; do python3 stats-per-train.py --only-blockers -w 1.33.0-wmf.$$i; done
	for i in {1..26}; do python3 stats-per-train.py --only-blockers -w 1.32.0-wmf.$$i; done
	for i in {1..30}; do python3 stats-per-train.py --only-blockers -w 1.31.0-wmf.$$i; done

dbs-from-scratch:
	for i in {1..6}; do python3 stats-per-train.py -w 1.37.0-wmf.$$i; done
	for i in {1..38}; do python3 stats-per-train.py -w 1.36.0-wmf.$$i; done
	for i in {1..41}; do python3 stats-per-train.py -w 1.35.0-wmf.$$i; done
	for i in {1..25}; do python3 stats-per-train.py -w 1.34.0-wmf.$$i; done
	for i in {1..25}; do python3 stats-per-train.py -w 1.33.0-wmf.$$i; done
	for i in {1..26}; do python3 stats-per-train.py -w 1.32.0-wmf.$$i; done
	for i in {1..30}; do python3 stats-per-train.py -w 1.31.0-wmf.$$i; done

.PHONY: bugs older start blockers dbs-from-scratch
