# Navigate to project directory
Set-Location "C:\Users\Admin\code\iaynomrah-local-server\"

# Define paths
$logPath = ".\cloudflared.log"
$errorLogPath = ".\cloudflared_error.log"
$envPath = ".\.env"
$rootPath = "C:\Users\Admin\code\iaynomrah-local-server\"

while ($true) {
    # Clear old logs
    Remove-Item $logPath -ErrorAction SilentlyContinue
    Remove-Item $errorLogPath -ErrorAction SilentlyContinue

    # Start cloudflared
    Write-Output "Starting Cloudflare tunnel..."
    Start-Process cloudflared -ArgumentList "tunnel --url http://localhost:8000 --no-autoupdate" `
        -RedirectStandardOutput $logPath `
        -RedirectStandardError $errorLogPath `
        -NoNewWindow

    # Wait for tunnel URL
    $url = $null
    $regex = "https://[a-zA-Z0-9\-]+\.trycloudflare\.com"

    Write-Output "Waiting for Cloudflared to provide tunnel URL..."
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 2
        Write-Output "Attempt $($i + 1)/30..."

        $cloudflaredOutput = ""
        if (Test-Path $logPath) {
            $cloudflaredOutput += Get-Content $logPath -Raw -ErrorAction SilentlyContinue
        }
        if (Test-Path $errorLogPath) {
            $cloudflaredOutput += Get-Content $errorLogPath -Raw -ErrorAction SilentlyContinue
        }

        if ($cloudflaredOutput) {
            $regexMatches = [regex]::Matches($cloudflaredOutput, $regex)
            if ($regexMatches.Count -gt 0) {
                $url = $regexMatches[0].Value
                break
            }
        }
    }

    if ($url) {
        if (Test-Path $envPath) {
            $content = Get-Content $envPath
            $updated = $false
            $newContent = $content | ForEach-Object {
                if ($_ -match "^API_BASE_URL=") {
                    $updated = $true
                    "API_BASE_URL=$url"
                } else {
                    $_
                }
            }
            if (-not $updated) { $newContent += "API_BASE_URL=$url" }
            $newContent | Set-Content $envPath -Encoding UTF8
        } else {
            "API_BASE_URL=$url" | Set-Content $envPath -Encoding UTF8
        }
        Write-Output "Updated .env with API_BASE_URL=$url"
    } else {
        Write-Output "Could not extract Cloudflare tunnel URL after waiting."
    }

    # Activate venv and run uvicorn
    .\.venv\Scripts\Activate.ps1
    try {
        Write-Output "Starting server..."
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    } finally {
        Write-Output "Shutting down cloudflared..."
        Stop-Process -Name "cloudflared" -ErrorAction SilentlyContinue
    }

    # After server stops, ask to restart
    Write-Host ""
    $choice = Read-Host "Server stopped. Press 'r' to Restart or 'n' to exit"

    if ($choice -eq "r") {
        Write-Output "Restarting..."
        Write-Host ""
        continue
    } else {
        Write-Output "Exiting."
        break
    }
}