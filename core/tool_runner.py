import subprocess
import threading
import os
import sys
import time
from PyQt6.QtCore import QObject, pyqtSignal

class CommandWorker(QObject):
    output_signal = pyqtSignal(str) # Emits line of stdout/stderr
    finished_signal = pyqtSignal(int, float) # exit_code, duration_sec
    error_signal = pyqtSignal(str)

    def __init__(self, cmd: list, sudo_password: str = ""):
        super().__init__()
        self.cmd = cmd
        self.sudo_password = sudo_password
        self._is_cancelled = False
        self._process = None

    def run(self):
        start_time = time.time()
        try:
            # Check if sudo password needed
            is_sudo_cmd = (len(self.cmd) >= 2 and self.cmd[0] == "sudo" and self.cmd[1] == "-S")
            
            self.output_signal.emit(f"[+] Запуск команды: {' '.join(self.cmd)}\n")

            self._process = subprocess.Popen(
                self.cmd,
                stdin=subprocess.PIPE if is_sudo_cmd else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            if is_sudo_cmd and self.sudo_password:
                try:
                    self._process.stdin.write(self.sudo_password + "\n")
                    self._process.stdin.flush()
                except Exception:
                    pass

            # Read stdout line by line
            for line in iter(self._process.stdout.readline, ''):
                if self._is_cancelled:
                    break
                if line:
                    # Filter out raw sudo password prompt line if present
                    if "[sudo] password for" in line:
                        continue
                    self.output_signal.emit(line)

            self._process.stdout.close()
            exit_code = self._process.wait()
            duration = time.time() - start_time

            if self._is_cancelled:
                self.output_signal.emit("\n[!] Процесс остановлен пользователем.\n")
                self.finished_signal.emit(-1, duration)
            else:
                self.output_signal.emit(f"\n[*] Завершено с кодом {exit_code} (Время: {duration:.2f} сек)\n")
                self.finished_signal.emit(exit_code, duration)

        except FileNotFoundError:
            self.output_signal.emit(f"\n[!] Ошибка: Исполняемый файл не найден ({self.cmd[0]}). Убедитесь, что инструмент установлен в Kali.\n")
            self.finished_signal.emit(127, 0.0)
        except Exception as e:
            self.output_signal.emit(f"\n[!] Критическая ошибка исполнения: {str(e)}\n")
            self.finished_signal.emit(1, 0.0)

    def cancel(self):
        self._is_cancelled = True
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass
