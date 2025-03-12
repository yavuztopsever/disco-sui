import os
from dotenv import load_dotenv
from smolagents import GradioUI, stream_to_gradio
from src.lib.agents.NoteManagementAgent import NoteManagementAgent

# Load environment variables
load_dotenv('.env.local')

# Initialize the agent
agent = NoteManagementAgent(os.getenv('VAULT_PATH', './notes'))

# Create the Gradio interface
ui = GradioUI(agent=agent, file_upload_folder="uploads")

# Define the chat interface
async def chat(message, history):
    async for response in stream_to_gradio(message, agent=agent):
        yield response

# Launch the interface
if __name__ == "__main__":
    import gradio as gr
    
    demo = gr.ChatInterface(
        fn=chat,
        title="DiscoSui - Note Management Assistant",
        description="A smart assistant for managing your notes using OpenAI.",
        examples=[
            "Create a new note titled 'Meeting Notes' with some content about today's meeting",
            "Update the note 'Meeting Notes' to include action items",
            "Create a folder called 'Projects' and move 'Meeting Notes' into it",
            "Add tags 'meeting, important' to the note"
        ],
        theme=gr.themes.Soft()
    )
    
    demo.launch(share=False) 