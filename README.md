# 🚀 MemeVault AI


DEMO API SERVER: https://cognai.space/memeselector/

Find any meme on your computer just by describing it. MemeVault AI uses a powerful vision model to analyze your local meme collection, creating a searchable database that you can query with natural language.


*(This is a sample image. You can replace it with a screenshot of your own running app!)*

---

## ✨ Features

*   **🧠 Semantic Search:** Don't remember the filename? Just describe the meme! Search for `"a confused guy looking at a butterfly"` or `"sad cat giving a thumbs up"`.
*   **🤖 AI-Powered Descriptions:** Utilizes the Grok vision model via OpenRouter to automatically generate detailed, descriptive captions for every meme in your collection.
*   **🏡 Local First:** Your memes and the search index never leave your computer. The only thing sent to an API is the image for the one-time description generation.
*   **🖼️ Simple UI:** A clean, two-tab graphical interface built with Gradio for easy searching and indexing. No command-line needed for daily use.
*   **🛠️ Useful Tools:**
    *   Displays search results as a gallery of images.
    *   "Copy All Paths" button to get a list of file locations for easy sharing.
    *   "Open File Location" button to jump directly to the folder containing a found meme.
*   **📦 Standalone Executable:** Includes instructions to package the entire application into a single `.exe` file for easy use on any Windows PC.

---

## ⚙️ How It Works

MemeVault AI combines several modern AI techniques to create its "magic":

1.  **Indexing:** When you point it to a folder, the application scans for new images. Each new image is sent to a multimodal AI (Grok Vision) which returns a detailed text description of what's in the meme.
2.  **Vectorizing:** This text description is converted into a list of numbers (a "vector embedding") that represents its semantic meaning.
3.  **Storing:** These vectors are stored in a highly efficient, local vector database (FAISS). This database is your personal search index.
4.  **Searching:** When you type a search query, it's also converted into a vector. The app then asks the FAISS database to find the vectors (and their associated memes) that are mathematically closest to your query's vector.

---

## 🔧 Setup and Installation

Follow these steps to get the application running on your machine.

### 1. Prerequisites
*   Python 3.9 or higher.

### 2. Clone the Repository
```bash
git clone <your-repository-url>
cd MemeVaultAI
```

### 3. Create a Virtual Environment (Recommended)
This keeps the project's dependencies isolated.

*   **On Windows:**
    ```bash
    python -m venv .venv
    .\.venv\Scripts\activate
    ```
*   **On macOS/Linux:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

### 4. Install Dependencies
Create a file named `requirements.txt` in your project folder and add the following lines:

**`requirements.txt`**
```
gradio
python-dotenv
langchain-openai
langchain-huggingface
faiss-cpu
pyperclip
webbrowser
Pillow
pyinstaller
```

Now, install them all with a single command:
```bash
pip install -r requirements.txt
```

### 5. Set Up Your API Key
The application needs an OpenRouter API key to generate image descriptions.

1.  Create a file named `.env` in the root of your project directory.
2.  Add your API key to this file like so:
    ```
    OPENROUTER_API_KEY="sk-or-v1-your-secret-api-key-goes-here"
    ```
**Important:** Never share your `.env` file or commit it to Git. Add `.env` to your `.gitignore` file.

---

## 🚀 Usage

### 1. Run the Application
With your virtual environment activated, run the `app.py` file:
```bash
python app.py
```
This will launch the Gradio UI in your default web browser.

### 2. Index Your Meme Folder (First-Time Step)
1.  Click on the **"Index Folder"** tab.
2.  Paste the **full path** to the folder containing your memes into the textbox (e.g., `C:\Users\YourName\Pictures\Memes`).
3.  Click the **"Start Indexing"** button.
4.  Wait for the process to complete. You can see the progress in the status box. This may take a while for large collections. You only need to do this once for new folders.

### 3. Search for a Meme
1.  Click on the **"Search Memes"** tab.
2.  Type a description of the meme you want into the search box.
3.  Click the **"Search"** button.
4.  Your results will appear in the image gallery below!

---

## 📦 Creating a Standalone Executable (.exe)

You can bundle the entire application into a single `.exe` file for easy distribution and use without needing to run Python scripts from a terminal.

1.  Make sure you have installed `pyinstaller` (`pip install pyinstaller`).
2.  Open a terminal in your project directory.
3.  Run the following command:
    ```bash
    pyinstaller --onefile --windowed --name MemeVaultAI app.py
    ```
    *   `--onefile`: Bundles everything into a single file.
    *   `--windowed`: Prevents a console window from opening when you run the app.
    *   `--name MemeVaultAI`: Sets the name of your final executable.

4.  After the process completes, a `dist` folder will be created. Inside, you will find `MemeVaultAI.exe`.

5.  **CRUCIAL FINAL STEP:** For the executable to work, you must copy the following files and folders into the `dist` folder, right next to `MemeVaultAI.exe`:
    *   Your **`.env`** file (so it can read your API key).
    *   The **`faiss_meme_index`** folder (your database).
    *   The **`indexed_files.json`** file.

Now you can move the `dist` folder anywhere on your computer and run `MemeVaultAI.exe` directly.

## 📁 Project Structure
```
MemeVaultAI/
├── .venv/
├── faiss_meme_index/     (Created after first indexing)
├── app.py                (The main UI application)
├── meme_vault_engine.py    (The core logic for searching and indexing)
├── .env                  (Your secret API key)
├── indexed_files.json    (Log of indexed files, created after first indexing)
├── requirements.txt      (List of Python dependencies)
└── README.md             (This file)
```
