# Handoff

## Current handoff — 2026-09-14: colour collection trial

The user judged every monochrome conversion (braille, shaded ASCII busts) as
not landing, and asked to research "cranking it to the max". The result is a
colour pipeline, live as the local default. The draft Omarchy PR was **not**
changed; the user wants more testing first.

Findings that drove the design (all measured on this workstation):

- `ttfx --existing-color-handling always|dynamic` preserves input SGR colour
  exactly (720 of 720 test colours). The stock renderer runs the default,
  `ignore`, which strips colour. `dynamic` animates in the effect's palette
  and settles on the artwork's colours; verified live.
- Font size is not a useful dial. A full-canvas `expand` takes 6 s at the stock
  137×36 grid and 189 s at 240×66 (size 10). Stock size 18 is the ceiling.
- Colour quadrant block elements (2×2 samples per cell, best two-colour
  partition) beat half blocks and every monochrome treatment. Names painted
  in the wallpapers stay legible at 127×36 cells.
- 12 effects paint the finished picture before disturbing it (burn,
  colorshift, crumble, errorcorrect, highlight, overflow, rings, smoke,
  spotlights, thunderstorm, unstable, vhstape). The user asked for those to go.
  Per-character effects run for minutes on a 4.5k-cell colour picture.
- 16colo.rs serves raw ANSI at `/pack/<pack>/raw/<file>`; a CP437 rasteriser
  in `.local/crank/tools/ans2txt.py` produces playable colour text. Classic
  hand-drawn ASCII (Joan Stark archive) is too small and monochrome for this goal.

What exists now in the repository:

- `scripts/convert-color.py`: raster → truecolour quadrant block text, fitted
  to a cell grid (default 137×36, 14:33 cell aspect), optional edge trim.
  ImageMagick with restricted limits does decoding; the cell fit is pure Python.
- `scripts/seed-giants-color.py`: converts all 18 Giants backgrounds from a
  clean checkout into `examples/giants-color/` with manifest, hashes and notices.
  Pinned to `TechLuddite/omarchy-giants-theme` at `1bd38f1` (the local checkout;
  the older `48d97ac` pin used by other collections is not available locally).
- `scripts/omarchy-screensaver-prepare-color`: the revised upstream preparer
  with one change: SGR sequences (`ESC [ digits ; m`) pass through, every other
  control character is still rejected, size limit raised to 1 MiB, line limits
  applied to the visible text.
- `scripts/omarchy-screensaver-color`: the revised upstream renderer with
  `--existing-color-handling dynamic` and an `include_effects` list passed as
  `--include-effects`. Stock timing, each effect runs to completion. The list
  is the user's own vote (21 yes, 16 no, recorded in
  `curation/votes/2026-09-14-giants-ada-lovelace.json`), made with the
  curation tool below. Earlier the same day an agent-chosen list plus a hold
  and a 60 s cap were tried and rejected as dull; the user then voted.
  Do not edit the list by hand; rerun the vote.
- `curation/`: `curate.py record|serve|apply|list`. Records every effect on a
  chosen artwork through a pty (asciicast with real timestamps), converts to
  30 fps cell-diff JSON (`frames.py`, a purpose-built decoder for ttfx output,
  not a terminal emulator), serves a local canvas player with y/n voting
  (`serve.py`, `index.html`, 127.0.0.1 only), and writes the yes list into the
  renderer. Working data lives in `.local/curation/` (ignored). Tests in
  `tests/test_curation.py` cover the decoder, the server, apply, and that the
  committed vote record matches the renderer.
- `scripts/validate.py --color` and `common.prepare(source, COLOR_PREPARER)`.
- `tests/test_color.py`: converter output shape, SGR-only guarantee, preparer
  acceptance/rejection cases, pinned preparer still rejecting colour, and the
  Giants colour manifest. 16 tests pass.

Local state: the user-owned trial copy at
`~/.local/share/omarchy/screensaver-development/source/bin/` now holds the
colour renderer and colour preparer; `installed.json` hashes and `source` were
updated so its uninstall tool still works. Originals are backed up under
`~/.local/state/omarchy/screensaver-development/color-trial-backup-*/`.
`shell.json` `screensaver.source` points at
`~/.local/share/omarchy/screensavers/giants-color`. Verified through the stock
`omarchy launch screensaver force` on eDP-1: colour renderer in use, effects
build up from an empty canvas, portraits settle in colour. Idle-to-lock and a
second display remain unverified.

