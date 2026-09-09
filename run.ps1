# ==============================================================================
# Automotive AI Agent - PowerShell Helper Script for Windows
# Equivalent to Makefile for Windows PowerShell environments (Podman / Docker)
# ==============================================================================

param (
    [Parameter(Position=0)]
    [ValidateSet("up", "down", "clean", "restart", "build", "ps", "logs", "logs-backend", "test", "lint", "health", "validate", "shell", "specs", "spec-validate", "help")]
    [string]$Command = "help"
)

# Ensure Python user scripts directory is in PATH for podman-compose
$PythonScriptsPath = "C:\Users\mathe\AppData\Local\Python\pythoncore-3.14-64\Scripts"
if ((Test-Path $PythonScriptsPath) -and ($env:PATH -notlike "*$PythonScriptsPath*")) {
    $env:PATH = "$PythonScriptsPath;$env:PATH"
}

# Detect compose command
$ComposeCmd = $null
if (Get-Command "podman-compose" -ErrorAction SilentlyContinue) {
    $ComposeCmd = "podman-compose"
} elseif (Get-Command "docker-compose" -ErrorAction SilentlyContinue) {
    $ComposeCmd = "docker-compose"
} elseif (Get-Command "podman" -ErrorAction SilentlyContinue) {
    $ComposeCmd = "podman compose"
} elseif (Get-Command "docker" -ErrorAction SilentlyContinue) {
    $ComposeCmd = "docker compose"
} else {
    # Fallback to py -m podman_compose
    $ComposeCmd = "py -m podman_compose"
}

function Show-Help {
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "Automotive AI Agent - Comandos PowerShell (Windows):" -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "  .\run.ps1 up            - Inicia todos os serviços em segundo plano"
    Write-Host "  .\run.ps1 down          - Para e remove os contêineres"
    Write-Host "  .\run.ps1 clean         - Remove contêineres e volumes (destrutivo)"
    Write-Host "  .\run.ps1 restart       - Reinicia os serviços"
    Write-Host "  .\run.ps1 build         - Reconstrói a imagem do backend"
    Write-Host "  .\run.ps1 ps            - Exibe status dos contêineres"
    Write-Host "  .\run.ps1 logs          - Exibe logs de todos os serviços"
    Write-Host "  .\run.ps1 logs-backend  - Exibe logs do backend FastAPI"
    Write-Host "  .\run.ps1 test          - Executa os testes automatizados (pytest)"
    Write-Host "  .\run.ps1 lint          - Executa verificação estática de código com ruff"
    Write-Host "  .\run.ps1 health        - Testa o endpoint de saúde do sistema"
    Write-Host "  .\run.ps1 validate      - Sobe o stack, valida a saúde e executa os testes"
    Write-Host "  .\run.ps1 specs         - Lista as capacidades ativas do OpenSpec"
    Write-Host "  .\run.ps1 spec-validate - Valida as especificações do OpenSpec"
    Write-Host "  .\run.ps1 shell         - Abre um shell interativo no contêiner backend"
    Write-Host "==========================================================" -ForegroundColor Cyan
}

function Invoke-Compose([string]$Args) {
    Write-Host "==> Executando: $ComposeCmd $Args" -ForegroundColor Yellow
    Invoke-Expression "$ComposeCmd $Args"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Falha ao executar '$ComposeCmd'. Verifique Docker Engine ou Podman Machine."
        exit $LASTEXITCODE
    }
}

switch ($Command) {
    "up" {
        Invoke-Compose "up -d"
    }
    "down" {
        Invoke-Compose "down"
    }
    "clean" {
        Invoke-Compose "down -v"
    }
    "restart" {
        Invoke-Compose "down"
        Invoke-Compose "up -d"
    }
    "build" {
        Invoke-Compose "build"
    }
    "ps" {
        Invoke-Compose "ps"
    }
    "logs" {
        Invoke-Compose "logs -f"
    }
    "logs-backend" {
        Invoke-Compose "logs -f backend"
    }
    "test" {
        Invoke-Compose "exec backend pytest -v"
    }
    "lint" {
        Invoke-Compose "exec backend ruff check app tests"
    }
    "health" {
        Write-Host "==> Verificando saúde dos serviços em http://localhost:8000/health..." -ForegroundColor Yellow
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
            $response | ConvertTo-Json -Depth 5 | Write-Host -ForegroundColor Green
        } catch {
            Write-Error "Falha ao conectar no endpoint de saúde. Os contêineres estão em execução?"
        }
    }
    "validate" {
        Invoke-Compose "up -d --build"
        & $PSCommandPath health
        Invoke-Compose "exec backend pytest -v"
    }
    "shell" {
        Invoke-Compose "exec backend /bin/bash"
    }
    "specs" {
        Write-Host "==> Listando especificações do OpenSpec..." -ForegroundColor Cyan
        openspec list --specs
    }
    "spec-validate" {
        Write-Host "==> Validando especificações do OpenSpec..." -ForegroundColor Cyan
        openspec validate --specs
    }
    Default {
        Show-Help
    }
}
