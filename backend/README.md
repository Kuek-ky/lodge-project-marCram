### 1. Create a Virtual Environment, we are using python 3.11.5!
```bash
python -m venv .venv
```

### 2. Activate the Virtual Environment

**Windows PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**
```cmd
.\.venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install python-dotenv anthropic requests uvicorn fastapi 
```

### 4. Configure Environment Variables
Create a `.env` file in the project directory with your API keys:
```
CLAUDE_API_KEY={api key here}

EMBED_MODEL=text-embedding-3-small
CHAT_MODEL={chat model here}

API_BASE_URL="http://localhost:8080"

MAX_SEARCHES_PER_REQUEST=5
ALLOWED_SEARCH_DOMAINS=[{your desired domains here}]
```

### 5. Run the Program
```bash
python "ai_model.py"
```