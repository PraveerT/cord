#!/usr/bin/env python3
"""System Monitor MCP Server - Provides system monitoring and management capabilities."""

import os
import platform
import psutil
from datetime import datetime
from typing import Dict, List, Any
from mcp.server.fastmcp import FastMCP

# Create the MCP server instance
mcp = FastMCP("SystemMonitor")

@mcp.tool()
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

@mcp.tool()
def get_cpu_usage(interval: float = 1.0) -> Dict[str, Any]:
    """Get current CPU usage statistics.
    
    Args:
        interval: Time interval in seconds for measuring CPU usage (default: 1.0)
    """
    cpu_percent = psutil.cpu_percent(interval=interval, percpu=True)
    cpu_freq = psutil.cpu_freq()
    
    return {
        "total_percent": psutil.cpu_percent(interval=interval),
        "per_cpu_percent": cpu_percent,
        "frequency": {
            "current": cpu_freq.current if cpu_freq else None,
            "min": cpu_freq.min if cpu_freq else None,
            "max": cpu_freq.max if cpu_freq else None,
        },
        "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,
    }

@mcp.tool()
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

@mcp.tool()
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

@mcp.tool()
def list_processes(sort_by: str = "cpu", limit: int = 20) -> List[Dict[str, Any]]:
    """List running processes sorted by resource usage.
    
    Args:
        sort_by: Sort criterion - 'cpu', 'memory', or 'name' (default: 'cpu')
        limit: Maximum number of processes to return (default: 20)
    """
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

@mcp.tool()
def kill_process(pid: int, force: bool = False) -> Dict[str, Any]:
    """Terminate a process by its PID.
    
    Args:
        pid: Process ID to terminate
        force: Use SIGKILL instead of SIGTERM (default: False)
    """
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

@mcp.tool()
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

@mcp.tool()
def get_process_info(pid: int) -> Dict[str, Any]:
    """Get detailed information about a specific process.
    
    Args:
        pid: Process ID to get information for
    """
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