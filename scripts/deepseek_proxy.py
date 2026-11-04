"""Identify this capture proxy without forwarding credentials or making an API call."""

from mitmproxy import http


def request(flow: http.HTTPFlow) -> None:
    if flow.request.method == "GET" and flow.request.path == "/_cs146s/upstream":
        expected = flow.server_conn.address == ("api.deepseek.com", 443)
        flow.response = http.Response.make(
            200 if expected else 503,
            b"https://api.deepseek.com/anthropic" if expected else b"Unexpected upstream",
            {"Content-Type": "text/plain"},
        )
