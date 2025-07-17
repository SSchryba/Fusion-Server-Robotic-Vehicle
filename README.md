# 24/7 AI Training Server

A comprehensive, automated AI model training system that continuously fine-tunes multiple LLMs on various datasets with intelligent resource management and monitoring.

## 🚀 Features

- **24/7 Continuous Training**: Automated training pipeline that runs continuously
- **Multi-Model Support**: Supports 20+ popular LLM models (Llama2, Mistral, CodeLlama, Gemma, etc.)
- **Dataset Variety**: Pre-configured with 10+ high-quality training datasets
- **Resource Management**: Intelligent monitoring and resource allocation
- **LoRA Fine-tuning**: Memory-efficient training with Parameter Efficient Fine-Tuning (PEFT)
- **REST API**: Full API control for monitoring and management
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Auto-Recovery**: Automatic service restart and error recovery
- **GPU Optimization**: CUDA support with 4-bit quantization for large models

## 📋 Requirements

### System Requirements
- **CPU**: Multi-core processor (8+ cores recommended)
- **RAM**: 16GB minimum, 32GB+ recommended
- **Storage**: 100GB+ free space (SSDs recommended)
- **GPU**: NVIDIA GPU with 8GB+ VRAM (optional but recommended)
- **Network**: Stable internet connection for downloading models/datasets

