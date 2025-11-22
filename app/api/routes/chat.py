from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.deps import get_db
from app.models.conversation import Conversation

router = APIRouter()


class ChatRequest(BaseModel):
    query: str


@router.post("/chat")
async def chat_query(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Process natural language query using NEAR AI.
    Returns response with TEE completion ID for verification.
    """
    # Import here to avoid circular imports
    from app.services.near_ai import NearAIService

    try:
        # Initialize NEAR AI service
        near_ai = NearAIService()

        # Get context from database for query
        context = await near_ai.build_context(db, request.query)

        # Send query to NEAR AI (GLM-4.6)
        response_data = await near_ai.chat(request.query, context)

        # The completion_id is returned instantly with the response
        # It can be used to fetch the cryptographic signature for TEE verification
        completion_id = response_data.get("completion_id")

        # Save conversation
        conversation = Conversation(
            query=request.query,
            response=response_data["response"],
            model_used=response_data["model"],
            completion_id=completion_id
        )
        db.add(conversation)
        db.commit()

        return {
            "response": response_data["response"],
            "completion_id": completion_id,
            "model": response_data["model"],
            "conversation_id": str(conversation.id)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.get("/chat/history")
def get_chat_history(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get recent chat conversation history."""
    conversations = (
        db.query(Conversation)
        .order_by(Conversation.timestamp.desc())
        .limit(limit)
        .all()
    )

    return {
        "conversations": [
            {
                "id": str(conv.id),
                "query": conv.query,
                "response": conv.response,
                "model_used": conv.model_used,
                "completion_id": conv.completion_id,
                "timestamp": conv.timestamp.isoformat()
            }
            for conv in conversations
        ]
    }
