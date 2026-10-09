#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
MW_CONFIG="$SCRIPT_DIR"/submodules/operations/mediawiki-config

# How long does group2 need to be on a version before we call it "Done"?
# I guess 24 hours ¯\_(ツ)_/¯
STABLE_WIKIVERSION_TIME=$(( 24 * 60 * 60 ))

usage() {
    cat<<USE
    USAGE:
      $0 <version|auto>
    EXAMPLES:
      $0 1.38.0-wmf.2
      $0 auto
USE
}

commit() {
    git -C "$SCRIPT_DIR" commit -a -m "$@"
}

submodules() {
    git -C "$MW_CONFIG" fetch || :
    git -C "$MW_CONFIG" checkout --force origin/master || :
}

pick_python() {
    p=python3
    if [ -d "$SCRIPT_DIR"/venv ]; then
        . "$SCRIPT_DIR"/venv/bin/activate
        p="$SCRIPT_DIR"/venv/bin/python3
        echo 'Activating magic 1'
    elif [ -d "$SCRIPT_DIR"/../venv ]; then
        . "$SCRIPT_DIR"/../venv/bin/activate
        p="$SCRIPT_DIR"/../venv/bin/python3
        echo 'Activating magic 2'
    elif [ -d "$SCRIPT_DIR"/.venv ]; then
        . "$SCRIPT_DIR"/.venv/bin/activate
        p="$SCRIPT_DIR"/.venv/bin/python3
        echo 'Activating magic 3'
    fi
}

collect() {
    "$p" "$SCRIPT_DIR"/deployinfo.py || echo 'deployinfo.py failed :(' >&2
}

newversion() {
    local version
    version="$1"
    $p "$SCRIPT_DIR"/trainstats.py -w "$version"
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

    pick_python
    collect

    submodules

    if [[ "$version" == "auto" ]]; then
        version="$(git -C "$MW_CONFIG" show origin/master:wikiversions.json | \
            jq -er '.enwiki | ltrimstr("php-")')"
        last_change="$(git -C "$MW_CONFIG" log -1 --format=%ct origin/master -- wikiversions.json)"
        age=$(( $(date +%s) - last_change ))
        if (( age <  STABLE_WIKIVERSION_TIME )); then
            printf 'enwiki went to %s %ss ago. Waiting for version to settle. Exiting...' \
                "$version" "$age" >&2
            exit 0
        fi
    fi

    indb=$("$SCRIPT_DIR"/scripts/get_version.py "$version")

    if [[ "$indb" == "$version" ]]; then
        printf '"%s" in Database. Nothing to do. Exiting...\n' "$version"
        exit 0
    fi

    newversion "$version"
    update_trains "$version"
    cd "$SCRIPT_DIR"
    make README.ipynb
    make README.md
    commit "./update.sh $version"
}

main "$@"
