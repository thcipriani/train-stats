#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

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
    git -C "$SCRIPT_DIR" commit -a -m "$msg"
}

submodules() {
    git -C "$SCRIPT_DIR"/submodules/operations/mediawiki-config fetch || :
    git -C "$SCRIPT_DIR"/submodules/operations/mediawiki-config checkout --force origin/master || :
    commit 'Bump operations/mediawiki-config' || :
}

newversion() {
    local version
    version="$1"
    python3 "$SCRIPT_DIR"/trainstats.py -w "$version"
}

update_trains() {
    local version trains
    version="$1"
    trains=$(tail +2 "$SCRIPT_DIR"/data/TRAINS)
    printf "%s\n%s" "$trains" "$version" > "$SCRIPT_DIR"/data/TRAINS
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

    indb=$("$SCRIPT_DIR"/scripts/get_version.py "$version")

    if [[ "$indb" == "$version" ]]; then
        printf '"%s" in Database. Nothing to do. Exiting...\n' "$version"
        exit 0
    fi

    submodules
    newversion "$version"
    update_trains "$version"
    cd "$SCRIPT_DIR"
    make README.ipynb
    make README.md
    commit "./update.sh $version"
}

main "$@"
