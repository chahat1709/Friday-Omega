"""System tools exposed to the agent."""

import platform
import csv
import io
import subprocess
import os
from typing import Dict, List, Optional, Any

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

KNOWN_APPS: Dict[str, str] = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "terminal": "wt.exe",
    "edge": "msedge.exe",
    "explorer": "explorer.exe",
}


def _expand_app_paths(app_map: Dict[str, str]) -> Dict[str, str]:
    return {key.lower(): os.path.expandvars(value) for key, value in app_map.items()}


APP_COMMANDS = _expand_app_paths(KNOWN_APPS)


async def run_subprocess(command: List[str]) -> str:
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        creationflags=CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    stdout, stderr = await process.communicate()
    output = stdout.decode(errors="ignore").strip()
    error = stderr.decode(errors="ignore").strip()
    if process.returncode != 0:
        raise RuntimeError(error or "Command failed")
    return output or (error if error else "")


async def launch_app(name: str) -> str:
    if not name:
        raise ValueError("Application name required.")
    needle = name.lower().strip()
    possibilities = list(APP_COMMANDS.keys())
    match = needle if needle in APP_COMMANDS else None
    if not match:
        candidates = get_close_matches(needle, possibilities, n=1, cutoff=0.82)
        if candidates:
            match = candidates[0]
    if not match:
        raise ValueError(f"No known application similar to '{name}'.")

    target = APP_COMMANDS[match]
    if not Path(target).exists() and not target.endswith(".exe"):
        pass  # We optimistically attempt to launch even if missing.

    if sys.platform == "win32":
        command = ["cmd.exe", "/c", "start", "", target]
        await run_subprocess(command)
    else:
        raise RuntimeError("launch_app currently supports Windows environments only.")
    return f"Launched {match} via {target}."


async def audit_hardware() -> Dict[str, Any]:
    disk_root = Path(os.getcwd()).anchor or "/"
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "cpu_cores": psutil.cpu_count(logical=True),
        "memory": psutil.virtual_memory()._asdict(),
        "uptime_seconds": int(time.time() - psutil.boot_time()),
        "disk": psutil.disk_usage(disk_root)._asdict(),
    }


def _parse_netsh_networks(raw: str) -> List[Dict[str, Any]]:
    networks: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {}
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("SSID"):
            if current:
                networks.append(current)
            current = {"ssid": line.split(":", 1)[-1].strip()}
        elif line.startswith("Signal"):
            current["signal"] = line.split(":", 1)[-1].strip()
        elif line.startswith("Authentication"):
            current["auth"] = line.split(":", 1)[-1].strip()
    if current:
        networks.append(current)
    return networks


async def scan_wifi() -> List[Dict[str, Any]]:
    if sys.platform != "win32":
        raise RuntimeError("scan_wifi currently supports Windows only.")
    command = ["netsh", "wlan", "show", "networks", "mode=Bssid"]
    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(stderr.decode(errors="ignore") or "Unable to scan Wi-Fi networks.")
    return _parse_netsh_networks(stdout.decode(errors="ignore"))


async def get_passwords() -> Dict[str, Optional[str]]:
    if sys.platform != "win32":
        raise RuntimeError("get_passwords currently supports Windows only.")

    profiles_cmd = ["netsh", "wlan", "show", "profiles"]
    proc = await asyncio.create_subprocess_exec(
        *profiles_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(stderr.decode(errors="ignore") or "Failed to enumerate profiles.")

    profile_names = re.findall(r"All User Profile\s*: (.*)", stdout.decode(errors="ignore"))
    secrets: Dict[str, Optional[str]] = {}
    for profile in profile_names:
        detail_cmd = ["netsh", "wlan", "show", "profile", f"name={profile}", "key=clear"]
        detail_proc = await asyncio.create_subprocess_exec(
            *detail_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        detail_out, _ = await detail_proc.communicate()
        if detail_proc.returncode != 0:
            secrets[profile] = None
            continue
        match = re.search(r"Key Content\s*: (.*)", detail_out.decode(errors="ignore"))
        secrets[profile] = match.group(1).strip() if match else None
    return secrets


async def search_web(ddg, query: str) -> List[Dict[str, Any]]:
    if not query:
        raise ValueError("Query required.")
    results: List[Dict[str, Any]] = []
    with ddg() as client:
        for item in client.text(query, region="us-en", safesearch="moderate", max_results=5):
            results.append(
                {
                    "title": item.get("title"),
                    "href": item.get("href"),
                    "snippet": item.get("body"),
                }
            )
    if not results:
        return [{"title": "No results", "href": None, "snippet": "DuckDuckGo returned no hits."}]
    return results


async def detect_os() -> Dict[str, Any]:
    """Detect the operating system and version."""
    system = platform.system()
    version = platform.version()
    release = platform.release()
    machine = platform.machine()
    return {
        "system": system,
        "version": version,
        "release": release,
        "machine": machine,
    }


async def list_installed_apps() -> List[str]:
    """List installed applications on the system."""
    if sys.platform == "win32":
        # Use WMIC to list installed products
        command = ["wmic", "product", "get", "name", "/format:csv"]
        output = await run_subprocess(command)
        reader = csv.reader(io.StringIO(output))
        apps = []
        for row in reader:
            if len(row) > 1 and row[1].strip():
                apps.append(row[1].strip())
        return apps[1:]  # Skip header
    else:
        # For other OS, placeholder
        return ["Listing apps not implemented for this OS"]


async def list_drivers() -> List[Dict[str, str]]:
    """List system drivers."""
    if sys.platform == "win32":
        command = ["wmic", "sysdriver", "get", "name,status", "/format:csv"]
        output = await run_subprocess(command)
        reader = csv.reader(io.StringIO(output))
        drivers = []
        for row in reader:
            if len(row) >= 3:
                drivers.append({"name": row[1].strip(), "status": row[2].strip()})
        return drivers[1:]  # Skip header
    else:
        return [{"name": "Not implemented", "status": "N/A"}]


async def access_terminal(command: str) -> str:
    """Execute a terminal command and return output."""
    if not command:
        raise ValueError("Command required.")
    # Split command into list
    cmd_list = command.split()
    return await run_subprocess(cmd_list)


TOOL_REGISTRY = {
    "launch_app": launch_app,
    "audit_hardware": audit_hardware,
    "scan_wifi": scan_wifi,
    "get_passwords": get_passwords,
    "detect_os": detect_os,
    "list_installed_apps": list_installed_apps,
    "list_drivers": list_drivers,
    "access_terminal": access_terminal,
}
