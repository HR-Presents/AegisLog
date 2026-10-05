# Install, upgrade, and uninstall

Use the published release wheel in an isolated pipx environment; see [installation](INSTALL.md#upgrade-and-verify) for setup and standalone executable upgrades.

```cmd
python -m pipx install --force "https://github.com/HR-Presents/AegisLog/releases/download/v2.1.7/aegislog_ai-2.1.7-py3-none-any.whl"
aegislog --version
python -m pipx uninstall aegislog-ai
```

Do not assume the PyPI package name resolves to this release. Verify 2.1.7 after installation. Exit AegisLog before upgrading, then regenerate reports to use the updated layout. Preserve old reports and original sources as needed.

Configuration, declarative rules, and investigation state are separate from the installed executable/package. Back up your configured state directory before major upgrades; uninstalling the package is not a request to delete local evidence. Inspect `aegislog doctor` for the configuration location. Do not erase it unless you intentionally want to remove local state.

The standalone executable does not update itself. Download the new copy and its matching checksum from the same release, verify the hash and run that copy. The executable is unsigned; checksums and build provenance are separate from publisher signing.
