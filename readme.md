# UiPath Automation Server

This is a FastAPI-based server designed to trigger and manage UiPath automations. It integrates with Supabase for data persistence and provides endpoints to list, create, and run automations.

## Features

- **FastAPI**: High-performance API framework.
- **Supabase Integration**: Stores automation metadata in a Supabase database.
- **UiPath Triggering**: helper functions to execute UiPath processes locally.
- **Cloudflare Tunnel**: Instructions included for exposing the local server to the internet.

## Prerequisites

- **Python 3.8+** installed on your system.
- **Supabase Account**: You need a project URL and API key.
- **UiPath**: (Optional) For actual execution of automations, UiPath Robot/Studio should be installed.

## Installation

1.  **Clone the repository** (if you haven't already):
    ```bash
    git clone <repository-url>
    cd iaynomrah-local-server
    ```

2.  **Create and Activate a Virtual Environment**:
    ```bash
    # Windows
    python -m venv .venv
    .venv\Scripts\activate

    # macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Configuration**:
    Create a `.env` file in the root directory and add your application secrets. You can use the example below:
    ```env
    SUPABASE_URL=your_supabase_url
    SUPABASE_KEY=your_supabase_anon_key
    # Add other variables as needed by app/core/supabase.py or app/helper/uipath.py
    ```

## Running the Application

To start the server, run the following command from the root directory:

```bash
python -m app.main
```

Alternatively, you can run it directly with `uvicorn`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 2026 --reload
```

The server will start at `http://localhost:2026`.
- API Documentation (Swagger UI): `http://localhost:2026/docs`

## Exposing via Cloudflare Tunnel

To expose your local server (running on port 2026) to the internet securely using Cloudflare Tunnel, follow these steps:

1.  **Install Cloudflared**:
    - **Windows**: `winget install Cloudflare.cloudflared`
    - **macOS**: `brew install cloudflare/cloudflare-oss/cloudflared`
    - **Linux**: Follow instructions on the [Cloudflare downloads page](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation).

2.  **Run the Tunnel**:
    Execute the following command in your terminal:

    ```bash
    cloudflared tunnel --url http://localhost:2026
    ```

    This command will generate a temporary public URL (e.g., `https://random-name.trycloudflare.com`) that tunnels traffic to your local port 2026.

## Project Structure

- `app/main.py`: Main application entry point and API routes.
- `app/core/`: Core configurations (Supabase connection).
- `app/helper/`: Helper modules (UiPath execution logic).
- `frontend/`: Static frontend files.
- `requirements.txt`: Python package dependencies.