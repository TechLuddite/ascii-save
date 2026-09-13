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
