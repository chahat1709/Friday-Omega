<#
FRIDAY Setup Models Script
Usage:
    powershell -ExecutionPolicy Bypass -File .\scripts\setup_models.ps1 -yolo -coqui -gpt4all
    powershell -ExecutionPolicy Bypass -File .\scripts\setup_models.ps1 -gpt4all -gptModels 'gpt4all-lora-quantized' -auto -force

This script attempts to install Python packages and download small/medium-sized models for offline operation.
Options:
    -auto : Automatically use a curated list of small/quantized GPT4All models and avoid interactive prompts
    -force : Force model downloads without additional confirmation prompts (useful in CI or scripted runs)
It avoids downloading extremely large models automatically; for bigger LLM models, we provide instructions and optional commands.
#>
param(
    [switch]$yolo,
    [switch]$yoloExtra,
    [switch]$coqui,
    [switch]$gpt4all,
    [string]$gptModels = '',
    [switch]$auto,
    [switch]$force
)

# Detect python version
$pyVersion = (& python -V 2>&1)
Write-Host "Detected Python version: $pyVersion" -ForegroundColor Cyan
try {
    $pyv = & python -c "import sys; print(sys.version_info[0], sys.version_info[1])" 2>$null
} catch {
    # ignore
}

function Install-Package([string[]]$pkg) {
    $pkgMessage = $pkg -join ' '
    Write-Host "Installing Python package: $pkgMessage" -ForegroundColor Cyan
    try {
        & python -m pip install @pkg
    } catch {
        Write-Host ('Failed to install {0}: {1}' -f $pkgMessage, $_.Exception.Message) -ForegroundColor Yellow
    }
}

function Get-Gpt4AllModels() {
    Write-Host "Fetching available GPT4All models (via gpt4all)..." -ForegroundColor Cyan
    try {
        $out = & python .\scripts\gpt4all_list_models.py 2>$null
        if ($out -eq $null -or $out.Trim().Length -eq 0) { Write-Host "gpt4all did not return a list; ensure gpt4all is installed." -ForegroundColor Yellow; return $null }
        $json = $out | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($json -and $json.success -and $json.models) {
            if ($json.PSObject.Properties.Match('note').Count -gt 0 -and $json.note) { Write-Host "(Note from gpt4all helper: $($json.note))" -ForegroundColor Yellow }
            return $json.models
        }
        return $null
    } catch {
        Write-Host "Failed to list gpt4all models: $_" -ForegroundColor Yellow
        return $null
    }
}

