# Harmony Orchestrator: UiPath Automation Server

Harmony is a powerful FastAPI-based orchestration server designed to manage, trigger, and monitor UiPath automations locally while providing a secure public interface via Cloudflare Tunnels.

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
- **UiPath Robot**: Installed and configured in your system path.

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

#run manually
uvicorn app.main:app --host 0.0.0.0 --port 2026 --reload

---

## 🖥️ Desktop Integration & Auto-Start

To make the server feel like a resident application on your Windows machine, follow these steps:

### 1. Run at Startup

To launch the Harmony server automatically when you log in:

1. Press `Win + R`, type `shell:startup`, and press **Enter**.
2. Right-click inside the folder and select **New > Shortcut**.
3. In the location box, paste the following (adjust the path if moved):
   ```powershell
   powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File "C:\Users\Admin\Desktop\Code\iaynomrah-local-server\script.ps1"
   ```
4. Click **Next** and name it `Harmony Server`.

### 2. Create a Dedicated Executable (.exe)

If you want to package the script as a single `.exe` file for easier distribution or to pin it to your taskbar:

1. **Install ps2exe Utility**:
   ```powershell
   Install-Module ps2exe -Scope CurrentUser
   ```
2. **Convert to EXE**:
   Run this command in the project root:
   ```powershell
   ps2exe .\scipt.ps1 HarmonyServer.exe -noConsole -title "Harmony Server"
   ```
   _This creates a `HarmonyServer.exe` that runs the orchestration logic in the background._

---

## 📂 Project Structure

- **`app/main.py`**: Principal FastAPI entry point.
- **`app/routes/`**: API endpoints (Automation, Runner, Trade, Dashboard).
- **`app/controller/`**: Core logic for UIPath execution and unit registration.
- **`frontend/`**: Vite-based React dashboard for real-time monitoring.
- **`db.sql`**: Schema for Supabase integration.
- **`scipt.ps1`**: The primary "Harmony Manager" script.

---

## 🔗 Environment Configuration

Your `.env` file should include:

- `PUBLIC_SUPABASE_URL`: Your project URL.
- `SUPABASE_SERVICE_SECRET_KEY`: For admin-level access.
- `UI_ROBOT_PATH`: Path to your `UiRobot.exe`.
- `PUBLISH_AUTOMATION_FOLDER`: Where your `.nupkg` files are stored.
