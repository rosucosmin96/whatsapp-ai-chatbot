const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const config = require('./config');

// Track when the bot started to avoid processing old messages
const botStartTime = Date.now();
let botReadyTime = null; // Track when bot becomes ready
let isProcessingEnabled = false; // Only process messages after ready + delay

console.log(`🤖 Bot started at: ${new Date(botStartTime).toISOString()}`);

// Initialize WhatsApp client
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
        headless: true,
    }
});

// Handle QR code generation
client.on('qr', (qr) => {
    console.log('QR RECEIVED, scan with WhatsApp:');
    qrcode.generate(qr, {small: true});
});

// Handle ready event
client.on('ready', () => {
    botReadyTime = Date.now();
    console.log(`✅ WhatsApp client is ready at: ${new Date(botReadyTime).toISOString()}`);
    
    // Add a delay before enabling message processing
    // This prevents processing message history that loads after ready event
    setTimeout(() => {
        isProcessingEnabled = true;
        console.log(`🚀 Message processing enabled at: ${new Date().toISOString()}`);
        console.log('✨ Bot is now ready to respond to NEW messages only!');
    }, 10000); // Wait 10 seconds after ready before processing messages
});

// Handle incoming messages
client.on('message', async (message) => {
    try {
        // Don't process anything until we're fully ready
        if (!isProcessingEnabled) {
            console.log(`⏸️  BLOCKED: Processing not enabled yet (message from ${message.from})`);
            return;
        }
        
        // MULTIPLE GROUP CHECKS for extra safety
        if (message.isGroupMsg) {
            console.log(`BLOCKED: Group message detected (isGroupMsg): ${message.from}`);
            return;
        }
        
        // Additional group detection by chat ID format
        if (message.from && message.from.includes('@g.us')) {
            console.log(`BLOCKED: Group detected by ID format: ${message.from}`);
            return;
        }
        
        // Skip messages from myself (prevent bot loops)
        if (message.fromMe) {
            console.log(`BLOCKED: Message from self: ${message.from}`);
            return;
        }
        
        // Enhanced timestamp checking - use botReadyTime instead of botStartTime
        const messageTimestamp = message.timestamp * 1000; // Convert to milliseconds
        const messageDate = new Date(messageTimestamp);
        const readyDate = new Date(botReadyTime);
        
        // Only process messages sent AFTER the bot became ready + delay
        const processingEnabledTime = botReadyTime + 10000; // Add the 10 second delay
        
        console.log(`⏰ TIMESTAMP CHECK:
        - Message timestamp: ${message.timestamp} (${messageDate.toISOString()})
        - Bot ready time: ${botReadyTime} (${readyDate.toISOString()})
        - Processing enabled at: ${processingEnabledTime} (${new Date(processingEnabledTime).toISOString()})
        - Message is ${messageTimestamp < processingEnabledTime ? 'OLDER' : 'NEWER'} than processing start`);
        
        if (messageTimestamp < processingEnabledTime) {
            console.log(`BLOCKED: Message after bot processing date (from ${message.from}: "${message.body}")`);
            return;
        }
        
        // Skip empty messages
        if (!message.body || message.body.trim() === '') {
            console.log(`BLOCKED: Empty message from ${message.from}`);
            return;
        }
        
        const userPhone = message.from;
        const messageContent = message.body;

        console.log(`✅ PROCESSING: NEW message from ${userPhone}: ${messageContent}`);
        
        // Send message to FastAPI
        const response = await axios.post(config.apiUrl, {
            phone: userPhone,
            message: messageContent
        });
        
        // Send response back to user
        await message.reply(response.data.response);
        console.log(`✅ SENT: Response to ${userPhone}`);
        
    } catch (error) {
        if (error.code === 'ECONNREFUSED') {
            console.error('❌ API server not running at localhost:8000');
            // Don't reply if API is down to avoid confusion
        } else {
            console.error('❌ ERROR processing message:', error.message);
            console.error('Message details:', {
                from: message.from,
                isGroup: message.isGroupMsg,
                fromMe: message.fromMe,
                timestamp: message.timestamp,
                timestampMs: message.timestamp * 1000,
                messageDate: new Date(message.timestamp * 1000).toISOString(),
                botReadyTime: botReadyTime,
                readyDate: new Date(botReadyTime || 0).toISOString(),
                body: message.body,
                processingEnabled: isProcessingEnabled
            });
        }
    }
});

// Initialize the client
client.initialize(); 