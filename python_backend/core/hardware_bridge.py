"""
FRIDAY Omega — Hardware Bridge (Real v3.0).
Unified interface for physical device communication.
Supports: Serial (pyserial), Flipper CLI (qFlipper), and Simulator.
Auto-detects connected hardware on initialization.
"""
import logging
import sys
import os
import subprocess

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class HardwareBridge:
    """
    The Physical Interface — routes commands to real hardware or simulator.
    """
    def __init__(self, mode: str = "auto"):
        self.mode = mode.lower()
        self.connected_devices = {}
        
        if self.mode == "auto":
            self._auto_detect()
        else:
            logging.info(f"[HardwareBridge] Forced mode: {self.mode}")

    def _auto_detect(self):
        """Auto-detect connected physical devices."""
        # Check for serial ports
        try:
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())
            if ports:
                for p in ports:
                    self.connected_devices[p.device] = {
                        "type": "serial", "description": p.description, "hwid": p.hwid
                    }
                    logging.info(f"[HardwareBridge] Found serial device: {p.device} ({p.description})")
        except ImportError:
            logging.info("[HardwareBridge] pyserial not installed. Serial devices unavailable.")
        
        # Check for Flipper Zero (qFlipper CLI)
        if self._check_command("qFlipper"):
            self.connected_devices["flipper_zero"] = {"type": "flipper", "description": "Flipper Zero via qFlipper"}
            logging.info("[HardwareBridge] Found Flipper Zero (qFlipper CLI)")
        
        if not self.connected_devices:
            self.mode = "simulator"
            logging.info("[HardwareBridge] No hardware detected. Running in SIMULATOR mode.")
        else:
            self.mode = "real"
            logging.info(f"[HardwareBridge] REAL mode. {len(self.connected_devices)} device(s) connected.")

    def _check_command(self, cmd: str) -> bool:
        """Check if a CLI tool is available."""
        import shutil
        return shutil.which(cmd) is not None

    def send_command(self, device_id: str, payload: str) -> str:
        """Send a command to a physical or simulated device."""
        logging.info(f"[HardwareBridge] TRANSMIT -> {device_id} | {len(payload)} bytes")
        
        if self.mode == "simulator":
            return self._simulate(device_id, payload)
        
        return self._real_dispatch(device_id, payload)

    def _simulate(self, device_id: str, payload: str) -> str:
        """Simulator for testing without hardware."""
        d = device_id.lower()
        if "flipper" in d:
            if "rfid" in payload.lower() or "clone" in payload.lower():
                return "SIM_FLIPPER: 125kHz RFID badge cloned to volatile bank. UID: 0x0102030405"
            if "subghz" in payload.lower() or "jam" in payload.lower():
                return "SIM_FLIPPER: Sub-GHz signal captured at 433.92MHz. Saved to /ext/subghz/capture.sub"
            if "ir" in payload.lower():
                return "SIM_FLIPPER: IR signal learned and replayed."
            return f"SIM_FLIPPER: Command '{payload[:30]}' executed."
        if "serial" in d or "uart" in d:
            return f"SIM_SERIAL: UART TX @ 115200 baud -> [{payload[:20]}...] -> RX: OK"
        if "proxmark" in d:
            return "SIM_PROXMARK: HF Search -> MIFARE Classic 1K detected. UID: AABBCCDD. Keys recovered."
        return f"SIM_HARDWARE: {payload[:30]} -> OK"

    def _real_dispatch(self, device_id: str, payload: str) -> str:
        """Route to real hardware drivers."""
        d = device_id.lower()
        
        if "serial" in d or "uart" in d:
            return self._real_serial(payload)
        
        if "flipper" in d:
            return self._real_flipper(payload)
        
        return f"REAL-ERROR: No driver for device '{device_id}'."

    def _real_serial(self, payload: str) -> str:
        """Send data over real serial/UART connection."""
        try:
            import serial
            # Use first available port
            port_name = list(self.connected_devices.keys())[0]
            ser = serial.Serial(port_name, 115200, timeout=2)
            ser.write(payload.encode())
            response = ser.read(1024).decode('utf-8', errors='replace')
            ser.close()
            return f"REAL-SERIAL [{port_name}]: TX={len(payload)}B | RX={response[:200]}"
        except Exception as e:
            return f"REAL-SERIAL ERROR: {e}"

    def _real_flipper(self, payload: str) -> str:
        """Interact with Flipper Zero via qFlipper CLI or serial."""
        try:
            result = subprocess.run(
                ["qFlipper", "--cli", payload],
                capture_output=True, text=True, timeout=10
            )
            return f"REAL-FLIPPER: {result.stdout[:500]}"
        except FileNotFoundError:
            return "REAL-FLIPPER ERROR: qFlipper CLI not found. Install from flipperzero.one."
        except Exception as e:
            return f"REAL-FLIPPER ERROR: {e}"

    def get_status(self) -> dict:
        """Return current hardware status."""
        return {
            "mode": self.mode,
            "devices": self.connected_devices,
            "device_count": len(self.connected_devices)
        }


hardware_bridge = HardwareBridge(mode="auto")
