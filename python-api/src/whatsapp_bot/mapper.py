from whatsapp_bot.database.models import ChatInteraction
from whatsapp_bot.database.schema import ChatInteraction as ChatInteractionModel, ChatRequest, ChatResponse

def map_db_interaction_to_api_interaction(interaction: ChatInteraction) -> ChatInteractionModel:
    return ChatInteractionModel(
        chat_request=ChatRequest(
            sender_phone=interaction.user.phone, 
            receiver_phone=interaction.receiver_phone,
            message=interaction.request_message
        ),
        chat_response=ChatResponse(response=interaction.response_message),
        timestamp=interaction.created_at,
        language=interaction.language
    )
