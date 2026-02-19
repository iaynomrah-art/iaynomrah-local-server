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
```

---

## 🖥️ Starting the Server

There are multiple ways to start the Harmony server depending on your preference.

### Option 1: Run Manually from PowerShell

The simplest way — just open PowerShell and run:

```powershell
cd C:\Users\Admin\Documents\code\iaynomrah-local-server
.\scipt.ps1
```

Or run from anywhere:

```powershell
powershell.exe -ExecutionPolicy Bypass -File "C:\Users\Admin\Documents\code\iaynomrah-local-server\scipt.ps1"
```

### Option 2: Right-Click → "Run with PowerShell"

Navigate to the project folder in File Explorer, right-click `scipt.ps1`, and select **Run with PowerShell**.

### Option 3: Desktop Shortcut (Double-Click to Start)

Create a shortcut on your desktop for quick access:

```powershell
$ws = New-Object -ComObject WScript.Shell
$shortcut = $ws.CreateShortcut("$env:USERPROFILE\Desktop\Start Server.lnk")
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = '-ExecutionPolicy Bypass -File "C:\Users\Admin\Documents\code\iaynomrah-local-server\scipt.ps1"'
$shortcut.WorkingDirectory = 'C:\Users\Admin\Documents\code\iaynomrah-local-server'
$shortcut.Save()
```

### Option 4: Task Scheduler (Auto-Start on Login)

Best option for auto-starting without the `shell:startup` folder:

1. Open **Task Scheduler** → press `Win + R`, type `taskschd.msc`, hit **Enter**.
2. Click **Create Task** (not "Basic Task").
3. **General tab**: Name it `Harmony Server`, check **"Run only when user is logged on"**.
4. **Triggers tab**: Click **New** → set **Begin the task** to **At log on** → select your user.
5. **Actions tab**: Click **New** →
   - **Program/script**: `powershell.exe`
   - **Add arguments**: `-ExecutionPolicy Bypass -File "C:\Users\Admin\Documents\code\iaynomrah-local-server\scipt.ps1"`
   - **Start in**: `C:\Users\Admin\Documents\code\iaynomrah-local-server`
6. Click **OK**.

### Option 5: Registry Run Key (Auto-Start on Login)

Add a registry entry so the script runs at login:

```powershell
# Register auto-start
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$command = 'powershell.exe -ExecutionPolicy Bypass -File "C:\Users\Admin\Documents\code\iaynomrah-local-server\scipt.ps1"'
Set-ItemProperty -Path $regPath -Name "HarmonyServer" -Value $command
```

To remove it later:

```powershell
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "HarmonyServer"
```

### Option 6: Shell Startup Folder

1. Press `Win + R`, type `shell:startup`, press **Enter**.
2. Right-click inside the folder → **New > Shortcut**.
3. Paste the following as the location:
   ```
   powershell.exe -ExecutionPolicy Bypass -File "C:\Users\Admin\Documents\code\iaynomrah-local-server\scipt.ps1"
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
