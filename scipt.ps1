# Navigate to project directory
Set-Location "C:\Users\Admin\Desktop\HARMONY\harmony-local-server"

# Define paths
$logPath = ".\cloudflared.log"
$errorLogPath = ".\cloudflared_error.log"
$envPath = ".\.env"
$rootPath = "C:\Users\Admin\Desktop\HARMONY\harmony-local-server"
$frontendPath = "$rootPath\frontend"

$skipSetup = $false
while ($true) {
    if (-not $skipSetup) {
        # Ask about git pull
    $doPull = Read-Host "Pull latest changes from git? (y/n)"
    if ($doPull -eq "y") {
        Write-Output "Pulling latest changes..."
        git pull
        if ($LASTEXITCODE -ne 0) {
            Write-Output "Git pull failed."
            Read-Host "Press Enter to try again or Ctrl+C to exit"
            continue
        }
    }

    # Ask about pip install
    $doInstall = Read-Host "Run pip install -r requirements.txt? (y/n)"
    if ($doInstall -eq "y") {
        Write-Output "Installing Python dependencies..."
        .\venv\Scripts\Activate.ps1
        pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Output "pip install failed."
            Read-Host "Press Enter to try again or Ctrl+C to exit"
            continue
        }
    }

    # Ask about frontend build
    $doBuild = Read-Host "Build frontend? (y/n)"
    if ($doBuild -eq "y") {
        Write-Output "Installing frontend dependencies..."
        Set-Location $frontendPath
        npm i
        if ($LASTEXITCODE -ne 0) {
            Write-Output "npm install failed."
            Set-Location $rootPath
            Read-Host "Press Enter to try again or Ctrl+C to exit"
            continue
        }

        Write-Output "Building frontend..."
        npm run build
        if ($LASTEXITCODE -ne 0) {
            Write-Output "Frontend build failed."
            Set-Location $rootPath
            Read-Host "Press Enter to try again or Ctrl+C to exit"
            continue
        }

        # Return to root
        Set-Location $rootPath
        Write-Output "Frontend build complete."
    }
}
$skipSetup = $false

    # Clear old logs
    Remove-Item $logPath -ErrorAction SilentlyContinue
    Remove-Item $errorLogPath -ErrorAction SilentlyContinue

    # Start cloudflared
    Write-Output "Starting Cloudflare tunnel..."
    Start-Process cloudflared -ArgumentList "tunnel --url http://localhost:2026 --no-autoupdate" `
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
    .\venv\Scripts\Activate.ps1
    try {
        Write-Output "Starting server..."
        uvicorn app.main:app --host 0.0.0.0 --port 2026 --reload
    } finally {
        Write-Output "Shutting down cloudflared..."
        Stop-Process -Name "cloudflared" -ErrorAction SilentlyContinue
    }

    # After server stops, ask to restart
    Write-Host ""
    $choice = Read-Host "Server stopped. Press 'r' to Quick Reload, 'y' for Setup + Start, or 'n' to exit"
    
    if ($choice -eq "r") {
        $skipSetup = $true
        Write-Output "Quick Reloading..."
        Write-Host ""
        continue
    }
    elseif ($choice -eq "y") {
        $skipSetup = $false
        Write-Output "Restarting with setup..."
        Write-Host ""
        continue
    }
    else {
        Write-Output "Exiting."
        break
    }
}