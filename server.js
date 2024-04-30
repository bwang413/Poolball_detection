const server = require('http').createServer();
const io = require('socket.io')(server);
console.log("started");
io.on('connection', (client) => {
  client.on('data', data => {
    console.log(data);
  });
  client.on('disconnect', () => {

  });
});
server.listen(8089);