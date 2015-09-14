#!/usr/bin/env bash
# This shows you Relay in action.  Point your browser to:
# http://<dockerip>:8080

# <dockerip> is probably "localhost"
# on mac, it's probably your boot2docker vm's IP address, $DOCKER_HOST


dir="$( cd "$( dirname "$( dirname "$0" )" )" && pwd )"

docker-compose build relay

(
echo opening browser tab
sleep 1
cat <<EOF | python
import webbrowser
webbrowser.open_new_tab("http://localdocker:8080")
EOF
) &

docker-compose up --x-smart-recreate

