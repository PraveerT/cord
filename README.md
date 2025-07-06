# System Monitor MCP Server

A powerful MCP (Model Context Protocol) server that provides system monitoring and management capabilities for Claude CLI.

## Features

### System Information
- **OS Details**: Get comprehensive operating system information
- **Hardware Info**: CPU count, architecture, and specifications
- **Boot Time**: System uptime tracking

### Resource Monitoring
- **CPU Usage**: Real-time CPU utilization with per-core statistics
- **Memory Stats**: RAM and swap usage monitoring
- **Disk Usage**: Storage information for all mounted partitions
- **Network Stats**: Interface statistics and connection counts

### Process Management
- **List Processes**: View running processes sorted by CPU/memory usage
- **Process Details**: Get detailed information about specific processes
- **Kill Processes**: Terminate processes by PID (with optional force kill)

## Installation

1. Clone or download this repository:
```bash
cd system-monitor-mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Add to Claude CLI:
```bash
# Add as a local MCP server (use server_standalone.py)
claude mcp add system-monitor python /path/to/system-monitor-mcp/server_standalone.py

# Or with a specific Python interpreter
claude mcp add system-monitor /usr/bin/python3 /path/to/system-monitor-mcp/server_standalone.py
```

## Usage Examples

Once installed, you can use the following commands in Claude:

### Check System Status
```
"What's my system status?"
"Show me CPU and memory usage"
```

### Monitor Resources
```
"How much disk space do I have?"
"What's using the most CPU?"
"Show me the top 10 memory-consuming processes"
```

### Process Management
```
"List all running processes"
"Get details about process 1234"
"Kill the process using port 8080"
```

### Network Information
```
"Show network statistics"
"What network interfaces are available?"
```

## Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_system_info()` | Get OS and hardware information | None |
| `get_cpu_usage()` | Get CPU usage statistics | `interval` (float, optional) |
| `get_memory_info()` | Get RAM and swap usage | None |
| `get_disk_usage()` | Get disk space for all partitions | None |
| `list_processes()` | List running processes | `sort_by` (str), `limit` (int) |
| `get_process_info()` | Get details about a specific process | `pid` (int) |
| `kill_process()` | Terminate a process | `pid` (int), `force` (bool) |
| `get_network_stats()` | Get network interface statistics | None |

## Resources

The server also provides a resource endpoint:
- `system://status` - Returns a formatted system status overview

## Security Notes

- Some operations may require elevated privileges (e.g., killing system processes)
- The server respects system permissions and will report access denied errors appropriately
- Use the `force` parameter with caution when killing processes

## Requirements

- Python 3.7+
- psutil library

**Note**: This server includes a standalone MCP implementation that doesn't require the official MCP Python SDK.

## Troubleshooting

### Permission Errors
Some system information may require elevated privileges. Run with appropriate permissions if needed.

### Process Not Found
Processes may terminate between listing and accessing. The server handles these cases gracefully.

### Platform Compatibility
This server is designed to work on Linux, macOS, and Windows, though some features may vary by platform.

## Contributing

Feel free to extend this server with additional monitoring capabilities or system management features!