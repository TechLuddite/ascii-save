# Giants — shaded refinement

All 18 pinned Giants compositions, with larger braille rendering, per-image contrast adjustment, and serpentine error diffusion to retain facial midtones and texture. Portraits use 186×56 cells. The wordmark is converted on a 208×52 grid, then its blank margins are removed so terminal centering aligns the lettering itself. Framing preserves the whole composition and printed names. Designed for 9×20-pixel terminal cells on a 1920×1200 display; smaller terminals can clip.

```bash
foot --fullscreen --app-id=ascii-save.preview -o font=monospace:size=11 python3 scripts/preview.py examples/giants-refined --seconds 300
```

Any key exits. Stock random character effects are the default; add `--effect highlight` for sepia. The original `examples/giants/` remains available for comparison.

To regenerate from the exact pinned upstream images in a local checkout:

```bash
python3 scripts/refine-giants.py /path/to/pinned/omarchy-giants-theme --output collections/giants-refined
```

The destination must not exist. The generator verifies source hashes before conversion and validates all resulting text. `manifest.json` records source revision, source/output hashes, conversion settings, and tool version.

These converted artworks are **not MIT-licensed**. Preserve [SOURCE-CREDITS.md](SOURCE-CREDITS.md) and [ARTWORK-NOTICE.md](ARTWORK-NOTICE.md); the refinement grants no new artwork rights.
