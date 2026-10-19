import copy
import json
import math
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple, cast
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 1024 * 1024  # 1 MB


def is_valid_url(url: Any) -> bool:
    if not isinstance(url, str):
        return False
    u = url.strip()
    return u.startswith("http://") or u.startswith("https://") or u.startswith("file://")


def _urls_match(u1: Any, u2: Any) -> bool:
    if not isinstance(u1, str) or not isinstance(u2, str):
        return False
    if not u1 or not u2:
        return False
    try:
        p1 = urlparse(u1)
        p2 = urlparse(u2)
        if p1.scheme.lower() != p2.scheme.lower():
            return False
        if p1.netloc.lower() != p2.netloc.lower():
            return False
        # Preserve path trailing slashes!
        if p1.path != p2.path:
            return False
        # Preserve query string differences!
        if p1.query != p2.query:
            return False
        return True
    except Exception:
        return False


def _forbid_json_constants(c: str) -> None:
    raise ValueError("Disallowed JSON constant: " + str(c))


def _check_json_depth(obj: Any, max_depth: int = 10, current_depth: int = 0) -> bool:
    if current_depth > max_depth:
        return False
    if isinstance(obj, dict):
        mapping = cast(Dict[Any, Any], obj)
        for v in mapping.values():
            if not _check_json_depth(v, max_depth, current_depth + 1):
                return False
    elif isinstance(obj, (list, tuple)):
        seq = cast(List[Any], obj)
        for item in seq:
            if not _check_json_depth(item, max_depth, current_depth + 1):
                return False
    return True


BINDING_FIELDS = (
    "actual_tab_id",
    "actual_frame_id",
    "actual_document_id",
    "document_instance_nonce",
    "document_url",
    "document_time_origin_ms",
    "witnessed_at_ms",
)


def _finite_number(value: Any) -> bool:
    return type(value) in (int, float) and abs(value) <= 1e16 and math.isfinite(value)


def _valid_binding(data: Dict[str, Any], req: "BridgeRequest") -> bool:
    return (
        type(data.get("actual_tab_id")) is int
        and data["actual_tab_id"] >= 0
        and type(data.get("actual_frame_id")) is int
        and data["actual_frame_id"] == 0
        and all(
            isinstance(data.get(key), str) and 0 < len(data[key]) <= 256
            for key in ("actual_document_id", "document_instance_nonce")
        )
        and _urls_match(data.get("document_url"), req.expected_url)
        and all(
            _finite_number(data.get(key)) and 0 < data[key] <= req.captured_at_ms
            for key in ("document_time_origin_ms", "witnessed_at_ms")
        )
    )


def _bounded_json(value: Any, depth: int = 0) -> bool:
    if depth > 10:
        return False
    if value is None or isinstance(value, (str, bool)):
        return not isinstance(value, str) or len(value) <= 20000
    if type(value) in (int, float):
        return _finite_number(value)
    if isinstance(value, list):
        sequence = cast(List[Any], value)
        return len(sequence) <= 256 and all(_bounded_json(v, depth + 1) for v in sequence)
    if isinstance(value, dict):
        mapping = cast(Dict[Any, Any], value)
        return len(mapping) <= 256 and all(
            isinstance(k, str) and len(k) <= 256 and _bounded_json(v, depth + 1) for k, v in mapping.items()
        )
    return False


class BridgeRequest:
    def __init__(
        self,
        request_id: str,
        target_info: Optional[Dict[str, Any]] = None,
        expected_url: Optional[str] = None,
        deadline: float = 2.0,
        captured_at_ms: Optional[float] = None,
    ) -> None:
        super().__init__()
        self.request_id: str = str(request_id)
        self.target_info: Dict[str, Any] = copy.deepcopy(target_info) if target_info is not None else {}
        self.expected_url: Optional[str] = expected_url
        self.captured_at_ms = captured_at_ms if captured_at_ms is not None else time.time() * 1000
        self.binding: Optional[Dict[str, Any]] = None
        self.created_at: float = time.monotonic()
        self.deadline: float = self.created_at + float(deadline)
        self.status: str = "pending"  # pending, claimed, completed, cancelled, expired, error
        self.event: threading.Event = threading.Event()
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.cancellation_reason: Optional[str] = None

    def is_expired(self, now: Optional[float] = None) -> bool:
        t = now if now is not None else time.monotonic()
        return t > self.deadline

    def complete(self, data: Dict[str, Any]) -> None:
        self.result = data
        self.status = "completed"
        self.event.set()

    def fail(self, error: str) -> None:
        self.error = error
        self.status = "error"
        self.event.set()

    def cancel(self, reason: str = "cancelled") -> None:
        self.status = "cancelled"
        self.cancellation_reason = reason
        self.event.set()


