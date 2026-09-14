# Giants in colour

All 17 portrait compositions and the Omarchy wordmark converted to truecolour
quadrant block text for the stock size-18 Foot screensaver (137×36 cells at
1920×1200). Every cell is one of 15 block-element glyphs with its own 24-bit
foreground and background, chosen as the best two-colour split of a 2×2 sample
grid, so the picture is effectively 274×72 pixels in full colour. Portraits are
127×36 cells with the painted names intact; the wordmark has its parchment
margins trimmed (20% fuzz) and is 137×33.

Files contain only SGR colour sequences and block glyphs, no cursor movement or
other controls. Play them with `ttfx --existing-color-handling dynamic` (or
`always`); the stock Omarchy renderer uses `ignore` and shows them without
colour. The pinned upstream preparer rejects escape sequences, so use
`scripts/omarchy-screensaver-prepare-color` or `scripts/validate.py --color`.

Regenerate from a clean checkout of the source repository pinned in
`manifest.json`:

```bash
python3 scripts/seed-giants-color.py /path/to/omarchy-giants-theme --output collections/giants-color
```

Giants artwork is **not covered by this repository's MIT license**. See
[ARTWORK-NOTICE.md](ARTWORK-NOTICE.md), [SOURCE-CREDITS.md](SOURCE-CREDITS.md), and
[manifest.json](manifest.json). Screenshots and original raster inputs remain private.
