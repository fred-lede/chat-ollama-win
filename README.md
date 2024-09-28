# Ollama Chat UI for Windows System
Use python to create a program that can let people use it link to Ollama service.

## 📦 Installation and Setup Windows

Follow these steps to set up and run Chat-Ollama-Win Local with Ollama on Windows:

1. **Install Ollama:**

    Visit [Ollama's website](https://ollama.com/) for installation files.

    ```pwsh
    ollama pull llama3.2
    ollama pull qwen2.5
    ollama serve
    ```

2. **Create conda environment and install packages:**
    ```pwsh
    git clone https://github.com/karthik-codex/autogen_graphRAG.git
    cd autogen_graphRAG
    python -m venv venv
    ./venv/Scripts/activate
    pip install -r requirements.txt
    ```    
3. **Run ollama-ui-win.py**
    ```pwsh
    python ollama-ui-win.py
    ```                