function Download-Gpt4AllModels([string[]]$models, [switch]$force) {
    if (-not $models -or $models.Count -eq 0) { Write-Host "No GPT4All models specified for download" -ForegroundColor Yellow; return }
    Write-Host "Preparing to download the following GPT4All models: $($models -join ', ')" -ForegroundColor Cyan
    # Prompt the user to confirm for large models unless forced
    $large = $false
    foreach ($m in $models) {
        if ($m -match '3b|13b|llama2|llama3' -or $m -match '\b(q2|gpt4.*)\b') { $large = $true }
    }
    if ($large -and (-not $force)) {
        Write-Host "One or more selected GPT4All models appear large. Use -force to bypass confirmation." -ForegroundColor Yellow
        $ans = Read-Host "Proceed to download these models now? (y/N)"
        if ($ans.ToLower() -ne 'y') { Write-Host 'Skipping GPT4All download', -ForegroundColor Yellow; return }
    }
    # Call the Python download script
    $args = $models -join ' '
    try {
        $out = & python .\scripts\gpt4all_download.py @models 2>$null
        if ($out) {
            $json = $out | ConvertFrom-Json -ErrorAction SilentlyContinue
            if ($json.success -eq $true) { Write-Host "Downloaded/initialized GPT4All models: $($models -join ', ')" -ForegroundColor Green; return $json.results }
            Write-Host "gpt4all download reported: $out" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "GPT4All download failed: $_" -ForegroundColor Yellow
    }
}

# Ensure pip is up-to-date to reduce compatibility issues
Write-Host 'Ensuring pip is up-to-date (this may need admin privileges)...' -ForegroundColor Cyan
try { & python -m pip install --upgrade pip } catch { Write-Host 'pip upgrade failed (non-fatal).' -ForegroundColor Yellow }

if ($yolo) {
    Write-Host "### YOLOv8 (Ultralytics) setup" -ForegroundColor Green
    Install-Package 'ultralytics'
    try {
        Write-Host 'Downloading yolov8n.pt (this may auto-download via ultralytics)...' -ForegroundColor Cyan
        & python -c "from ultralytics import YOLO; m=YOLO('yolov8n.pt'); print('YOLO model path:', getattr(m, 'model', 'N/A'))"
    } catch {
        Write-Host "YOLO download failed or needs credentials: $_" -ForegroundColor Yellow
    }
}

if ($coqui) {
    Write-Host "### Coqui TTS setup" -ForegroundColor Green
    Write-Host "Note: Coqui TTS may require PyTorch (torch) for some models. If the automatic install fails, please follow the instructions in README_OFFLINE.md to install a compatible torch wheel for your system and Python version." -ForegroundColor Yellow
    # Ensure torch (CPU) is present; this may take time. We'll attempt a CPU-only wheel via the official pytorch CPU index first.
    # Use array parameter to ensure the '--index-url' option isn't combined with the package name.
    try {
        Install-Package '--index-url', 'https://download.pytorch.org/whl/cpu', 'torch'
    } catch {
        Write-Host "Attempt to install CPU-only torch failed. Trying generic 'torch' install from PyPI..." -ForegroundColor Yellow
        Install-Package 'torch'
    }
    # Install Coqui TTS and provide pyttsx3 as a recommended fallback
    Install-Package 'TTS'
    Install-Package 'pyttsx3'
    # Verify if TTS imported correctly
    try {
        $ttsCheck = & python -c "import importlib; print('FOUND_TTS' if importlib.util.find_spec('TTS') else 'NO_TTS')" 2>$null
        if ($ttsCheck -eq 'NO_TTS') {
            Write-Host "Coqui TTS is not available for this Python version. Consider installing Python 3.10/3.11, or use 'pyttsx3' local TTS fallback. See README_OFFLINE.md for details." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Coqui TTS might not be installed or is not compatible with this Python version. Refer to README_OFFLINE.md for manual install instructions (choose Python 3.10/3.11 and compatible torch wheels)." -ForegroundColor Yellow
    }
    try {
        Write-Host 'Downloading Coqui TTS example model (small LJSpeech) — may trigger additional downloads' -ForegroundColor Cyan
        & python -c "from TTS.api import TTS; t=TTS('tts_models/en/ljspeech/tacotron2-DDC'); print('Coqui tts model loaded: OK')"
    } catch {
        Write-Host "Coqui model load failed or requires torch: $_" -ForegroundColor Yellow
    }
}

if ($gpt4all) 
    Write-Host "### GPT4All (local LLM) setup" -ForegroundColor Green
    Write-Host "We will attempt to install the `gpt4all` python package to make model downloads easier. This is a lightweight local LLM option." -ForegroundColor Cyan
    Install-Package 'gpt4all'
    try {
        Write-Host 'Attempting to list available gpt4all models via helper script...' -ForegroundColor Cyan
        $avail = Get-Gpt4AllModels
        if ($avail -and $avail.Count -gt 0) { Write-Host "gpt4all helper reported ${($avail | Measure-Object).Count} models" -ForegroundColor Cyan }
    } catch {
        Write-Host "gpt4all list helper failed: $_" -ForegroundColor Yellow
        Write-Host "If you prefer LLaMA/ggml models, consider using 'llama.cpp' or 'ollama' to download model images manually." -ForegroundColor Yellow
    }

    # A small curated list of well-known, small/quantized GPT4All models suitable for offline pre-download
    $curatedModels = 'gpt4all-lora-quantized'
    if ($gptModels -eq '') {
        if ($auto) { Write-Host "Auto mode: using curated models: $curatedModels" -ForegroundColor Cyan; $gptModels = $curatedModels }
        else {
        Write-Host "No gpt4all models specified in -gptModels." -ForegroundColor Cyan
        # Attempt to present an interactive list if this is an interactive shell
        $available = Get-Gpt4AllModels
        if ($available -ne $null -and $available.Count -gt 0 -and $Host.UI.RawUI.KeyAvailable -ne $null) {
            Write-Host "Available GPT4All models (sample):" -ForegroundColor Cyan
            $count = [Math]::Min(20, $available.Count)
            for ($i=0; $i -lt $count; $i++) {
                $m = $available[$i]
                $id = $null
                if ($m -is [string]) { $id = $m } else {
                    if ($m.PSObject.Properties.Match('name').Count -gt 0) { $id = $m.name }
                    elseif ($m.PSObject.Properties.Match('id').Count -gt 0) { $id = $m.id }
                }
                $size = $null
                if ($m -is [System.Management.Automation.PSObject]) { if ($m.PSObject.Properties.Match('size').Count -gt 0) { $size = $m.size } }
                $sizeStr = ""
                if ($size) { $sizeStr = "(size: $size)" }
                # Retrieve potential model 'id' and 'name' to show both
                $name = $null
                if ($m.PSObject.Properties.Match('name').Count -gt 0) { $name = $m.name }
                $mId = $null
                if ($m.PSObject.Properties.Match('id').Count -gt 0) { $mId = $m.id }
                $display = $name
                if ($mId -and $mId -ne $name) { $display = "$name (id: $mId)" }
                Write-Host ("{0}. {1} {2}" -f ($i+1), ($display), $sizeStr)
            }
            Write-Host 'Enter the model name(s) or numbers you want to download from the list above, comma-separated (or press Enter to use default small quantized):' -ForegroundColor Yellow
            $input = Read-Host 'Model(s, use numbers or exact ids/names)'
            if ($input -and $input.Trim().Length -gt 0) {
                $tokens = $input.Split(',') | ForEach-Object { $_.Trim() }
                $selected = @()
                # construct canonical model id list for the displayed models
                $displayModels = @()
                for ($i=0; $i -lt $count; $i++) {
                    $m = $available[$i]
                    $id = $null
                    if ($m -is [string]) { $id = $m } else {
                        if ($m.PSObject.Properties.Match('id').Count -gt 0) { $id = $m.id }
                        elseif ($m.PSObject.Properties.Match('name').Count -gt 0) { $id = $m.name }
                    }
                    if ($id) { $displayModels += $id } else { $displayModels += '' }
                }
                foreach ($t in $tokens) {
                    if ($t -match '^[0-9]+$') {
                        $idx = [int]$t - 1
                        if ($idx -ge 0 -and $idx -lt $displayModels.Count) { $val = $displayModels[$idx]; if ($val) { $selected += $val } }
                    } elseif ($t -match '^[0-9]+\s*-\s*[0-9]+$') {
                        $parts = $t -split '-' | ForEach-Object { [int]$_ }
                        $start = $parts[0] - 1; $end = $parts[1] - 1
                        for ($j=$start; $j -le $end; $j++) { if ($j -ge 0 -and $j -lt $displayModels.Count) { $selected += $displayModels[$j] } }
                    } else {
                        # assume it's a model id/name; keep as is
                        if ($t -ne '') { $selected += $t }
                    }
                }
                if ($selected.Count -gt 0) { $gptModels = ($selected -join ',') } else { $gptModels = $input.Trim() }
            } else { $gptModels = $curatedModels }
        } else {
            Write-Host "Falling back to default: gpt4all-lora-quantized" -ForegroundColor Cyan
            $gptModels = $curatedModels
        }
    }

    if ($gptModels -ne '') {
        Write-Host "Downloading and initializing GPT4All models: $gptModels" -ForegroundColor Cyan
        $split = $gptModels.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
        # Attempt to list available models for validation
        $availableModels = Get-Gpt4AllModels
        if ($availableModels -eq $null) {
            Write-Host "Could not fetch available gpt4all models (list call failed); proceed carefully." -ForegroundColor Yellow
            $interactiveFallback = $true
        } else { $interactiveFallback = $false }
        foreach ($m in $split) {
            Write-Host "Attempting to initialize model: $m" -ForegroundColor Cyan
            # Validate if possible
            if ($availableModels -ne $null) {
                $valid = $availableModels | Where-Object { $_.name -eq $m -or $_.id -eq $m } | Select-Object -First 1
                if (-not $valid) { Write-Host "Model $m not found in GPT4All registry. Use the exact model id or run the list script. Skipping." -ForegroundColor Yellow; continue }
            }
            # Attempt download via our helper that calls gpt4all
                try {
                $res = Download-Gpt4AllModels -models @($m) -force:$force
                if ($res -and $res.$m -and $res.$m.success -eq $true) { Write-Host "Model $m downloaded/initialized: $($res.$m.path)" -ForegroundColor Green }
                elseif ($res -and $res.$m -and $res.$m.error) { Write-Host "Model init for $m returned error: $($res.$m.error)" -ForegroundColor Yellow }
            } catch {
                Write-Host "Model $m initialization failed: $_" -ForegroundColor Yellow
                Write-Host "If this persists, verify the model name or pre-download manually. For example, try: python -c \"from gpt4all import GPT4All; print(GPT4All.list_models())\"" -ForegroundColor Cyan
                Write-Host "Or check https://gpt4all.io for available models and instructions on manual gguf downloads." -ForegroundColor Cyan
            }
        }
    }
    if ($interactiveFallback -and ($split -and $split.Count -gt 0)) {
        Write-Host "Because the gpt4all registry listing failed, consider verifying model names manually." -ForegroundColor Yellow
        Write-Host "You can list remote gpt4all models by running: python .\scripts\gpt4all_list_models.py (may still fail on some systems)" -ForegroundColor Cyan
    }
}

Write-Host "Setup script complete. Check the README_OFFLINE.md for further instructions and manual steps for bigger models." -ForegroundColor Green
