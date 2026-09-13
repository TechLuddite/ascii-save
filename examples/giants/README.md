# Giants — complete braille collection

The first ascii-save example contains every image in the upstream theme's `backgrounds/` directory: 17 portrait compositions and the Omarchy wordmark, converted to braille text. The original theme is [dhh/omarchy-giants-theme](https://github.com/dhh/omarchy-giants-theme).

Pinned source commit: `48d97ac3f9795f039a0e779487a6f2a1342cb870`.

```bash
python3 scripts/validate.py examples/giants
python3 scripts/preview.py examples/giants
```

The numeric output prefixes preserve the theme's portrait sequence rather than lexicographically putting 10 before 2. The wordmark comes last. Each artwork is rendered by the existing text-effects engine; this is a content collection, not a replacement image renderer or a native installer.

## Conversion and provenance

`manifest.json` maps every source image to its text conversion and records SHA-256 hashes, source revision, and conversion settings. Conversion used Omarchy's existing ASCII converter at 140 columns × 46 rows, threshold 55, no trimming. A typical fullscreen terminal at font size 11 has room for these artworks; choose a smaller font for smaller windows. The tool does not promise automatic fitting on all displays.

To regenerate from a clean local checkout (output must be empty):

```bash
python3 scripts/seed-giants.py /path/to/omarchy-giants-theme --output collections/giants-regenerated
```

Check out the pinned revision first for the same inputs. Installed converter and ImageMagick versions can affect output; compare hashes and inspect changes before replacing committed examples. The seeder does not fetch, watch, or execute upstream repository scripts. It invokes the installed Omarchy image converter on the selected local files.

See [source credits](SOURCE-CREDITS.md) and [artwork notice](ARTWORK-NOTICE.md). These generated text conversions are not screenshots or screen recordings.
