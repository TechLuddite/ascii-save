# Handoff

## Intended outcome

Bring native ASCII collection playback to the user's Omarchy system and build a comfortable workflow for creating, previewing, and testing ASCII/braille screensavers. This repository seeds that work; it does not activate native integration yet.

The user liked a live preview of Giants theme portraits converted with `omarchy transcode ascii`, animated by real `ttfx` in a fullscreen Foot terminal. The sepia highlight treatment was especially successful. The preview was a temporary terminal, not a desktop wallpaper. At the user's request, braille conversions of the entire current Giants series are now the default example under `examples/giants/`. The original raster portraits and private visual captures are not included. This explicitly authorized artwork seed does not authorize publishing screenshots or recordings.

## Upstream work already done

- [Draft PR #11626](https://github.com/omacom/omarchy/pull/11626): Add file and directory sources for ASCII screensavers.
- Author branch: `TechLuddite/omarchy:ascii-screensaver-collections`.
- Submitted commit: `fce24d4ddac2a18c4361dd3adee8a411e5b705f9`.
- Upstream base: `31bd80daa4613ffdee995ac27467fce5a2990806`, branch `quattro`.
- Observed 2026-09-13: open and draft. Check current status before reimplementing or applying it.

The optional `screensaver.source` field in `~/.config/omarchy/shell.json` accepts an absolute or `~/` path to a file or directory. A directory supplies visible `.txt` files in filename order. Playback advances after each complete random effect and wraps. Monitors animate independently. No setting preserves the original live-editable branding file.

Configured artwork is copied into a private temporary directory at startup. Missing, empty, invalid, or unpreparable sources use the existing branding fallback, then the bundled logo if the user logo is absent. Temporary copies are removed at exit. The helper rejects symlink entries, special files, invalid UTF-8 and control sequences; it bounds entries, artworks, bytes, line lengths and line counts. Preparation has a five-second deadline in the runtime.

The draft is configuration-only. The branding menu continues to edit the fallback logo while a source override exists. Remove that field to return to usual branding behavior. Consider this UX explicitly before local integration.

## Evidence and gaps

Focused collection tests passed. The upstream CLI tests passed. Full headless `./test/all` had the same five failed shell files on candidate and clean base: `config`, `launch-about`, `locate`, `snapper`, `unowned-system-paths`. Three require the separate `omarchy-pkgs` checkout. Do not describe the complete upstream suite as green.

Live testing on one 1920×1200 display with Foot and real `ttfx` confirmed three portraits played `000 → 001 → 002 → 000`, keyboard dismissal exited, and temporary playback files were removed. Multi-monitor playback and a full automatic idle-to-lock cycle were not live-tested. The current repo's preview tooling is separate from that historical verification.

## Separate proposals

[Amiga PR #11191](https://github.com/omacom/omarchy/pull/11191) proposes an emulator screensaver, not image slideshows or ASCII collections. It overlaps with future backend selection, menus, and lifecycle integration. Its runtime uses Bubblewrap plus process ownership and lock-state checks. Those are useful design references, not proof that the entire proposal is safer or a reason to import its emulator stack.

Keep ASCII collection support, full-resolution image slideshows, and live desktop backgrounds as separately reviewable changes. Configuring an artwork directory alone does not make a wallpaper backend.
