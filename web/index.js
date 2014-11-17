var express = require('express');
var app = express();
var server = require('http').Server(app);
var io = require('socket.io')(server);

// receive zmq messages
var zmq = require('zmq');
var subscriber = zmq.socket('sub');
subscriber.connect('ipc:///tmp/relaylog');
subscriber.subscribe('');

// when a client connects via websockets,
// forward relevant zmq message data to the client
io.on('connection', function (socket) {

  subscriber.on('message', function () {
    var payload = JSON.parse(arguments[1].toString());
    if (payload.PV) {
      socket.emit('pvdata', {y: payload.PV});
    }
    if (payload.MV) {
      socket.emit('mvdata', {y: payload.MV});
    }
    if (payload.SP) {
      socket.emit('spdata', {y: payload.SP});
    }
  });
});

// configure webserver
server.listen(8080);
app.use('/vendor', express.static(__dirname + '/vendor'));
app.get('/', function (req, res) {
    res.sendFile(__dirname + '/index.html');
});

