"""
Routes for AI-powered text improvement.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/text", tags=["text-improvement"])

# TextImprover instance (lazy initialization)
_text_improver = None


def get_text_improver():
    """Get or create TextImprover instance."""
    global _text_improver
    if _text_improver is None:
        from text_improver import TextImprover
        _text_improver = TextImprover()
    return _text_improver


class TextImprovementRequest(BaseModel):
    """Request model for text improvement."""
    text: str
    instruction: str
    include_comment: bool = False


@router.post("/improve")
async def improve_text(request: TextImprovementRequest):
    """
    Improve text with Jinja template syntax preservation.
    
    Request Body:
        text: Text to improve (can contain Jinja tags)
        instruction: Instruction for LLM (e.g., "Improve grammar", "Translate to English")
        include_comment: Optional - if true, includes explanation of changes
    
    Response:
        improved_text: Improved text with preserved Jinja tags
        comment: Optional - explanation of changes (if include_comment=true)
        model: Name of the LLM model used
    """
    try:
        improver = get_text_improver()
        result = improver.improve_text(
            text=request.text,
            user_instruction=request.instruction,
            include_comment=request.include_comment
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Text improvement failed: {str(e)}"
        )