import json

import pytest

from aegislog.sanitize import redact_sensitive


@pytest.mark.parametrize('key', ['api-key', 'apiKey', 'API KEY', 'client-secret', 'clientSecret',
                                'access-token', 'accessToken', 'refresh-token', 'refreshToken',
                                'set-cookie', 'SetCookie', ' PASSWORD '])
def test_nested_json_credential_key_variants_are_redacted(key):
    original = {'events': [{'details': {key: 'synthetic-private-value', 'status': 'accepted'}}]}
    result = json.loads(redact_sensitive(json.dumps(original)))
    assert result['events'][0]['details'][key] == '[REDACTED]'
    assert result['events'][0]['details']['status'] == 'accepted'
    assert original['events'][0]['details'][key] == 'synthetic-private-value'


def test_noncredential_keys_are_not_redacted_by_partial_match():
    original = {'token_count': 4, 'secretary': 'office', 'api_key_rotation_enabled': True}
    assert json.loads(redact_sensitive(json.dumps(original))) == original
