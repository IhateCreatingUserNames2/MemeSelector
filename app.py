import gradio as gr
import meme_vault_engine as engine  # Import our refactored logic
import pyperclip  # For the copy-to-clipboard functionality
import os
import webbrowser


# We need to install pyperclip: pip install pyperclip

# --- UI Helper Functions ---
def ui_search(query):
    """Function that Gradio will call when the search button is clicked."""
    if not query.strip():
        # THE FIX: Ensure we return 4 values even for an empty query
        return None, "Please enter a search term.", gr.update(visible=False), gr.update(visible=False)

    # The engine function returns two values: paths and a status message
    image_paths, status_message = engine.search_memes(query)

    # THE FIX: Create a single update instruction for both buttons
    button_visibility_update = gr.update(visible=True) if image_paths else gr.update(visible=False)

    # THE FIX: Return all four required values
    return image_paths, status_message, button_visibility_update, button_visibility_update


def ui_index(folder_path, progress=gr.Progress()):
    """Function that Gradio will call for indexing."""
    return engine.index_memes(folder_path, progress)


def copy_paths_to_clipboard(image_paths):
    """Copies the list of file paths to the clipboard, one per line."""
    if image_paths:
        # On Windows, paths use backslashes. Let's ensure they are correct.
        cleaned_paths = [os.path.normpath(p) for p in image_paths]
        pyperclip.copy("\n".join(cleaned_paths))
        return "Paths copied to clipboard!"
    return ""


def open_file_explorer(image_paths):
    """Opens the folder containing the first found meme."""
    if image_paths:
        first_path = os.path.normpath(image_paths[0])
        folder = os.path.dirname(first_path)
        # Use webbrowser to open the folder in the default file explorer
        webbrowser.open(f'file:///{folder}')
        return "Opened file location!"
    return ""


# --- Build the Gradio Interface ---
with gr.Blocks(theme=gr.themes.Soft(), title="MemeVault AI") as demo:
    gr.Markdown("# MemeVault AI\nDescribe the meme you want. Find it instantly.")

    with gr.Tabs():
        with gr.TabItem("Search Memes"):
            with gr.Row():
                search_input = gr.Textbox(label="Describe the meme...",
                                          placeholder="e.g., confused guy looking at butterfly", scale=4)
                search_button = gr.Button("Search", variant="primary", scale=1)

            with gr.Row():
                # These buttons fulfill your feature requests
                copy_button = gr.Button("📋 Copy All Paths", visible=False)
                open_folder_button = gr.Button("📁 Open File Location", visible=False)

            status_output = gr.Textbox(label="Status", interactive=False)
            copy_status_output = gr.Textbox(label="Clipboard Status", interactive=False)

            # The gallery is perfect for displaying image results
            gallery_output = gr.Gallery(label="Search Results", show_label=True, elem_id="gallery", columns=3,
                                        height="auto")

        with gr.TabItem("Index Folder"):
            gr.Markdown("Add a folder of memes to the search index. This can take a while.")
            folder_input = gr.Textbox(label="Enter the full path to your meme folder")
            index_button = gr.Button("Start Indexing", variant="primary")
            index_status_output = gr.Textbox(label="Indexing Progress", interactive=False, lines=10)

    # --- Wire up the UI components ---
    search_button.click(
        fn=ui_search,
        inputs=[search_input],
        outputs=[gallery_output, status_output, copy_button, open_folder_button]
    )
    copy_button.click(
        fn=copy_paths_to_clipboard,
        inputs=[gallery_output],  # Pass the gallery's value (list of paths)
        outputs=[copy_status_output]
    )
    open_folder_button.click(
        fn=open_file_explorer,
        inputs=[gallery_output],
        outputs=[copy_status_output]
    )
    index_button.click(
        fn=ui_index,
        inputs=[folder_input],
        outputs=[index_status_output]
    )

if __name__ == "__main__":
    print("Launching MemeVault AI...")
    # Initialize the models once on startup to make the first search faster.
    engine.initialize_models()
    demo.launch()