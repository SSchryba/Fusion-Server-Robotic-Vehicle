# AutoFix System - Piraz OS Code Correction

A comprehensive self-correcting code generation and validation system that integrates with hybrid LLM fusion servers to provide intelligent code correction with Piraz OS knowledge base integration.

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the AutoFix Server**
   ```bash
   python run_autofix.py
   ```

3. **Access the Web Interface**
   Open your browser to `http://localhost:8003`

## 📋 System Components

### 1. **Piraz OS Knowledge Base** (`piraz_os_kb.json`)
- **Boot Sequence**: Hardware initialization, bootloader, kernel, services
- **Core Services**: piraz-core, piraz-network, piraz-storage, piraz-security
- **Error Codes**: PIRAZ_ERR_001 to PIRAZ_ERR_005 with fixes
- **Command Syntax**: piraz-service, piraz-config, piraz-log, piraz-net, piraz-storage
- **Validation Rules**: Service management, configuration, error handling patterns
- **Learning Feedback**: Correction history, pattern improvements, metrics

### 2. **Fusion Absorption** (`fusion_absorb_with_kb.py`)
- **Knowledge Integration**: Injects Piraz OS KB into fusion pipeline
- **Model Selection**: Prioritizes DeepSeek-coder, CodeLlama, Mistral for code tasks
- **Weighted Fusion**: Adjusts model weights for code correction (35% code, 30% system, 25% error handling)
- **Capability Boost**: Enhances deep reasoning (1.2x), code generation (1.3x), error detection (1.4x)

### 3. **AutoFix Server** (`autofix_server.py`)
- **FastAPI Backend**: REST API with `/autofix`, `/autofix/history`, `/autofix/feedback`
- **Code Analysis**: Piraz OS pattern detection, anti-pattern identification
- **Hybrid Model Integration**: Uses fusion server for intelligent corrections
- **Real-time Processing**: Async code fixing with background logging

### 4. **Knowledge Base Updater** (`update_kb.py`)
- **Correction Logging**: Tracks all fixes with metadata
- **Pattern Analysis**: Identifies frequent error patterns
- **Performance Metrics**: Success rates, confidence tracking
- **Learning Suggestions**: Recommends KB improvements
- **Data Cleanup**: Removes old correction data

### 5. **Web Frontend** (`autofix_frontend/index.html`)
- **Modern UI**: Responsive design with gradient backgrounds
- **Code Editor**: Syntax highlighting, multiple language support
- **Real-time Status**: Fusion connection, KB version, correction count
- **Result Display**: Confidence meters, fix explanations, applied changes
- **User Feedback**: Star ratings, text feedback, correction history

## 🔧 API Endpoints

### AutoFix Server (Port 8003)

#### `POST /autofix`
Fix code with Piraz OS knowledge integration
```json
{
  "code": "print('Hello')",
  "language": "python",
  "fix_type": "comprehensive",
  "context": "Service initialization script",
  "max_iterations": 3
}
```

**Response:**
```json
{
  "original_code": "print('Hello')",
  "fixed_code": "logger.info('Hello')",
  "explanation": "Replaced print with logging for better practice",
  "fixes_applied": ["replace_print_with_logging"],
  "confidence": 0.95,
  "error_type": "logging_improvement",
  "piraz_compatibility": true,
  "fix_time": 1.23,
  "iterations_used": 1
}
```

#### `GET /autofix/status`
Get system status and metrics
```json
{
  "autofix_server": "running",
  "fusion_connected": true,
  "kb_version": "1.0.0",
  "corrections_performed": 42,
  "available_models": 5,
  "piraz_error_codes": 5,
  "validation_rules": 3
}
```

#### `GET /autofix/history?limit=50`
Get correction history
```json
{
  "corrections": [...],
  "total": 123
}
```

#### `POST /autofix/feedback`
Submit user feedback
```json
{
  "correction_id": "fix_20240115_143022_1",
  "feedback": "Great fix, improved error handling",
  "rating": 5
}
```

#### `POST /autofix/update-kb`
Update knowledge base from recent corrections

#### `POST /autofix/trigger-absorption`
Trigger knowledge base enhanced absorption

## 📊 Usage Examples

### Command Line Tools

#### Knowledge Base Absorption
```bash
# Trigger KB-enhanced absorption
python fusion_absorb_with_kb.py

# Show KB summary
python fusion_absorb_with_kb.py --summary

# Force absorption
python fusion_absorb_with_kb.py --force
```

#### Knowledge Base Updates
```bash
# Show learning statistics
python update_kb.py --stats

# Get improvement suggestions
python update_kb.py --suggestions

# Clean up old data (30+ days)
python update_kb.py --cleanup 30

# Add test correction
python update_kb.py --test-correction
```

#### AutoFix Server
```bash
# Start server
python run_autofix.py

# Custom host/port
python run_autofix.py --host 127.0.0.1 --port 8004

# Development mode with auto-reload
python run_autofix.py --dev
```

### Python API Usage

```python
from autofix_server import AutoFixServer
from fusion_absorb_with_kb import KnowledgeBaseFusion
from update_kb import KnowledgeBaseUpdater

# Initialize components
kb_fusion = KnowledgeBaseFusion()
kb_updater = KnowledgeBaseUpdater()
autofix_server = AutoFixServer()

# Trigger KB absorption
result = kb_fusion.trigger_kb_absorption()
print(f"Absorption result: {result}")

# Get learning statistics
stats = kb_updater.get_learning_stats()
print(f"Total corrections: {stats['total_corrections']}")

# Manual code fix
request = {
    "code": "os.system('rm -rf /')",
    "language": "python",
    "fix_type": "security"
}
# This would be handled by the FastAPI endpoint
```