class BridgeLifecycleManager:
    def __init__(self) -> None:
        super().__init__()
        self._lock: threading.Lock = threading.Lock()
        self._poll_condition: threading.Condition = threading.Condition(self._lock)
        self._active_request: Optional[BridgeRequest] = None
        self._requests: Dict[str, BridgeRequest] = {}
        self._latest_dom_data: Dict[str, Any] = {}

    def _evict_stale_locked(self, now: Optional[float] = None) -> None:
        t = now if now is not None else time.monotonic()
        to_del: List[str] = []
        for req_id, r in self._requests.items():
            if r is self._active_request:
                continue
            is_finished = r.status in ("completed", "cancelled", "error")
            is_expired = r.is_expired(t)
            if (is_finished and (t - r.created_at > 5.0)) or (is_expired and (t - r.deadline > 5.0)):
                to_del.append(req_id)
        for req_id in to_del:
            _ = self._requests.pop(req_id, None)
        if len(self._requests) > 20:
            excess = len(self._requests) - 20
            for req_id in list(self._requests.keys())[:excess]:
                if self._requests[req_id] is not self._active_request:
                    _ = self._requests.pop(req_id, None)

    def create_request(
        self,
        request_id: str,
        target_info: Optional[Dict[str, Any]] = None,
        expected_url: Optional[str] = None,
        deadline: float = 2.0,
        captured_at_ms: Optional[float] = None,
    ) -> Optional[BridgeRequest]:
        if not is_valid_url(expected_url):
            logger.debug("Native fallback: expected document URL unavailable")
            return None
        with self._lock:
            self._evict_stale_locked()
            if self._active_request is not None and self._active_request.status in (
                "pending",
                "claimed",
                "bound",
            ):
                self._active_request.cancel(reason="superseded")

            req = BridgeRequest(
                request_id=request_id,
                target_info=target_info,
                expected_url=expected_url,
                deadline=deadline,
                captured_at_ms=captured_at_ms,
            )
            self._active_request = req
            self._requests[req.request_id] = req
            self._poll_condition.notify_all()
            return req

    def get_active_request(self) -> Optional[BridgeRequest]:
        with self._lock:
            return self._active_request

    def cancel_active_request(self, reason: str = "cancelled") -> Optional[BridgeRequest]:
        with self._lock:
            self._evict_stale_locked()
            if self._active_request is not None and self._active_request.status in (
                "pending",
                "claimed",
                "bound",
            ):
                self._active_request.cancel(reason=reason)
                req = self._active_request
                self._active_request = None
                return req
            return None

    def cancel_request_by_id(self, request_id: str, reason: str = "cancelled") -> Optional[BridgeRequest]:
        with self._lock:
            self._evict_stale_locked()
            req = self._requests.get(request_id)
            if req is not None and req.status in ("pending", "claimed", "bound"):
                req.cancel(reason=reason)
                if self._active_request is req:
                    self._active_request = None
                return req
            return None

    def poll_claim(self, timeout: float = 10.0) -> Dict[str, Any]:
        with self._lock:
            self._evict_stale_locked()
            end_time = time.monotonic() + timeout
            while True:
                now = time.monotonic()
                if self._active_request is not None:
                    if self._active_request.status == "pending":
                        if self._active_request.is_expired(now):
                            self._active_request.status = "expired"
                            self._active_request.event.set()
                            self._active_request = None
                        else:
                            req = self._active_request
                            req.status = "claimed"
                            return {
                                "action": "get_dom",
                                "request_id": req.request_id,
                                "target": req.target_info,
                                "expected_url": req.expected_url,
                                "captured_at_ms": req.captured_at_ms,
                                "deadline_ms": time.time() * 1000 + (req.deadline - now) * 1000,
                            }
                remaining = end_time - now
                if remaining <= 0:
                    return {"action": "none"}
                _ = self._poll_condition.wait(timeout=min(remaining, 0.5))

    def bind_request(self, data: Any) -> Tuple[bool, int, str]:
        with self._lock:
            if not isinstance(data, dict):
                return False, 400, "Invalid binding"
            envelope = cast(Dict[str, Any], data)
            request_id = envelope.get("request_id")
            if not isinstance(request_id, str):
                return False, 400, "Invalid binding"
            req = self._requests.get(request_id)
            if req is None or req.status not in ("claimed", "bound"):
                return False, 409, "Request is not awaiting binding"
            if req.is_expired():
                req.fail("deadline_expired")
                return False, 408, "Request expired"
            if not _valid_binding(envelope, req):
                req.fail("unverified_document")
                return False, 400, "Invalid document binding"
            binding = {key: envelope[key] for key in BINDING_FIELDS}
            if req.binding is not None and req.binding != binding:
                req.fail("document_changed")
                return False, 409, "Document binding changed"
            req.binding = binding
            req.status = "bound"
            return True, 200, "Bound"

    def handle_update(self, data: Any) -> Tuple[bool, int, str]:
        with self._lock:
            self._evict_stale_locked()
            if not isinstance(data, dict):
                return False, 400, "Invalid envelope"
            envelope = cast(Dict[str, Any], data)
            request_id = envelope.get("request_id")
            if not isinstance(request_id, str):
                return False, 400, "Invalid envelope"
            req = self._requests.get(request_id)
            if req is None:
                return False, 400, "Unknown request"
            if req.status not in ("claimed", "bound"):
                return False, 409, "Request is not awaiting a result"
            if req.is_expired():
                req.fail("deadline_expired")
                return False, 408, "Request expired"
            error = envelope.get("error")
            if isinstance(error, str) and 0 < len(error) <= 256:
                req.fail("bridge_unavailable")
                if self._active_request is req:
                    self._active_request = None
                return True, 200, "Native fallback"
            raw_payload = envelope.get("result")
            payload = cast(Dict[str, Any], raw_payload) if isinstance(raw_payload, dict) else {}
            valid = (
                req.status == "bound"
                and req.binding is not None
                and _valid_binding(envelope, req)
                and all(envelope.get(key) == req.binding[key] for key in BINDING_FIELDS)
                and envelope.get("connected_target") is True
                and isinstance(raw_payload, dict)
                and _bounded_json(payload)
                and payload.get("request_id") == req.request_id
                and _urls_match(payload.get("document_url"), req.expected_url)
                and payload.get("documentNonce") == req.binding["document_instance_nonce"]
                and type(payload.get("frame_id")) is int
                and payload["frame_id"] == 0
                and payload.get("is_top_frame") is True
                and payload.get("isConnected") is True
                and isinstance(payload.get("tag"), str)
                and 0 < len(payload["tag"]) <= 32
                and (not req.target_info.get("id") or payload.get("id") == req.target_info["id"])
                and (not req.target_info.get("tag") or payload["tag"] == req.target_info["tag"])
            )
            if not valid:
                req.fail("unverified_result")
                if self._active_request is req:
                    self._active_request = None
                return False, 400, "Unverified result"
            frozen = copy.deepcopy(payload)
            frozen["_bridge_binding"] = dict(cast(Dict[str, Any], req.binding))
            req.complete(frozen)
            self._latest_dom_data = copy.deepcopy(frozen)
            if self._active_request is req:
                self._active_request = None
            return True, 200, "OK"

    def wait_for_request(
        self, req: BridgeRequest, timeout: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        if timeout is None:
            remaining = req.deadline - time.monotonic()
            wait_time = max(0.0, remaining)
        else:
            wait_time = float(timeout)

        _ = req.event.wait(timeout=wait_time)
        with self._lock:
            if req.status == "completed":
                return req.result
            if req.status in ("pending", "claimed", "bound"):
                if req.is_expired():
                    req.status = "expired"
                    req.event.set()
                    if self._active_request is req:
                        self._active_request = None
            return None

    def get_latest_dom_data(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._latest_dom_data)

    def clear(self) -> None:
        with self._lock:
            if self._active_request is not None and self._active_request.status in (
                "pending",
                "claimed",
                "bound",
            ):
                self._active_request.cancel(reason="cleared")
            self._active_request = None
            self._requests.clear()
            self._latest_dom_data.clear()


_manager = BridgeLifecycleManager()
_server_instance: Optional[ThreadingHTTPServer] = None
_server_lock = threading.Lock()


try:
    from typing_extensions import override  # type: ignore[attr-defined]
except Exception:

    def override(fn: Any) -> Any:
        return fn


class BridgeRequestHandler(BaseHTTPRequestHandler):
    @override
    def setup(self) -> None:
        super().setup()
        try:
            self.request.settimeout(5.0)
        except Exception:
            pass

    def _originIsAllowed(self) -> bool:
        origin = self.headers.get("Origin")
        return not origin or origin.startswith("chrome-extension://")

    def _sendCorsHeaders(self) -> None:
        origin = self.headers.get("Origin")
        if origin and origin.startswith("chrome-extension://"):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        if self.headers.get("Access-Control-Request-Private-Network") == "true":
            self.send_header("Access-Control-Allow-Private-Network", "true")

    def _rejectDisallowedOrigin(self) -> bool:
        if self._originIsAllowed():
            return False
        self.send_response(403)
        self.end_headers()
        return True

    def do_OPTIONS(self) -> None:
        if self._rejectDisallowedOrigin():
            return
        self.send_response(200)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self._sendCorsHeaders()
        self.end_headers()

    def do_GET(self) -> None:
        if self._rejectDisallowedOrigin():
            return
        if self.path == "/poll":
            response_data = _manager.poll_claim(timeout=10.0)
            try:
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self._sendCorsHeaders()
                self.end_headers()
                _ = self.wfile.write(json.dumps(response_data).encode("utf-8"))
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                pass
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        if self._rejectDisallowedOrigin():
            return
        if self.path in ("/bind", "/update"):
            raw_len = self.headers.get("Content-Length", 0)
            try:
                content_length = int(raw_len)
            except (ValueError, TypeError):
                content_length = 0

            if content_length > MAX_CONTENT_LENGTH:
                self.send_response(413)
                self.end_headers()
                return

            if content_length <= 0:
                self.send_response(400)
                self.end_headers()
                return

            try:
                body = self.rfile.read(content_length)
                data = json.loads(
                    body.decode("utf-8"),
                    parse_constant=_forbid_json_constants,
                )
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            if not _check_json_depth(data, max_depth=10):
                self.send_response(400)
                self.end_headers()
                return

            handler = _manager.bind_request if self.path == "/bind" else _manager.handle_update
            _, code, _ = handler(data)
            self.send_response(code)
            self._sendCorsHeaders()
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    @override
    def log_message(self, format: str, *args: Any) -> None:
        pass


def run_server() -> None:
    server_address = ("127.0.0.1", 63333)
    httpd = ThreadingHTTPServer(server_address, BridgeRequestHandler)
    logger.info("HTTP long-polling server started at 127.0.0.1:63333.")
    httpd.serve_forever()


def start_server_in_background() -> None:
    global _server_instance
    with _server_lock:
        if _server_instance is not None:
            return
        server_address = ("127.0.0.1", 63333)
        try:
            httpd = ThreadingHTTPServer(server_address, BridgeRequestHandler)
            _server_instance = httpd
            server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            server_thread.start()
        except Exception as e:
            logger.error("Could not start bridge server: %s", e)


def stop_server() -> None:
    global _server_instance
    _ = _manager.cancel_active_request(reason="server_shutdown")
    with _server_lock:
        if _server_instance is not None:
            try:
                _server_instance.shutdown()
                _server_instance.server_close()
            except Exception:
                pass
            _server_instance = None


def create_bridge_request(
    request_id: str,
    target_info: Optional[Dict[str, Any]] = None,
    expected_url: Optional[str] = None,
    deadline: float = 2.0,
    captured_at_ms: Optional[float] = None,
) -> Optional[BridgeRequest]:
    return _manager.create_request(
        request_id=request_id,
        target_info=target_info,
        expected_url=expected_url,
        deadline=deadline,
        captured_at_ms=captured_at_ms,
    )


def wait_for_request(req: BridgeRequest, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
    return _manager.wait_for_request(req, timeout=timeout)


def cancel_active_request(reason: str = "cancelled") -> Optional[BridgeRequest]:
    return _manager.cancel_active_request(reason=reason)


def cancel_request_by_id(request_id: str, reason: str = "cancelled") -> Optional[BridgeRequest]:
    return _manager.cancel_request_by_id(request_id, reason=reason)


def get_latest_dom_data() -> Dict[str, Any]:
    return _manager.get_latest_dom_data()


def request_dom_data_from_clients(
    target_info: Optional[Dict[str, Any]] = None,
    expected_url: Optional[str] = None,
) -> Optional[BridgeRequest]:
    import uuid

    req_id = str(uuid.uuid4())
    return create_bridge_request(req_id, target_info, expected_url=expected_url)


def get_ai_analysis() -> str:
    dom_data = _manager.get_latest_dom_data()
    if not dom_data:
        try:
            return _(  # type: ignore[name-defined]
                "No DOM data has been received from the Chrome extension yet."
            )
        except Exception:
            return "No DOM data has been received from the Chrome extension yet."

    from . import ai_handler

    dom_text = json.dumps(dom_data, indent=2, ensure_ascii=False)
    ai_mod = cast(Any, ai_handler)
    res: Any = ai_mod.analyze_dom_with_gemini(dom_text)
    return str(res)


if __name__ == "__main__":
    run_server()
