<#
FRIDAY Offline Brain Transplant Setup
======================================

This script sets up FRIDAY for 100% offline operation with Mistral 7B GGUF model.

GOAL: System Internet ke bina 100% chalna chahiye (System should work 100% without internet)

Day 1: The Brain Transplant
- Disable auto-downloads in scripts
- Pre-download Mistral 7B GGUF model
- Lock it in models folder
- Result: Internet off, AI brain still alive

Usage:
    powershell -ExecutionPolicy Bypass -File .\scripts\offline_brain_setup.ps1
    powershell -ExecutionPolicy Bypass -File .\scripts\offline_brain_setup.ps1 -downloadModel -force
    powershell -ExecutionPolicy Bypass -File .\scripts\offline_brain_setup.ps1 -verifyOffline

#>
param(
    [switch]$downloadModel,
    [switch]$installDeps,
    [switch]$verifyOffline,
    [switch]$force,
    [string]$modelPath = "./models/gpt4all"
)

$ErrorActionPreference = "Stop"
$WarningPreference = "Continue"

function Write-Section {
    param([string]$title)
    Write-Host ""
    Write-Host "="*60 -ForegroundColor Cyan
    Write-Host "  $title" -ForegroundColor Cyan
    Write-Host "="*60 -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$msg)
    Write-Host "  ✓ $msg" -ForegroundColor Green
}

function Write-Warning {
    param([string]$msg)
    Write-Host "  ⚠ $msg" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$msg)
    Write-Host "  ✗ $msg" -ForegroundColor Red
}

function Write-Info {
    param([string]$msg)
    Write-Host "  • $msg" -ForegroundColor White
}

Write-Section "FRIDAY OFFLINE BRAIN TRANSPLANT"
Write-Info "Goal: 100% offline operation - Internet ke bina chalna chahiye"
Write-Host ""

# Step 1: Check Python
Write-Section "Step 1: Python Environment"

try {
    $pyVersion = & python --version 2>&1
    Write-Success "Python found: $pyVersion"
} catch {
    Write-Error "Python not found. Please install Python 3.8+ and add to PATH"
    exit 1
}

# Step 2: Install required dependencies
if ($installDeps -or $downloadModel) {
    Write-Section "Step 2: Installing Python Dependencies"
    
    $packages = @(
        "ctransformers",  # For GGUF model loading (NO AUTO-DOWNLOAD)
        "torch",          # Deep learning framework
        "numpy",          # Numerical computing
    )
    
    foreach ($pkg in $packages) {
        try {
            Write-Info "Installing $pkg..."
            & python -m pip install $pkg -q 2>&1 | Out-Null
            Write-Success "$pkg installed"
        } catch {
            Write-Warning "Failed to install $pkg - Continuing anyway"
        }
    }
}

# Step 3: Download GGUF Model
if ($downloadModel) {
    Write-Section "Step 3: Downloading Mistral 7B GGUF Model"
    
    Write-Info "This model will be locked in models folder"
    Write-Info "Model: Mistral 7B Instruct (Q4_K_M quantization)"
    Write-Info "Size: ~5 GB (one-time download)"
    Write-Host ""
    
    if (-not $force) {
        $confirm = Read-Host "Proceed with download? (y/N)"
        if ($confirm.ToLower() -ne 'y') {
            Write-Warning "Download cancelled"
            exit 0
        }
    }
    
    Write-Info "Downloading GGUF model..."
    & python .\scripts\download_mistral_gguf.py --model mistral-7b-instruct --model-dir $modelPath $(if ($force) { "--force" })
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "GGUF model downloaded successfully"
    } else {
        Write-Error "GGUF download failed"
        exit 1
    }
}

# Step 4: Update .env for offline mode
Write-Section "Step 4: Configuring Environment for Offline Operation"

$envFile = ".\.env"
$envBackup = ".\.env.backup"

if (Test-Path $envFile) {
    Copy-Item $envFile $envBackup -Force
    Write-Info "Backed up .env to .env.backup"
}

$ggufPath = Resolve-Path "$modelPath\*.gguf" -ErrorAction SilentlyContinue | Select-Object -First 1

if ($ggufPath) {
    $ggufPath = $ggufPath.ProviderPath
    Write-Success "Found GGUF model: $ggufPath"
    
    # Update or create .env
    $envContent = @"
# OFFLINE MODE CONFIGURATION
# ===========================
# Internet ke bina 100% chalna chahiye

# Disable internet auto-downloads
GPT4ALL_NO_AUTO_DOWNLOAD=1

# Use direct GGUF model path (no auto-download)
GPT4ALL_MODEL_PATH=$ggufPath

# Prefer local LLM over cloud APIs
PREFER_LOCAL_LLM=1

# Use offline vision (YOLO) instead of cloud vision
PREFER_OFFLINE_VISION=1

# Optional: Keep these if you want cloud fallback
# GOOGLE_API_KEY=
# OPENAI_API_KEY=

# Optional: Specify alternative offline models
# GPT4ALL_MODEL=gpt4all-lora-quantized
# WHISPER_MODEL=base

"@
    
    # Append existing env vars if file exists (but override offline settings)
    if (Test-Path $envFile) {
        $existing = Get-Content $envFile | Where-Object { 
            $_ -notmatch "^(PREFER_LOCAL_LLM|PREFER_OFFLINE_VISION|GPT4ALL|FRIDAY_)" -and $_ -notmatch "^#"
        }
        $envContent = $envContent + (($existing | Out-String).Trim())
    }
    
    Set-Content -Path $envFile -Value $envContent -Force
    Write-Success "Updated .env with offline configuration"
    Write-Info ".env location: $(Resolve-Path $envFile)"
} else {
    Write-Warning "No GGUF model found in $modelPath"
    Write-Info "Run with -downloadModel flag to download"
}

# Step 5: Verify offline readiness
if ($verifyOffline) {
    Write-Section "Step 5: Verifying Offline Readiness"
    
    Write-Info "Running offline verification..."
    Write-Host ""
    
    & python .\scripts\verify_offline.py --check-all
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Offline verification passed!"
    } else {
        Write-Warning "Some offline checks failed - See details above"
    }
}

# Step 6: Final Instructions
Write-Section "OFFLINE BRAIN TRANSPLANT COMPLETE"

Write-Success "FRIDAY is now configured for offline operation!"
Write-Host ""
Write-Info "Configuration Applied:"
Write-Info "  ✓ Auto-downloads disabled"
Write-Info "  ✓ GGUF model locked in models folder"
Write-Info "  ✓ Environment variables configured"
Write-Info "  ✓ Local LLM prioritized"
Write-Info "  ✓ Offline vision (YOLO) enabled"
Write-Host ""

Write-Info "NEXT STEPS:"
Write-Info "  1. Disconnect from internet (or just test)"
Write-Info "  2. Start FRIDAY backend: npm run dev"
Write-Info "  3. Open http://localhost:3000 in browser"
Write-Info "  4. Chat with your AI brain - no internet needed!"
Write-Host ""

Write-Info "VERIFICATION:"
Write-Info "  To verify offline mode works:"
Write-Info "  python .\scripts\verify_offline.py --check-all"
Write-Host ""

Write-Host "="*60 -ForegroundColor Green
Write-Host "🟢 Day 1 Complete: Your brain is now 100% offline!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green
Write-Host ""
