from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pathlib import Path
import shutil
import uuid

# Import the engine and API models
from . import meme_selector_engine as engine
from .meme_selector_engine import DescriptionResponse, EmbeddingResponse

router = APIRouter(
    prefix="/memeselector",
    tags=["Meme Selector"]
)


# --- Endpoints for Web Frontend ---

@router.post("/upload")
async def upload_meme_for_indexing(file: UploadFile = File(...)):
    """Endpoint for the WEB UI to upload a meme to the server."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed.")

    # Create a unique filename to avoid conflicts
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = engine.MEME_STORAGE_PATH / unique_filename

    # Save the uploaded file to the server's storage
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Get description and add it to the index
    description = engine.get_description_for_image(file_path.read_bytes())
    engine.add_meme_to_index(file_path, description)

    return {"filename": unique_filename, "description": description, "status": "Indexed successfully"}


@router.get("/search")
async def search_server_memes(query: str):
    """Endpoint for the WEB UI to search memes stored on the server."""
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    results = engine.search_memes_in_index(query)

    # Construct web-accessible URLs for the results
    base_url = "/memeselector/memes/"
    result_urls = [f"{base_url}{filename}" for filename in results]

    return {"results": result_urls}


# --- Endpoints specifically for the ANDROID APP ---

@router.post("/describe-image", response_model=DescriptionResponse)
async def api_describe_image(file: UploadFile = File(...)):
    """
    ANDROID APP API: Receives an image, returns a description.
    The app will store this description locally.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed.")

    image_bytes = await file.read()
    description = engine.get_description_for_image(image_bytes)
    return {"description": description}


@router.post("/embed-text", response_model=EmbeddingResponse)
async def api_embed_text(text: str = Form(...)):
    """
    ANDROID APP API: Receives text (a description or a query), returns its vector.
    The app will store this vector or use it for local searching.
    """
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    vector = engine.get_embedding_for_text(text)
    return {"vector": vector}