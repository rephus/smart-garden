#!/bin/bash

# Runing from `/etc/rc.local`
python3 -u app.py | tee -a "run.log"