#!/usr/bin/env python3
"""System Monitor MCP Server - Standalone implementation without external MCP dependencies."""

import json
import sys
import os
import platform
import psutil
from datetime import datetime
from typing import Dict, List, Any, Optional

class MCPServer:
    """Simple MCP server implementation for system monitoring."""
    
    def __init__(self, name: str):
        self.name = name
        self.tools = {}
        self.tool_functions = {}
        self.resources = {}
    
    def tool(self, func):
        """Decorator to register a tool."""
        self.tools[func.__name__] = {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "inputSchema": self._get_schema(func)
        }
        self.tool_functions[func.__name__] = func
        return func
    
    def resource(self, uri: str):
        """Decorator to register a resource."""
        def decorator(func):
            self.resources[uri] = func
            return func
        return decorator
    
    def _get_schema(self, func):
        """Generate a simple schema from function annotations."""
        import inspect
        sig = inspect.signature(func)
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else "string"
            properties[param_name] = {
                "type": self._python_type_to_json_type(param_type)
            }
            
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def _python_type_to_json_type(self, python_type):
        """Convert Python type to JSON schema type."""
        type_map = {
            int: "integer",
            float: "number",
            str: "string",
            bool: "boolean",
            list: "array",
            dict: "object"
        }
        
        if hasattr(python_type, '__origin__'):
            return type_map.get(python_type.__origin__, "string")
        
        return type_map.get(python_type, "string")
    
    def handle_request(self, request: dict) -> dict:
        """Handle incoming MCP requests."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                return self._handle_initialize(request_id)
            elif method == "tools/list":
                return self._handle_tools_list(request_id)
            elif method == "tools/call":
                return self._handle_tool_call(params, request_id)
            elif method == "resources/list":
                return self._handle_resources_list(request_id)
            elif method == "resources/read":
                return self._handle_resource_read(params, request_id)
            else:
                return self._error_response(request_id, -32601, f"Method not found: {method}")
        except Exception as e:
            return self._error_response(request_id, -32603, str(e))
    
    def _handle_initialize(self, request_id):
        """Handle initialization request."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": self.name,
                    "version": "1.0.0"
                }
            }
        }
    
    def _handle_tools_list(self, request_id):
        """List available tools."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": list(self.tools.values())
            }
        }
    
    def _handle_tool_call(self, params, request_id):
        """Execute a tool call."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return self._error_response(request_id, -32602, f"Unknown tool: {tool_name}")
        
        # Get the actual function
        func = self.tool_functions[tool_name]
        result = func(**arguments)
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        }
    
    def _handle_resources_list(self, request_id):
        """List available resources."""
        resources = []
        for uri in self.resources:
            resources.append({
                "uri": uri,
                "name": uri.split("://")[1] if "://" in uri else uri,
                "mimeType": "text/plain"
            })
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": resources
            }
        }
    
    def _handle_resource_read(self, params, request_id):
        """Read a resource."""
        uri = params.get("uri")
        
        if uri not in self.resources:
            return self._error_response(request_id, -32602, f"Unknown resource: {uri}")
        
        func = self.resources[uri]
        content = func()
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "text/plain",
                        "text": content
                    }
                ]
            }
        }
    
    def _error_response(self, request_id, code, message):
        """Generate an error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
    
    def run(self):
        """Run the MCP server on stdio."""
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line)
                response = self.handle_request(request)
                
                print(json.dumps(response))
                sys.stdout.flush()
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()

# Create the MCP server instance
mcp = MCPServer("SystemMonitor")

@mcp.tool
def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information including OS, hardware, and environment."""
    return {
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "python_version": platform.python_version(),
        "hostname": platform.node(),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        "cpu_count": {
            "physical": psutil.cpu_count(logical=False),
            "logical": psutil.cpu_count(logical=True),
        }
    }

@mcp.tool
def get_cpu_usage(interval: float = 1.0) -> Dict[str, Any]:
    """Get current CPU usage statistics."""
    cpu_percent = psutil.cpu_percent(interval=interval, percpu=True)
    
    # Try to get CPU frequency, handle WSL/Docker limitations
    try:
        cpu_freq = psutil.cpu_freq()
        freq_info = {
            "current": cpu_freq.current if cpu_freq else None,
            "min": cpu_freq.min if cpu_freq else None,
            "max": cpu_freq.max if cpu_freq else None,
        }
    except (FileNotFoundError, PermissionError):
        freq_info = {
            "current": None,
            "min": None,
            "max": None,
            "note": "CPU frequency not available in this environment"
        }
    
    return {
        "total_percent": psutil.cpu_percent(interval=interval),
        "per_cpu_percent": cpu_percent,
        "frequency": freq_info,
        "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,
    }

@mcp.tool
def get_memory_info() -> Dict[str, Any]:
    """Get memory (RAM and swap) usage statistics."""
    virtual_mem = psutil.virtual_memory()
    swap_mem = psutil.swap_memory()
    
    return {
        "ram": {
            "total": virtual_mem.total,
            "available": virtual_mem.available,
            "used": virtual_mem.used,
            "free": virtual_mem.free,
            "percent": virtual_mem.percent,
            "total_gb": round(virtual_mem.total / (1024**3), 2),
            "available_gb": round(virtual_mem.available / (1024**3), 2),
        },
        "swap": {
            "total": swap_mem.total,
            "used": swap_mem.used,
            "free": swap_mem.free,
            "percent": swap_mem.percent,
            "total_gb": round(swap_mem.total / (1024**3), 2),
        }
    }

