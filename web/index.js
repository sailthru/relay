var express = require('express');
var app = express();
var server = require('http').Server(app);
var io = require('socket.io')(server);
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
