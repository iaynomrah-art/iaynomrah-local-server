# Harmony Orchestrator: UiPath Automation Server

Harmony is a powerful FastAPI-based orchestration server designed to manage, trigger, and monitor automations locally while providing a secure public interface via Cloudflare Tunnels.

---

## 🚀 Quick Start (Recommended)

The project includes a robust PowerShell management script (`scipt.ps1`) that automates the entire lifecycle of the server, including dependency management, frontend builds, and tunnel configuration.

### 1. Running the Script

Open a PowerShell terminal and run:

```powershell
.\scipt.ps1
```

### 2. Script Features

- **Smart Setup**: Optionally pulls latest code, installs Python `requirements.txt`, and builds the React frontend.
- **Auto-Tunneling**: Automatically starts `cloudflared`, extracts your unique URL, and updates your `.env` file for you.
- **Quick Reload**: Press `r` at the menu to immediately restart the tunnel and server without re-running setup steps—perfect for development.
- **Auto-Venv**: Automatically activates the virtual environment if it exists.

---

## 🛠️ Installation & Requirements

### Prerequisites

- **Python 3.12+**: (Recommended for best performance and library compatibility).
- **Node.js & NPM**: Required for building the frontend dashboard.
- **Playwright**: Required for cTrader browser automation (`pip install playwright && playwright install`).

### Manual Python Setup

If you wish to install dependencies manually:

```powershell
# Create virtual environment
python -m venv venv

# Activate venv
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

#run the tunnel
cloudflared tunnel --url http://localhost:8000

# Run the server
uvicorn app.main:app --port 8000 --reload
```

### Manual Server Startup

If you are not using the `scipt.ps1` script, you can start the server manually by following these steps:

1. **Start the Cloudflare Tunnel**:
   Open a terminal and run the test tunnel for port 8000:
   ```powershell
   cloudflared tunnel --url http://localhost:8000
   ```
2. **Update `.env`**:
   Copy the generated tunnel URL from the output and paste it into your `.env` file.
3. **Start the Server**:
   Open a new terminal (in your virtual environment) and run:
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```

---

## 🖥️ Starting the Server

There are multiple ways to start the Harmony server depending on your preference.

### Option 1: Run Manually from PowerShell

The simplest way — just open PowerShell and run:

1. Press `Win + R`, type `shell:startup`, and press **Enter**.
2. Right-click inside the folder and select **New > Shortcut**.
3. In the location box, paste the following (adjust the path if moved):

   ```powershell
   powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File "C:\Users\Admin\Desktop\Code\iaynomrah-local-server\script.ps1"
   ```

   powershell.exe -ExecutionPolicy Bypass -File "C:\Users\Admin\Documents\code\iaynomrah-local-server\scipt.ps1"

   ```

   ```

4. Name it `Harmony Server` and click **Finish**.

### Option 7: Package as Executable (.exe)

If you want a single `.exe` file to pin to your taskbar or distribute:

1. **Install ps2exe**:
   ```powershell
   Install-Module ps2exe -Scope CurrentUser
   ```
2. **Convert to EXE**:
   ```powershell
   ps2exe .\scipt.ps1 HarmonyServer.exe -noConsole -title "Harmony Server"
   ```

---

## 📂 Project Structure

- **`app/main.py`**: Principal FastAPI entry point.
- **`app/routes/`**: API endpoints (Automation, Runner, Trade, Dashboard).
- **`app/controller/`**: Core logic for unit registration.
- **`app/automation/ctrader/`**: Playwright-based cTrader automation modules.
  - `main.py` — Entry point for the cTrader automation.
  - `login.py` — Handles login flow with randomized delays.
  - `check-user.py` — Verifies account and selects the correct trading account.
  - `place-order.py` — Places new orders.
  - `edit-place-order.py` — Edits existing orders.
  - `input-order.py` — Handles order input fields.
- **`frontend/`**: Vite-based React dashboard for real-time monitoring.
- **`scipt.ps1`**: The primary "Harmony Manager" script.

---

## 🔗 Environment Configuration

Your `.env` file should include:

- `PUBLIC_SUPABASE_URL`: Your Supabase project URL.
- `SUPABASE_SERVICE_SECRET_KEY`: For admin-level access.
- `FRANCHISE_ID`: Your franchise identifier.
- `API_BASE_URL`: Auto-updated by `scipt.ps1` with the Cloudflare tunnel URL.
