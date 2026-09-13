# Cosmos — original natural space

Five original, full-screen braille compositions created for ascii-save with Codex. Natural celestial subjects only: Corona, Spiral, Ringed Giant, Pillars, and Crescent. No downloaded images, third-party artwork, captions, borders, or technology imagery. The code and generated art use the project's MIT license.

Each scene is composed on a 208-column × 56-row canvas. This fills the local 1920×1200 display with Foot at font size 11, leaving a small terminal margin. Empty regions are deliberate space within the composition. Artwork does not automatically resize on other displays.

```bash
foot --fullscreen --app-id=ascii-save.preview --font='monospace:size=11' -o colors-dark.background=080c14 python3 scripts/preview.py examples/cosmos --seconds 180
```

`colors-dark.background` is the current installed Foot syntax; omit that override on terminals using a different configuration schema. This is a temporary window with no saved desktop changes. Any key closes it. The existing preview supplies stock Omarchy random character effects and their colors; the text collection itself contains no animation or color escapes.

## Compositions

- **Corona:** a dark disk, sharp luminous rim, and extended uneven coronal streams.
- **Spiral:** an inclined galaxy with a bright central bulge, winding arms, and dark dust lanes.
- **Ringed Giant:** a shaded, banded globe within tilted rings, gaps, and cast shadows.
- **Pillars:** eroded molecular-cloud silhouettes edged by luminous, turbulent gas.
- **Crescent:** a large, partially cropped lunar limb with craters and a faint distant star band.

These are artistic interpretations, not observational images or physically accurate simulations. Shading is encoded as braille dot coverage; forms and shadows remain visible in monochrome.

## Source and regeneration

The original source is [scripts/create-cosmos.py](../../scripts/create-cosmos.py). It uses Python's standard library, mathematical fields, seeded noise, and direct braille drawing. No image converter or image-generation service is involved. `manifest.json` records dimensions, seeds, generator hash, and output hashes.

```bash
python3 scripts/create-cosmos.py --output collections/cosmos-regenerated
python3 scripts/validate.py collections/cosmos-regenerated
```

The output directory must not exist. For a smaller terminal, generate a separate collection with `--width 160 --height 44`. Shapes are recomposed for the selected aspect ratio. Retain the source code and MIT license with redistributed artwork. This workshop creates no persistent screensaver integration; removing a generated directory removes only its artwork.

## Review

All five final stills were inspected in an isolated fullscreen Foot terminal on the local 1920×1200 display. The first pass was revised to strengthen the corona rim, galaxy core, and planetary shading. Review captures remain private. Native idle/lock integration and multi-monitor behavior are not established by this artwork preview.

All five files passed snapshot validation and exact regeneration checks. The seven workshop tests and reference collection regression test passed.
