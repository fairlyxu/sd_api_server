#!/bin/sh
#nohup sh -x run_client.sh >/dev/null 2>log &
#nohup sh -x run.sh >/dev/null 2>log &

while [ 1 ]; do
  python3 client_v2.py
done
