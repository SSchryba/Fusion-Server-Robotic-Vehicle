#!/usr/bin/env bash
# Enhanced AI Training Server - 24/7 Multi-Model Training
set -euo pipefail

# Configuration
PROJECT_DIR="${HOME}/faith-server"
VENV_DIR="${PROJECT_DIR}/venv"
SERVER_DIR="${PROJECT_DIR}/server"
LOGS_DIR="${PROJECT_DIR}/logs"
MODELS_DIR="${PROJECT_DIR}/models"
DATA_DIR="${PROJECT_DIR}/training_data"
CONFIG_DIR="${PROJECT_DIR}/config"

# Resource limits and monitoring
MAX_MEMORY_USAGE=80  # Percentage
MAX_GPU_USAGE=95     # Percentage
MIN_DISK_SPACE=10    # GB

# Create necessary directories
mkdir -p "$LOGS_DIR" "$MODELS_DIR" "$DATA_DIR" "$CONFIG_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGS_DIR/training_server.log"
}

# Resource monitoring function
check_resources() {
    local mem_usage=$(free | grep '^Mem:' | awk '{printf "%.0f", $3/$2 * 100.0}')
    local disk_free=$(df -BG "$PROJECT_DIR" | tail -1 | awk '{print $4}' | sed 's/G//')
    
    if [ "$mem_usage" -gt "$MAX_MEMORY_USAGE" ]; then
        log "WARNING: Memory usage at ${mem_usage}% - pausing new training jobs"
        return 1
    fi
    
    if [ "$disk_free" -lt "$MIN_DISK_SPACE" ]; then
        log "WARNING: Low disk space (${disk_free}GB) - cleaning up old models"
        cleanup_old_models
        return 1
    fi
    
    return 0
}

# Cleanup function for old models
cleanup_old_models() {
    log "Cleaning up old model checkpoints..."
    find "$MODELS_DIR" -name "*.pt" -mtime +7 -delete
    find "$LOGS_DIR" -name "*.log" -mtime +30 -delete
}

# GPU detection and setup
setup_gpu() {
    if command -v nvidia-smi >/dev/null 2>&1; then
        log "NVIDIA GPU detected - enabling CUDA acceleration"
        export CUDA_VISIBLE_DEVICES="0,1,2,3"  # Use all available GPUs
        export OMP_NUM_THREADS=1
        export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
    else
        log "No NVIDIA GPU detected - using CPU training"
        export CUDA_VISIBLE_DEVICES=""
    fi
}

# Enhanced model list for diverse training
declare -a MODELS=(
    "llama2:latest"
    "llama2:13b"
    "llama2:70b"
    "codellama:latest"
    "codellama:13b"
    "mistral:latest"
    "mistral:7b"
    "mixtral:8x7b"
    "neural-chat:latest"
    "starling-lm:latest"
    "solar:latest"
    "gemma:2b"
    "gemma:7b"
    "phi:latest"
    "dolphin-mixtral:latest"
    "openchat:latest"
    "wizard-vicuna-uncensored:latest"
    "orca-mini:latest"
    "vicuna:latest"
    "alpaca:latest"
)

# Training datasets for different tasks
declare -a TRAINING_DATASETS=(
    "alpaca"
    "dolly"
    "oasst1"
    "code_alpaca"
    "math_qa"
    "gsm8k"
    "commonsense_qa"
    "squad"
    "natural_questions"
    "trivia_qa"
)

# Start services function
start_services() {
    log "=== Starting Enhanced AI Training Server ==="
    
    # Activate virtual environment
    log "Activating virtual environment..."
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    else
        log "Virtual environment not found - creating one..."
        python3 -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
        pip install --upgrade pip
        pip install torch torchvision torchaudio transformers datasets accelerate peft bitsandbytes
        pip install fastapi uvicorn ollama-python requests psutil
    fi
    
    # Setup GPU environment
    setup_gpu
    
    # Start Ollama daemon
    if ! pgrep -x "ollama" >/dev/null; then
        log "Starting Ollama daemon..."
        ollama serve --port 11434 &> "$LOGS_DIR/ollama.log" &
        OLLAMA_PID=$!
        sleep 5
        
        # Verify Ollama is running
        if ! curl -s http://localhost:11434/api/version >/dev/null; then
            log "ERROR: Failed to start Ollama daemon"
            exit 1
        fi
        log "Ollama daemon started successfully (PID: $OLLAMA_PID)"
    else
        log "Ollama daemon already running"
    fi
    
    # Pull and manage models
    log "Pulling models for training..."
    for model in "${MODELS[@]}"; do
        if check_resources; then
            log "Pulling model: $model"
            ollama pull "$model" || log "Failed to pull $model"
            sleep 2
        else
            log "Skipping model pull due to resource constraints"
            break
        fi
    done
    
    # Start training orchestrator
    start_training_orchestrator &
    
    # Start monitoring service
    start_monitoring_service &
    
    # Start FastAPI server
    log "Starting FastAPI training server..."
    cd "$SERVER_DIR"
    uvicorn main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 4 \
        --access-log \
        --log-file "$LOGS_DIR/api_server.log" &
    
    API_PID=$!
    log "FastAPI server started (PID: $API_PID)"
}

