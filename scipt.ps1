# Navigate to project directory
Set-Location "C:\Users\Admin\Documents\code\iaynomrah-local-server"

# Define paths
$logPath = ".\cloudflared.log"
$errorLogPath = ".\cloudflared_error.log"
$envPath = ".\.env"

# Start cloudflared in background, redirecting stdout and stderr to separate files
Start-Process cloudflared -ArgumentList "tunnel --url http://localhost:2026" `
    -RedirectStandardOutput $logPath `
    -RedirectStandardError $errorLogPath `
    -NoNewWindow

# Loop until the .trycloudflare.com URL appears in the log
$url = $null
$regex = "https://[a-zA-Z0-9\-]+\.trycloudflare\.com"

Write-Output "Waiting for Cloudflared to provide tunnel URL..."
for ($i = 0; $i -lt 30; $i++) {   # up to ~30 seconds
    Start-Sleep -Seconds 2
    
    # Check both log files since cloudflared might output to either
    $cloudflaredOutput = ""
    if (Test-Path $logPath) {
        $cloudflaredOutput += Get-Content $logPath -Raw -ErrorAction SilentlyContinue
    }
    if (Test-Path $errorLogPath) {
        $cloudflaredOutput += Get-Content $errorLogPath -Raw -ErrorAction SilentlyContinue
    }
    
    if ($cloudflaredOutput) {
        $matches = [regex]::Matches($cloudflaredOutput, $regex)
        if ($matches.Count -gt 0) {
            $url = $matches[0].Value
            break
        }
    }
}

if ($url) {
    # Update or create API_BASE_URL in .env
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
        if (-not $updated) {
            $newContent += "API_BASE_URL=$url"
        }
        $newContent | Set-Content $envPath
    } else {
        "API_BASE_URL=$url" | Set-Content $envPath
    }

    Write-Output "Updated .env with API_BASE_URL=$url"
} else {
    Write-Output "Could not extract Cloudflare tunnel URL after waiting."
}

# Finally, run uvicorn in foreground so you see logs
uvicorn app.main:app --host 0.0.0.0 --port 2026 --reload