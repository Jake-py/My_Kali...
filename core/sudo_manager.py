import os
import subprocess
from PyQt6.QtCore import QObject, pyqtSignal

class SudoManager(QObject):
    sudo_state_changed = pyqtSignal(bool, str) # active (bool), message (str)

    def __init__(self):
        super().__init__()
        self._is_root = (os.geteuid() == 0)
        self._is_sudo_active = self._is_root
        self._sudo_password = ""

    @property
    def is_root(self) -> bool:
        return self._is_root

    @property
    def is_active(self) -> bool:
        return self._is_root or self._is_sudo_active

    @property
    def password(self) -> str:
        return self._sudo_password

    def authenticate(self, password: str) -> bool:
        if self._is_root:
            self._is_sudo_active = True
            self.sudo_state_changed.emit(True, "Запущен с правами Root")
            return True

        try:
            # Test password with sudo -S true
            proc = subprocess.Popen(
                ["sudo", "-S", "-k", "true"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            _, stderr = proc.communicate(input=password + "\n", timeout=5)
            if proc.returncode == 0:
                self._sudo_password = password
                self._is_sudo_active = True
                self.sudo_state_changed.emit(True, "Sudo успешно активирован")
                return True
            else:
                self._is_sudo_active = False
                self._sudo_password = ""
                err_msg = stderr.strip() if stderr else "Неверный пароль sudo"
                self.sudo_state_changed.emit(False, f"Ошибка авторизации: {err_msg}")
                return False
        except Exception as e:
            self._is_sudo_active = False
            self._sudo_password = ""
            self.sudo_state_changed.emit(False, f"Ошибка: {str(e)}")
            return False

    def deactivate(self):
        if not self._is_root:
            self._is_sudo_active = False
            self._sudo_password = ""
            # Reset sudo timestamp
            subprocess.run(["sudo", "-k"], capture_output=True)
            self.sudo_state_changed.emit(False, "Sudo деактивирован")

    def wrap_command(self, cmd_list: list, require_sudo: bool = False) -> list:
        """Wraps a command with sudo if sudo is active and required."""
        if require_sudo or self.is_active:
            if self._is_root:
                return cmd_list
            elif self._is_sudo_active and self._sudo_password:
                return ["sudo", "-S"] + cmd_list
        return cmd_list
