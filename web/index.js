var express = require('express');
var app = express();
var server = require('http').Server(app);
var io = require('socket.io')(server);

// console.log('configure zmq');
var zmq = require('zmq');
var sub = zmq.socket('sub');
sub.connect('tcp://127.0.0.1:2001');
sub.subscribe('');
sub.on('message', function () {
  for (var key in arguments) {
    console.log('FROMJS ' + arguments[key]);
  }
});

server.listen(8080);

app.use('/vendor', express.static(__dirname + '/vendor'));

app.get('/', function (req, res) {
    res.sendFile(__dirname + '/index.html');
});

io.on('connection', function (socket) {
    socket.emit('news', { x: 'world' });
      socket.on('my other event', function (data) {
            console.log(data);
              });

    setInterval(function() {
      socket.emit('pvdata', {x: x, y: x % 20}); x = (x+1)%20;},
      20);
});

var x = 1;
