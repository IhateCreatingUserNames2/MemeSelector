import os
import base64
import sys
from pathlib import Path
import json

# LangChain & AI Components
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

# --- Configuration & Initialization ---
# This engine will be part of a larger app, so we'll make initialization explicit.

grok_vision_client = None
embedding_model = None

# Define where this service will store its data relative to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MEME_STORAGE_PATH = PROJECT_ROOT / "meme_storage"
FAISS_INDEX_PATH = MEME_STORAGE_PATH / "faiss_meme_index"
INDEXED_FILES_LOG = MEME_STORAGE_PATH / "indexed_files.json"

# Ensure storage directories exist
MEME_STORAGE_PATH.mkdir(parents=True, exist_ok=True)


def initialize_models():
    """Initializes the AI models. Called once on API startup."""
    global grok_vision_client, embedding_model

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        raise RuntimeError("FATAL: OPENROUTER_API_KEY is not set in the environment.")

    if grok_vision_client is None:
        print("Initializing Vision Model for Meme Selector...")
        grok_vision_client = ChatOpenAI(
            model="x-ai/grok-4-fast:free",
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=OPENROUTER_API_KEY,
            max_tokens=200,
            default_headers={"HTTP-Referer": "https://cognai.space", "X-Title": "MemeVault AI"}
        )

    if embedding_model is None:
        print("Initializing Embedding Model for Meme Selector...")
        embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


# --- Pydantic Models for API Data Validation ---
class DescriptionResponse(BaseModel):
    description: str


class EmbeddingResponse(BaseModel):
    vector: list[float]


# --- Core Service Functions ---

def get_description_for_image(image_bytes: bytes) -> str:
    """Gets a text description for a given image in bytes."""
    if not grok_vision_client: initialize_models()
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    message = HumanMessage(
        content=[
            {"type": "text", "text": "Generate a detailed, descriptive caption for this meme."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
        ]
    )
    response = grok_vision_client.invoke([message])
    return response.content


def get_embedding_for_text(text: str) -> list[float]:
    """Gets a vector embedding for a given string of text."""
    if not embedding_model: initialize_models()
    return embedding_model.embed_query(text)


def add_meme_to_index(filepath: Path, description: str):
    """Adds a single meme's description and path to the server's FAISS index."""
    if not embedding_model: initialize_models()
    doc = Document(page_content=description, metadata={"path": str(filepath)})

    if FAISS_INDEX_PATH.exists():
        vector_store = FAISS.load_local(str(FAISS_INDEX_PATH), embedding_model, allow_dangerous_deserialization=True)
        vector_store.add_documents([doc])
    else:
        vector_store = FAISS.from_documents([doc], embedding_model)

    vector_store.save_local(str(FAISS_INDEX_PATH))


def search_memes_in_index(query: str, top_k: int = 9) -> list[str]:
    """Searches the server's FAISS index and returns file paths."""
    if not embedding_model: initialize_models()

    if not FAISS_INDEX_PATH.exists():
        return []

    vector_store = FAISS.load_local(str(FAISS_INDEX_PATH), embedding_model, allow_dangerous_deserialization=True)
    results = vector_store.similarity_search(query, k=top_k)

    # Return a web-accessible path, not a local file system path
    return [Path(doc.metadata.get('path')).name for doc in results]