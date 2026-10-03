import http.client
import json
import threading

from aegislog.desktop import PAGE, create_server


def test_local_session_auth_source_analysis_reports_and_shutdown(tmp_path, monkeypatch):
    monkeypatch.setattr('aegislog.desktop.discover_sources', lambda: [{'label': 'System', 'status': 'readable'}])
    server = create_server(tmp_path / 'output', token='test-session-secret')
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    def request(method, route, data=None, token='test-session-secret', origin=None, host=None):
        conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
        headers = {'X-Aegis-Token': token}
        if origin:
            headers['Origin'] = origin
        if host:
            headers['Host'] = host
        conn.request(method, route, json.dumps(data or {}) if method == 'POST' else None, headers)
        response = conn.getresponse()
        status, body = response.status, response.read().decode()
        conn.close()
        return status, body
    try:
        assert request('GET', '/')[0] == 200
        assert request('POST', '/api/sources', token='wrong')[0] == 403
        assert request('POST', '/api/sources', origin='https://outside.example')[0] == 403
        assert request('GET', '/', host='outside.example')[0] == 403
        assert request('POST', '/api/sources')[0] == 200
        source = tmp_path / 'source.log'
        source.write_text('2026-10-03T00:00:00Z ERROR app: timeout token=secret-value\n')
        status, body = request('POST', '/api/analyze', {'path': str(source)})
        assert status == 200
        assert 'secret-value' not in body
        result = json.loads(body)
        summary = result['downloads']['Summary report']
        assert request('GET', summary)[0] == 403
        status, html = request('GET', summary + '?token=test-session-secret')
        assert status == 200 and '?token=test-session-secret' in html
        for path in (tmp_path / 'output').rglob('*.html'):
            assert 'test-session-secret' not in path.read_text()
        assert request('POST', '/api/analyze', {'path': str(tmp_path / 'missing')})[0] == 400
        assert request('POST', '/api/quit')[0] == 200
        thread.join(timeout=5)
        assert not thread.is_alive()
    finally:
        server.shutdown()
        server.server_close()


def test_accessible_offline_page_has_safe_evidence_rendering():
    assert 'aria-live="polite"' in PAGE and 'aria-pressed="false"' in PAGE
    assert 'textContent=item.evidence' in PAGE
    assert 'innerHTML' not in PAGE
    assert '<script src=' not in PAGE and '<link ' not in PAGE
    assert 'Extra large' in PAGE and 'Switch to analyst view' in PAGE
    assert 'Quit AegisLog' in PAGE
