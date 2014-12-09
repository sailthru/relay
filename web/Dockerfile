FROM dockerfile/nodejs
EXPOSE 8080
EXPOSE 5673
RUN apt-get update && apt-get install -y -f libzmq3 libzmq3-dev
WORKDIR /relay/web
COPY ./package.json /relay/web/
RUN npm install
COPY ./src /relay/web/src/
COPY ./vendor /relay/web/vendor/
CMD node src/index.js tcp://0.0.0.0:5673
