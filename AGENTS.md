# Agent instructions

Read `docs/CONTEXT.md`, `docs/LOCAL-INTEGRATION.md`, and `docs/SECURITY.md` before changing integration behavior. If `.local/workstation.md` exists, read it for private machine-specific context. Never commit `.local/`.

## Scope and preferences

- This repo is the user's local ASCII screensaver workshop and implementation handoff. Prioritize running, reviewable changes and clear install/uninstall behavior.
- The existing upstream draft covers ASCII file/directory sources. Image slideshows and live animated desktop backgrounds are separate work. Do not merge or change the upstream PR as a side effect of work here.
- Do not upload or attach recordings or screenshots anywhere without explicit user approval. This restriction includes Git commits, PRs, issues, releases, and external hosting. A request to publish source code is not approval to publish visual evidence.
- Preserve artwork licensing and attribution. Never assume the project's MIT license covers downloaded portraits or their ASCII conversions. Original sample art in `examples/` is MIT.
- Do not request confirmation for ordinary authorized local development or repeat permissions already granted. Production desktop changes require task context authorizing them; this seed task did not install persistent integration.

## Omarchy integration

- Use the installed Omarchy skill before desktop/config changes when available. Read current packaged scripts to verify compatibility; the reference snapshot is historical, not a system override.
- Never edit `/usr/share/omarchy/` for end-user customization. Use an isolated development checkout or a documented user-owned integration point.
- Do not silently shadow system commands in PATH. Native integration must be deliberate, reversible, and verified through the actual launcher environment.
- Keep lock timing intact. Distinguish playback failure from user dismissal. Do not broaden process termination beyond owned child PIDs.
- Never execute collection entries or load QML, scripts, config, or URLs from an artwork directory.

## Work and verification

- Use argument arrays, bounded descriptor-based reads, temporary private snapshots, and cleanup on exit. Preserve the protections in the reference preparer.
- Run `python3 -m unittest discover -s tests -v` and the reference collection regression test after relevant changes. Tests must not reach the real compositor, branding, or user processes.
- Verify visual changes locally in an isolated preview. Automated tests do not establish live lock or multi-monitor behavior. Keep evidence local unless the user approves publication.
- Prefer small changes. Keep `reference/` pinned; implement improvements outside it or explicitly update provenance and the corresponding tests.
- Update handoff docs when behavior or outstanding work changes. State limitations without claiming unperformed tests passed.
