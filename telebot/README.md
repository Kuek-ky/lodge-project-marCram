# lodge-project-marCram

A project to help me study better..... and also get exp :]

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
pip install requests python-dotenv "python-telegram-bot[job-queue]" telegram "psycopg[binary]" asyncio starlette uvicorn

```

### 4. Get a neondb table :D

### 5. Configure Environment Variables
Create a `.env` file in the project directory with your API keys:
```
API_BASE_URL = {backend API link here} #Backend access
TELE_RENDER_URL = {render url for your bot} #render url for telebot

# Telegram bot token from @BotFather
TELEGRAM_BOT_TOKEN={tokenhere}

DATABASE_URL="postgresql://[user]:[password]@[neon_hostname]/[dbname]?sslmode=require&channel_binding=require"

API_BASE_URL = "http://localhost:8080" 

TELE_PORT=3000
```

### 6. Run the Program
```bash
python "bot.py"
```