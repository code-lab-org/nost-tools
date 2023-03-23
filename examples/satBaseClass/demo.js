**const** mqtt = require('mqtt');
**const** fs = require('fs');


**const** client = mqtt.connect('', {
key: fs.readFileSync('client.key'),
cert: fs.readFileSync('client.pem'),
});


client.on('connect', () => {
client.subscribe('demotopic');
client.publish('demotopic', 'Hello mqtt');
});


client.on('message', (topic, message) => {
console.log(`Received message: ${message.toString()}`);
client.end();
});

