Working tools that are not repository code live under the ignored
`.local/crank/` (Pillow venv, headless proof renderer, contact sheet tool,
ANSI rasteriser, pty runner, effect survey data). The `/tmp` scratchpad is a
tmpfs and was lost on a reboot mid-session; keep tooling under `.local/`.

Repository state: this work was committed on branch `color-screensaver` and merged to `main` through a pull request on 2026-09-14 with the user's explicit authorization to push, open and merge. The README credits DHH and the Omarchy team for Omarchy, ttfx and the Giants artwork.

Video pipelines (2026-09-14) are in the repository under `video/` (opener, showcase, blackhole override, renderer, tests in `tests/test_video.py`), superseding the private `.local/giants-video/color/` prototypes. The opener renders a 26 s sequence offscreen: accelerating full-screen colour slides, the last portrait shrinks into a 4/4/3/3/3 grid, tiles pop in, the adapted TTE blackhole (vendored 0.15.0, colour kept) consumes the grid and explodes into the stock `logo.txt` doubled to 162×20 cells. Canvas 210×58 at 9×20 px. The showcase follows it with one curated effect per portrait (17 of the 21 yes votes, the four slowest left out), effects over 5 s time-compressed to about 4 to 5 s with a 1.5 s hold; 116.8 s total. Outputs `artifacts/giants-opener-color.mp4`, `artifacts/giants-showcase-color.mp4` and copies in `~/Videos`; evidence stays local. The earlier monochrome finale in `.local/giants-video/` is superseded but retained.

Draft PR update (2026-09-14, authorized by the user after an adversarial review): Omarchy PR #11626 now stands at `667b14c` on the fork branch `ascii-screensaver-collections` (checkout `~/Projects/omarchy-ascii-collections`). It adds per-artwork colour handling (`dynamic` only for text carrying SGR, `ignore` for plain text), an optional validated `screensaver.effects` list, an SGR-only preparer with a strict parameter grammar and a 1 MiB cap, `omarchy transcode ascii --mode color`, and colour-by-default folder import. The review (an independent agent, 26 tool calls) found nine issues; the six that mattered were fixed before the push: unconditional `dynamic` stripped gradients from plain text, the SGR regex admitted a `ttfx` integer-overflow panic and wrong-arity parameters, animated WebP aborted colour import, an unknown effect name left a black screensaver, large files could exceed the 5 s preparation timeout, and non-string list entries were silently dropped. The PR description carries the same summary. Live verification of that exact revision on a display has not been done; headless tests and a sandboxed import pass.

The local trial copy now runs the PR's renderer, preparer and importer (backups under `~/.local/state/omarchy/screensaver-development/pr-scripts-backup-*`), with `screensaver.effects` in `shell.json` set to the 21 voted effects. `scripts/omarchy-screensaver-color` and `scripts/omarchy-screensaver-prepare-color` in this repository mirror the reviewed behaviour.

Lesson recorded the hard way: a verification command whose text contains `org.omarchy.screensaver` makes the launcher's `pgrep -f` see the agent's own shell and exit, and a scripted Escape key then lands in whatever window is focused, which was the user's terminal running the agent. Any live check must come from a script file and must confirm the active window class before sending keys.

Giants licence, checked 2026-09-14: the upstream repository was created with an MIT LICENSE (commit `ad0c3b1`, three wallpapers) and dropped it in `640b2d6` on 2026-08-12, before the 17-portrait series was added. The pinned commits carry no licence file. The artwork notices' wording stands.

Open items: install `chafa` (needs root) and compare its symbol/dither output
against `convert-color.py`; a curated Blocktronics ANSI collection with a
row-count picker; the ASCII art skill on top of the proof renderer; PR changes
only after the user says testing is sufficient.

## Previous handoff — 2026-09-13

Portrait revision after user feedback: the earlier bust treatments were not satisfactory. The fullscreen set now uses a varied ASCII character ramp and source-positive lighting instead of braille shading for the 17 busts. Centered names and the wordmark are byte-for-byte unchanged. All 18 stills were reviewed locally; this is a new visual trial for user judgment, not an approved quality result. The previous collection remains available locally.

Fullscreen improvement pass: the active native trial now selects a stable copy
of `examples/giants-fullscreen`, replacing the small stock-converted import.
All 18 Giants remain enabled. Busts are 124×28 cells plus readable centered
terminal names; the enlarged wordmark is at most 124×11. The generator's
`--profile native-fullscreen` replaces the wallpaper's bottom caption band.
All 18 stills were reviewed in fullscreen stock Foot at 1920×1200; short native
ttfx playback was checked. Eleven workshop tests, reference regressions, hashes,
and independent regeneration passed. The second display was disconnected and
idle-to-lock remains unverified. Renderer files and idle settings are unchanged;
the previous import is retained and the private uninstall record is updated.

