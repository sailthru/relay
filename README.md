Relay: A thermostat for distributed systems
============

Quickstart with a demo!
------------

```
./bin/demo.sh  # You must have Docker installed
```

Navigate your browser to:

```
http://<dockerip>:8080  # <dockerip> is probably $DOCKER_HOST or "localhost"
```

What problem does it solve?
------------

Imagine I wish to manually manage the temperature of a room.  I have a
thermostat at one corner and a heater and/or cooler at the other, and
let's say I wish to maintain a target temperature of 68 degrees.  I
decide on a simple rule: add heat to the room until the thermometer
reaches 68 degress.  There is a problem, though.  Heat takes some time
to appear on the thermometer.  If I wait until the thermometer reads my
target temperature, I drastically overheat the room.  So I decide on
another rule: slowly add heat to the room until it reaches the target
temperature.  After trying this out, I realize that the temperature in
the room doesn't get above 60 degrees because it is apparently so cold
outside that I'm not adding enough heat to counter-balance those
effects.

It looks like I need a more sophisticated temperature regulating
algorithm.  This type of problem is often quite complex, and there is a
field called Control Theory dedicated to problems like the ones that a
thermostat solves.

How does this apply to distributed systems?
------------

Distributed systems need thermostats everywhere!  Perhaps you have a
need to add workers in proportion to a queue size.  Or in another
scenario, you may need to add more aws nodes when there's a lot of work
to do.  Perhaps your grid scheduler needs to maintain a constant number
of jobs running at a time, once per node, but the number of nodes is
dynamic.  You could use Relay to tune hyper-parameters for online
machine learning algorithms.  Can you think of any applications?  If you
can't, look at a couple timeseries and you'll come up with good ideas,
and there is a good chance that Relay makes solving those quite a bit easier.

In general, Relay is a good candidate for any scenario where you find
yourself looking at some metric and then responding to that metric by
running some code or tweaking your system.

Background: A lesson on PID controllers
------------

A PID controller is a mechanism that implements a control loop.  A
control loop leverages feedback from its previous decisions to make new
decisions about what to do next.  According to
[Wikipedia](http://en.wikipedia.org/wiki/PID_controller), "In the
absence of knowledge of the underlying process, a PID controller has
historically been considered to be the best controller."

PID controllers look at a metric, like room temperature over time, and
represent it as three components.  "P," the "proportional" term, defines
the amount of error between the current metric value and the target
value.  (How far off is the temperature from the target temperature?).
"I" and "D" look at the integral and derivative of the metric.  The
amount of "heating" or "cooling" a PID controller decides to add depends
on a weighted sum of those three terms.


    MV = K_p * P + K_i * I + K_d * D

        where
        P = error between current value and target value
        I = integral of this error over time
        D = derivative of this error over time
        K_* - these are weights for the above

        MV = the amount of heat or cooling to add to the system

The challenge, in general, is to find the ideal weighting for the
```K_*``` terms.


Background: How does Relay solve this?
------------

Relay is technically a modified PI controller.
Specifically, ```K_p = 1```, ```K_d * D = 0```, and ```K_i``` is chosen
according to a tuning algorithm.  Given ```P```, ```I```, and an error
history, the amount of heat or cooling to add (MV) is:

    MV = P + K_i * I

        where
        P = PV - SP .... (metric value - target) value at timestep i
        I = sum(P_hist) / len(P_hist) .... average value of P over time.
        K_i is defined below as a weighted sum of component frequencies.

The challenge in this problem is to answer the question: "At the current
moment in time, how important is the history of errors?"  Here's how
Relay does this:

If we can assume the signal is made up of various periodic (repeating)
functions, we can evaluate, at any point in time, how far away from
“zero error” each periodic function is.  By joining all these errors
as a weighted sum, we can estimate how important the error is by
considering the relative presence of the signal's repeating components.

A Fast Fourier Transform (we use FFT) breaks down a signal (ie Relay's
error history) into a number of repeating sine waves of different
frequencies.  For any given component frequency, ```f_j``` we can look
at the current phase, ```ø_i```, of the wave we happen to be in.  Since
we sample the signal (and therefore each component frequency) at a known
rate, we can also calculate the number of samples, ```n```, in this
particular frequency that we consider.  In one period, large frequency
components will have less samples than small frequency components.
Given a component frequency, ```f_j```, the current phase, ```ø```, and
the number of samples in one wavelength, ```n```, we can then look back
we can find how much of ```n - 1``` most recent samples the the current
phase is worth, or
```h_j = abs(sin(ø_i)) / Σ_k [ abs(sin(ø_(i-k))) ]  where k = [0:n)```.

If we calculate ```h_j``` for each frequency, ```j```, and than take a
weighted sum of frequencies, we define a tuning parameter, ```K_i```,
that responds quite well to periodicity of the signal!

At the current timestep:
    For each f_j:
      n=num samples in f_j
      h_j = abs(sin(ø_i)) / Σ_k [ abs(sin(ø_(i-k))) ]  where k = [0:n)

    K_i = Σ_j [ f_j * h_j ]


    And finally:
    MV = P + K_i * I


Quick Start!
------------

Install relay

    pip install relay.runner

      OR for this demo:

    pip install "relay.runner[webui]"  # webui needs ZeroMQ installed

Look at the usage

    relay -h

Try a demo.  This demo runs monitors the number of a certain kind of bash echo command running every .1 seconds, and if there aren't enough of them running, will add more.

    relay --metric bash_echo_metric --warmer bash_echo_warmer --delay .1 --sendstats webui --target 20

    # navigate to localhost:8080 in a web browser

    # demos 2 and 3: changing target values over time
    relay --metric bash_echo_metric --warmer bash_echo_warmer --delay .1 --sendstats webui --target oscillating_setpoint
    relay --metric bash_echo_metric --warmer bash_echo_warmer --delay .1 --sendstats webui --target squarewave_setpoint

    # demo 4: running a heater and cooler at the same time
    relay --metric bash_echo_metric --warmer bash_echo_warmer --delay .1 --sendstats webui --target squarewave_setpoint --cooler bash_echo_cooler


Detailed Usage:
------------

Relay has 4 main components:

    metric - a timeseries of numbers that you wish to monitor (ie temperature)
    target - a numerical value (or timeseries) that you'd like the
        metric to be at (ie same units as the metric)

    warmer - a function that Relay assumes will increase the metric
    cooler - a function that Relay assumes will decrease the metric

In certain cases it can be more efficient to run a heater and air
conditioner at the same time, but generally it's not.  It's usually safe
to apply this reasoning to Relay.  You generaly should define only a
warmer or a cooler, but sometimes it is better to define both.


Relay makes some assumptions:

- The metric you monitoring is eventually consistent.  This means that
  if it takes a little while for effects to become apparent, Relay will
  figure this out as soon as it acquires enough error history to do so.

- The signal you're monitoring is continuous, integrable, and otherwise
  valid input to a Fourier Transforms.

- Warmer functions increase metric values and Cooler functions decrease
  metric values.

- If Relay accrues a large history of error, it will remember that error
  for n samples, where n is the size of Relay's lookback window.  If a
  warmer or cooler function suddenly stops working or something changes
  how it affects themetric, Relay's decisions may become less predictable
  until it stabilizes.

- You can run multiple redundant Relays!  If you add multiple Relay
  processes, they will each account for a part of the signal.  If you
  stop multiple Relays, the remaining ones will figure this out and
  re-adjust themselves over the next few samples.
