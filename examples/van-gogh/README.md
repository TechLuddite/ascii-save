# Vincent van Gogh — eight paintings in braille

The second artist collection follows Giants with eight paintings from The Met: Wheat Field with Cypresses, Self-Portrait with a Straw Hat, Shoes, Roses, Women Picking Olives, L’Arlésienne, Oleanders, and Peasant Woman Cooking by a Fireplace. This is an initial selection, not a complete catalog of Van Gogh’s work.

```bash
python3 scripts/validate.py examples/van-gogh
foot --fullscreen --app-id=ascii-save.preview --font='monospace:size=11' python3 scripts/preview.py examples/van-gogh --seconds 180
```

Any key closes the temporary preview. It cycles in numeric filename order with stock Omarchy’s random `ttfx` character effects at 120 fps. Each completed effect advances to the next painting. Add `--effect highlight` for the gentle sepia treatment. Each painting carries its title and date. This collection is ready for terminal playback; native idle activation remains separate work.

## Conversion

The installed Omarchy converter produces braille at a maximum of 140 columns × 44 art rows, threshold 55, without trimming the source composition. Two additional lines hold spacing and a caption. Aspect ratios are preserved by the converter; paintings occupy different widths. Colors come from the selected effect, not the original painting. The optional highlight effect uses sepia. Thresholding loses some brushwork and shadow detail.

Source images are the museum’s web-size JPEGs. See [source credits](SOURCE-CREDITS.md), [artwork notice](ARTWORK-NOTICE.md), and `manifest.json` for provenance, exact image URLs, source hashes, converter hash, and ImageMagick version.

## Regenerate locally

Download each `source_url` in `manifest.json` into a private directory using its `source` filename (for example, `436535.jpg`). No original images need to be committed. The current workstation’s private source folder is recorded in its local handoff.

```bash
python3 scripts/seed-van-gogh.py /path/to/local-jpegs --output collections/van-gogh-regenerated
```

The output directory must not exist. The seeder performs no network access. It rejects symlinks, special files, changing files, oversized inputs, and source hash mismatches, then converts private temporary snapshots with the installed converter. All generated artwork must match the recorded output hashes and pass the reference preparer before an output collection is created. Different tool versions may produce different output; investigate rather than overwriting the baseline. Removing the generated directory uninstalls nothing because this workflow adds no desktop integration.

## Verification

On 2026-09-13: all eight files passed snapshot validation and offline regeneration reproduced every output hash. The seven workshop unit tests and reference collection regression test passed. A local fullscreen Foot/real-ttfx spot check at 1920×1200 confirmed braille and caption fit; this is not a visual review of every completed animation. Multi-monitor playback and automatic idle-to-lock behavior have not been tested for this collection. Captures remain private.
