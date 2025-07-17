# 🧬 Fusion Tools Suite

A comprehensive set of tools for managing and interacting with your local hybrid LLM fusion server. This suite provides monitoring, control, and chat interfaces for the intelligent model fusion system.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Components](#components)
- [Usage](#usage)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## 🌟 Overview

The Fusion Tools Suite consists of four main components:

1. **Fusion Status Monitor** - Real-time monitoring of fusion system status
2. **Fusion Controller** - Automated model evaluation, selection, and fusion
3. **Chat Interface** - Web-based chat with hybrid fusion models
4. **Configuration Management** - Centralized configuration with constraints and rules

## ✨ Features

### 🔍 Fusion Status Monitor
- **Real-time dashboard** with live system metrics
- **Beautiful terminal UI** with rich formatting
- **Auto-refresh** every 5 seconds
- **System health monitoring**
- **Model status tracking**
- **Fusion cycle history**

### 🤖 Fusion Controller
- **Intelligent model evaluation** with scoring algorithms
- **Automated model selection** based on performance and constraints
- **Continuous fusion cycles** (every 56 hours by default)
- **DeepSeek model integration** with priority handling
- **Constraint enforcement** (parameter limits, capability thresholds)
- **Backup and recovery** functionality

### 💬 Chat Interface
- **Modern web interface** with responsive design
- **Real-time chat** with WebSocket support
- **Model selection** (hybrid and standard models)
- **Conversation history** with persistent storage
- **Performance metrics** display
- **System status integration**

### ⚙️ Configuration Management
- **YAML-based configuration** with validation
- **Model constraints** and capability requirements
- **Disqualification rules** for model filtering
- **Fusion control parameters**
- **Chat interface settings**

## 📦 Installation

### Prerequisites
- Python 3.8+
- Running fusion server at `http://localhost:8000`
- Ollama service running at `http://localhost:11434`

### Install Dependencies
```bash
cd fusion_tools
pip install -r requirements.txt
```

### Quick Start
```bash
# 1. Start the fusion status monitor
python run_monitor.py

# 2. In another terminal, start the fusion controller
python run_controller.py --mode continuous

# 3. In another terminal, start the chat interface
python run_chat.py
```

## 🗂️ Components

### File Structure
```
fusion_tools/
├── config/
│   ├── fusion_config.yaml      # Main configuration file
│   └── __init__.py
├── monitor/
│   ├── status_monitor.py       # Terminal-based status monitor
│   ├── web_monitor.py          # Web-based monitor (future)
│   └── __init__.py
├── control/
│   ├── fusion_controller.py    # Main fusion controller
│   ├── model_evaluator.py      # Model evaluation logic
│   └── __init__.py
├── chat/
│   ├── backend/
│   │   ├── chat_server.py      # FastAPI chat server
│   │   └── __init__.py
│   ├── frontend/
│   │   ├── index.html          # Chat interface HTML
│   │   ├── script.js           # Frontend JavaScript
│   │   └── style.css           # Modern styling
│   └── __init__.py
├── utils/
│   ├── api_client.py           # Fusion server API client
│   ├── config_loader.py        # Configuration management
│   └── __init__.py
├── requirements.txt            # Python dependencies
├── run_monitor.py              # Monitor launcher
├── run_controller.py           # Controller launcher
├── run_chat.py                 # Chat interface launcher
└── README.md                   # This file
```

## 🚀 Usage

### Fusion Status Monitor

**Terminal Mode (Default):**
```bash
python run_monitor.py
```

**Options:**
```bash
python run_monitor.py --refresh 10 --log-level DEBUG
```

**Features:**
- Live system status with color-coded indicators
- Available models list with type classification
- Hybrid models with parameter counts
- Recent fusion activity
- Auto-refresh with customizable intervals

### Fusion Controller

**Run Single Cycle:**
```bash
python run_controller.py --mode cycle
```

**Continuous Mode:**
```bash
python run_controller.py --mode continuous --interval 56
```

**Model Evaluation Only:**
```bash
python run_controller.py --mode evaluate
```

**System Status:**
```bash
python run_controller.py --mode status
```

**Force Fusion:**
```bash
python run_controller.py --mode force
```

**Advanced Options:**
```bash
python run_controller.py --mode continuous \
  --interval 24 \
  --models 4 \
  --health-check \
  --backup \
  --log-level INFO
```

### Chat Interface

**Start Chat Server:**
```bash
python run_chat.py
```

**Custom Configuration:**
```bash
python run_chat.py --host 0.0.0.0 --port 8001 --fusion-host localhost --fusion-port 8000
```

**Features:**
- Navigate to `http://localhost:8001`
- Select between hybrid and standard models
- Real-time chat with performance metrics
- Conversation history and management
- System status integration
- WebSocket support for real-time updates

## ⚙️ Configuration

### Main Configuration File: `config/fusion_config.yaml`

```yaml
# Fusion Server Settings
fusion_server:
  host: "localhost"
  port: 8000
  timeout: 30

# Model Constraints
model_constraints:
  max_parameter_size: "13B"
  min_capability_threshold: 7.5
  max_hallucination_rate: 0.20

# Capability Requirements
capability_requirements:
  deep_reasoning: 7.5
  code_generation: 7.0
  math: 6.5
  following_instructions: 8.0
  general: 6.0

# Fusion Control
fusion_control:
  cycle_interval_hours: 56
  models_per_fusion: 3
  max_concurrent_fusions: 2

# Chat Interface
chat:
  default_model: "hybrid-fusion-v1"
  max_message_length: 4096
  response_timeout: 60
  enable_history: true
  max_history_size: 100

# Disqualification Rules
disqualification_rules:
  - condition: "hallucination_rate > 0.25"
    action: "remove"
  - condition: "response_time > 30"
    action: "deprioritize"
  - condition: "capability_score < 6.0"
    action: "remove"

# Priority Models
priority_models:
  - "deepseek-coder:latest"
  - "deepseek-math:latest"
  - "deepseek-v2:latest"
  - "mistral:latest"
  - "codellama:latest"
```

### Configuration Sections

#### Model Constraints
- **max_parameter_size**: Maximum model size (1B, 2B, 7B, 13B, 33B, 70B)
- **min_capability_threshold**: Minimum overall capability score (0-10)
- **max_hallucination_rate**: Maximum allowable hallucination rate (0-1)

#### Capability Requirements
Define minimum scores for specific capabilities:
- **deep_reasoning**: Logical reasoning and problem-solving
- **code_generation**: Programming and code creation
- **math**: Mathematical problem-solving
- **following_instructions**: Instruction adherence
- **general**: General knowledge and conversation

#### Fusion Control
- **cycle_interval_hours**: Time between automatic fusion cycles
- **models_per_fusion**: Number of models to combine per fusion
- **max_concurrent_fusions**: Maximum simultaneous fusion processes

#### Disqualification Rules
Automatic model filtering based on performance metrics:
- **condition**: Performance condition to evaluate
- **action**: Action to take (remove, deprioritize, keep)

## 📡 API Reference

### Fusion Status Monitor API
The monitor connects to the fusion server's REST API:

- `GET /fusion/status` - Get fusion system status
- `GET /models` - Get available models
- `GET /fusion/hybrids` - Get hybrid models
- `GET /health` - Get server health

### Fusion Controller API
The controller orchestrates fusion operations:

- `POST /fusion/pull-deepseek` - Pull DeepSeek models
- `POST /fusion/create-hybrid` - Create hybrid model
- `POST /fusion/start-absorption` - Start continuous absorption

### Chat Interface API
The chat server provides:

- `POST /chat` - Send chat message
- `GET /models` - Get available models
- `GET /conversations` - Get conversation list
- `GET /conversations/{id}` - Get specific conversation
- `WebSocket /ws` - Real-time chat connection

## 🔧 Development

### Adding New Features

1. **New Monitor Components:**
   - Add to `monitor/` directory
   - Implement using rich library for terminal UI
   - Follow existing patterns for API integration

2. **New Controller Features:**
   - Extend `FusionController` class
   - Add new evaluation criteria in `ModelEvaluator`
   - Update configuration schema

3. **Chat Interface Enhancements:**
   - Backend: Extend `ChatServer` class
   - Frontend: Modify HTML/CSS/JavaScript files
   - Add new API endpoints as needed

### Testing

```bash
# Test individual components
python -m monitor.status_monitor
python -m control.fusion_controller --mode evaluate
python -m chat.backend.chat_server

# Test configuration loading
python -c "from utils.config_loader import ConfigLoader; print(ConfigLoader().get_fusion_config())"
```

### Logging

All components use Python's logging module:
- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages
- **WARNING**: Warning conditions
- **ERROR**: Error conditions

## 🐛 Troubleshooting

### Common Issues

#### Monitor Not Connecting
```bash
# Check if fusion server is running
curl http://localhost:8000/health

# Check configuration
python -c "from utils.config_loader import ConfigLoader; print(ConfigLoader().get_server_config())"
```

#### Controller Failing
```bash
# Run health check
python run_controller.py --mode status --health-check

# Check model availability
python -c "from utils.api_client import FusionAPIClient; print(FusionAPIClient().get_available_models())"
```

#### Chat Interface Issues
```bash
# Check chat server logs
python run_chat.py --log-level DEBUG

# Test fusion server connection
python -c "from utils.api_client import FusionAPIClient; print(FusionAPIClient().get_server_health())"
```

### Performance Tips

1. **Monitor Performance:**
   - Reduce refresh interval if CPU usage is high
   - Use web mode for remote monitoring

2. **Controller Optimization:**
   - Adjust fusion interval based on model availability
   - Use evaluation mode to test model selection

3. **Chat Interface:**
   - Enable WebSocket for better real-time performance
   - Adjust message length limits for better response times

### Error Codes

- **Connection refused**: Fusion server not running
- **Timeout errors**: Increase timeout in configuration
- **Model not found**: Check model availability
- **Permission errors**: Check file permissions in project directory

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review log files for detailed error messages
3. Verify configuration settings
4. Ensure all dependencies are installed

---

**Built with ❤️ for the Fusion AI Community** 