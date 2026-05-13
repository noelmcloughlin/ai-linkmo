"""Pytest configuration and fixtures for CLI testing."""

import os
import subprocess
import time
from pathlib import Path

import pytest
import requests


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def api_server(project_root):
    """Start the FastAPI server for testing.
    
    This fixture starts the uvicorn server in the background,
    waits for it to be ready, yields control to tests,
    then shuts it down after all tests complete.
    """
    # Check if server is already running
    try:
        response = requests.get("http://localhost:8000/health", timeout=1)
        if response.status_code == 200:
            # Server already running, use it
            yield "http://localhost:8000"
            return
    except requests.exceptions.RequestException:
        pass
    
    # Start server
    server_process = subprocess.Popen(
        ["uv", "run", "uvicorn", "lib.api.server:app", "--host", "localhost", "--port", "8000"],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy()
    )
    
    # Wait for server to be ready (max 30 seconds)
    max_wait = 30
    start_time = time.time()
    server_ready = False
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get("http://localhost:8000/health", timeout=1)
            if response.status_code == 200:
                server_ready = True
                break
        except requests.exceptions.RequestException:
            time.sleep(0.5)
    
    if not server_ready:
        server_process.terminate()
        server_process.wait()
        pytest.fail("Server failed to start within 30 seconds")
    
    yield "http://localhost:8000"
    
    # Cleanup: terminate server
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_process.kill()
        server_process.wait()


@pytest.fixture
def cli_command(project_root, api_server):
    """Return a function to execute CLI commands.
    
    Returns a function that takes command args and returns (stdout, stderr, returncode).
    """
    def execute(*args, mode=None, timeout=30):
        """Execute CLI command with given arguments.
        
        Args:
            *args: Command arguments (e.g., 'risk', '--count')
            mode: Optional mode override ('api' or 'local')
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr, returncode)
        """
        cmd = [str(project_root / "ai")]
        
        # Add arguments
        cmd.extend(str(arg) for arg in args)
        
        # Add mode if specified
        if mode:
            cmd.append(f"--mode={mode}")
        
        # Print the command being executed
        print(f"\n→ Executing: {' '.join(cmd)}")

        # Pass the known server URL so the CLI skips the /health detection probe
        env = os.environ.copy()
        env["AI_ATLAS_API_URL"] = api_server

        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        
        return result.stdout, result.stderr, result.returncode
    
    return execute
