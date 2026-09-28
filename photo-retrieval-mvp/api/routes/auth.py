"""
api/routes/auth.py
Handles OAuth 2.0 flow for Google Photos.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from api.dependencies import get_google_photos
from integrations.google_photos import GooglePhotosAdapter

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/google")
async def auth_google(
    adapter: GooglePhotosAdapter = Depends(get_google_photos),
):
    """Initiates the OAuth 2.0 flow by redirecting the user to Google."""
    auth_url = adapter.get_auth_url(state="dummy_state")
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def auth_callback(
    request: Request,
    adapter: GooglePhotosAdapter = Depends(get_google_photos),
):
    """
    Handles the OAuth callback, exchanges code for tokens.
    In a real app, this would also associate the token with the logged-in user.
    """
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing auth code")
        
    try:
        tokens = await adapter.exchange_code(code)
        # Here we would save tokens to postgres for the user ID
        # e.g., await db.save_tokens("test_user_001", tokens)
        
        # We redirect back to the frontend (e.g. localhost:5173)
        return RedirectResponse(url="http://localhost:5173/?auth=success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
