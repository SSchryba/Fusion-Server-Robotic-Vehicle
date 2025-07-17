# Root-Level Autonomous AI Agent

⚠️ **CRITICAL SECURITY WARNING** ⚠️

This is a root-level autonomous AI agent with **FULL SYSTEM ACCESS**. It can:
- Execute arbitrary commands with root privileges
- Read, write, and delete any file on the system
- Monitor and control system processes
- Modify system configurations
- Access encrypted volumes and removable drives

**Only use this on systems you own and fully understand the risks!**

## 🚀 Features

### Core Capabilities
- **Root-Level Execution**: Runs with full administrator/root privileges
- **Full Filesystem Access**: Read, write, delete files from any location
- **Arbitrary Shell Commands**: Execute any system command
- **System Monitoring**: Real-time system resource monitoring
- **Background Service**: Runs as a persistent systemd service
- **Comprehensive Logging**: All operations logged to `/var/log/aiagent.log`

### Security Features
- **Rate Limiting**: Prevents excessive operations
- **Protected File Blocking**: Blocks access to critical system files
- **Dangerous Command Filtering**: Prevents destructive commands
- **Operation Auditing**: Full audit trail of all activities
- **Permission Validation**: Ensures proper root access before starting

### System Integration
- **Systemd Service**: Integrates with Linux service management
- **Cross-Platform**: Works on Linux and Windows
- **Resource Monitoring**: Tracks system resources and performance
- **Removable Drive Detection**: Identifies USB drives and encrypted volumes

## 📋 Requirements

- Python 3.7+
- Root/Administrator privileges
- Linux (preferred) or Windows
- Required Python packages:
  - `psutil>=5.9.0`
  - `pathlib2>=2.3.7`
  - `typing-extensions>=4.0.0`

## 🔧 Installation

### Linux (Recommended)

1. **Clone/Download the agent**:
   ```bash
   git clone <repository-url>
   cd root_agent
   ```

2. **Run the installation script**:
   ```bash
   sudo ./scripts/install.sh
   ```

3. **Start the service**:
   ```bash
   sudo systemctl start aiagent
   sudo systemctl enable aiagent
   ```

### Manual Installation

1. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Copy to system location**:
   ```bash
   sudo cp -r . /opt/root_agent
   sudo chown -R root:root /opt/root_agent
   ```

3. **Install systemd service**:
   ```bash
   sudo cp aiagent.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable aiagent
   ```

## 🎯 Usage

### As a System Service

```bash
# Start the agent service
sudo systemctl start aiagent

# Check service status
sudo systemctl status aiagent

# View real-time logs
sudo journalctl -u aiagent -f

# Stop the service
sudo systemctl stop aiagent
```

### Direct Python Usage

```python
#!/usr/bin/env python3
from agent import RootSystemAgent

# Initialize the agent
agent = RootSystemAgent()

# Execute shell commands
result = agent.run_cmd("ls -la /")
print(result)

# Read system files
content = agent.read_file("/etc/hostname")
print(content)

# Write files
agent.write_file("/tmp/test.txt", "Hello from root agent!")

# Get system information
sys_info = agent.get_system_info()
print(f"System: {sys_info['system']['platform']}")
print(f"Memory: {sys_info['memory']['percent_used']}%")

# List filesystem
fs_info = agent.list_filesystem("/home", max_depth=2)
print(f"Found {len(fs_info['files'])} files")

# Detect removable drives
drives = agent.detect_removable_drives()
for drive in drives:
    if drive['removable']:
        print(f"Removable drive: {drive['device']}")
```

### Running the Demo

```bash
# Run comprehensive demo (requires root)
sudo python3 /opt/root_agent/demo.py

# Or from source directory
sudo python3 demo.py
```

## 🔒 Security Considerations

### Built-in Safeguards

1. **Rate Limiting**: Maximum 100 operations per minute
2. **Protected Files**: Blocks access to:
   - `/etc/passwd`, `/etc/shadow`, `/etc/sudoers`
   - `C:\Windows\System32\config\SAM`
