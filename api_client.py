import json
import threading
import httpx
import time


class APIError(Exception):

    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class APIClient:

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._client = httpx.Client(timeout=httpx.Timeout(timeout))
        self._closed = False

    def __del__(self):
        if not self._closed:
            try:
                self._client.close()
            except Exception:
                pass

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def list_models(self) -> list:
        try:
            url = self._build_url("models")
            resp = self._client.get(url, headers=self._headers(), timeout=15.0)
            if resp.status_code == 200:
                data = resp.json()
                models = []
                if isinstance(data, dict) and "data" in data:
                    models = [m.get("id", "") for m in data["data"] if isinstance(m, dict)]
                elif isinstance(data, list):
                    models = [m.get("id", "") if isinstance(m, dict) else str(m) for m in data]
                return [m for m in models if m]
            elif resp.status_code == 401:
                raise APIError("API Key 无效，请检查密钥", 401)
            else:
                raise APIError(f"获取模型列表失败: HTTP {resp.status_code}", resp.status_code)
        except httpx.TimeoutException:
            raise APIError("获取模型列表超时", 0)
        except httpx.ConnectError:
            raise APIError("无法连接到服务器", 0)
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"获取模型列表失败: {str(e)}")

    def test_connection(self) -> bool:
        try:
            url = self._build_url("models")
            resp = self._client.get(url, headers=self._headers(), timeout=15.0)
            if resp.status_code == 200:
                return True
            elif resp.status_code == 401:
                raise APIError("API Key 无效，请检查密钥", 401)
            elif resp.status_code == 404:
                return True
            else:
                raise APIError(f"连接失败: HTTP {resp.status_code}", resp.status_code)
        except httpx.TimeoutException:
            raise APIError("连接超时，请检查 Base URL 是否正确")
        except httpx.ConnectError:
            raise APIError("无法连接到服务器，请检查 Base URL")
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"连接测试失败: {str(e)}")

    def chat_completion(
        self,
        messages: list,
        model: str = None,
        temperature: float = 0.8,
        max_tokens: int = 4096,
        max_retries: int = 3,
        stop_event=None,
    ) -> str:
        url = self._build_url("chat/completions")
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_error = None
        for attempt in range(max_retries):
            try:
                if stop_event and stop_event.is_set():
                    raise APIError("用户停止生成", 0)

                resp = self._client.post(url, json=payload, headers=self._headers())
                if resp.status_code == 200:
                    if stop_event and stop_event.is_set():
                        raise APIError("用户停止生成", 0)
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                elif resp.status_code == 429:
                    wait = min(2**attempt, 30)
                    print(f"速率限制 (429)，等待 {wait}s 后重试...")
                    time.sleep(wait)
                    continue
                elif resp.status_code in (500, 502, 503):
                    wait = min(2**attempt, 15)
                    print(f"服务器错误 ({resp.status_code})，等待 {wait}s 后重试...")
                    time.sleep(wait)
                    continue
                else:
                    error_msg = f"API 错误 ({resp.status_code}): {resp.text[:500]}"
                    raise APIError(error_msg, resp.status_code)
            except APIError:
                raise
            except httpx.TimeoutException:
                last_error = "请求超时"
                if attempt < max_retries - 1:
                    print(f"请求超时，重试 {attempt + 2}/{max_retries}...")
                    time.sleep(1)
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    print(f"请求异常: {e}，重试 {attempt + 2}/{max_retries}...")
                    time.sleep(1)

        raise APIError(f"请求失败（已重试 {max_retries} 次）: {last_error}")

    def close(self):
        self._closed = True
        try:
            self._client.close()
        except Exception:
            pass

    def chat_completion_stream(
        self,
        messages: list,
        model: str = None,
        temperature: float = 0.8,
        max_tokens: int = 4096,
        max_retries: int = 3,
        stop_event=None,
    ):
        url = self._build_url("chat/completions")
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        last_error = None
        for attempt in range(max_retries):
            try:
                if stop_event and stop_event.is_set():
                    return

                with self._client.stream("POST", url, json=payload, headers=self._headers()) as resp:
                    if resp.status_code == 200:
                        if stop_event and stop_event.is_set():
                            return

                        if stop_event:
                            done_event = threading.Event()

                            def _abort_monitor():
                                stop_event.wait()
                                if not done_event.is_set():
                                    try:
                                        resp.close()
                                    except Exception:
                                        pass
                            abort_thread = threading.Thread(target=_abort_monitor, daemon=True)
                            abort_thread.start()

                        for line in resp.iter_lines():
                            if stop_event and stop_event.is_set():
                                break
                            if not line:
                                continue
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str == "[DONE]":
                                    break
                                try:
                                    data = json.loads(data_str)
                                except json.JSONDecodeError:
                                    continue
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content

                        if stop_event:
                            done_event.set()
                        return
                    elif resp.status_code == 429:
                        wait = min(2**attempt, 30)
                        print(f"速率限制 (429)，等待 {wait}s 后重试...")
                        time.sleep(wait)
                        continue
                    elif resp.status_code in (500, 502, 503):
                        wait = min(2**attempt, 15)
                        print(f"服务器错误 ({resp.status_code})，等待 {wait}s 后重试...")
                        time.sleep(wait)
                        continue
                    else:
                        error_msg = f"API 错误 ({resp.status_code}): {resp.text[:500]}"
                        raise APIError(error_msg, resp.status_code)
            except APIError:
                raise
            except httpx.TimeoutException:
                last_error = "请求超时"
                if attempt < max_retries - 1:
                    print(f"请求超时，重试 {attempt + 2}/{max_retries}...")
                    time.sleep(1)
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    print(f"请求异常: {e}，重试 {attempt + 2}/{max_retries}...")
                    time.sleep(1)

        raise APIError(f"请求失败（已重试 {max_retries} 次）: {last_error}")