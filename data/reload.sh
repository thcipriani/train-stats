#!/bin/bash
# This is a script that can be used to reload datasette and refresh firefox when you save changes.
# Auto reload/refresh makes testing changes a lot easier/quicker.
#
# This is essentially an infinite loop that restarts datasette when datasette exits,
# then triggers firefox to refresh the current tab using xdotool (unix/xwindows only, sorry mac people)
#
# This script triggers a restart by sending a signal to the datasette process:
#
# SIGUSR1 causes datasette to exit and the loop below restarts it.
#
# To make this useful, I have a vs.code plugin set up to run this script every time
# I save a file in the data/ subdirectory. This avoids complex/resource limited filesystem watchers.
#
# run this script in a spare terminal to keep datasette running, then have your editor trigger
# this same script to restart datasette. The script doesn't go into an infinite loop if it finds
# and existing datasette process to kill. If no datasette process is founed then it loops.
# ctrl-c to end the infinite loop.
#
source venv/bin/activate

PORT=8002

refresh() {
    # refresh the active tab in the first visible firefox window that is found.
    # if you have more than one firefox window, minimize all but one.

    sleep 2
    CURRENT_WID=$(xdotool getwindowfocus)

    WID=$(xdotool search --onlyvisible --limit 1 --name "Mozilla Firefox")
    xdotool windowactivate $WID
    xdotool key F5
    xdotool windowactivate $CURRENT_WID
    exit 0 # don't run the infinite loop if we successfully killed a background process
}

# restart and refresh
pkill -f "datasette.+$PORT" -USR1 && refresh;

# we only get this far if datasette wasn't already running, so start it and go into the loop:

command="datasette -p $PORT -h 0.0.0.0 --reload ${fileDirname} $@"

echo "running: $command"
cleanup () {
    exit 0;
}
trap "cleanup" SIGINT
# trap the SIGINT so that ctrl+c still works in the controlling terminal.
while [ 1 ]; do
 echo $command;
 $command;

done
echo "Exiting..."
