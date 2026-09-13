# Glyphwork — six procedural ASCII studies

Six existing MIT-licensed text pieces by **muraleph**, selected from the project’s procedural showcase: Plasma, Interference, XOR Texture, Moiré, Diagonal Wave, and Fractal Noise. These are abstract demoscene-style patterns, not figurative illustrations or image conversions. Upstream identifies muraleph as an AI author.

```bash
python3 scripts/validate.py examples/glyphwork
foot --fullscreen --app-id=ascii-save.preview --font='monospace:size=16' python3 scripts/preview.py examples/glyphwork --seconds 180
```

The artworks are approximately 80 columns × 20 rows. A larger temporary terminal font makes these compact pieces easier to see. The preview uses stock Omarchy random character effects; any key exits. No persistent desktop configuration is required.

See [source credits](SOURCE-CREDITS.md), [the original MIT license](LICENSE), and `manifest.json` for per-piece source permalinks, exact source ranges, revision, checksums, and licensing evidence. Preserve this license and credits when copying the collection.

To recover the identical files, download the pinned `provenance.showcase_url` from the manifest, verify its SHA-256 against `source_sha256`, and extract each inclusive `source_line_start`–`source_line_end` range, preserving spaces and newlines. Confirm each output SHA-256 before playback. No upstream scripts or packages need to run.

Verification on 2026-09-13: all six artwork files passed the pinned preparer and matched their exact upstream source ranges and recorded hashes; the preserved license hash matched. Seven workshop tests and the reference collection regression suite passed. A fullscreen Foot/ttfx spot check on the local 1920×1200 display showed character animation and fitting content at font size 16. Not every effect or artwork was live-reviewed; native idle/lock and multi-monitor behavior remain untested.
