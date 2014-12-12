# This shows you Relay in action.  Point your browser to:
# http://<dockerip>:8080

# <dockerip> is probably "localhost"
# on mac, it's probably your boot2docker vm's IP address, $DOCKER_HOST


dir="$( cd "$( dirname "$( dirname "$0" )" )" && pwd )"

echo start the Relay.web UI
docker run -itd \
  --name relay.web -p 8080:8080 -p 5673:5673 \
  adgaudio/relay.web

(cd $dir && docker build -t adgaudio/relay.runner .)

trap "echo removing relay.web docker container && (docker rm -f relay.web) &" \
  EXIT SIGINT SIGTERM

echo start Relay.runner
docker run -it --rm \
  --name relay.runner \
  --link relay.web:web \
  -e RELAY_WARMER=bash_echo_warmer \
  -e RELAY_METRIC=bash_echo_metric \
  -e RELAY_TARGET=oscillating_setpoint \
  -e RELAY_DELAY=0.1 \
  -e RELAY_RAMP=10 \
  -e RELAY_SENDSTATS='tcp://web:5673' \
  adgaudio/relay.runner


