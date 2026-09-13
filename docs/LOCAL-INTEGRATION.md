# Local integration plan

This is a plan for the next authorized implementation task, not an installer. The preview tools can be used now without changing the desktop.

1. Inspect the current Omarchy version, launcher, renderer, shell config, and PR status. Determine whether file/directory sources have already landed. Read the installed Omarchy skill for user configuration changes; follow upstream AGENTS.md for source development.
2. If upstream supports `screensaver.source`, use that support. Otherwise, reproduce the small source-selection change in an isolated Omarchy development checkout, starting from the pinned patch in `reference/`. Inspect `omarchy dev` help before choosing a development-link workflow. Do not overwrite package-managed scripts or assume a PATH shim will reach commands launched by the desktop shell.
3. Implement explicit installation and removal. Record exactly which files/settings are owned, save the original `screensaver.source` value (including whether it existed), and use atomic writes. Preserve unrelated `shell.json` fields and symlinked dotfiles. Repeated install and uninstall must be safe. If the user edits an owned setting after installation, removal must preserve it rather than blindly restoring an old whole-file backup.
4. Validate the collection before activating it. Test empty/missing directories, links, FIFOs, invalid UTF-8, terminal controls, oversized files, preparation timeout, and permission failures. Reading arbitrary image formats is not part of this ASCII task.
5. Prove the actual native launcher invokes the intended renderer. Verify manual preview, keyboard/mouse dismissal, cursor restoration, temporary cleanup, failures during preparation/playback, multiple monitors, and the automatic lock deadline. Use owned process IDs, not broad `pkill` patterns. The reference renderer retains upstream broad process matching; do not treat that as a security endorsement for a new launcher.
6. Exercise uninstall and verify stock behavior returns. Document how to return to the packaged Omarchy version if a development link was used. Do not mark native integration complete until these lifecycle checks pass.

## Proposed configuration once supported

Add this alongside the existing `idle`, `bar`, and other fields in `shell.json`:

```json
"screensaver": {
  "source": "~/Projects/ascii-save/collections/my-art"
}
```

Do not replace the entire config with this fragment. The setting controls content, while `idle.screensaver` and `idle.lock` remain timing settings. Existing installed Omarchy versions may ignore this setting until the code change is present.

## Development approach

Start with the included Giants collection or the small original observatory examples. Then convert user-selected local images into ignored `collections/` folders and inspect them. No background daemon, network watcher, theme installation, scheduled task, or publishing automation is needed to create a collection. Add those only if separately requested.
