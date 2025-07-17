# Enhanced AI Training Server - 24/7 Multi-Model Training (PowerShell Version)
param(
    [switch]$SkipModelPull,
    [switch]$Verbose
)

# Configuration
$PROJECT_DIR = "$env:USERPROFILE\faith-server"
$VENV_DIR = "$PROJECT_DIR\venv"
$SERVER_DIR = "$PROJECT_DIR\server"
$LOGS_DIR = "$PROJECT_DIR\logs"
$MODELS_DIR = "$PROJECT_DIR\models"
$DATA_DIR = "$PROJECT_DIR\training_data"
$CONFIG_DIR = "$PROJECT_DIR\config"

# Resource limits
$MAX_MEMORY_USAGE = 80
$MAX_GPU_USAGE = 95
$MIN_DISK_SPACE = 10

# Logging function
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor Green
    Add-Content -Path "$LOGS_DIR\training_server.log" -Value $logMessage
}

# Error handling
function Write-Error-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] ERROR: $Message"
    Write-Host $logMessage -ForegroundColor Red
    Add-Content -Path "$LOGS_DIR\training_server.log" -Value $logMessage
}

# Resource monitoring
function Test-SystemResources {
    try {
        $memory = Get-WmiObject -Class Win32_OperatingSystem
        $memoryUsage = [math]::Round((($memory.TotalVisibleMemorySize - $memory.FreePhysicalMemory) / $memory.TotalVisibleMemorySize) * 100, 2)
        
        if ($memoryUsage -gt $MAX_MEMORY_USAGE) {
            Write-Error-Log "Memory usage at $memoryUsage% - pausing new training jobs"
            return $false
        }
        
        $disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
        $diskFreeGB = [math]::Round($disk.FreeSpace / 1GB, 2)
        
        if ($diskFreeGB -lt $MIN_DISK_SPACE) {
            Write-Error-Log "Low disk space ($diskFreeGB GB) - cleaning up old models"
            Invoke-Cleanup
            return $false
        }
        
        return $true
    }
    catch {
        Write-Error-Log "Failed to check system resources: $_"
        return $false
    }
}

# Cleanup function
function Invoke-Cleanup {
    Write-Log "Cleaning up old model checkpoints..."
    
    try {
        # Clean old model files (older than 7 days)
        $cutoffDate = (Get-Date).AddDays(-7)
        Get-ChildItem -Path $MODELS_DIR -Recurse -Directory | 
            Where-Object { $_.LastWriteTime -lt $cutoffDate } |
            Remove-Item -Recurse -Force
        
        # Clean old log files (older than 30 days)
        $logCutoffDate = (Get-Date).AddDays(-30)
        Get-ChildItem -Path $LOGS_DIR -Filter "*.log" |
            Where-Object { $_.LastWriteTime -lt $logCutoffDate } |
            Remove-Item -Force
            
        Write-Log "Cleanup completed"
    }
    catch {
        Write-Error-Log "Cleanup failed: $_"
    }
}

# GPU detection
function Test-GPUAvailability {
    try {
        $gpuInfo = Get-WmiObject -Class Win32_VideoController | Where-Object { $_.Name -like "*NVIDIA*" }
        if ($gpuInfo) {
            Write-Log "NVIDIA GPU detected: $($gpuInfo.Name)"
            $env:CUDA_VISIBLE_DEVICES = "0,1,2,3"
            $env:OMP_NUM_THREADS = "1"
            $env:PYTORCH_CUDA_ALLOC_CONF = "max_split_size_mb:512"
            return $true
        }
        else {
            Write-Log "No NVIDIA GPU detected - using CPU training"
            $env:CUDA_VISIBLE_DEVICES = ""
            return $false
        }
    }
    catch {
        Write-Log "Could not detect GPU: $_"
        return $false
    }
}

# Virtual environment management
function Initialize-VirtualEnvironment {
    Write-Log "Setting up Python virtual environment..."
    
    if (-not (Test-Path $VENV_DIR)) {
        Write-Log "Creating virtual environment..."
        python -m venv $VENV_DIR
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Log "Failed to create virtual environment"
            return $false
        }
    }
    
    # Activate virtual environment
    Write-Log "Activating virtual environment..."
    & "$VENV_DIR\Scripts\Activate.ps1"
    
    # Upgrade pip and install requirements
    Write-Log "Installing Python dependencies..."
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Log "Some packages failed to install"
    }
    
    return $true
}

# Ollama management
function Start-OllamaService {
    Write-Log "Starting Ollama service..."
    
    # Check if Ollama is installed
    try {
        $null = Get-Command ollama -ErrorAction Stop
    }
    catch {
        Write-Error-Log "Ollama not found. Please install from https://ollama.ai/"
        return $false
    }
    
    # Check if already running
    $ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
    if ($ollamaProcess) {
        Write-Log "Ollama already running (PID: $($ollamaProcess.Id))"
    }
    else {
        Write-Log "Starting Ollama daemon..."
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -RedirectStandardOutput "$LOGS_DIR\ollama.log"
        Start-Sleep -Seconds 5
    }
    
    # Verify Ollama is responding
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/version" -TimeoutSec 5
        Write-Log "Ollama daemon responding (Version: $($response.version))"
        return $true
    }
    catch {
        Write-Error-Log "Ollama daemon not responding: $_"
        return $false
    }
}

