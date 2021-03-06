#!/bin/bash

# Runing from `/etc/rc.local`

export FLASK_APP=web
flask run --host=0.0.0.0 &

while true
do
    echo -e "\nrun.sh: Python app.py starting\n" | tee -a "run.log"
    python3 -u app.py | tee -a "run.log"
    echo "run.sh: Python app.py killed, restarting" | tee -a "run.log"
done