3. **Dangerous Commands**: Blocks:
   - `rm -rf /`
   - `format`
   - `del /f /s /q C:\`
   - `mkfs`
4. **Audit Logging**: All operations logged with timestamps

### Security Best Practices

- **Monitor Logs**: Regularly check `/var/log/aiagent.log`
- **Network Isolation**: Run on isolated/test systems only
- **Regular Updates**: Keep the agent and dependencies updated
- **Backup Systems**: Always have system backups before use
- **Access Control**: Limit who can access the agent

## 📊 API Reference

### Core Methods

#### `run_cmd(cmd: str) -> str`
Execute arbitrary shell commands with root privileges.

```python
result = agent.run_cmd("systemctl status sshd")
```

#### `read_file(path: str) -> str`
Read file contents with full filesystem access.

```python
content = agent.read_file("/etc/fstab")
```

#### `write_file(path: str, content: str) -> bool`
Write content to any file on the system.

```python
success = agent.write_file("/etc/motd", "Welcome to the system!")
```

#### `delete_file(path: str) -> bool`
Delete files or directories (with safeguards).

```python
success = agent.delete_file("/tmp/old_file.txt")
```

#### `modify_config(path: str, new_contents: str) -> bool`
Modify configuration files with automatic backup.

```python
success = agent.modify_config("/etc/hosts", new_hosts_content)
```

#### `list_filesystem(root_path: str, max_depth: int) -> Dict`
Recursively list filesystem contents.

```python
fs_info = agent.list_filesystem("/var/log", max_depth=2)
```

#### `get_system_info() -> Dict`
Get comprehensive system information.

```python
info = agent.get_system_info()
print(f"Platform: {info['system']['platform']}")
print(f"Memory: {info['memory']['percent_used']}%")
```

#### `detect_removable_drives() -> List[Dict]`
Detect removable drives and encrypted volumes.

```python
drives = agent.detect_removable_drives()
for drive in drives:
    print(f"Drive: {drive['device']} ({'removable' if drive['removable'] else 'fixed'})")
```

#### `wipe_logs(log_directory: str) -> bool`
Wipe log files from specified directory.

```python
success = agent.wipe_logs("/var/log")
```

## 📝 Logging

All operations are logged to `/var/log/aiagent.log` with the following format:

```
2024-01-15 10:30:25 - agent - INFO - Operation: SHELL_EXECUTE on ls -la / - success
2024-01-15 10:30:26 - agent - INFO - Operation: READ_FILE on /etc/hostname - success
2024-01-15 10:30:27 - agent - WARNING - ⚠️ Blocked write to protected file: /etc/shadow
```

### Log Levels
- **INFO**: Normal operations
- **WARNING**: Blocked operations, rate limits
- **ERROR**: Failed operations, system errors

## 🔧 Configuration

### Environment Variables
- `PYTHONPATH`: Set to agent directory
- `PYTHONUNBUFFERED`: Set to 1 for immediate output

### Service Configuration
Edit `/etc/systemd/system/aiagent.service` to modify:
- Resource limits (CPU, memory)
- Restart policies
- Environment variables

## 🚨 Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   sudo python3 agent.py
   ```

2. **Service Won't Start**
   ```bash
   sudo systemctl status aiagent
   sudo journalctl -u aiagent
   ```

3. **Log File Not Found**
   ```bash
   sudo mkdir -p /var/log
   sudo touch /var/log/aiagent.log
   ```

4. **Python Dependencies Missing**
   ```bash
   pip3 install -r requirements.txt
   ```

### Debug Mode
Enable debug logging by modifying the agent:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 Uninstallation

To completely remove the agent:

```bash
# Stop and disable service
sudo systemctl stop aiagent
sudo systemctl disable aiagent

# Remove service file
sudo rm /etc/systemd/system/aiagent.service

# Remove installation directory
sudo rm -rf /opt/root_agent

# Remove log file
sudo rm /var/log/aiagent.log

# Reload systemd
sudo systemctl daemon-reload
```

## ⚠️ Legal and Ethical Considerations

- **Use Only on Owned Systems**: Only use this agent on systems you own or have explicit permission to modify
- **Compliance**: Ensure compliance with local laws and regulations
- **Monitoring**: Always monitor the agent's activities
- **Responsibility**: Users are fully responsible for the agent's actions
- **No Warranty**: This software is provided as-is without warranty

## 📈 Monitoring and Maintenance

### Regular Monitoring
- Check logs daily: `sudo tail -f /var/log/aiagent.log`
- Monitor system resources: `sudo systemctl status aiagent`
- Review operation history in the agent's logs

### Updates
- Keep Python and dependencies updated
- Monitor for security patches
- Test updates in isolated environments first

---

**Remember: With great power comes great responsibility. Use this agent wisely and ethically.** 