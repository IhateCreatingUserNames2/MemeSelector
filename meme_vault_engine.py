import os
import base64
import sys
from dotenv import load_dotenv

# --- LangChain Components ---
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
import json

# We no longer need tqdm here as Gradio provides its own progress tracker

# --- 1. Configuration ---
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

grok_vision_client = None
embedding_model = None


def initialize_models():
    """Initializes the LLM and embedding models if they haven't been already."""
    global grok_vision_client, embedding_model
    if not OPENROUTER_API_KEY:
        print("FATAL ERROR: OPENROUTER_API_KEY not found.")
        sys.exit(1)

    if grok_vision_client is None:
        print("Initializing Vision Model...")
        grok_vision_client = ChatOpenAI(
            model="x-ai/grok-4-fast:free",
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=OPENROUTER_API_KEY,
            max_tokens=200,
            default_headers={"HTTP-Referer": "http://localhost", "X-Title": "MemeVault AI"}
        )

    if embedding_model is None:
        print("Initializing Embedding Model...")
        embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


# --- 2. Database Management ---
FAISS_INDEX_PATH = "./faiss_meme_index"
INDEXED_FILES_LOG = "./indexed_files.json"


def load_vector_store():
    initialize_models()
    if os.path.exists(FAISS_INDEX_PATH):
        return FAISS.load_local(FAISS_INDEX_PATH, embedding_model, allow_dangerous_deserialization=True)
    return None


def get_indexed_paths():
    if os.path.exists(INDEXED_FILES_LOG):
        with open(INDEXED_FILES_LOG, 'r') as f:
            return set(json.load(f))
    return set()


def save_indexed_paths(paths):
    with open(INDEXED_FILES_LOG, 'w') as f:
        json.dump(list(paths), f)


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


# --- 3. Core App Logic (Corrected) ---

# THE FIX IS HERE: The function now accepts 'progress' as an optional argument.
# It defaults to None, so it no longer depends on Gradio ('gr').
def index_memes(folder_path: str, progress=None):
    """Scans a folder, generates descriptions, and stores them. Returns a status string."""
    initialize_models()
    if not folder_path or not os.path.isdir(folder_path):
        return "Error: Please provide a valid folder path."

    # --- PATH STANDARDIZATION FIX ---
    # Convert all stored paths to absolute paths to prevent duplicates.
    indexed_paths = {os.path.abspath(p) for p in get_indexed_paths()}

    image_files = [
        # Convert found paths to absolute immediately.
        os.path.abspath(os.path.join(root, file))
        for root, _, files in os.walk(folder_path)
        for file in files
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
    ]
    # The check for existing files is now much more reliable.
    files_to_index = [f for f in image_files if f not in indexed_paths]
    # --- END OF FIX ---

    if not files_to_index:
        return "All memes are already indexed. Nothing to do."

    status = f"Found {len(files_to_index)} new memes to index...\n"

    documents_to_add = []

    for i, image_path in enumerate(files_to_index):
        if progress:
            progress(i / len(files_to_index), desc=f"Analyzing {os.path.basename(image_path)}")

        try:
            base64_image = encode_image(image_path)
            message = HumanMessage(
                content=[
                    {"type": "text", "text": "Generate a detailed, descriptive caption for this meme."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                ]
            )
            response = grok_vision_client.invoke([message])
            description = response.content
            # The path stored in metadata will now be the absolute path.
            doc = Document(page_content=description, metadata={"path": image_path})
            documents_to_add.append(doc)
            status += f"Generated description for '{os.path.basename(image_path)}'\n"
        except Exception as e:
            status += f"Could not process {image_path}: {e}\n"

    if documents_to_add:
        vector_store = load_vector_store()
        if vector_store is None:
            vector_store = FAISS.from_documents(documents_to_add, embedding_model)
        else:
            vector_store.add_documents(documents_to_add)
        vector_store.save_local(FAISS_INDEX_PATH)

        new_paths = {doc.metadata['path'] for doc in documents_to_add}
        # Union of absolute paths.
        updated_paths = indexed_paths.union(new_paths)
        save_indexed_paths(updated_paths)
        status += f"\nSuccessfully indexed {len(documents_to_add)} new memes."

    return status


def search_memes(query: str, top_k: int = 9):
    """Searches for memes and returns a list of file paths."""
    if not query.strip():
        return [], "Please enter a search query."

    vector_store = load_vector_store()
    if vector_store is None:
        return [], "Database not found. Please index your memes first."

    results = vector_store.similarity_search(query, k=top_k)

    if not results:
        return [], "No matching memes found."

    result_paths = [doc.metadata.get('path') for doc in results]
    paths_text = "\n".join(result_paths)
    return result_paths, f"Found {len(result_paths)} results:\n{paths_text}"