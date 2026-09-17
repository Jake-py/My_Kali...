import time
from PyQt6.QtCore import QObject, pyqtSignal
from core.leakcheck_adapter import leakcheck_adapter

class LeakCheckWorker(QObject):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int, float)

    def __init__(self, query: str):
        super().__init__()
        self.query = query

    def run(self):
        start_time = time.time()
        self.output_signal.emit(f"[+] Инициализация запроса LeakCheck Public API для: {self.query}\n")
        self.output_signal.emit("[i] Ограничение скорости: 1 запрос в секунду (Rate-Limit Enforced)\n")

        res = leakcheck_adapter.run(self.query)
        duration = time.time() - start_time

        if res["status"] == "error":
            self.output_signal.emit(f"\n[!] ОШИБКА: {res['error']}\n")
            self.finished_signal.emit(1, duration)
            return

        parsed = res.get("parsed_data", {})
        if parsed.get("is_clean"):
            self.output_signal.emit("\n========================================================\n")
            self.output_signal.emit(f"✅ ОТЛИЧНАЯ НОВОСТЬ: Утечек для цели '{self.query}' не найдено!\n")
            self.output_signal.emit("Идентификатор не зафиксирован ни в одной известной базе данных.\n")
            self.output_signal.emit("========================================================\n")
            self.finished_signal.emit(0, duration)
            return

        found_cnt = parsed.get("found_count", 0)
        fields = parsed.get("exposed_fields", [])
        critical = parsed.get("critical_fields", [])
        sources = parsed.get("sources", [])

        self.output_signal.emit("\n========================================================\n")
        self.output_signal.emit(f"⚠️ ОБНАРУЖЕНЫ УТЕЧКИ! Цель: {self.query}\n")
        self.output_signal.emit(f"📊 Всего скомпрометировано в базах: {found_cnt} раз(а)\n")
        self.output_signal.emit("========================================================\n\n")

        # Highlight Critical Fields in RED
        if critical:
            self.output_signal.emit("🚨 КРИТИЧЕСКИЕ СКОМПРОМЕТИРОВАННЫЕ ДАННЫЕ:\n")
            for crit in critical:
                self.output_signal.emit(f"  ❌ {crit.upper()} — Пароли / Секреты попали в утечку!\n")
            self.output_signal.emit("\n")

        if fields:
            self.output_signal.emit(f"📋 Категории раскрытых полей ({len(fields)}): {', '.join(fields)}\n\n")

        if sources:
            self.output_signal.emit(f"📁 Источники и базы утечек (показано {min(len(sources), 300)} из {len(sources)}):\n")
            for idx, src in enumerate(sources[:300], 1):
                name = src.get("name", "Неизвестный источник")
                dt = src.get("date", "Дата не указана")
                dt_str = f"[{dt}]" if dt else "[Без даты]"
                self.output_signal.emit(f"  {idx:03d}. {name:<35} {dt_str}\n")

            if len(sources) > 300:
                self.output_signal.emit(f"\n[i] ... и еще {len(sources) - 300} источников скомпрометированы.\n")

        self.output_signal.emit("\n--------------------------------------------------------\n")
        self.output_signal.emit("ℹ️ Данные предоставлены LeakCheck Public API (Powered by LeakCheck)\n")
        self.output_signal.emit("--------------------------------------------------------\n")

        self.finished_signal.emit(0, duration)
