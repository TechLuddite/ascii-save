"""TerminalTextEffects Blackhole adapted for the opener: a coloured gallery is
consumed and the explosion forms a different picture (the Omarchy logo).

Requires terminaltexteffects==0.15.0 (MIT). Three departures from upstream
prepare_blackhole, kept as an override rather than a patched copy:
  1. every character keeps its own glyph instead of a random star symbol,
  2. starfield colour is the brightest gradient stop rather than random,
  3. characters start at their input position rather than a random one.
Input colours are preserved throughout with existing_color_handling="always".
explode_singularity swaps the targets for the logo characters, then hands
the motion back to upstream.

usage: blackhole.py MONTAGE.txt LOGO.json OUT_DIR [--cols 210 --rows 58 --seed 917]
writes OUT_DIR/NNNNN.txt frames and OUT_DIR/phases.json
"""
import argparse
import json
from pathlib import Path
import random

from terminaltexteffects import Color, Coord, EventHandler, Gradient, Scene, easing, geometry
from terminaltexteffects.effects.effect_blackhole import Blackhole, BlackholeIterator
from terminaltexteffects.utils.graphics import ColorPair


class GalleryIterator(BlackholeIterator):
    logo = {'cols': 0, 'rows': 0, 'cells': []}

    def prepare_blackhole(self):
        starfield_colors = Gradient(Color('#4a4a4d'), Color('#ffffff'), steps=6).spectrum
        gradient_map = {color: Gradient(color, Color('#000000'), steps=10) for color in starfield_colors}
        available = list(self.terminal._input_characters)
        while len(self.blackhole_chars) < self.blackhole_radius * 3 and available:
            self.blackhole_chars.append(available.pop(random.randrange(0, len(available))))
        ring = geometry.find_coords_on_circle(self.terminal.canvas.center, self.blackhole_radius, len(self.blackhole_chars))
        for index, character in enumerate(self.blackhole_chars):
            path = character.motion.new_path(path_id='blackhole', speed=0.7, ease=easing.in_out_sine)
            path.new_waypoint(ring[index])
            scene = character.animation.new_scene(scene_id='blackhole')
            scene.add_frame('*', 1, colors=ColorPair(fg=self.config.blackhole_color))
            character.event_handler.register_event(EventHandler.Event.PATH_ACTIVATED, path,
                                                   EventHandler.Action.SET_LAYER, 1)
            rotation = character.motion.new_path(path_id='blackhole_rotation', speed=0.45, loop=True)
            for coord in ring[index:] + ring[:index]:
                rotation.new_waypoint(coord, waypoint_id=str(len(rotation.waypoints)))
        for character in self.terminal.get_characters():
            self.terminal.set_character_visibility(character, is_visible=True)
            starting = character.animation.new_scene()
            symbol = character.input_symbol                      # (1)
            color = starfield_colors[-1]                         # (2)
            starting.add_frame(symbol, 1, colors=ColorPair(fg=color))
            character.animation.activate_scene(starting)
            if character not in self.blackhole_chars:
                character.motion.set_coordinate(character.input_coord)   # (3)
                singularity = character.motion.new_path(path_id='singularity', speed=random.uniform(0.17, 0.30),
                                                        ease=easing.in_expo)
                singularity.new_waypoint(self.terminal.canvas.center)
                consumed = character.animation.new_scene()
                for c in gradient_map[color]:
                    consumed.add_frame(symbol, 1, colors=ColorPair(fg=c))
                consumed.add_frame(' ', 1)
                consumed.sync = Scene.SyncMetric.DISTANCE
                character.event_handler.register_event(EventHandler.Event.PATH_ACTIVATED, singularity,
                                                       EventHandler.Action.SET_LAYER, 2)
                character.event_handler.register_event(EventHandler.Event.PATH_ACTIVATED, singularity,
                                                       EventHandler.Action.ACTIVATE_SCENE, consumed)
                self.awaiting_consumption_chars.append(character)
        random.shuffle(self.awaiting_consumption_chars)

    def explode_singularity(self):
        for ch in self.terminal.get_characters():
            self.terminal.set_character_visibility(ch, is_visible=False)
        width, height = self.logo['cols'], self.logo['rows']
        left = (self.terminal.canvas.width - width) // 2 + 1
        bottom = (self.terminal.canvas.height - height) // 2 + 1
        targets = []
        for y, row in enumerate(self.logo['cells']):
            for x, cell in enumerate(row):
                if not cell:
                    continue
                glyph, color = cell
                ch = self.terminal.add_character(glyph, Coord(left + x, bottom + height - y - 1))
                ch.motion.set_coordinate(self.terminal.canvas.center)
                self.terminal.set_character_visibility(ch, is_visible=True)
                self.character_final_color_map[ch] = Color(color)
                targets.append(ch)
        self.terminal._input_characters = targets
        self.active_characters.clear()
        super().explode_singularity()


class Gallery(Blackhole):
    @property
    def _iterator_cls(self):
        return GalleryIterator


def run(montage_text, logo, out_dir, cols=210, rows=58, seed=917, limit=6000):
    GalleryIterator.logo = logo
    random.seed(seed)
    effect = Gallery(montage_text)
    effect.terminal_config.canvas_width = cols
    effect.terminal_config.canvas_height = rows
    effect.terminal_config.anchor_canvas = 'c'
    effect.terminal_config.anchor_text = 'c'
    effect.terminal_config.ignore_terminal_dimensions = True
    effect.terminal_config.frame_rate = 0
    effect.terminal_config.existing_color_handling = 'always'
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob('*.txt'):
        old.unlink()
    it = iter(effect)
    (out / '00000.txt').write_text(it.frame)
    phases, count = [], 0
    for count, frame in enumerate(it, 1):
        (out / f'{count:05d}.txt').write_text(frame)
        if not phases or phases[-1]['phase'] != it.phase:
            phases.append({'frame': count, 'phase': it.phase})
        if count > limit:
            raise RuntimeError('unexpected animation length')
    (out / 'phases.json').write_text(json.dumps({'frame_count': count, 'phases': phases}, indent=1))
    return count, phases


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('montage')
    ap.add_argument('logo')
    ap.add_argument('out_dir')
    ap.add_argument('--cols', type=int, default=210)
    ap.add_argument('--rows', type=int, default=58)
    ap.add_argument('--seed', type=int, default=917)
    a = ap.parse_args()
    count, phases = run(Path(a.montage).read_text(), json.loads(Path(a.logo).read_text()), a.out_dir, a.cols, a.rows, a.seed)
    print(json.dumps({'frame_count': count, 'phases': phases}))


if __name__ == '__main__':
    main()
