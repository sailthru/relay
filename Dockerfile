FROM continuumio/miniconda
MAINTAINER Alex Gaudio <agaudio@sailthru.com>
ENV PATH /opt/anaconda/bin:$PATH

RUN apt-get install -y -f procps
WORKDIR /relay
COPY ./setup.py /relay/
RUN conda install setuptools numpy pyzmq && python setup.py install
COPY ./relay /relay/relay
RUN python setup.py develop

EXPOSE 8080

CMD relay
