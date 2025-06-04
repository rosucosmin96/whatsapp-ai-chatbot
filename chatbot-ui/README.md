# WhatsApp OpenAI Bot - Chainlit UI

This is a Chainlit-based user interface for the WhatsApp OpenAI Bot API. It provides a web-based chat interface that communicates with the Python API backend.

## Features

- 🤖 Interactive chatbot interface using Chainlit
- 🔗 Direct integration with the Python API `/chat` endpoint  
- ⚡ Real-time messaging with typing indicators
- 🛡️ Error handling and connection status monitoring
- 📱 Configurable phone number for API requests
- 🎨 Clean and modern UI

## Prerequisites

- Python 3.8+
- The Python API server running (see `../python-api/`)
- Node.js and npm (optional, for additional frontend customization)

## Setup

1. **Install dependencies:**
   ```bash
   cd chatbot-ui
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env file with your settings
   ```

3. **Environment Variables:**
   - `API_BASE_URL`: URL of the Python API (default: http://localhost:8000)
   - `DEFAULT_PHONE`: Phone number to use for API requests (default: +1234567890)
   - `CHAINLIT_HOST`: Host for the Chainlit server (default: 0.0.0.0)
   - `CHAINLIT_PORT`: Port for the Chainlit server (default: 8080)

## Running the Application

1. **Start the Python API** (in another terminal):
   ```bash
   cd ../python-api
   uvicorn src.whatsapp_bot.main:app --reload --port 8000
   ```

2. **Start the Chainlit UI**:
   ```bash
   cd chatbot-ui
   chainlit run app.py --port 8080
   ```

3. **Access the UI:**
   Open your browser and go to `http://localhost:8080`

## Usage

1. The UI will automatically check the API connection status when you start a chat
2. Type your message in the chat input
3. The message will be sent to the Python API with the configured phone number
4. The AI assistant's response will be displayed in the chat interface
5. All conversation history is maintained by the backend API

## Configuration

### Phone Number
The default phone number can be changed in the `.env` file. This number is used for all API requests to maintain conversation context.

### API Endpoint
Make sure the `API_BASE_URL` in your `.env` file matches where your Python API is running.

### UI Customization
You can customize the Chainlit interface by modifying:
- `chainlit.toml` - General UI settings and branding
- `app.py` - Application logic and message handling
- Add custom CSS in `public/` directory (create if needed)

## API Integration

The UI integrates with these Python API endpoints:

- `POST /chat` - Send messages to the chatbot
  - Request: `{"phone": "string", "message": "string"}`  
  - Response: `{"response": "string"}`

- `GET /health` - Check API health status
  - Response: `{"status": "ok"}`

## Troubleshooting

### API Connection Issues
- Ensure the Python API is running on the correct port
- Check that `API_BASE_URL` in `.env` is correct
- Verify there are no firewall issues blocking the connection

### Installation Issues
- Make sure you're using Python 3.8+
- Try upgrading pip: `pip install --upgrade pip`
- Consider using a virtual environment

### UI Not Loading
- Check that port 8080 is not in use by another application
- Try changing the port in `.env` and restart
- Check console for JavaScript errors (if any)

## Development

To extend or modify the UI:

1. **Add new features** by modifying `app.py`
2. **Customize styling** by adding CSS files to a `public/` directory
3. **Modify configuration** in `chainlit.toml`
4. **Add environment variables** in `.env` as needed

## Production Deployment

For production deployment:

1. Set appropriate environment variables
2. Use a proper WSGI server or containerize the application
3. Configure reverse proxy (nginx) if needed
4. Ensure proper security measures are in place
5. Monitor both the UI and API components 