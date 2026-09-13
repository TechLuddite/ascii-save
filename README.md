# ascii-save

A workshop for making and testing ASCII/braille screensaver collections on Omarchy. Includes a terminal preview, the complete Giants art collection, a Van Gogh collection, original sample art, and agent context for bringing file-or-directory playback to a local system.

**Status:** experimental development seed. It does not install a screensaver, replace a desktop background, or change idle/lock settings. The native integration is proposed in [Omarchy draft PR #11626](https://github.com/omacom/omarchy/pull/11626).

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

## Included collections

The default [Giants collection](examples/giants/README.md) contains braille conversions of all 18 upstream backgrounds: 17 portrait compositions and the Omarchy wordmark. Source hashes, conversion settings, and attribution are included. Original raster wallpapers and private screenshots/recordings are not included. Giants artwork is excluded from the project MIT license; see its [artwork notice](examples/giants/ARTWORK-NOTICE.md).

The [refined Giants collection](examples/giants-refined/README.md) offers larger portraits with shaded facial detail and per-image contrast adjustment. Preview it with `python3 scripts/preview.py examples/giants-refined`. Its original artwork notices still apply.

The [Van Gogh collection](examples/van-gogh/README.md) adds eight public-domain Met paintings converted to captioned braille. Preview it with `python3 scripts/preview.py examples/van-gogh`. Museum credits, pinned source hashes, and offline regeneration instructions are included.

The [Glyphwork collection](examples/glyphwork/README.md) contains six MIT-licensed procedural ASCII patterns with a preserved upstream license and per-piece source credits. Preview it with `python3 scripts/preview.py examples/glyphwork`.

The original [Cosmos collection](examples/cosmos/README.md) contains five full-screen natural-space braille compositions: an eclipse, spiral galaxy, ringed giant, nebula pillars, and a cratered crescent. It is MIT-licensed and generated directly from the included Python source.

`examples/observatory` is a small original MIT-licensed collection for simple tests. Pass its path to either command to use it.

## Make a collection

Put local artwork in `collections/<name>/` (ignored by Git). Each `.txt` is one frame of artwork. ASCII, braille, and block characters are supported; ANSI control sequences are not.

```bash
mkdir -p collections/my-art
omarchy transcode ascii /absolute/path/to/image.png collections/my-art/01.txt --width 100 --height 35
python3 scripts/validate.py collections/my-art
python3 scripts/preview.py collections/my-art
```

The converter is an existing Omarchy command. Its availability and visual quality depend on the installed version and source image. Inspect results before using them. Converted images retain their source licensing obligations; this project's MIT license does not license third-party artwork.

## Continue development

Start with [AGENTS.md](AGENTS.md), [the handoff](docs/CONTEXT.md), [local integration plan](docs/LOCAL-INTEGRATION.md), and [security notes](docs/SECURITY.md). The exact proposed upstream change is preserved under [reference/](reference/README.md).

```bash
python3 -m unittest discover -s tests -v
bash reference/omarchy/test/shell.d/screensaver-collection-test.sh
```

No installation is needed for these tools. Removing the checkout removes the preview tooling. Before adding persistent integration, implement ownership-aware install/uninstall and backup restoration as described in the plan.

Code and original example artwork: MIT. Vendored Omarchy code retains its upstream MIT notice. See [LICENSE](LICENSE) and [reference/omarchy/LICENSE](reference/omarchy/LICENSE).
