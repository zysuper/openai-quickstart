#! /bin/bash

nohup jupyter lab --no-browser --port=8888 \
--ip=0.0.0.0 --allow-root --NotebookApp.token='' --NotebookApp.password='' \
--notebook-dir=./ 2>&1 > /dev/null &
