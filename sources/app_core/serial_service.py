from __future__ import annotations

from dataclasses import dataclass
import time

import serial
import serial.tools.list_ports


DEVICE_GPP = "GPP"
DEVICE_KEYSIGHT = "Keysight"


@dataclass
class SerialService:
    connection: serial.Serial | None = None
    device_type: str = DEVICE_GPP

    def is_connected(self) -> bool:
        return self.connection is not None and self.connection.is_open

    def list_ports(self) -> list[str]:
        return [p.device for p in serial.tools.list_ports.comports()]

    def set_device_type(self, device_type: str) -> None:
        self.device_type = device_type

    def connect(self, port: str, baudrate: int) -> str:
        conn = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=1,
        )
        conn.write(b"*IDN?\r\n")
        time.sleep(0.05)
        idn = conn.readline().decode(errors="ignore").strip()
        self._validate_idn(idn)
        self.connection = conn
        return idn

    def disconnect(self) -> None:
        if self.connection and self.connection.is_open:
            self.connection.close()
        self.connection = None

    def send(self, cmd: str, read_response: bool = False, response_delay: float = 0.1) -> str:
        if not self.is_connected():
            return ""

        assert self.connection is not None
        line_ending = "\r\n" if self.device_type == DEVICE_GPP else "\n"
        self.connection.write((cmd + line_ending).encode("ascii"))

        if not read_response:
            return ""

        time.sleep(response_delay)
        return self.connection.readline().decode(errors="ignore").strip()

    def _validate_idn(self, idn: str) -> None:
        if self.device_type == DEVICE_GPP and "GW Instek" not in idn:
            raise ValueError(f"Invalid GPP device response: {idn}")
        if self.device_type == DEVICE_KEYSIGHT and "E3646A" not in idn and "Agilent" not in idn:
            raise ValueError(f"Invalid Keysight device response: {idn}")

