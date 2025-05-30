const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const config = require('./config');

// Track when the bot started to avoid processing old messages
const botStartTime = Date.now();
let botReadyTime = null;
let isProcessingEnabled = false;

console.log(`🤖 Bot started at: ${new Date(botStartTime).toISOString()}`);

// Simple FIFO Message Queue
class MessageQueue {
    constructor() {
        this.queue = [];
        this.isProcessing = false;
        this.processInterval = 5000; // Process every 5 seconds
        this.stats = {
            total_queued: 0,
            total_processed: 0,
            total_failed_attempts: 0
        };
        
        console.log('📥 FIFO Message queue initialized');
    }
    
    // Add message to end of queue (FIFO)
    enqueue(userPhone, messageContent, originalMessage) {
        const queuedMessage = {
            id: Date.now() + Math.random(),
            userPhone,
            messageContent,
            originalMessage,
            queuedAt: Date.now(),
            attemptCount: 0
        };
        
        this.queue.push(queuedMessage);
        this.stats.total_queued++;
        
        console.log(`📥 QUEUED: ${userPhone} | Queue position: ${this.queue.length} | Message: "${messageContent.substring(0, 50)}..."`);
        
        return queuedMessage.id;
    }
    
    // Get first message from queue (FIFO - First In, First Out)
    peek() {
        return this.queue.length > 0 ? this.queue[0] : null;
    }
    
    // Remove first message from queue (after successful processing)
    dequeue() {
        if (this.queue.length > 0) {
            const processed = this.queue.shift();
            this.stats.total_processed++;
            console.log(`✅ REMOVED from queue: ${processed.userPhone} | Remaining: ${this.queue.length}`);
            return processed;
        }
        return null;
    }
    
    // Start the queue processor
    startProcessor() {
        if (this.processorInterval) {
            clearInterval(this.processorInterval);
        }
        
        this.processorInterval = setInterval(() => {
            this.processNextMessage();
        }, this.processInterval);
        
        console.log(`🚀 Queue processor started (checking every ${this.processInterval/1000} seconds)`);
    }
    
    // Process the next message in queue
    async processNextMessage() {
        if (this.isProcessing || this.queue.length === 0) {
            return;
        }
        
        this.isProcessing = true;
        
        const message = this.peek(); // Get first message without removing it
        if (!message) {
            this.isProcessing = false;
            return;
        }
        
        message.attemptCount++;
        this.stats.total_failed_attempts++; // Will be decremented if successful
        
        console.log(`🔄 PROCESSING: ${message.userPhone} (Attempt ${message.attemptCount}) | Queue: ${this.queue.length} messages`);
        
        try {
            // Try to process the message
            const response = await axios.post(config.apiUrl, {
                phone: message.userPhone,
                message: message.messageContent
            }, {
                timeout: 30000 // 30 second timeout
            });
            
            // Check if we got a valid response
            if (response.data && response.data.response && response.data.response.trim() !== '') {
                // SUCCESS: Send response and remove from queue
                await message.originalMessage.reply(response.data.response);
                this.dequeue(); // Remove the successfully processed message
                this.stats.total_failed_attempts--; // Correction: this wasn't actually a failed attempt
                
                console.log(`✅ SUCCESS: Sent response to ${message.userPhone}`);
                
            } else {
                // FAILED: Empty response, keep in queue
                console.log(`⚠️ FAILED: Empty response for ${message.userPhone}, keeping in queue`);
            }
            
        } catch (error) {
            // FAILED: Error occurred, keep in queue
            if (error.code === 'ECONNREFUSED') {
                console.log(`⚠️ FAILED: API server not available for ${message.userPhone}, keeping in queue`);
            } else if (error.code === 'ECONNABORTED') {
                console.log(`⚠️ FAILED: Timeout for ${message.userPhone}, keeping in queue`);
            } else if (error.response && error.response.status === 429) {
                console.log(`⚠️ FAILED: Rate limited for ${message.userPhone}, keeping in queue`);
            } else {
                console.log(`⚠️ FAILED: Error for ${message.userPhone}: ${error.message}, keeping in queue`);
            }
        }
        
        this.isProcessing = false;
    }
    
    // Get queue statistics
    getStats() {
        const now = Date.now();
        const oldestMessageAge = this.queue.length > 0 ? 
            Math.round((now - this.queue[0].queuedAt) / 1000) : 0;
        
        return {
            current_queue_size: this.queue.length,
            total_queued: this.stats.total_queued,
            total_processed: this.stats.total_processed,
            total_failed_attempts: this.stats.total_failed_attempts,
            is_processing: this.isProcessing,
            oldest_message_age_seconds: oldestMessageAge,
            success_rate: this.stats.total_queued > 0 ? 
                ((this.stats.total_processed / this.stats.total_queued) * 100).toFixed(1) + '%' : '0%'
        };
    }
    
    // Stop the processor
    stopProcessor() {
        if (this.processorInterval) {
            clearInterval(this.processorInterval);
            this.processorInterval = null;
        }
        console.log('🛑 Queue processor stopped');
    }
    
    // Get queue preview (for admin)
    getQueuePreview(limit = 5) {
        return this.queue.slice(0, limit).map((msg, index) => ({
            position: index + 1,
            phone: msg.userPhone,
            message: msg.messageContent.substring(0, 30) + '...',
            queued_ago: Math.round((Date.now() - msg.queuedAt) / 1000) + 's',
            attempts: msg.attemptCount
        }));
    }
    
    // Clear queue (admin function)
    clearQueue() {
        const cleared = this.queue.length;
        this.queue = [];
        console.log(`🗑️ Cleared ${cleared} messages from queue`);
        return cleared;
    }
}

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
        messageQueue.enqueue(userPhone, messageContent, message);
        
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
        '+1234567890'  // Replace with your admin number
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