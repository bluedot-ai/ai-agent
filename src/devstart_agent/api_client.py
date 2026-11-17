from urllib.parse import urlsplit
import httpx

class BackendError(Exception):
    def __init__(self, code, status=None):
        self.code, self.status = code, status
        super().__init__(code)

class ApiClient:
    def __init__(self, base_url, token, training_id, audit, transport=None):
        if type(training_id) is not int or training_id <= 0:
            raise ValueError("invalid training id")
        u = urlsplit(base_url)
        if u.scheme not in {"http", "https"} or not u.hostname or u.username or u.password or u.query or u.fragment or u.path not in {"", "/"}:
            raise ValueError("invalid backend origin")
        if u.scheme == "http" and u.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("remote backend requires HTTPS")
        self.training_id, self.audit = training_id, audit
        self._stages = set()
        self._http = httpx.AsyncClient(base_url=base_url.rstrip('/') + '/api/v1/',
            headers={"Authorization": "Bearer " + token}, timeout=httpx.Timeout(10),
            follow_redirects=False, transport=transport, trust_env=False)

    async def _get(self, path):
        try:
            async with self._http.stream("GET", path) as r:
                self.audit.record("http", http_status=r.status_code)
                if r.status_code != 200:
                    raise BackendError({401:"TOKEN_EXPIRED_OR_INVALID",403:"PERMISSION_DENIED"}.get(r.status_code,"BACKEND_HTTP_ERROR"), r.status_code)
                data = bytearray()
                async for chunk in r.aiter_bytes():
                    data.extend(chunk)
                    if len(data) > 262144:
                        raise BackendError("RESPONSE_TOO_LARGE")
                import json
                body = json.loads(data)
                if body.get("success") is not True:
                    raise BackendError("BACKEND_ERROR")
                return body["data"]
        except httpx.TimeoutException:
            raise BackendError("BACKEND_TIMEOUT") from None
        except httpx.HTTPError:
            raise BackendError("BACKEND_UNAVAILABLE") from None
        except (ValueError, KeyError, TypeError):
            raise BackendError("BACKEND_SCHEMA_ERROR") from None

    async def me(self): return await self._get("users/me")
    async def training(self): return await self._get(f"trainings/{self.training_id}")
    async def stages(self):
        rows = await self._get(f"trainings/{self.training_id}/stages")
        if any(r["training_id"] != self.training_id for r in rows):
            raise BackendError("SCOPE_MISMATCH")
        self._stages = {r["id"] for r in rows}
        return rows
    async def stage(self, sid):
        if type(sid) is not int or sid not in self._stages:
            raise BackendError("SCOPE_MISMATCH")
        r = await self._get(f"stages/{sid}")
        if r["training_id"] != self.training_id or r["id"] != sid:
            raise BackendError("SCOPE_MISMATCH")
        return r
    async def challenges(self): return await self._get("challenges")
    async def close(self): await self._http.aclose()
