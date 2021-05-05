SHELL=/bin/bash

zomg:
	for i in {1..3}; do python3 stats-per-train.py --append-stats-for-thcipriani-zomg -w 1.37.0-wmf.$$i; done
	for i in {1..38}; do python3 stats-per-train.py --append-stats-for-thcipriani-zomg -w 1.36.0-wmf.$$i; done
	for i in {1..41}; do python3 stats-per-train.py --append-stats-for-thcipriani-zomg -w 1.35.0-wmf.$$i; done
	for i in {1..25}; do python3 stats-per-train.py --append-stats-for-thcipriani-zomg -w 1.34.0-wmf.$$i; done
	for i in {1..25}; do python3 stats-per-train.py --append-stats-for-thcipriani-zomg -w 1.33.0-wmf.$$i; done
	for i in {1..26}; do python3 stats-per-train.py --append-stats-for-thcipriani-zomg -w 1.32.0-wmf.$$i; done
	for i in {1..30}; do python3 stats-per-train.py --append-stats-for-thcipriani-zomg -w 1.31.0-wmf.$$i; done

csvs-from-scratch:
	for i in {1..3}; do python3 stats-per-train.py -w 1.37.0-wmf.$$i; done
	for i in {1..38}; do python3 stats-per-train.py -w 1.36.0-wmf.$$i; done
	for i in {1..41}; do python3 stats-per-train.py -w 1.35.0-wmf.$$i; done
	for i in {1..25}; do python3 stats-per-train.py -w 1.34.0-wmf.$$i; done
	for i in {1..25}; do python3 stats-per-train.py -w 1.33.0-wmf.$$i; done
	for i in {1..26}; do python3 stats-per-train.py -w 1.32.0-wmf.$$i; done
	for i in {1..30}; do python3 stats-per-train.py -w 1.31.0-wmf.$$i; done

README.md:
	jupyter nbconvert README.ipynb --to markdown --output README.md

.PHONY: csvs-from-scratch zomg