# Model management
function Pull-Models {
    if ($SkipModelPull) {
        Write-Log "Skipping model pull as requested"
        return
    }
    
    $essentialModels = @(
        "llama2:latest",
        "mistral:latest", 
        "codellama:latest",
        "gemma:2b",
        "phi:latest"
    )
    
    Write-Log "Pulling essential models..."
    foreach ($model in $essentialModels) {
        if (Test-SystemResources) {
            Write-Log "Pulling model: $model"
            ollama pull $model
            if ($LASTEXITCODE -ne 0) {
                Write-Error-Log "Failed to pull model: $model"
            }
            Start-Sleep -Seconds 2
        }
        else {
            Write-Log "Skipping model pull due to resource constraints"
            break
        }
    }
}

# Monitoring service
function Start-MonitoringService {
    Write-Log "Starting monitoring service..."
    
    $monitoringScript = {
        param($LogsDir, $ProjectDir)
        
        function Write-Monitor-Log {
            param([string]$Message)
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            Add-Content -Path "$LogsDir\monitoring.log" -Value "[$timestamp] $Message"
        }
        
        while ($true) {
            try {
                # Get system metrics
                $cpu = Get-WmiObject -Class Win32_Processor | Measure-Object -Property LoadPercentage -Average
                $memory = Get-WmiObject -Class Win32_OperatingSystem
                $memoryUsage = [math]::Round((($memory.TotalVisibleMemorySize - $memory.FreePhysicalMemory) / $memory.TotalVisibleMemorySize) * 100, 2)
                $disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
                $diskUsage = [math]::Round((($disk.Size - $disk.FreeSpace) / $disk.Size) * 100, 2)
                
                Write-Monitor-Log "METRICS: CPU=$($cpu.Average)% MEM=$memoryUsage% DISK=$diskUsage%"
                
                # Check if Ollama is still running
                $ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
                if (-not $ollamaProcess) {
                    Write-Monitor-Log "Ollama daemon died - restarting..."
                    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
                }
                
                Start-Sleep -Seconds 60
            }
            catch {
                Write-Monitor-Log "Monitoring error: $_"
                Start-Sleep -Seconds 60
            }
        }
    }
    
    Start-Job -ScriptBlock $monitoringScript -ArgumentList $LOGS_DIR, $PROJECT_DIR | Out-Null
}

# FastAPI server
function Start-APIServer {
    Write-Log "Starting FastAPI training server..."
    
    Set-Location $SERVER_DIR
    
    $apiScript = {
        param($ServerDir, $LogsDir)
        Set-Location $ServerDir
        uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --access-log --log-file "$LogsDir\api_server.log"
    }
    
    Start-Job -ScriptBlock $apiScript -ArgumentList $SERVER_DIR, $LOGS_DIR | Out-Null
    Start-Sleep -Seconds 3
    
    # Verify API is responding
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 10
        Write-Log "FastAPI server started successfully"
        return $true
    }
    catch {
        Write-Error-Log "Failed to start FastAPI server: $_"
        return $false
    }
}

# Main execution
function Start-AITrainingServer {
    Write-Log "=== Starting Enhanced AI Training Server ==="
    Write-Log "Project directory: $PROJECT_DIR"
    Write-Log "OS: $env:OS"
    Write-Log "PowerShell version: $($PSVersionTable.PSVersion)"
    
    # Create directories
    @($LOGS_DIR, $MODELS_DIR, $DATA_DIR, $CONFIG_DIR) | ForEach-Object {
        if (-not (Test-Path $_)) {
            New-Item -ItemType Directory -Path $_ -Force | Out-Null
        }
    }
    
    # Initialize environment
    if (-not (Initialize-VirtualEnvironment)) {
        Write-Error-Log "Failed to initialize virtual environment"
        return
    }
    
    # Setup GPU environment
    Test-GPUAvailability | Out-Null
    
    # Start Ollama
    if (-not (Start-OllamaService)) {
        Write-Error-Log "Failed to start Ollama service"
        return
    }
    
    # Pull models
    Pull-Models
    
    # Start monitoring
    Start-MonitoringService
    
    # Start API server
    if (-not (Start-APIServer)) {
        Write-Error-Log "Failed to start API server"
        return
    }
    
    # Main server loop
    Write-Log "AI Training Server is now running 24/7"
    Write-Log "Monitor logs in: $LOGS_DIR"
    Write-Log "API endpoint: http://localhost:8000"
    Write-Log "API documentation: http://localhost:8000/docs"
    Write-Log "Ollama endpoint: http://localhost:11434"
    Write-Log "Press Ctrl+C to stop the server"
    
    try {
        while ($true) {
            Start-Sleep -Seconds 3600
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            Write-Log "Server heartbeat - $timestamp"
            
            if (-not (Test-SystemResources)) {
                Write-Log "Resource check completed with warnings"
            }
        }
    }
    catch {
        Write-Log "Server interrupted: $_"
    }
    finally {
        Write-Log "Shutting down AI training server..."
        Get-Job | Stop-Job
        Get-Job | Remove-Job
        Write-Log "Cleanup completed"
    }
}

# Script entry point
try {
    Start-AITrainingServer
}
catch {
    Write-Error-Log "Critical error: $_"
    exit 1
} 