import requests
import time
import re
from typing import Dict, Any

class LeakCheckAdapter:
    """
    Adapter for LeakCheck Public API (https://leakcheck.io/api/public)
    Fetches leak metadata (found count, compromised field types, leak sources)
    without exposing target parameters or requiring API keys.
    """
    BASE_URL = "https://leakcheck.io/api/public"
    RATE_LIMIT_SEC = 1.0  # 1 request per second max
    TIMEOUT_SEC = 10.0
    _last_call_time = 0.0

    HIGH_RISK_FIELDS = {
        "password", "pass", "hash", "ssn", "credit_card", "card", 
        "pin", "secret", "cvv", "dob", "birthdate"
    }

    def validate_query(self, query: str) -> tuple[bool, str]:
        """Validates target string before network request."""
        if not query:
            return False, "Запрос не может быть пустым"
        
        q = query.strip()
        
        # Email check
        if "@" in q:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', q):
                return False, "Некорректный формат Email адреса"
            return True, "email"

        # SHA256 Hash check (24 or 64 hex chars)
        if re.match(r'^[a-fA-F0-9]{24,64}$', q):
            return True, "hash"

        # Username check (min 3 chars)
        if len(q) < 3:
            return False, "Имя пользователя должно содержать минимум 3 символа"

        return True, "username"

    def run(self, query: str) -> Dict[str, Any]:
        """Executes LeakCheck query with rate limiting and error handling."""
        q = query.strip()
        is_valid, query_type_or_err = self.validate_query(q)
        
        if not is_valid:
            return {
                "status": "error",
                "raw_output": None,
                "parsed_data": None,
                "error": f"Ошибка клиентской валидации: {query_type_or_err}"
            }

        # Enforce Rate Limit (1 req/sec)
        elapsed = time.time() - LeakCheckAdapter._last_call_time
        if elapsed < self.RATE_LIMIT_SEC:
            time.sleep(self.RATE_LIMIT_SEC - elapsed)

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Kali OSINT Suite; Linux Debian x86_64)"
            }
            resp = requests.get(
                self.BASE_URL,
                params={"check": q},
                headers=headers,
                timeout=self.TIMEOUT_SEC
            )
            LeakCheckAdapter._last_call_time = time.time()

            if resp.status_code == 429:
                return {
                    "status": "error",
                    "raw_output": None,
                    "parsed_data": None,
                    "error": "Превышен лимит запросов (Rate Limit 1req/sec)."
                }

            resp.raise_for_status()
            data = resp.json()

        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "raw_output": None,
                "parsed_data": None,
                "error": "Превышено время ожидания ответа от сервиса LeakCheck (Timeout)."
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "raw_output": None,
                "parsed_data": None,
                "error": "Ошибка подключения к сети. Проверьте соединение с интернетом."
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "raw_output": None,
                "parsed_data": None,
                "error": f"Сетевая ошибка HTTP: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "raw_output": None,
                "parsed_data": None,
                "error": f"Ошибка обработки ответа JSON: {str(e)}"
            }

        # Handle 'Not found' or success=False correctly (Rule #6)
        if not data.get("success"):
            err_msg = str(data.get("error", "")).lower()
            if "not found" in err_msg or data.get("found", 0) == 0:
                return {
                    "status": "ok",
                    "raw_output": data,
                    "parsed_data": {
                        "found_count": 0,
                        "exposed_fields": [],
                        "critical_fields": [],
                        "sources": [],
                        "is_clean": True,
                        "query_type": query_type_or_err
                    },
                    "error": None
                }
            return {
                "status": "error",
                "raw_output": data,
                "parsed_data": None,
                "error": f"API LeakCheck вернул ошибку: {data.get('error', 'success=false')}"
            }

        fields = data.get("fields", [])
        critical = [f for f in fields if f.lower() in self.HIGH_RISK_FIELDS]
        found_cnt = data.get("found", len(data.get("sources", [])))

        return {
            "status": "ok",
            "raw_output": data,
            "parsed_data": {
                "found_count": found_cnt,
                "exposed_fields": fields,
                "critical_fields": critical,
                "sources": data.get("sources", []),
                "is_clean": (found_cnt == 0),
                "query_type": query_type_or_err
            },
            "error": None
        }

leakcheck_adapter = LeakCheckAdapter()