The user asked to reuse Omarchy's existing screensaver capabilities, revise the upstream draft, and leave all 18 Giants enabled as the local default. The active setup now uses user-owned copies of the revised Omarchy scripts. The separate workshop Python renderer was uninstalled. Do not reinstall it as a routine repair or update; see [local integration](LOCAL-INTEGRATION.md) for the distinction and ownership records.

[Omarchy PR #11626](https://github.com/omacom/omarchy/pull/11626) was updated to `76d74b355c1750b7e3353d4cadc3e159f6053051`, titled **Add ASCII collection selection and image-folder import**, and remains open/draft as last checked. It adds native image-folder import and text-folder selection; successful image/text/reset branding actions clear `screensaver.source`. It reuses Omarchy's converter and effects. The config helper preserves symlink targets, and renderer cleanup now targets its own effects and validated screensaver windows. The packaged system-lock command remains unchanged.

Before the fullscreen improvement pass, the original 18 Giants raster sources were converted with stock `omarchy-transcode-ascii` defaults (braille, maximum 80×26), then selected as a text collection. These differ from the larger, shaded `examples/giants-refined` artworks. Both connected displays completed all 18 entries and wraparound with real random effects. Keyboard dismissal, cursor restoration, snapshot cleanup, unrelated-command survival, menu layout, and directory-picker cancellation were checked live. A full automatic idle-to-lock cycle remains unverified. Captures and exact workstation paths stay private.

The revised upstream focused collection/branding/menu/bar/CLI checks pass. Its full headless run had the same five failing shell files previously reproduced on clean base: `config`, `launch-about`, `locate`, `snapper`, and `unowned-system-paths` (5 of 238 files). Three require the separate `omarchy-pkgs` checkout. Focused tests were rerun after final cleanup changes. No upstream CI checks were listed at final verification; do not claim upstream CI passed.

This section supersedes installation/status claims in the historical notes below. The vendored `reference/` stays pinned to the original draft for reproducibility. It has not been updated to the current upstream implementation.

## Intended outcome

Bring native ASCII collection playback to the user's Omarchy system and build a comfortable workflow for creating, previewing, and testing ASCII/braille screensavers. The repository now includes opt-in native Giants installation; see the Installed Giants screensaver section below. Earlier sections preserve the history of the seed and upstream proposal.

The user liked a live preview of Giants theme portraits converted with `omarchy transcode ascii`, animated by real `ttfx` in a fullscreen Foot terminal. The sepia highlight treatment was especially successful. The preview was a temporary terminal, not a desktop wallpaper. At the user's request, braille conversions of the entire current Giants series are now the default example under `examples/giants/`. The original raster portraits and private visual captures are not included. This explicitly authorized artwork seed does not authorize publishing screenshots or recordings.

## Original upstream proposal (historical)

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

## Second collection: Vincent van Gogh

`examples/van-gogh/` contains eight captioned braille conversions from The Met’s public-domain image collection, with CC0 source attribution and pinned hashes. `scripts/seed-van-gogh.py` regenerates them offline from exact local JPEGs into a new output directory, using bounded regular-file snapshots and hash checks. See the collection README for playback and regeneration. The preview now defaults to stock Omarchy’s random character effects at 120 fps, advancing immediately after each completed effect; `--effect highlight` retains the earlier sepia treatment at 30 fps. Original painting colors and fine shadow/brushwork detail are not preserved. Native integration and the upstream draft remain separate work.

Verification on 2026-09-13: seven workshop tests and reference collection regressions passed; all eight regenerated text files matched their hashes. Fullscreen Foot/ttfx was visually spot-checked on one 1920×1200 display. Full collection animation review, multi-monitor playback, and native idle/lock lifecycle checks remain outstanding.

## MIT artwork collection: Glyphwork

`examples/glyphwork/` contains six verbatim 80×20 procedural pattern samples from `muraleph/glyphwork` at `38212210c5e920a85e22ff66d6f25e0b20e729ca`: Plasma, Interference, XOR Texture, Moiré, Diagonal Wave, and Fractal Noise. The upstream MIT license is included; `SOURCE-CREDITS.md` and `manifest.json` record author, AI-author disclosure, source line ranges, pinned URLs, and hashes. Licensing confirmation is based on the upstream license, committed examples, and reviewed mathematical generator; no external image sources or art-specific exclusions were identified for these samples. No upstream code was executed.

InterCentury and Temaprint remain unconfirmed for artwork provenance and were not imported. Asciiville is not a strict MIT-art match: its separate artwork notice says Apache-2.0, and its README also describes restrictions on some collected art. Do not treat a repository-wide MIT badge as blanket clearance.

Verification on 2026-09-13: all six artwork files passed the pinned preparer and matched their exact upstream source ranges and recorded hashes; the preserved license hash matched. Seven workshop tests and the reference collection regression suite passed. A fullscreen Foot/ttfx spot check on the local 1920×1200 display showed character animation and fitting content at font size 16. Not every effect or artwork was live-reviewed; native idle/lock and multi-monitor behavior remain untested.

## Original Cosmos collection and visual direction

The user found the earlier collections pleasant but insufficiently striking. Giants remains the strongest reference, though it also needs refinement. The new direction prioritizes original full-screen natural-space compositions, with animation supplied entirely by existing Omarchy/ttfx code.

`examples/cosmos/` now contains five original MIT braille compositions (Corona, Spiral, Ringed Giant, Pillars, Crescent), authored directly with `scripts/create-cosmos.py`. Default dimensions are 208×56, composed for the current 1920×1200 display and Foot font size 11. Generator options allow separate sizes; there is no automatic fitting. No original images or third-party artwork were used. The manifest records seeds and hashes. All five final stills were visually reviewed in a temporary fullscreen terminal; evidence stays under ignored `.local/space-review/`.

Cosmos is a first authored collection for user review, not a claim that the user has approved its visual quality.

## Giants refinement

The preview also supports `--effect fast`: a repeating sequence of Expand, Middleout, Scattered, Wipe, and Waves with faster settings at 120 fps, advancing immediately after each effect. It uses the same owned-child cleanup and keyboard dismissal as other preview modes.

`examples/giants-refined/` adds a separate refinement of all 18 original pinned sources. `scripts/refine-giants.py` verifies bounded local source snapshots against the original manifest, uses per-image percentile contrast and serpentine Floyd–Steinberg shading, and validates the output through the pinned preparer. Portraits are 186×56 cells, composed for 9×20-pixel terminal cells. The wordmark is sampled at 208×52, with blank margins subsequently removed (88×10 lettering bounds) to fix its off-center placement. This restores midtone texture and increases the displayed size without cropping names or compositions. The original default collection is preserved for comparison. Source credits and the non-MIT artwork notice accompany the refined set. The local theme checkout differs from the pinned sources; regenerate only from hash-matching inputs.

Verification on 2026-09-13: all 18 outputs matched a separate regeneration and manifest hashes; notices matched the original collection byte-for-byte. Seven workshop tests and the reference collection regression suite passed. All 18 rasterized text proofs were reviewed as a contact sheet, and Turing–von Neumann was spot-checked in fullscreen Foot at 1920×1200. No native idle/lock or multi-monitor verification was performed.

## Local showcase workflow

The local showcase uses nine installed native effects with finished-image holds below two seconds. Its finale fills the viewport with 17 portrait compositions in rows of 4/4/3/3/3, consumes their actual characters in a rotating blackhole, and reveals the centered Omarchy wordmark only at the final explosion. This requires a private adaptation of the original Python TerminalTextEffects blackhole; it is not an unmodified installed ttfx effect or part of the public preview CLI.

Local recording drivers, pinned effect provenance, phase records, and visual evidence remain under ignored `.local/giants-video/` and `artifacts/`. Do not commit or upload them. The start/end layouts were verified against generated frames and visually checked in Foot. The measured viewport is 210×58 cells with current padding; respect it to avoid scrolling or clipping. Recording temporarily enables DND and restores its previous state on exit. These demonstrations do not verify native idle/lock or multi-monitor behavior.

## Workshop renderer installation (historical)

The user authorized persistent local installation and a PR/merge in **TechLuddite/ascii-save**. `scripts/install.py` now installs a standalone copy of `scripts/native.py` and the entire refined Giants set. A marked Lua user-config block explicitly overrides only `omarchy-screensaver` for compositor-launched terminals. No package files or upstream PR were changed. Playback runs all 18 entries in order with wraparound, using unfiltered `ttfx --random-effect` at 120 fps and terminal-aware braille fitting.

See `docs/LOCAL-INTEGRATION.md` for ownership, uninstall, failure behavior, evidence, and remaining live-test limits. Keep screenshots/recordings private. This implementation supersedes the earlier plan to require a whole Omarchy development link.