### Software Requirements
- **Python 3.8+** (3.10+ recommended)
- **Git**
- **Ollama** ([Download here](https://ollama.ai/))
- **CUDA 11.8+** (for GPU support)

## 🛠️ Installation

### Windows Setup

1. **Clone the repository:**
   ```cmd
   git clone <repository-url>
   cd server
   ```

2. **Install Ollama:**
   - Download from [ollama.ai](https://ollama.ai/)
   - Run the installer
   - Verify installation: `ollama --version`

3. **Run the setup script:**
   ```cmd
   start_all.bat
   ```

### Linux/macOS Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd server
   ```

2. **Install Ollama:**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

3. **Make script executable and run:**
   ```bash
   chmod +x start_all.sh.sh
   ./start_all.sh.sh
   ```

## 🎯 Quick Start

1. **Start the server:**
   - Windows: Double-click `start_all.bat`
   - Linux/macOS: `./start_all.sh.sh`

2. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Server Status: http://localhost:8000/status

3. **Monitor training:**
   - View logs in the `logs/` directory
   - Check training jobs: `GET /jobs`
   - Monitor metrics: `GET /metrics`

## 🎮 API Usage

### Start a Training Job
```bash
curl -X POST "http://localhost:8000/train" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "llama2:latest",
    "dataset": "alpaca",
    "max_steps": 1000,
    "learning_rate": 2e-4
  }'
```

### Check Server Status
```bash
curl http://localhost:8000/status
```

### View Training Jobs
```bash
curl http://localhost:8000/jobs
```

### Monitor System Metrics
```bash
curl http://localhost:8000/metrics
```

### Pull New Models
```bash
curl -X POST "http://localhost:8000/ollama/pull?model_name=mistral:latest"
```

## 📊 Supported Models

### Small Models (2-7B parameters)
- `llama2:latest` - General purpose
- `mistral:latest` - High performance
- `gemma:2b` - Lightweight
- `phi:latest` - Microsoft's efficient model
- `codellama:latest` - Code generation

### Large Models (13B+ parameters)
- `llama2:13b` - Enhanced capabilities
- `llama2:70b` - Maximum performance
- `mixtral:8x7b` - Mixture of experts
- `codellama:13b` - Advanced coding

### Specialized Models
- `neural-chat:latest` - Conversational AI
- `starling-lm:latest` - RLHF optimized
- `solar:latest` - High efficiency
- `dolphin-mixtral:latest` - Uncensored
- `wizard-vicuna-uncensored:latest` - Creative tasks

## 📚 Datasets

### General Training
- **Alpaca**: Instruction following dataset
- **Dolly**: High-quality human demonstrations
- **OASST1**: Open Assistant conversations

### Specialized Domains
- **Code Alpaca**: Programming and code generation
- **Math QA**: Mathematical reasoning
- **GSM8K**: Grade school math problems
- **CommonsenseQA**: Common sense reasoning
- **SQuAD**: Reading comprehension
- **Natural Questions**: Real user questions

## ⚙️ Configuration

Edit `config/training_config.json` to customize:

```json
{
  "system": {
    "max_memory_usage_percent": 80,
    "max_concurrent_jobs": 2
  },
  "training": {
    "default_max_steps": 1000,
    "default_learning_rate": 2e-4,
    "use_4bit_quantization": true
  }
}
```

### Key Settings
- **max_memory_usage_percent**: Stop training when memory exceeds this
- **max_concurrent_jobs**: Maximum simultaneous training jobs
- **default_max_steps**: Training duration per job
- **use_4bit_quantization**: Enable for large models on limited VRAM

## 📈 Monitoring & Logs

### Log Files
- `logs/training_server.log` - Main server log
- `logs/training_*.log` - Individual training job logs
- `logs/ollama.log` - Ollama daemon log
- `logs/api_server.log` - FastAPI server log

### Metrics Dashboard
Access real-time metrics at:
- **System Health**: http://localhost:8000/health
- **Resource Usage**: http://localhost:8000/metrics
- **Active Jobs**: http://localhost:8000/jobs

### Resource Monitoring
The system automatically monitors:
- CPU usage
- Memory consumption
- Disk space
- GPU utilization (if available)
- Training progress
- Model performance

## 🔧 Troubleshooting

### Common Issues

**1. Ollama not starting**
```bash
# Check if Ollama is installed
ollama --version

# Manually start Ollama
ollama serve

# Check port availability
netstat -an | grep 11434
```

**2. Out of memory errors**
- Reduce `max_concurrent_jobs` in config
- Enable 4-bit quantization
- Use smaller models (2B-7B parameters)
- Increase virtual memory/swap

**3. GPU not detected**
```bash
# Check CUDA installation
nvidia-smi

# Verify PyTorch CUDA support
python -c "import torch; print(torch.cuda.is_available())"
```

**4. Training jobs failing**
- Check individual job logs in `logs/training_*.log`
- Verify model exists: `ollama list`
- Ensure sufficient disk space
- Check internet connection for dataset downloads

**5. API server not responding**
```bash
# Check if port 8000 is in use
netstat -an | grep 8000

# View API server logs
tail -f logs/api_server.log
```

### Performance Optimization

**For Maximum Throughput:**
- Use multiple smaller models simultaneously
- Enable 4-bit quantization
- Use NVMe SSDs for model storage
- Ensure adequate cooling for 24/7 operation

**For Limited Resources:**
- Set `max_concurrent_jobs: 1`
- Use only small models (2B-7B)
- Reduce `max_dataset_samples`
- Enable aggressive cleanup

## 🚦 System Health

### Health Check Endpoints
- `GET /health` - Overall system health
- `GET /status` - Detailed server status
- `GET /metrics` - Real-time metrics

### Health Indicators
- **Healthy**: All systems operational
- **Warning**: High resource usage (>80% CPU/Memory)
- **Critical**: Very high usage (>95%) or service failures

### Automatic Recovery
The system includes automatic recovery for:
- Ollama daemon crashes
- API server failures
- Training job hangs
- Resource exhaustion

## 📝 Advanced Usage

### Custom Training Scripts
Add your own training logic by modifying `server/train_model.py`:

```python
class CustomTrainer(ModelTrainer):
    def custom_training_loop(self):
        # Your custom training logic here
        pass
```

### Adding New Datasets
Extend the `DatasetManager` class in `server/train_model.py`:

```python
DATASET_CONFIGS = {
    'your_dataset': {
        'name': 'your-dataset-name',
        'text_column': 'text',
        'format_func': 'format_your_dataset'
    }
}
```

### Scheduling Training Jobs
Use the API to schedule training with cron jobs:

```bash
# Linux/macOS cron example (train every 6 hours)
0 */6 * * * curl -X POST http://localhost:8000/train -H "Content-Type: application/json" -d '{"model_name":"mistral:latest","dataset":"alpaca"}'
```

## 🛡️ Security Considerations

- The API runs on all interfaces (0.0.0.0) - use firewall rules in production
- Model files can be large - ensure adequate storage security
- Training logs may contain sensitive data - implement log rotation
- Consider using API authentication for production deployments

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review logs in the `logs/` directory
3. Open an issue on GitHub
4. Join our community discussions

## 🎉 Acknowledgments

- [Ollama](https://ollama.ai/) for the local model runtime
- [Hugging Face](https://huggingface.co/) for transformers and datasets
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [PyTorch](https://pytorch.org/) for the ML framework
- The open-source AI community for datasets and models 