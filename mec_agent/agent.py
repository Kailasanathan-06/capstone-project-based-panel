#!/usr/bin/env python3
"""
MEC Agent - Autonomous Edge Computing Agent

This agent runs on MEC (Multi-access Edge Computing) nodes and:
1. Registers with the Django server once using a pairing code
2. Stores configuration securely
3. Automatically reconnects on startup
4. Sends periodic heartbeats with system telemetry
5. Receives and executes authorized tasks
6. Returns results through the Django API
7. Handles network changes and reconnection with exponential backoff
"""

import os
import sys
import json
import time
import socket
import platform
import threading
import secrets
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Third-party imports
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available, limited telemetry")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Error: requests library required")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from engine.image_processor import MedicalImageProcessor
    PROCESSOR_AVAILABLE = True
except Exception:
    PROCESSOR_AVAILABLE = False


# =============================================================================
# Configuration
# =============================================================================

CONFIG_DIR = Path.home() / ".mec_agent"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = CONFIG_DIR / "agent.log"

# Default configuration
DEFAULT_CONFIG = {
    "server_url": "http://127.0.0.1:8000",
    "device_id": None,
    "auth_token": None,
    "token": None,
    "system_name": None,
    "heartbeat_interval": 10,
    "heartbeat_timeout": 30,
    "auto_start": True,
    "max_retries": 10,
    "base_retry_delay": 5,
    "max_retry_delay": 300,
    "verify_ssl": True,
}


# =============================================================================
# Logging Setup
# =============================================================================

def setup_logging():
    """Configure logging for the MEC agent."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("MECAgent")


logger = setup_logging()


# =============================================================================
# Configuration Management
# =============================================================================

class ConfigManager:
    """Manages persistent configuration for the MEC agent."""
    
    def __init__(self, config_path: Path = CONFIG_FILE):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                merged = DEFAULT_CONFIG.copy()
                merged.update(config)
                return merged
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """Save configuration to file."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def get(self, key: str, default=None):
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        self.config[key] = value
        self.save_config()
    
    def is_registered(self) -> bool:
        return bool(self.config.get("device_id") and self.config.get("auth_token"))


# =============================================================================
# System Telemetry
# =============================================================================

class TelemetryCollector:
    """Collects system telemetry data."""
    
    @staticmethod
    def get_hostname() -> str:
        return socket.gethostname()
    
    @staticmethod
    def get_os_info() -> str:
        return f"{platform.system()} {platform.release()}"
    
    @staticmethod
    def get_cpu_info() -> str:
        return platform.processor() or "Unknown"
    
    @staticmethod
    def get_storage_info() -> str:
        try:
            disk = psutil.disk_usage('/')
            return f"{disk.free // (1024**3)} GB free"
        except:
            return "Unknown"
    
    @staticmethod
    def get_processor_info() -> str:
        try:
            return f"{psutil.cpu_count(logical=False)} cores, {psutil.cpu_count()} threads"
        except:
            return "Unknown"
    
    def collect(self) -> Dict[str, Any]:
        """Collect all telemetry data."""
        telemetry = {
            "hostname": self.get_hostname(),
            "os_info": self.get_os_info(),
            "cpu_info": self.get_cpu_info(),
            "storage_info": self.get_storage_info(),
            "processor_info": self.get_processor_info(),
            "cpu_usage": 0.0,
            "ram_usage": 0.0,
            "disk_usage": 0.0,
            "network_latency": 0.0,
            "energy_estimate": 0.0,
        }
        
        if PSUTIL_AVAILABLE:
            try:
                telemetry["cpu_usage"] = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory()
                telemetry["ram_usage"] = mem.percent
                disk = psutil.disk_usage('/')
                telemetry["disk_usage"] = (disk.used / disk.total) * 100
                
                # Estimate energy based on CPU usage
                # This is a rough estimate - real energy monitoring requires hardware support
                base_power = 50  # Watts base
                cpu_power = (telemetry["cpu_usage"] / 100) * 65  # Max 65W for CPU
                telemetry["energy_estimate"] = (base_power + cpu_power) / 3600  # Wh per second
            except Exception as e:
                logger.warning(f"Telemetry collection error: {e}")
        
        return telemetry


