"""Verify an explicitly reviewed GitHub release identity and its downloaded bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


def stream_digest(stream):
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        digest.update(chunk)
    return 'sha256:' + digest.hexdigest()


def file_digest(path):
    with Path(path).open('rb') as stream:
        return stream_digest(stream)


def validate_identity(manifest, release, *, require_draft=True):
    tag = manifest.get('tag', '')
    if not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+', tag):
        raise ValueError('Invalid reviewed release tag')
    if not re.fullmatch(r'[a-f0-9]{40}', manifest.get('commit', '')):
        raise ValueError('Invalid reviewed build commit')
    version = tag[1:]
    names = {'AegisLog.exe', 'AegisLog.exe.sha256', f'AegisLog-{tag}-Windows.zip',
             f'AegisLog-{tag}-Windows.zip.sha256', f'aegislog_ai-{version}-py3-none-any.whl',
             f'aegislog_ai-{version}.tar.gz', 'SHA256SUMS'}
    expected = manifest.get('assets', {})
    if set(expected) != names or any(not re.fullmatch(r'sha256:[a-f0-9]{64}', d) for d in expected.values()):
        raise ValueError('Invalid reviewed seven-asset digest manifest')
    if release.get('id') != manifest.get('release_id') or release.get('tag_name') != tag:
        raise ValueError('Release identity differs from reviewed draft')
    if release.get('target_commitish') != manifest['commit']:
        raise ValueError('Release build commit changed')
    if require_draft and release.get('draft') is not True:
        raise ValueError('Expected an unpublished reviewed draft')
    if 'unsigned' not in release.get('body', '').lower():
        raise ValueError('Unsigned executable disclosure missing')
    assets = release.get('assets', [])
    if len(assets) != len(names) or {a['name']: a.get('digest') for a in assets} != expected:
        raise ValueError('Reviewed release assets changed')
    return tag


def validate_bytes(manifest, directory):
    root = Path(directory)
    for name, expected in manifest['assets'].items():
        path = root / name
        if path.is_symlink() or not path.is_file() or file_digest(path) != expected:
            raise ValueError(f'Release bytes do not match reviewed digest: {name}')
    with zipfile.ZipFile(root / f"AegisLog-{manifest['tag']}-Windows.zip") as archive:
        item = archive.getinfo('dist/AegisLog.exe')
        if item.file_size > 256 * 1024 * 1024:
            raise ValueError('Unexpected executable size')
        with archive.open(item) as stream:
            digest = stream_digest(stream)
        if digest != manifest['assets']['AegisLog.exe']:
            raise ValueError('Bundled executable differs from standalone executable')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest', type=Path)
    parser.add_argument('release', type=Path)
    parser.add_argument('--directory', type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    release = json.loads(args.release.read_text())
    validate_identity(manifest, release)
    if args.directory:
        validate_bytes(manifest, args.directory)
    print('Reviewed release identity, asset digests and requested bytes verified')


if __name__ == '__main__':
    main()
