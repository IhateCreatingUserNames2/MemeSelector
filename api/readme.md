# API Server Setup Instructions

## Files Called by Another API Server

**Add the following code to your API server:**

```python
# IMPORT MEME SELECTOR
from .meme_selector_routes import router as meme_selector_router

# Define the path to the new frontend directory
memeselector_frontend_path = Path(__file__).resolve().parent.parent / "frontend" / "memeselector"

# Mount the entire directory to the /memeselector path.
# The `html=True` option tells FastAPI to automatically serve `index.html`
# for requests to the root of the mounted path (i.e., "/memeselector").
if memeselector_frontend_path.is_dir():
    app.mount("/memeselector", StaticFiles(directory=memeselector_frontend_path, html=True), name="memeselector-frontend")
    print(f"INFO: Mounted Meme Selector frontend at /memeselector from {memeselector_frontend_path}")
else:
    print(f"WARNING: Meme Selector frontend directory not found at {memeselector_frontend_path}. The /memeselector URL will not work.")
```

## What This Code Does

- **Imports** the meme selector router from a separate routes file
- **Defines** the path to the meme selector frontend directory
- **Mounts** the frontend directory as a static file server at the `/memeselector` endpoint
- **Enables** automatic serving of `index.html` when accessing the root path
- **Provides** informational logging about the mount status
