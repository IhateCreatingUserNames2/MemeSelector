document.addEventListener('DOMContentLoaded', () => {
    // --- Element References ---
    const folderInputIndex = document.getElementById('folder-input-index');
    const indexStatus = document.getElementById('index-status');
    const downloadIndexBtn = document.getElementById('download-index-btn');
    const indexUploadInput = document.getElementById('index-upload-input');
    const folderInputSearch = document.getElementById('folder-input-search');
    const sessionStatus = document.getElementById('session-status');
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const searchStatus = document.getElementById('search-status');
    const gallery = document.getElementById('results-gallery');

    // --- State Management ---
    let localIndexData = null;
    let localFileHandles = null; // NEW: Will store file references from the user's folder selection
    let newIndexData = [];

    // --- API Endpoints ---
    const DESCRIBE_ENDPOINT = '/memeselector/describe-image';
    const EMBED_ENDPOINT = '/memeselector/embed-text';

    // --- Core Logic ---

    // 1. Indexing Logic
    folderInputIndex.addEventListener('change', async (event) => {
        const files = event.target.files;
        if (!files.length) return;

        newIndexData = [];
        indexStatus.textContent = `Found ${files.length} files. Starting processing...`;
        downloadIndexBtn.style.display = 'none';

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            indexStatus.textContent = `Processing ${i + 1}/${files.length}: ${file.name}`;
            if (file.type.startsWith('image/')) {
                try {
                    const { description, vector } = await processImage(file);
                    newIndexData.push({ path: file.webkitRelativePath, description, vector });
                } catch (error) { console.error(`Failed to process ${file.name}:`, error); }
            }
        }

        indexStatus.textContent = `Indexing complete! Found ${newIndexData.length} images. Click below to save your index file.`;
        downloadIndexBtn.style.display = 'block';
    });

    async function processImage(file) {
        const formDataDesc = new FormData();
        formDataDesc.append('file', file);
        const descResponse = await fetch(DESCRIBE_ENDPOINT, { method: 'POST', body: formDataDesc });
        if (!descResponse.ok) throw new Error('Failed to get description from server.');
        const { description } = await descResponse.json();

        const formDataEmbed = new FormData();
        formDataEmbed.append('text', description);
        const embedResponse = await fetch(EMBED_ENDPOINT, { method: 'POST', body: formDataEmbed });
        if (!embedResponse.ok) throw new Error('Failed to get vector from server.');
        const { vector } = await embedResponse.json();

        return { description, vector };
    }

    downloadIndexBtn.addEventListener('click', () => {
        const blob = new Blob([JSON.stringify(newIndexData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = 'index.json';
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // 2. Search Session Setup
    indexUploadInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                localIndexData = JSON.parse(e.target.result);
                sessionStatus.textContent = `Index loaded (${localIndexData.length} memes). Now select the folder.`;
                checkIfReadyToSearch();
            } catch (error) { sessionStatus.textContent = 'Error: Invalid index file.'; }
        };
        reader.readAsText(file);
    });

    folderInputSearch.addEventListener('change', (event) => {
        const files = event.target.files;
        if (!files.length) return;
        // Create a Map for fast lookups: { "relative/path/meme.jpg": FileObject }
        localFileHandles = new Map(Array.from(files).map(file => [file.webkitRelativePath, file]));
        sessionStatus.textContent = `Folder selected (${localFileHandles.size} files). Ready to search.`;
        checkIfReadyToSearch();
    });

    function checkIfReadyToSearch() {
        if (localIndexData && localFileHandles) {
            sessionStatus.textContent = `✅ Session ready! Loaded ${localIndexData.length} indexed memes and ${localFileHandles.size} local files.`;
            searchInput.disabled = false;
            searchBtn.disabled = false;
        }
    }

    // 3. Search Logic
    searchBtn.addEventListener('click', async () => {
        const query = searchInput.value;
        if (!query || !localIndexData || !localFileHandles) return;

        searchStatus.textContent = 'Getting query vector from server...';
        gallery.innerHTML = '';

        try {
            const formDataEmbed = new FormData();
            formDataEmbed.append('text', query);
            const response = await fetch(EMBED_ENDPOINT, { method: 'POST', body: formDataEmbed });
            if (!response.ok) throw new Error('Failed to get query vector.');
            const { vector: queryVector } = await response.json();

            searchStatus.textContent = 'Searching locally and displaying images...';

            const results = localIndexData.map(item => ({
                ...item,
                similarity: cosineSimilarity(queryVector, item.vector)
            }));

            results.sort((a, b) => b.similarity - a.similarity);
            const topResults = results.slice(0, 12); // Show more results

            if (topResults.length > 0) {
                searchStatus.textContent = `Found ${topResults.length} results.`;
                topResults.forEach(result => {
                    const fileHandle = localFileHandles.get(result.path);
                    if (fileHandle) {
                        const img = document.createElement('img');
                        img.src = URL.createObjectURL(fileHandle);
                        img.title = `${result.path}\nSimilarity: ${result.similarity.toFixed(3)}`;
                        gallery.appendChild(img);
                    }
                });
            } else {
                searchStatus.textContent = 'No matching memes found.';
            }

        } catch (error) {
            searchStatus.textContent = `Error: ${error.message}`;
        }
    });

    // --- Helper Function ---
    function cosineSimilarity(vecA, vecB) {
        if (!vecA || !vecB || vecA.length !== vecB.length) return 0;
        let dotProduct = 0.0, normA = 0.0, normB = 0.0;
        for (let i = 0; i < vecA.length; i++) {
            dotProduct += vecA[i] * vecB[i];
            normA += vecA[i] * vecA[i];
            normB += vecB[i] * vecB[i];
        }
        if (normA === 0 || normB === 0) return 0;
        return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
    }
});