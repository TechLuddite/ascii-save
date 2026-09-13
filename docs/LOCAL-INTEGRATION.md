# Native Giants integration

The current installer targets Omarchy with Lua Hyprland configuration and the compositor-dispatched stock screensaver launcher. It does not apply the separate upstream draft or edit package files.

Run `python3 scripts/install.py install` from the checkout. To remove it, close any active screensaver and run `python3 scripts/install.py uninstall`. Repeated installation/removal is safe; upgrade by uninstalling first. An edited managed configuration block causes removal to stop and preserve the installation for manual resolution.

## Owned files and activation

- `~/.local/share/ascii-save/`: stable renderer, pinned text preparer, validated refined Giants snapshot, artwork notices and code licenses.
- `~/.local/share/ascii-save/overrides/omarchy-screensaver`: the only overridden command, executing the installed Python renderer.
- `~/.local/state/ascii-save/`: original config backup and installed-file hashes. The backup remains after removal.
- `~/.config/hypr/hyprland.lua`: one marked block using `hl.env` to prepend the renderer directory, followed by the normal Omarchy command directory. Symlinked config targets are preserved. No shell startup file or system PATH file is changed.

Activation and removal run `hyprctl reload` and `hyprctl configerrors`; validation failure rolls the config back. Removal preserves edits outside the block and does not delete modified installed files. The stock launcher remains responsible for fullscreen terminals, monitor selection, and existing idle integration. Installation does not enable a previously disabled screensaver or change any timer.

## Playback and lifecycle

All 18 refined Giants entries play in filename order, wrapping after the wordmark. Each new terminal starts at the first entry. Effects finish before advancing; full-suite random selection can repeat effects. Braille dot resampling fits portraits to the available terminal cells. Oversized non-braille text uses the OMARCHY fallback instead of clipping. This native installer currently selects Giants; arbitrary collections remain supported by the separate preview CLI.

The preparer makes a private validated snapshot. Preparation failures fall back to safe built-in text. Animation failures retry with a delay while keeping the terminal open: the current idle service interprets the disappearance of all screensaver windows as dismissal, so a failure must not accidentally cancel a pending lock.

Keyboard input, mouse movement after a two-second launch grace period, and confirmed focus departure dismiss playback. Compositor query errors do not count as input. Private Unix datagrams coordinate dismissal across renderer windows; each renderer terminates and reaps only its own animation child. No global process-name matching is used. If private IPC cannot initialize, dismissal coordination is unavailable; local input/focus and normal Omarchy lock-window cleanup still apply.

Transient status records and sockets live in `$XDG_RUNTIME_DIR/ascii-save` (owner-only directory) and are removed on normal exit. Status includes the zero-based playback sequence, prepared artwork ordinal, count, and terminal dimensions. It contains no artwork content. Stock Omarchy's separate lock command retains its own existing process cleanup behavior.

## Verification on 2026-09-13

Automated tests cover every Giants fit, real PTY playback through an entire wrap with a mocked compositor/effects engine, failure survival, input dismissal, unrelated process survival, snapshot cleanup, symlinked config installation, repeated operations, preservation of user edits, and config-validation rollback. The pinned upstream collection regression suite also passes.

Live on one 1920×1200 display with Foot and installed `ttfx`: the actual packaged launcher resolved the installed Python renderer, created a fullscreen screensaver with `inhibitingIdle: false`, and advanced between portraits. A private visual spot check confirmed animated fitted artwork. Injected Escape dismissed it, removed runtime records, and restored the cursor. Uninstall restored `/usr/share/omarchy/bin/omarchy-screensaver` through the same launcher. Giants was then reinstalled.

Real multi-monitor behavior and a complete automatic idle-to-lock cycle remain unverified. The existing idle values were preserved; headless tests do not prove that live lifecycle. No screenshots or recordings are included in the repository or PR.
