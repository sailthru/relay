import json
import zmq
import pandas as pd
import pylab


def getstream(address):
    c = zmq.Context()
    s = c.socket(zmq.SUB)
    s.setsockopt(zmq.SUBSCRIBE, '')
    s.connect(address)
    while True:
        yield s.recv()


def populate(df, n, stream):
    m = df.shape[0]
    while True:
        next(stream)
        j = next(stream)

        d = json.loads(j).get('data')
        if d:
            df.loc[df.shape[0]] = d

        if df.shape[0] >= n + m:
            break


def plot_df(df):
    for i in range(df.shape[1]):
        pylab.subplot(df.shape[1], 1, i + 1)
        pylab.plot(df[i])
    pylab.show(block=False)


address = 'ipc:///tmp/relaylog'
df = pd.DataFrame(columns=[0, 1, 2])
populate(df, 500, getstream(address))
plot_df(df)


import IPython
IPython.embed()
