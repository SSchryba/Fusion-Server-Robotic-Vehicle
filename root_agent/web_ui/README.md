# 🤖 Root Agent Web UI

A friendly, modern web interface for the Root System Agent. This interface provides an intuitive way to interact with all agent functions through a beautiful, responsive web application.

## ✨ Features

- **🎨 Modern Design** - Beautiful gradient UI with smooth animations
- **⚡ Real-time Updates** - Live feedback and status updates
- **🔒 Security Aware** - Shows security status and blocks dangerous operations
- **📱 Responsive** - Works on desktop, tablet, and mobile devices
- **🚀 Easy to Use** - Point-and-click interface for all agent functions

## 🚀 Quick Start

### Option 1: Easy Launch (Recommended)
```bash
cd root_agent/web_ui
python start_ui.py
```

### Option 2: Manual Launch
```bash
cd root_agent/web_ui
pip install -r requirements.txt
python app.py
```

The web interface will automatically open in your browser at `http://localhost:5000`

## 🎯 Available Functions

### ⚡ Execute Command
- Run system commands safely
- Built-in security checks
- Real-time output display

### 📁 File Operations
- Read and write files
- Simple text editor interface
- Path validation

### 💻 System Information
- Get detailed system stats
- Hardware and software info
- Performance metrics

### 🗂️ Directory Explorer
- Browse filesystem
- Navigate directories
- View file listings

### 💾 Drive Scanner
- Detect removable drives
- Show drive information
- Monitor storage devices

### 🚀 Quick Actions
- Test network connectivity
- Check current user
- Get date and time
- One-click common operations

## 🔒 Security Features

The web UI includes all the security features of the root agent:

- ✅ **Dangerous Command Protection** - Blocks harmful commands
- ✅ **Protected File Access Control** - Prevents access to critical system files
- ✅ **Rate Limiting** - Prevents abuse and overuse
- ✅ **Operation Logging** - Tracks all activities
- ✅ **Error Handling** - Graceful failure management

## 🎨 Interface Components

### Status Bar
- **Green Dot**: Agent is online and ready
- **Operation Counter**: Shows total operations performed
- **Last Operation**: Timestamp of most recent action

### Output Console
- **Real-time Feedback**: See command results instantly
- **Color-coded Messages**: Success (green), errors (red), info (blue)
- **Scrollable History**: Review past operations
- **Timestamps**: Track when operations occurred

### Function Cards
- **Hover Effects**: Interactive feedback
- **Loading States**: Visual indication during processing
- **Input Validation**: Prevents invalid operations
- **Responsive Layout**: Adapts to screen size

## 🛠️ Technical Details

### Built With
- **Frontend**: HTML5, CSS3, JavaScript ES6+
- **Backend**: Python Flask
- **Styling**: Modern CSS with gradients and animations
- **Communication**: RESTful API with JSON

### API Endpoints
- `POST /api/command` - Execute system commands
- `POST /api/read_file` - Read file contents
- `POST /api/write_file` - Write to files
- `POST /api/system_info` - Get system information
- `POST /api/list_directory` - List directory contents
- `POST /api/detect_drives` - Scan for drives
- `GET /api/status` - Get agent status

### Requirements
- Python 3.7+
- Flask 2.3.3+
- Flask-CORS 4.0.0+
- Modern web browser

## 🔧 Configuration

The web UI runs on `localhost:5000` by default. To change the configuration:

1. Edit `app.py`
2. Modify the `app.run()` parameters:
   ```python
   app.run(host='0.0.0.0', port=8080, debug=False)
   ```

## 🚨 Important Notes

- **Administrator Privileges**: Some functions may require admin rights
- **Security**: The web interface bypasses admin checks for demonstration
- **Rate Limiting**: Operations are limited to prevent abuse
- **Logging**: All operations are logged for security

## 🎉 Getting Started

1. **Launch the Interface**:
   ```bash
   python start_ui.py
   ```

2. **Try a Simple Command**:
   - Go to "Execute Command"
   - Type: `echo Hello World`
   - Click "Run Command"

3. **Explore Files**:
   - Go to "File Operations"
   - Enter a file path like `C:\temp\test.txt`
   - Add some content and click "Write File"
   - Click "Read File" to verify

4. **Check System Info**:
   - Click "Get System Info" to see your system details

5. **Browse Directories**:
   - Enter a path like `C:\Users`
   - Click "Browse Directory"

## 🆘 Troubleshooting

### Common Issues

**Port Already in Use**:
```bash
# Kill process using port 5000
netstat -ano | findstr :5000
taskkill /PID <process_id> /F
```

**Dependencies Missing**:
```bash
pip install -r requirements.txt
```

**Agent Permissions**:
- Some functions require administrator privileges
- Run PowerShell as Administrator for full functionality

## 📝 License

This web interface is part of the Root Agent project and follows the same licensing terms.

---

Enjoy using the Root Agent Web UI! 🎉

For support or questions, please refer to the main Root Agent documentation. 