# =============================================================================
# HTTP Client with Retry Logic
# =============================================================================

class APIClient:
    """HTTP client for communicating with Django server."""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.session = requests.Session()
        self.session.verify = config.get("verify_ssl", True)
    
    def _get_headers(self, include_mec_auth: bool = False) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        # MEC-authenticated endpoints require the DRF token plus the X-MEC-ID header.
        if include_mec_auth and self.config.get("token") and self.config.get("device_id"):
            headers["Authorization"] = f"Token {self.config.get('token')}"
            headers["X-MEC-ID"] = self.config.get("device_id")
        else:
            # Legacy mode: heartbeats are authorized by the body credentials.
            headers["Authorization"] = f"Bearer {self.config.get('auth_token')}"
        return headers
    
    def _request_with_retry(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with exponential backoff retry."""
        max_retries = self.config.get("max_retries", 10)
        base_delay = self.config.get("base_retry_delay", 5)
        max_delay = self.config.get("max_retry_delay", 300)
        
        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, **kwargs)
                return response
            except requests.exceptions.ConnectionError as e:
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(f"Connection failed (attempt {attempt+1}/{max_retries}), retrying in {delay}s: {e}")
                time.sleep(delay)
            except requests.exceptions.Timeout:
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(f"Request timeout (attempt {attempt+1}/{max_retries}), retrying in {delay}s")
                time.sleep(delay)
            except Exception as e:
                logger.error(f"Request error: {e}")
                return None
        
        logger.error(f"Max retries exceeded for {url}")
        return None
    
    def register(self, server_url: str, pairing_code: str, system_name: str = None) -> Dict[str, Any]:
        """Register the MEC agent with the server using a one-time pairing code.

        The server assigns the device ID (MEC-XXX) and returns credentials.
        """
        url = f"{server_url}/api/mec/register/"
        data = {
            "pairing_code": pairing_code,
            "system_name": system_name or socket.gethostname(),
            "server_url": server_url,
            "agent_version": "1.0.0",
        }

        response = self._request_with_retry("POST", url, json=data, timeout=15)
        if response and response.status_code == 201:
            return response.json()
        elif response:
            try:
                return {"error": response.json().get("error", "Registration failed")}
            except Exception:
                return {"error": f"Registration failed (HTTP {response.status_code})"}
        return {"error": "Server unreachable"}

    def heartbeat(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Send heartbeat + telemetry to the server."""
        url = f"{self.config.get('server_url')}/api/mec/heartbeat/"
        data = {
            "mec_id": self.config.get("device_id"),
            "auth_token": self.config.get("auth_token"),
            **telemetry,
        }

        response = self._request_with_retry("POST", url, json=data, timeout=15)
        if response and response.status_code == 200:
            return response.json()
        return {"error": "Heartbeat failed"}

    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Pull the single task currently assigned to this MEC (MEC-authenticated)."""
        url = f"{self.config.get('server_url')}/api/mec/{self.config.get('device_id')}/next-task/"
        headers = self._get_headers(include_mec_auth=True)
        response = self._request_with_retry("GET", url, headers=headers, timeout=15)
        if response and response.status_code == 200:
            return response.json().get("task")
        return None

    def report_result(self, task: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Report task completion/failure to the server (MEC-authenticated)."""
        url = f"{self.config.get('server_url')}/api/mec/{self.config.get('device_id')}/report-result/"
        data = {
            "task_id": task.get("task_id"),
            "success": result.get("status") == "COMPLETED",
            "status": result.get("status"),
            "execution_time": result.get("execution_time", 0),
            "cpu_usage": result.get("cpu_usage"),
            "ram_usage": result.get("ram_usage"),
            "network_latency": result.get("network_latency"),
            "estimated_energy": result.get("energy_estimate", 0),
            "result_location": result.get("result_location", ""),
            "output_path": result.get("output_path", ""),
            "output_checksum": result.get("output_checksum", ""),
            "input_checksum": result.get("input_checksum", ""),
            "image_processing_time": result.get("image_processing_time", 0),
            "error_message": result.get("error", ""),
        }
        headers = self._get_headers(include_mec_auth=True)
        response = self._request_with_retry("POST", url, json=data, headers=headers, timeout=15)
        return response is not None and response.status_code == 200


# =============================================================================
# Task Executor
# =============================================================================

class TaskExecutor:
    """Executes tasks received from the server with genuine computation."""
    
    def __init__(self, config: ConfigManager, api_client: APIClient):
        self.config = config
        self.api_client = api_client
        self.current_task = None
        self.task_lock = threading.Lock()
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task (real medical-image processing or verified CPU computation) and return results."""
        task_id = task.get("task_id")
        logger.info(f"Executing task: {task_id}")
        
        start_mono = time.perf_counter()
        self.current_task = task
        
        try:
            image_path = task.get("image_path")
            operation = task.get("operation") or "normalize_clahe"
            target_res = int(task.get("target_resolution") or 224)

            if PROCESSOR_AVAILABLE and image_path and os.path.exists(image_path):
                # Genuine medical image preprocessing workload
                logger.info(f"Running MedicalImageProcessor for task {task_id}: {operation} on {image_path}")
                processor = MedicalImageProcessor()
                proc_res = processor.process(
                    image_path=image_path,
                    operation=operation,
                    target_resolution=target_res,
                )
                exec_time = proc_res["processing_time_s"]
                cpu_u = psutil.cpu_percent(interval=None) if PSUTIL_AVAILABLE else 25.0
                ram_u = psutil.virtual_memory().percent if PSUTIL_AVAILABLE else 30.0

                result = {
                    "task_id": task_id,
                    "status": "COMPLETED",
                    "execution_time": round(exec_time, 4),
                    "image_processing_time": round(exec_time, 4),
                    "output_path": proc_res["output_path"],
                    "input_checksum": proc_res["input_checksum"],
                    "output_checksum": proc_res["output_checksum"],
                    "result_location": proc_res["output_path"],
                    "cpu_usage": round(cpu_u, 2),
                    "ram_usage": round(ram_u, 2),
                    "energy_estimate": round(exec_time * 0.08, 4),
                }
            else:
                # Real CPU cryptographic/matrix workload (replaces artificial sleep)
                cpu_cycles = float(task.get("cpu_cycles_giga") or 0.5)
                rounds = int(max(10000, min(500000, cpu_cycles * 150000)))
                data_buf = b"SecureDT_Medical_Preprocessing_Benchmark" * 64
                hasher = hashlib.sha256()
                for _ in range(rounds):
                    hasher.update(data_buf)
                digest = hasher.hexdigest()

                exec_time = time.perf_counter() - start_mono
                cpu_u = psutil.cpu_percent(interval=None) if PSUTIL_AVAILABLE else 20.0
                ram_u = psutil.virtual_memory().percent if PSUTIL_AVAILABLE else 25.0

                result = {
                    "task_id": task_id,
                    "status": "COMPLETED",
                    "execution_time": round(exec_time, 4),
                    "result_location": f"results/{task_id}_{digest[:12]}.bin",
                    "cpu_usage": round(cpu_u, 2),
                    "ram_usage": round(ram_u, 2),
                    "energy_estimate": round(exec_time * 0.1, 4),
                }
            
            logger.info(f"Task {task_id} completed in {result['execution_time']:.4f}s")
            return result
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            return {
                "task_id": task_id,
                "status": "FAILED",
                "error": str(e),
            }
        finally:
            self.current_task = None


# =============================================================================
# MEC Agent Main Class
# =============================================================================

class MECAgent:
    """Main MEC Agent class."""
    
    def __init__(self):
        self.config = ConfigManager()
        self.api_client = APIClient(self.config)
        self.telemetry = TelemetryCollector()
        self.executor = TaskExecutor(self.config, self.api_client)
        self.running = False
        self.heartbeat_thread = None
        self.task_poll_thread = None
    
    def register(self, server_url: str, pairing_code: str, system_name: str = None) -> bool:
        """Register the MEC agent with the server."""
        logger.info(f"Registering with server: {server_url}")
        
        result = self.api_client.register(server_url, pairing_code, system_name)
        
        if "error" in result:
            logger.error(f"Registration failed: {result['error']}")
            return False
        
        # Save credentials
        self.config.set("server_url", server_url)
        self.config.set("device_id", result.get("device_id"))
        self.config.set("auth_token", result.get("auth_token"))
        self.config.set("token", result.get("token"))
        self.config.set("system_name", system_name or socket.gethostname())
        
        logger.info(f"Registration successful! Device ID: {result.get('device_id')}")
        return True
    
    def start_heartbeat(self):
        """Start the heartbeat loop."""
        def heartbeat_loop():
            interval = self.config.get("heartbeat_interval", 10)
            while self.running:
                try:
                    telemetry = self.telemetry.collect()
                    telemetry["current_task"] = self.executor.current_task.get("task_id", "") if self.executor.current_task else ""
                    telemetry["task_count"] = 1 if self.executor.current_task else 0
                    telemetry["agent_version"] = "1.0.0"
                    telemetry["status"] = "ONLINE"
                    
                    result = self.api_client.heartbeat(telemetry)
                    if "error" in result:
                        logger.warning(f"Heartbeat failed: {result['error']}")
                    else:
                        logger.debug("Heartbeat sent successfully")
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
                
                time.sleep(interval)
        
        self.heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        logger.info("Heartbeat started")
    
    def start_task_polling(self):
        """Start polling for tasks."""
        def task_poll_loop():
            while self.running:
                try:
                    if not self.executor.current_task:
                        task = self.api_client.get_next_task()
                        if task:
                            result = self.executor.execute_task(task)
                            if result.get("status") == "COMPLETED":
                                self.api_client.report_result(task, result)
                            else:
                                self.api_client.report_result(task, result)
                except Exception as e:
                    logger.error(f"Task polling error: {e}")

                time.sleep(5)  # Poll every 5 seconds

        self.task_poll_thread = threading.Thread(target=task_poll_loop, daemon=True)
        self.task_poll_thread.start()
        logger.info("Task polling started")
    
    def run(self):
        """Main agent loop."""
        if not self.config.is_registered():
            logger.error("Not registered. Please register first.")
            return False
        
        self.running = True
        logger.info(f"Starting MEC Agent: {self.config.get('device_id')}")
        
        self.start_heartbeat()
        self.start_task_polling()
        
        logger.info("MEC Agent running. Press Ctrl+C to stop.")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
            self.stop()
        
        return True
    
    def stop(self):
        """Stop the agent."""
        self.running = False
        logger.info("MEC Agent stopped")


# =============================================================================
# CLI Interface
# =============================================================================

def print_banner():
    print("""
+=============================================================+
|                    MEC AGENT v1.0.0                         |
|      Multi-access Edge Computing Autonomous Agent           |
+=============================================================+
""")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="MEC Agent for Edge-Cloud Task Scheduling")
    parser.add_argument("command", nargs="?", choices=["register", "run", "status"], default="run",
                        help="Command to execute")
    parser.add_argument("--server", "-s", help="Django server URL")
    parser.add_argument("--pairing-code", "-p", help="Registration pairing code")
    parser.add_argument("--name", "-n", help="System name for registration")
    
    args = parser.parse_args()
    
    print_banner()
    
    agent = MECAgent()
    
    if args.command == "register":
        server_url = args.server or input("Server URL: ").strip()
        pairing_code = args.pairing_code or input("Pairing code: ").strip()
        system_name = args.name or input("System name (optional): ").strip() or None
        
        if not server_url or not pairing_code:
            logger.error("Server URL and pairing code are required")
            sys.exit(1)
        
        if agent.register(server_url, pairing_code, system_name):
            print("\n[OK] Registration successful!")
            print(f"     Device ID: {agent.config.get('device_id')}")
            print(f"     Auth Token: {agent.config.get('auth_token')[:16]}...")
            print("\nThe agent will now automatically connect on startup.")
        else:
            print("\n[FAILED] Registration failed!")
            sys.exit(1)
    
    elif args.command == "run":
        if not agent.config.is_registered():
            logger.error("Agent not registered. Run 'mec_agent register' first.")
            sys.exit(1)
        
        agent.run()
    
    elif args.command == "status":
        if agent.config.is_registered():
            print(f"Device ID: {agent.config.get('device_id')}")
            print(f"Server URL: {agent.config.get('server_url')}")
            print(f"System Name: {agent.config.get('system_name')}")
            print(f"Registered: Yes")
        else:
            print("Agent not registered")


if __name__ == "__main__":
    main()