# Training orchestrator - manages continuous training
start_training_orchestrator() {
    log "Starting training orchestrator..."
    
    while true; do
        if check_resources; then
            # Select random model and dataset for training
            model=${MODELS[$RANDOM % ${#MODELS[@]}]}
            dataset=${TRAINING_DATASETS[$RANDOM % ${#TRAINING_DATASETS[@]}]}
            
            log "Starting training session: Model=$model, Dataset=$dataset"
            
            # Run training (this would call your actual training script)
            python3 "$SERVER_DIR/train_model.py" \
                --model "$model" \
                --dataset "$dataset" \
                --output_dir "$MODELS_DIR/$(date +%Y%m%d_%H%M%S)_${model//[:\/]/_}_$dataset" \
                --max_steps 1000 \
                --save_steps 250 \
                --logging_steps 50 \
                --eval_steps 500 \
                &> "$LOGS_DIR/training_$(date +%Y%m%d_%H%M%S).log" &
            
            TRAINING_PID=$!
            log "Training started (PID: $TRAINING_PID)"
            
            # Wait for training to complete or resource issues
            wait $TRAINING_PID
            log "Training session completed"
        else
            log "Resource constraints detected - waiting 300 seconds before retry"
            sleep 300
        fi
        
        # Brief pause between training sessions
        sleep 60
    done
}

# Monitoring service
start_monitoring_service() {
    log "Starting monitoring service..."
    
    while true; do
        # System metrics
        memory_usage=$(free | grep '^Mem:' | awk '{printf "%.1f", $3/$2 * 100.0}')
        cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
        disk_usage=$(df -h "$PROJECT_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
        
        # GPU metrics (if available)
        if command -v nvidia-smi >/dev/null 2>&1; then
            gpu_usage=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -1)
            gpu_memory=$(nvidia-smi --query-gpu=utilization.memory --format=csv,noheader,nounits | head -1)
            log "METRICS: CPU=${cpu_usage}% MEM=${memory_usage}% DISK=${disk_usage}% GPU=${gpu_usage}% GPU_MEM=${gpu_memory}%"
        else
            log "METRICS: CPU=${cpu_usage}% MEM=${memory_usage}% DISK=${disk_usage}%"
        fi
        
        # Check for dead processes and restart if needed
        if ! pgrep -x "ollama" >/dev/null; then
            log "Ollama daemon died - restarting..."
            ollama serve --port 11434 &> "$LOGS_DIR/ollama.log" &
        fi
        
        sleep 60
    done
}

# Cleanup function
cleanup() {
    log "Shutting down AI training server..."
    pkill -f "uvicorn main:app" || true
    pkill -f "ollama serve" || true
    pkill -f "train_model.py" || true
    log "Cleanup completed"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Main execution
main() {
    log "Initializing 24/7 AI Training Server"
    log "Project directory: $PROJECT_DIR"
    log "Available models: ${#MODELS[@]}"
    log "Available datasets: ${#TRAINING_DATASETS[@]}"
    
    start_services
    
    # Keep the main process alive
    log "AI Training Server is now running 24/7"
    log "Monitor logs in: $LOGS_DIR"
    log "API endpoint: http://localhost:8000"
    log "Ollama endpoint: http://localhost:11434"
    
    # Wait indefinitely
    while true; do
        sleep 3600  # Check hourly
        log "Server heartbeat - $(date)"
        check_resources || log "Resource check completed"
    done
}

# Run main function
main "$@"
