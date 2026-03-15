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
pip install requests python-dotenv "python-telegram-bot[job-queue]" telegram "psycopg[binary]"

```

### 4. Get a neondb table :D

### 5. Configure Environment Variables
Create a `.env` file in the project directory with your API keys:
```
API_BASE_URL = {backend API link here}

# Telegram bot token from @BotFather
TELEGRAM_BOT_TOKEN={tokenhere}

DATABASE_URL="postgresql://[user]:[password]@[neon_hostname]/[dbname]?sslmode=require&channel_binding=require"
```

### 6. Run the Program
```bash
python "bot.py"
```