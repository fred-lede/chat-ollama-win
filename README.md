# Ollama Chat UI for Windows System
Use python to create a program that can let people use it link to Ollama service.

## 📦 Installation and Setup for Windows

Follow these steps to set up and run Chat-Ollama-Win Local with Ollama on Windows:

1. **Install Ollama:**
    1.1 Visit [Ollama's website](https://ollama.com/) to download Ollama for Windows and install the file.
        Ollama and chat-ollama-win are in the same host. The default Ollama service is http://127.0.01:11434. The app can run directly.
        If you install Ollama in A PC and chat-ollama-win in B PC, 
        You need to create a new system Environment Variables as "OLLAMA_HOST=0.0.0.0:11434".
    ```pwsh
      ollama pull llama3.2
      ollama pull qwen2.5
      ollama serve 
    ```
    1.2  Visit [Ollama's website](https://ollama.com/) to download Ollama for macOS and install the file.
         Ollama and chat-ollama-win can in different host. The default Ollama service is http://127.0.01:11434.
         So that you need to "export OLLAMA_HOST=0.0.0.0:11434", Please visit internet to search detail setting process. 
    ```pwsh
      ollama pull llama3.2
      ollama pull qwen2.5
      ollama serve
    ```

2. **Create Python Environment and Install Packages:**
    ```pwsh
    git clone https://github.com/fred-lede/chat-ollama-win.git
    cd chat-ollama-win
    python -m venv venv
    
    #Windows PowerShell
    ./venv/Scripts/activate
    
    #Windows Command
    venv\Scripts\activate
    
    pip install -r requirements.txt
    ```    
3. **Run ollama-ui-win.py**
    ```pwsh
    python ollama-ui-win.py
    ```                
