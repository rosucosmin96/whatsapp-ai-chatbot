const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const config = require('./config');

// Initialize WhatsApp client
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

// Handle QR code generation
client.on('qr', (qr) => {
    console.log('QR RECEIVED, scan with WhatsApp:');
    qrcode.generate(qr, {small: true});
});

// Handle ready event
client.on('ready', () => {
    console.log('WhatsApp client is ready!');
});

// Handle incoming messages
client.on('message', async (message) => {
    if (message.isGroupMsg) return; // Skip group messages
    
    const userPhone = message.from;
    const messageContent = message.body;

    try {
        console.log(`Message from ${userPhone}: ${messageContent}`);
        
        // Send message to FastAPI
        const response = await axios.post(config.apiUrl, {
            phone: userPhone,
            message: messageContent
        });
        
        // Send response back to user
        await message.reply(response.data.response);
        
    } catch (error) {
        console.error('Error processing message:', error);
    }
});

// Initialize the client
client.initialize(); 