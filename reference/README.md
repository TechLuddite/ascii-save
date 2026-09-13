# Pinned upstream reference

`ascii-collections.patch` is the exact diff from Omarchy base `31bd80daa4613ffdee995ac27467fce5a2990806` to submitted commit `fce24d4ddac2a18c4361dd3adee8a411e5b705f9`, from [draft PR #11626](https://github.com/omacom/omarchy/pull/11626).

`omarchy/` contains the two renderer/preparation scripts, the focused collection tests and their base library, and the bundled fallback logo needed by those tests. Files were extracted directly from that commit. The upstream MIT notice is retained in `omarchy/LICENSE`.

These are reference files, not an installed replacement for Omarchy. The standalone tools invoke only the bounded preparation helper. Do not run the reference native renderer casually: it expects the Omarchy window class and retains upstream global process termination behavior. Use `scripts/preview.py` for experiments.

```bash
bash reference/omarchy/test/shell.d/screensaver-collection-test.sh
```

That test uses fake home directories and desktop/process stubs. It does not require or alter the running desktop. Applying the patch to another version requires checking compatibility; do not blindly copy it over packaged files.