@mcp.tool
def get_disk_usage() -> List[Dict[str, Any]]:
    """Get disk usage information for all mounted partitions."""
    disk_partitions = psutil.disk_partitions()
    disk_info = []
    
    for partition in disk_partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_info.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "filesystem": partition.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
                "total_gb": round(usage.total / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
            })
        except PermissionError:
            disk_info.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "error": "Permission denied"
            })
    
    return disk_info

@mcp.tool
def list_processes(sort_by: str = "cpu", limit: int = 20) -> List[Dict[str, Any]]:
    """List running processes sorted by resource usage."""
    processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
        try:
            proc_info = proc.info
            processes.append({
                "pid": proc_info['pid'],
                "name": proc_info['name'],
                "cpu_percent": proc_info['cpu_percent'] or 0,
                "memory_percent": round(proc_info['memory_percent'] or 0, 2),
                "status": proc_info['status'],
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Sort processes
    if sort_by == 'cpu':
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    elif sort_by == 'memory':
        processes.sort(key=lambda x: x['memory_percent'], reverse=True)
    elif sort_by == 'name':
        processes.sort(key=lambda x: x['name'].lower())
    
    return processes[:limit]

@mcp.tool
def kill_process(pid: int, force: bool = False) -> Dict[str, Any]:
    """Terminate a process by its PID."""
    try:
        process = psutil.Process(pid)
        process_name = process.name()
        
        if force:
            process.kill()  # SIGKILL
        else:
            process.terminate()  # SIGTERM
        
        return {
            "success": True,
            "pid": pid,
            "name": process_name,
            "message": f"Process {pid} ({process_name}) terminated successfully"
        }
    except psutil.NoSuchProcess:
        return {
            "success": False,
            "pid": pid,
            "error": f"No process found with PID {pid}"
        }
    except psutil.AccessDenied:
        return {
            "success": False,
            "pid": pid,
            "error": f"Access denied to terminate process {pid}"
        }
    except Exception as e:
        return {
            "success": False,
            "pid": pid,
            "error": str(e)
        }

@mcp.tool
def get_network_stats() -> Dict[str, Any]:
    """Get network interface statistics and connections."""
    net_io = psutil.net_io_counters()
    net_if_addrs = psutil.net_if_addrs()
    net_if_stats = psutil.net_if_stats()
    
    interfaces = {}
    for interface, addrs in net_if_addrs.items():
        if_stats = net_if_stats.get(interface)
        interfaces[interface] = {
            "is_up": if_stats.isup if if_stats else None,
            "speed": if_stats.speed if if_stats else None,
            "addresses": [
                {
                    "family": addr.family.name,
                    "address": addr.address,
                    "netmask": addr.netmask,
                }
                for addr in addrs
            ]
        }
    
    return {
        "global_stats": {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "errin": net_io.errin,
            "errout": net_io.errout,
            "dropin": net_io.dropin,
            "dropout": net_io.dropout,
        },
        "interfaces": interfaces,
        "connections_count": len(psutil.net_connections()),
    }

@mcp.tool
def get_process_info(pid: int) -> Dict[str, Any]:
    """Get detailed information about a specific process."""
    try:
        process = psutil.Process(pid)
        
        with process.oneshot():
            return {
                "pid": pid,
                "name": process.name(),
                "status": process.status(),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
                "cpu_percent": process.cpu_percent(interval=0.1),
                "memory_info": {
                    "rss": process.memory_info().rss,
                    "vms": process.memory_info().vms,
                    "percent": round(process.memory_percent(), 2),
                },
                "num_threads": process.num_threads(),
                "ppid": process.ppid(),
                "cmdline": process.cmdline(),
                "cwd": process.cwd() if hasattr(process, 'cwd') else None,
                "username": process.username() if hasattr(process, 'username') else None,
            }
    except psutil.NoSuchProcess:
        return {"error": f"No process found with PID {pid}"}
    except psutil.AccessDenied:
        return {"error": f"Access denied to process {pid}"}
    except Exception as e:
        return {"error": str(e)}

# Resource for system status overview
@mcp.resource("system://status")
def get_system_status() -> str:
    """Get a comprehensive system status overview."""
    cpu_percent = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    status = f"""System Status Overview
=====================
CPU Usage: {cpu_percent}%
Memory: {mem.percent}% used ({round(mem.used / (1024**3), 1)} GB / {round(mem.total / (1024**3), 1)} GB)
Disk: {disk.percent}% used ({round(disk.used / (1024**3), 1)} GB / {round(disk.total / (1024**3), 1)} GB)
Uptime: {datetime.now() - datetime.fromtimestamp(psutil.boot_time())}
Processes: {len(psutil.pids())}
"""
    return status

if __name__ == "__main__":
    mcp.run()