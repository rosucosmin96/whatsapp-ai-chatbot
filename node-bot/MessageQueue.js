const axios = require('axios');
const config = require('./config');
const limitsExceeded = 'limits exceeded';

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
    enqueue(userPhone, botPhone, messageContent, originalMessage) {
        const queuedMessage = {
            id: Date.now() + Math.random(),
            userPhone,
            botPhone,
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
                sender_phone: message.userPhone,
                receiver_phone: message.botPhone,
                message: message.messageContent
            }, {
                timeout: 30000 // 30 second timeout
            });
            
            // Check if we got a valid response
            if (response.data && response.data.response && response.data.response.trim() !== limitsExceeded) {
                // SUCCESS: Send response and remove from queue
                await message.originalMessage.reply(response.data.response);
                this.dequeue(); // Remove the successfully processed message
                this.stats.total_failed_attempts--; // Correction: this wasn't actually a failed attempt
                
                console.log(`✅ SUCCESS: Sent response to ${message.userPhone}`);
                
            } else {
                // FAILED: Empty response, keep in queue
                console.log(`⚠️ FAILED: Limits exceeded for ${message.userPhone}, keeping in queue`);
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

module.exports = MessageQueue; 