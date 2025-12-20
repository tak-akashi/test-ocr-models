<#
.SYNOPSIS
    Document Processing Docker Helper Script for Windows

.DESCRIPTION
    Provides easy-to-use commands for running the document processing Docker container.
    Supports layout analysis, OCR processing, preprocessing, and Jupyter Lab.

.EXAMPLE
    .\docker-run.ps1 layout -Models all
    Run layout analysis with all models

.EXAMPLE
    .\docker-run.ps1 ocr -Models upstage,azure
    Run OCR with specific models

.EXAMPLE
    .\docker-run.ps1 jupyter
    Start Jupyter Lab server

.EXAMPLE
    .\docker-run.ps1 shell
    Start interactive bash shell

.NOTES
    Requires Docker Desktop for Windows with WSL2 backend
#>

param(
    [Parameter(Position = 0)]
    [ValidateSet("layout", "ocr", "preprocess", "jupyter", "shell", "build", "help")]
    [string]$Command = "help",

    [Parameter()]
    [string[]]$Models,

    [Parameter()]
    [switch]$GPU,

    [Parameter()]
    [switch]$Optimize,

    [Parameter()]
    [int]$Samples,

    [Parameter()]
    [string]$Input,

    [Parameter(ValueFromRemainingArguments)]
    [string[]]$ExtraArgs
)

# Configuration
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ServiceName = if ($GPU) { "document-processor-gpu" } else { "document-processor" }
$Profile = if ($GPU) { "--profile gpu" } else { "" }

# Ensure we're in the project directory
Push-Location $ProjectRoot

try {
    # Check Docker is running
    $dockerStatus = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker is not running. Please start Docker Desktop."
        exit 1
    }

    # Ensure required directories exist
    if (-not (Test-Path "data")) { New-Item -ItemType Directory -Path "data" -Force | Out-Null }
    if (-not (Test-Path "output")) { New-Item -ItemType Directory -Path "output" -Force | Out-Null }
    if (-not (Test-Path ".cache")) { New-Item -ItemType Directory -Path ".cache" -Force | Out-Null }

    switch ($Command) {
        "layout" {
            $args = @("--models")
            if ($Models) {
                $args += $Models -join " "
            } else {
                $args += "all"
            }
            if ($Optimize) { $args += "--optimize" }
            if ($Samples) { $args += "--n-samples", $Samples }
            if ($Input) { $args += "--input", $Input }
            if ($ExtraArgs) { $args += $ExtraArgs }

            Write-Host "Running layout analysis..." -ForegroundColor Cyan
            $cmd = "docker compose $Profile run --rm $ServiceName layout $($args -join ' ')"
            Write-Host "Command: $cmd" -ForegroundColor Gray
            Invoke-Expression $cmd
        }

        "ocr" {
            $args = @("--models")
            if ($Models) {
                $args += $Models -join " "
            } else {
                $args += "all"
            }
            if ($Samples) { $args += "--n-samples", $Samples }
            if ($Input) { $args += "--input", $Input }
            if ($ExtraArgs) { $args += $ExtraArgs }

            Write-Host "Running OCR processing..." -ForegroundColor Cyan
            $cmd = "docker compose $Profile run --rm $ServiceName ocr $($args -join ' ')"
            Write-Host "Command: $cmd" -ForegroundColor Gray
            Invoke-Expression $cmd
        }

        "preprocess" {
            Write-Host "Running preprocessing..." -ForegroundColor Cyan
            $cmd = "docker compose run --rm $ServiceName preprocess $($ExtraArgs -join ' ')"
            Write-Host "Command: $cmd" -ForegroundColor Gray
            Invoke-Expression $cmd
        }

        "jupyter" {
            Write-Host "Starting Jupyter Lab..." -ForegroundColor Cyan
            Write-Host "Access at: http://localhost:8890" -ForegroundColor Yellow
            docker compose --profile jupyter up jupyter
        }

        "shell" {
            Write-Host "Starting interactive shell..." -ForegroundColor Cyan
            docker compose $Profile run --rm $ServiceName bash
        }

        "build" {
            Write-Host "Building Docker images..." -ForegroundColor Cyan
            if ($GPU) {
                docker compose --profile gpu build
            } else {
                docker compose build
            }
        }

        "help" {
            Write-Host @"

Document Processing Docker Helper
=================================

USAGE:
    .\docker-run.ps1 <command> [options]

COMMANDS:
    layout      Run layout analysis models
    ocr         Run OCR-only processing
    preprocess  Run PDF preprocessing utilities
    jupyter     Start Jupyter Lab server
    shell       Start interactive bash shell
    build       Build Docker images
    help        Show this help message

OPTIONS:
    -Models     Comma-separated list of models (upstage,azure,yomitoku,gemini,claude,qwen or 'all')
    -GPU        Use GPU-enabled container (requires NVIDIA GPU)
    -Optimize   Enable GPU optimization for Qwen model
    -Samples    Limit processing to first N files
    -Input      Specify input file or directory

EXAMPLES:
    # Run all layout models
    .\docker-run.ps1 layout -Models all

    # Run specific OCR models
    .\docker-run.ps1 ocr -Models upstage,azure

    # Run Qwen with GPU
    .\docker-run.ps1 layout -Models qwen -GPU -Optimize

    # Process first 5 files only
    .\docker-run.ps1 layout -Models upstage -Samples 5

    # Start Jupyter Lab
    .\docker-run.ps1 jupyter

    # Interactive shell
    .\docker-run.ps1 shell

REQUIREMENTS:
    - Docker Desktop for Windows with WSL2 backend
    - .env file with API keys (UPSTAGE_API_KEY, etc.)
    - For GPU: NVIDIA GPU with CUDA support

"@ -ForegroundColor White
        }
    }
}
finally {
    Pop-Location
}
