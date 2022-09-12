SHELL=/bin/bash

README.ipynb: data/train.db data/TRAINS
	jupyter nbconvert --to notebook --inplace --execute "README.ipynb"

README.md: README.ipynb
	jupyter nbconvert README.ipynb --to markdown --output README.md

.PHONY: bugs older start blockers dbs-from-scratch
