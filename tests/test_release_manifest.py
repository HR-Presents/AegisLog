import copy
import hashlib
import importlib.util
import zipfile
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('release_manifest', Path(__file__).resolve().parents[1] / 'tools/verify_release_manifest.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture(tmp_path):
    tag, version = 'v2.1.12', '2.1.12'
    names = ['AegisLog.exe', 'AegisLog.exe.sha256', f'AegisLog-{tag}-Windows.zip',
             f'AegisLog-{tag}-Windows.zip.sha256', f'aegislog_ai-{version}-py3-none-any.whl',
             f'aegislog_ai-{version}.tar.gz', 'SHA256SUMS']
    for name in names:
        (tmp_path / name).write_bytes(b'synthetic-test-data')
    with zipfile.ZipFile(tmp_path / names[2], 'w') as archive:
        archive.writestr('dist/AegisLog.exe', b'synthetic-test-data')
    assets = {name: module.file_digest(tmp_path / name) for name in names}
    manifest = dict(tag=tag, commit='a' * 40, release_id=123, assets=assets)
    release = dict(id=123, tag_name=tag, target_commitish='a' * 40, draft=True, body='Unsigned test executable',
                   assets=[dict(name=name, digest=digest) for name, digest in assets.items()])
    return manifest, release


def test_reviewed_identity_and_download_bytes_match(tmp_path):
    manifest, release = fixture(tmp_path)
    assert module.validate_identity(manifest, release) == 'v2.1.12'
    module.validate_bytes(manifest, tmp_path)


@pytest.mark.parametrize('change', ['commit', 'asset', 'published', 'disclosure'])
def test_changed_draft_fails_closed(tmp_path, change):
    manifest, release = fixture(tmp_path)
    if change == 'commit':
        release['target_commitish'] = 'b' * 40
    elif change == 'asset':
        release['assets'][0]['digest'] = 'sha256:' + 'f' * 64
    elif change == 'published':
        release['draft'] = False
    else:
        release['body'] = 'No signing disclosure'
    with pytest.raises(ValueError):
        module.validate_identity(manifest, release)


def test_tampered_download_fails_closed(tmp_path):
    manifest, _ = fixture(tmp_path)
    (tmp_path / 'AegisLog.exe').write_bytes(b'different')
    with pytest.raises(ValueError, match='digest'):
        module.validate_bytes(manifest, tmp_path)


def test_zip_cannot_substitute_different_executable(tmp_path):
    manifest, _ = fixture(tmp_path)
    path = tmp_path / 'AegisLog-v2.1.12-Windows.zip'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('dist/AegisLog.exe', b'different')
    manifest = copy.deepcopy(manifest)
    manifest['assets'][path.name] = 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match='Bundled executable'):
        module.validate_bytes(manifest, tmp_path)
