#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat<<USE
    USAGE:
      $0 <version>
    EXAMPLE:
      $0 1.38.0-wmf.2
USE
}

commit() {
    local msg
    msg="$@"
    git commit -a -m "$msg"
}

submodules() {
    git -C submodules/operations/mediawiki-config fetch || :
    git -C submodules/operations/mediawiki-config rebase || :
    commit 'Bump operations/mediawiki-config' || :
}

newversion() {
    local version
    version="$1"
    python3 trainstats.py -w "$version"
}

update_trains() {
    local version trains
    version="$1"
    trains=$(tail +2 data/TRAINS)
    printf "%s\n%s" "$trains" "$version" > data/TRAINS
}

main() {
    if (( $# < 1 )); then
        usage
        exit 1
    else
        version="$@"
    fi

    if [[ "$version" == "auto" ]]; then
        version=$(git ls-remote --heads https://gerrit.wikimedia.org/r/mediawiki/core refs/heads/wmf/* | \
            awk '{print $2}' | \
            sort --version-sort --reverse | \
            head -1 | \
            cut -d'/' -f4
        )
    fi

    indb=$(printf 'select version from train where version = "%s"\n' "$version" | sqlite3 data/train.db)

    if [[ "$indb" == "$version" ]]; then
        printf '"%s" in Database. Nothing to do. Exiting...\n' "$version"
        exit 0
    fi

    if [ ! -d submodules/operations/mediawiki-config ] || [ ! -f trainstats.py ]; then
        echo "You're running this from the wrong directory, bub"
        usage
        exit 1
    fi
    submodules
    newversion "$version"
    update_trains "$version"
    make README.ipynb
    make README.md
    commit "./update.sh $version"
}

main "$@"
