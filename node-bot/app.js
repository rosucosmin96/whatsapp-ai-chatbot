const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const MessageQueue = require('./MessageQueue');

// Track when the bot started to avoid processing old messages
const botStartTime = Date.now();
let botReadyTime = null;
let isProcessingEnabled = false;

console.log(`🤖 Bot started at: ${new Date(botStartTime).toISOString()}`);

// Initialize the message queue
const messageQueue = new MessageQueue();

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
    
    // Start the queue processor
    messageQueue.startProcessor();
    
    // Add a delay before enabling message processing
    setTimeout(() => {
        isProcessingEnabled = true;
        console.log(`🚀 Message processing enabled at: ${new Date().toISOString()}`);
        console.log('✨ Bot is now ready to queue and process messages!');
    }, 10000); // Wait 10 seconds after ready
});

// Handle client disconnection
client.on('disconnected', (reason) => {
    console.log('WhatsApp client disconnected:', reason);
    messageQueue.stopProcessor();
});

// Main message handler - QUEUE ALL VALID MESSAGES
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
        const botPhone = getBotInfo().phoneNumber;
        
        // Only process messages sent AFTER the bot became ready + delay
        const processingEnabledTime = botReadyTime + 10000; // Add the 10 second delay
        
        console.log(`⏰ TIMESTAMP CHECK:
        - Message timestamp: ${message.timestamp} (${messageDate.toISOString()})
        - Bot ready time: ${botReadyTime} (${readyDate.toISOString()})
        - Processing enabled at: ${processingEnabledTime} (${new Date(processingEnabledTime).toISOString()})
        - Message is ${messageTimestamp < processingEnabledTime ? 'OLDER' : 'NEWER'} than processing start`);
        
        if (messageTimestamp < processingEnabledTime) {
            console.log(`BLOCKED: Message before processing enabled (from ${message.from}: "${message.body}")`);
            return;
        }
        
        // Skip empty messages
        if (!message.body || message.body.trim() === '') {
            console.log(`BLOCKED: Empty message from ${message.from}`);
            return;
        }
        
        const userPhone = message.from;
        const messageContent = message.body;
        
        console.log(`✅ VALID: NEW message from ${userPhone}: ${messageContent}`);
        
        // Add to queue - NO IMMEDIATE RESPONSE
        messageQueue.enqueue(userPhone, botPhone, messageContent, message);
        
        // Note: No reply sent here - user will get response only when processing succeeds
        
    } catch (error) {
        console.error('❌ ERROR in message handler:', error.message);
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
});

// Admin commands for queue management
client.on('message', async (message) => {
    // Define admin phone numbers (replace with your actual admin numbers)
    const adminNumbers = [
        '+00000000000'  // Replace with your admin number
    ];
    
    // Check if message is from admin
    const isAdmin = adminNumbers.some(admin => 
        message.from.includes(admin.replace('+', '').replace(/\D/g, ''))
    );
    
    if (!isAdmin || message.fromMe) {
        return;
    }
    
    const command = message.body.toLowerCase().trim();
    
    if (command === '/queue' || command === '/stats') {
        const stats = messageQueue.getStats();
        const preview = messageQueue.getQueuePreview(3);
        
        let response = `📊 **Queue Statistics**
• Current queue: ${stats.current_queue_size} messages
• Total queued: ${stats.total_queued}
• Total processed: ${stats.total_processed}
• Failed attempts: ${stats.total_failed_attempts}
• Success rate: ${stats.success_rate}
• Oldest message: ${stats.oldest_message_age_seconds}s ago
• Currently processing: ${stats.is_processing ? 'Yes' : 'No'}`;

        if (preview.length > 0) {
            response += `\n\n📋 **Next ${preview.length} in queue:**`;
            preview.forEach(item => {
                response += `\n${item.position}. ${item.phone} (${item.queued_ago}) - ${item.message}`;
            });
        }
        
        await message.reply(response);
        
    } else if (command === '/clear') {
        const cleared = messageQueue.clearQueue();
        await message.reply(`🗑️ Cleared ${cleared} messages from queue`);
        
    } else if (command === '/process') {
        if (!messageQueue.isProcessing) {
            messageQueue.processNextMessage();
            await message.reply('🔄 Manual processing triggered');
        } else {
            await message.reply('⚠️ Already processing a message');
        }
        
    } else if (command === '/help') {
        const response = `🤖 **Admin Commands:**
• /queue or /stats - Show queue statistics
• /clear - Clear all queued messages  
• /process - Manually process next message
• /help - Show this help`;
        
        await message.reply(response);
    }
});

// Periodic stats logging (every 3 minutes)
setInterval(() => {
    const stats = messageQueue.getStats();
    if (stats.current_queue_size > 0) {
        console.log(`📊 Queue: ${stats.current_queue_size} messages | Processed: ${stats.total_processed} | Success: ${stats.success_rate}`);
        
        // Log details of first few messages in queue
        const preview = messageQueue.getQueuePreview(2);
        if (preview.length > 0) {
            console.log(`📋 Next in queue: ${preview.map(p => `${p.phone} (${p.queued_ago})`).join(', ')}`);
        }
    }
}, 180000);

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('🛑 Shutting down gracefully...');
    const stats = messageQueue.getStats();
    console.log(`📊 Final stats - Queue: ${stats.current_queue_size}, Processed: ${stats.total_processed}`);
    messageQueue.stopProcessor();
    client.destroy();
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('🛑 Shutting down gracefully...');
    messageQueue.stopProcessor();
    client.destroy();
    process.exit(0);
});

// Initialize the client
client.initialize();

// Add this function after your client initialization
function getBotInfo() {
    if (client.info) {
        const botInfo = client.info;
        return {
            phoneNumber: `+${botInfo.wid.user}`,
            pushname: botInfo.pushname,
            wid: botInfo.wid._serialized,
            platform: botInfo.platform
        };
    }
    return null;
} 