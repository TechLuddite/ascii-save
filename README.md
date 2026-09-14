# ascii-save

A workshop for making and testing ASCII/braille screensaver collections on Omarchy. Includes a terminal preview, the complete Giants art collection, a Van Gogh collection, original sample art, and agent context for bringing file-or-directory playback to a local system.

**Status:** includes an opt-in Giants screensaver installer for Lua-based Omarchy. It uses the existing desktop launcher and idle service. The separate upstream collection proposal remains [Omarchy draft PR #11626](https://github.com/omacom/omarchy/pull/11626).

## Try it

Requires Linux, Bash, Python 3, GNU coreutils, and `ttfx` for animation. The reference regression tests also use `jq`. Omarchy normally provides these tools; nothing is installed automatically.

```bash
git clone https://github.com/TechLuddite/ascii-save.git
cd ascii-save
python3 scripts/validate.py
python3 scripts/preview.py
```

Run the preview in a terminal. Any key closes it, and it stops automatically after 60 seconds. `--seconds 120` changes that limit. It cycles in filename order using stock Omarchy’s random `ttfx` character effects at 120 fps, advancing after each complete effect. Use `--effect highlight` for the gentler sepia highlight at 30 fps with a short pause between artworks. This previews content; it does not emulate Omarchy's idle/lock behavior or provide a live wallpaper.

Use `--effect fast` to cycle only Expand, Middleout, Scattered, Wipe, and Waves with faster movement/reveal settings at 120 fps and no pause between pieces.

For a fullscreen temporary terminal on a system with Foot:

```bash
foot --fullscreen --app-id=ascii-save.preview python3 scripts/preview.py
```

## Optional workshop installer

This installer manages the standalone workshop Python renderer. The development workstation now uses the revised native Omarchy draft instead; its menu/import workflow and separate ownership/removal instructions are in [local integration](docs/LOCAL-INTEGRATION.md). Do not use this installer to update that trial or install both overrides together.

On Omarchy with Lua Hyprland configuration and `ttfx` installed:

```bash
python3 scripts/install.py install
omarchy launch screensaver force
# Restore the stock renderer:
python3 scripts/install.py uninstall
```

Installation copies all 18 refined Giants artworks into a stable user-owned directory. Each session starts at the first portrait, advances after each complete random animation, shows the Omarchy wordmark last, then repeats. `ttfx --random-effect` chooses from the entire installed suite at 120 fps; effects can repeat and their durations vary. Braille artwork scales down to fit the terminal without cropping. Each monitor progresses independently. A key, mouse movement, or focus leaving the screensaver dismisses it.

The installer adds a marked PATH override to `~/.config/hypr/hyprland.lua` for **only** the renderer command. It keeps the packaged launcher, idle service, fonts, branding, and lock timings. It backs up the config and validates Hyprland after applying it. Uninstall removes the exact managed block, preserves unrelated edits and modified installed files, and restores stock command resolution. Uninstall before installing a newer version; close any running screensaver first. The installation survives moving or deleting this checkout, but keep the installer available for removal.

This is an experimental integration, verified with Foot on one display. Real multi-monitor and automatic idle-to-lock testing remain outstanding. See [integration details](docs/LOCAL-INTEGRATION.md). If screensavers were previously disabled, enable them with `omarchy toggle screensaver`; installation does not change that preference.

## Included collections

The default [Giants collection](examples/giants/README.md) contains braille conversions of all 18 upstream backgrounds: 17 portrait compositions and the Omarchy wordmark. Source hashes, conversion settings, and attribution are included. Original raster wallpapers and private screenshots/recordings are not included. Giants artwork is excluded from the project MIT license; see its [artwork notice](examples/giants/ARTWORK-NOTICE.md).

The [refined Giants collection](examples/giants-refined/README.md) offers larger portraits with shaded facial detail and per-image contrast adjustment. Preview it with `python3 scripts/preview.py examples/giants-refined`. Its original artwork notices still apply.

The [native fullscreen Giants collection](examples/giants-fullscreen/README.md) pairs 124-column shaded busts with readable terminal-text names and an enlarged wordmark. It fits the stock size-18 Foot screensaver at a minimum 126×32 cells.

The [colour Giants collection](examples/giants-color/README.md) converts the same 18 wallpapers to truecolour quadrant block text: each cell carries two 24-bit colours and one of 15 block glyphs, so the stock 137×36 grid shows a 274×72 colour picture with the painted names legible. It is the current local selection. Colour files contain SGR sequences, so validate them with `python3 scripts/validate.py --color examples/giants-color` and play them with `ttfx --existing-color-handling dynamic`; the stock renderer strips colour. `scripts/omarchy-screensaver-color` and `scripts/omarchy-screensaver-prepare-color` are the renderer and preparer variants that do this. Convert your own images with `python3 scripts/convert-color.py image.jpg out.txt`.

The colour renderer plays a voted subset of the `ttfx` effects. Watch every effect on your own artwork and vote yes or no in a local browser page with the [curation tool](curation/README.md); `python3 curation/curate.py apply` writes the yes list into the renderer. The current list came from the vote record in `curation/votes/`.

The [Van Gogh collection](examples/van-gogh/README.md) adds eight public-domain Met paintings converted to captioned braille. Preview it with `python3 scripts/preview.py examples/van-gogh`. Museum credits, pinned source hashes, and offline regeneration instructions are included.

The [Glyphwork collection](examples/glyphwork/README.md) contains six MIT-licensed procedural ASCII patterns with a preserved upstream license and per-piece source credits. Preview it with `python3 scripts/preview.py examples/glyphwork`.

The original [Cosmos collection](examples/cosmos/README.md) contains five full-screen natural-space braille compositions: an eclipse, spiral galaxy, ringed giant, nebula pillars, and a cratered crescent. It is MIT-licensed and generated directly from the included Python source.

`examples/observatory` is a small original MIT-licensed collection for simple tests. Pass its path to either command to use it.

## Make a demo video

`video/opener.py` renders the colour opener (accelerating slides, shrink to a grid, blackhole into the stock logo) and `video/showcase.py` renders the opener followed by one curated effect per artwork, time-compressed to a target length. Both run entirely offscreen and need a virtualenv with `video/requirements.txt` (Pillow, numpy, TerminalTextEffects 0.15.0). See [video/README.md](video/README.md).

## Make a collection

Put local artwork in `collections/<name>/` (ignored by Git). Each `.txt` is one frame of artwork. ASCII, braille, and block characters are supported. Cursor movement and other terminal controls are rejected; SGR colour sequences are accepted only by the colour preparer (`scripts/validate.py --color`).

```bash
mkdir -p collections/my-art
omarchy transcode ascii /absolute/path/to/image.png collections/my-art/01.txt --width 100 --height 35
python3 scripts/validate.py collections/my-art
python3 scripts/preview.py collections/my-art
```

The converter is an existing Omarchy command. Its availability and visual quality depend on the installed version and source image. Inspect results before using them. Converted images retain their source licensing obligations; this project's MIT license does not license third-party artwork.

## Credits and thanks

This project is a workshop built on other people's work. Loudly, and with links:

**Omarchy, by DHH and the Omarchy team.** [Omarchy](https://omarchy.org/) is the desktop this all runs in: the idle service, the screensaver launcher, the terminal configs, and the `omarchy transcode ascii` converter. The colour renderer and preparer here are small edits of the Omarchy screensaver scripts and keep their MIT notice. Thank you for a screensaver worth obsessing over, and for shipping it as plain shell scripts anyone can read.

**ttfx, by the Omarchy team.** [ttfx](https://github.com/omacom-io/ttfx) (MIT) is the single-binary Rust port of TerminalTextEffects that every Omarchy screensaver runs. Every animation in this project is theirs. This project only chooses which ones play, passes colour through, and records them.

**TerminalTextEffects, by ChrisBuilds.** [TerminalTextEffects](https://github.com/ChrisBuilds/terminaltexteffects) (MIT) is the original Python effects engine and the source of every effect `ttfx` ports. The video opener uses its Blackhole effect directly, with a small subclass in `video/blackhole.py`. Documentation is at [chrisbuilds.github.io/terminaltexteffects](https://chrisbuilds.github.io/terminaltexteffects/).

**The Giants wallpaper series, by DHH.** [omarchy-giants-theme](https://github.com/dhh/omarchy-giants-theme) is the artwork in every Giants collection here. Its credits for each portrait's identity reference are carried alongside every conversion in `SOURCE-CREDITS.md`. The artwork is not covered by this project's license; see each collection's `ARTWORK-NOTICE.md`.

**The Metropolitan Museum of Art.** The Van Gogh collection converts eight paintings released under the Met's [Open Access](https://www.metmuseum.org/hubs/open-access) program (CC0). Museum credit lines are in `examples/van-gogh/SOURCE-CREDITS.md`.

**muraleph.** The Glyphwork collection reproduces six procedural pieces from [muraleph/glyphwork](https://github.com/muraleph/glyphwork) (MIT), with the upstream license preserved in `examples/glyphwork/LICENSE`.

**Foot, by Daniel Eklöf and contributors.** [Foot](https://codeberg.org/dnkl/foot) (MIT) is the terminal the screensaver was measured and previewed in. Its exact block-element rendering is what the offscreen video renderer imitates.

**JetBrains Mono and Nerd Fonts.** The measured grids and the video renderer use [JetBrains Mono](https://www.jetbrains.com/lp/mono/) as patched by [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) (SIL OFL 1.1).

**Hyprland.** [Hyprland](https://github.com/hyprwm/Hyprland) (BSD-3-Clause) is the compositor Omarchy runs on; the local integration talks to it through `hyprctl`.

**ImageMagick, ffmpeg, Pillow and numpy.** [ImageMagick](https://www.imagemagick.org/) decodes and resamples every image the converters touch. [ffmpeg](https://ffmpeg.org) assembles the videos. [Pillow](https://python-pillow.org/) and [numpy](https://numpy.org/) paint the offscreen frames.

The upstream draft this workshop feeds is [Omarchy PR #11626](https://github.com/omacom/omarchy/pull/11626). Nothing in this repository changes that draft.

If your work is used here and is not credited the way you would like, open an issue and it will be fixed.

## Continue development

Start with [AGENTS.md](AGENTS.md), [the handoff](docs/CONTEXT.md), [local integration plan](docs/LOCAL-INTEGRATION.md), and [security notes](docs/SECURITY.md). The exact proposed upstream change is preserved under [reference/](reference/README.md).

```bash
python3 -m unittest discover -s tests -v
bash reference/omarchy/test/shell.d/screensaver-collection-test.sh
```

The preview needs no installation. Native playback is opt-in through the installer above; removing the checkout alone does not uninstall it.

Code and original example artwork: MIT. Vendored Omarchy code retains its upstream MIT notice. See [LICENSE](LICENSE) and [reference/omarchy/LICENSE](reference/omarchy/LICENSE).