## 🧠 Learning System

### Correction Types
- **syntax_error**: Basic syntax issues
- **logic_error**: Logical flow problems
- **performance_issue**: Optimization opportunities
- **security_vulnerability**: Security concerns
- **compatibility_issue**: Piraz OS compatibility

### Confidence Levels
- **High (0.8-1.0)**: Strong confidence in fix
- **Medium (0.5-0.8)**: Moderate confidence
- **Low (0.0-0.5)**: Uncertain fix, requires review

### Improvement Areas
- **error_handling**: Better exception management
- **resource_management**: Memory and file handling
- **configuration_validation**: Config file validation
- **service_lifecycle**: Service management patterns
- **security_practices**: Security best practices

## 🔄 Feedback Loop

### Automatic Learning
1. **Correction Logging**: Every fix is logged with metadata
2. **Pattern Analysis**: Identifies recurring error patterns
3. **Performance Tracking**: Monitors success rates and confidence
4. **Knowledge Base Updates**: Automatically improves KB from corrections

### Manual Feedback
1. **User Ratings**: 1-5 star ratings for fixes
2. **Text Feedback**: Detailed user comments
3. **Correction Validation**: User confirms fix effectiveness
4. **Improvement Suggestions**: System suggests KB enhancements

### Continuous Improvement
- **56-Hour Cycles**: Automatic KB-enhanced absorption
- **Pattern Recognition**: Learns from correction history
- **Model Optimization**: Adjusts fusion weights based on performance
- **Knowledge Expansion**: Adds new error codes and patterns

## 🛠️ Configuration

### Knowledge Base Configuration
Edit `piraz_os_kb.json` to customize:
- Error codes and descriptions
- Service management patterns
- Command syntax examples
- Validation rules
- Boot sequence information

### Fusion Configuration
Edit `config/fusion_config.yaml` for:
- Model selection preferences
- Fusion weights and parameters
- Capability boost settings
- Learning focus areas

### Server Configuration
Environment variables:
- `AUTOFIX_HOST`: Server host (default: 0.0.0.0)
- `AUTOFIX_PORT`: Server port (default: 8003)
- `AUTOFIX_KB_FILE`: Knowledge base file path
- `AUTOFIX_LOG_LEVEL`: Logging level (INFO, DEBUG, etc.)

## 🚨 Error Handling

### Common Issues

#### "Fusion server not accessible"
- Check if fusion server is running on localhost:8000
- Verify network connectivity
- Review fusion server logs

#### "Knowledge base file not found"
- Ensure `piraz_os_kb.json` exists in the correct location
- Check file permissions
- Verify JSON syntax

#### "Not enough models for fusion"
- Pull more models using the fusion server
- Check available models list
- Verify model compatibility

#### "Code fix generation failed"
- Check hybrid model availability
- Review fusion server status
- Verify knowledge base integrity

### Debugging Tips

1. **Enable Debug Logging**
   ```bash
   python run_autofix.py --log-level DEBUG
   ```

2. **Check System Status**
   ```bash
   curl http://localhost:8003/autofix/status
   ```

3. **Monitor Fusion Server**
   ```bash
   curl http://localhost:8000/fusion/status
   ```

4. **Validate Knowledge Base**
   ```bash
   python -m json.tool piraz_os_kb.json
   ```

## 🔐 Security Considerations

### Code Execution
- **No Code Execution**: System only analyzes and suggests fixes
- **Sandboxed Analysis**: Code analysis runs in isolated environment
- **Input Validation**: All inputs are validated and sanitized

### Data Privacy
- **Local Processing**: All code analysis happens locally
- **No External Calls**: No code sent to external services
- **Secure Storage**: Correction history stored locally

### Access Control
- **Local Network Only**: Default configuration for local network
- **Authentication**: Can be extended with authentication middleware
- **Rate Limiting**: Built-in request rate limiting

## 📈 Performance Monitoring

### Metrics Tracked
- **Correction Success Rate**: Percentage of successful fixes
- **Average Confidence**: Mean confidence score
- **Processing Time**: Time taken for code fixes
- **Error Pattern Frequency**: Most common error types
- **User Satisfaction**: Feedback ratings and comments

### Performance Optimization
- **Async Processing**: Non-blocking code analysis
- **Caching**: Results cached for similar code patterns
- **Model Optimization**: Efficient model selection
- **Memory Management**: Automatic cleanup of old data

## 🤝 Contributing

### Adding New Error Codes
1. Edit `piraz_os_kb.json`
2. Add error code with description, causes, and fixes
3. Include code patterns for detection
4. Update validation rules if needed

### Extending Language Support
1. Add language to frontend dropdown
2. Update code analysis patterns
3. Add language-specific validation rules
4. Test with sample code

### Improving Pattern Recognition
1. Analyze correction history for patterns
2. Add new validation rules
3. Update anti-pattern detection
4. Enhance fix suggestions

## 📚 Additional Resources

- [Fusion Tools Documentation](README.md)
- [Piraz OS Command Reference](piraz_os_kb.json)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Model Fusion Guide](fusion_absorb_with_kb.py)

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review system logs with `--log-level DEBUG`
3. Verify all dependencies are installed
4. Check fusion server connectivity

---

**AutoFix System v1.0.0** - Intelligent Code Correction with Piraz OS Integration 