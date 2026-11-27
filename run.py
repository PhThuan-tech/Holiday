"""Holiday ASCII launcher.

    python run.py                          # pick a theme from the menu
    python run.py new-year                 # run a theme directly
    python run.py birthday Alice 25        # extra arguments are passed to the theme
    python run.py --list                   # list themes

    python run.py new-year --record out.gif [--seconds 6] [--start 3]
    python run.py --record-all [docs/demo] # record a demo GIF for every theme
"""
import argparse
import importlib
import os
import sys

from engine import run

# name: (module, description, (demo start second, demo length in seconds))
THEMES = {
    "christmas-tree": ("themes.christmas_tree.scene",
                       "Rotating 3D Christmas tree with garland, baubles, gifts and snow", (8, 6)),
    "new-year": ("themes.new_year_fireworks.scene",
                 "Fireworks over a city skyline: 11 burst patterns + the year in sparks", (3, 7)),
    "lunar-new-year": ("themes.lunar_new_year.scene",
                       "Blooming peach / apricot branch, swaying lanterns, red envelopes", (9, 6)),
    "valentine": ("themes.valentine_heart.scene",
                  "Spinning, beating 3D heart with floating hearts", (2, 5)),
    "easter": ("themes.easter.scene",
               "Painted 3D eggs spinning in a basket, hopping bunny, butterflies", (2, 6)),
    "mid-autumn": ("themes.mid_autumn.scene",
                   "Giant moon, rotating star lanterns, sky lanterns, mooncakes", (3, 6)),
    "halloween": ("themes.halloween.scene",
                  "Jack-o'-lanterns, bats, ghosts, a spider, fog and lightning", (3, 7)),
    "winter": ("themes.winter.scene",
               "Snowman, log cabin, aurora and big rotating snowflakes", (3, 6)),
    "national-day": ("themes.national_day.scene",
                     "Vietnam 2/9: Ho Chi Minh Mausoleum, waving flag, sun, portrait  [photo]", (2, 5)),
    "birthday": ("themes.birthday.scene",
                 "Cake with candles to blow out, balloons, confetti  [name] [age]", (6, 7)),
}


def list_themes():
    for i, (name, (_, desc, _)) in enumerate(THEMES.items(), 1):
        print(f"  {i:>2}. {name:<16} {desc}")


def choose():
    print("Holiday ASCII - choose a theme:\n")
    list_themes()
    answer = input("\nNumber or name: ").strip()
    if answer.isdigit() and 1 <= int(answer) <= len(THEMES):
        return list(THEMES)[int(answer) - 1]
    return answer


def load_scene(name, extra):
    module = importlib.import_module(THEMES[name][0])
    return module.SCENE(*extra)


def record_one(name, extra, path, seconds, start):
    from engine.record import record
    demo_start, demo_seconds = THEMES[name][2]
    start = demo_start if start is None else start
    seconds = demo_seconds if seconds is None else seconds
    print(f"Recording {name} ({seconds}s from t={start}s) -> {path} ...", flush=True)
    size = record(load_scene(name, extra), path, seconds=seconds, start=start)
    print(f"  done, {size / 1e6:.1f} MB")


def main():
    parser = argparse.ArgumentParser(description="Animated holiday ASCII art.")
    parser.add_argument("theme", nargs="?", help="theme name (omit for a menu)")
    parser.add_argument("extra", nargs="*", help="extra arguments for the theme")
    parser.add_argument("-l", "--list", action="store_true", help="list themes")
    parser.add_argument("--record", metavar="FILE.gif", help="save a GIF instead of opening a window")
    parser.add_argument("--record-all", nargs="?", const="docs/demo", metavar="DIR",
                        help="save a demo GIF for every theme (default: docs/demo)")
    parser.add_argument("--seconds", type=float, help="length of the recording")
    parser.add_argument("--start", type=float, help="scene time where the recording starts")
    args = parser.parse_args()

    if args.list:
        list_themes()
        return
    if args.record_all:
        for name in THEMES:
            record_one(name, [], os.path.join(args.record_all, f"{name}.gif"), args.seconds, args.start)
        return

    name = args.theme or choose()
    if name not in THEMES:
        print(f"Unknown theme '{name}'. Available themes:")
        list_themes()
        sys.exit(1)
    if args.record:
        record_one(name, args.extra, args.record, args.seconds, args.start)
    else:
        run(load_scene(name, args.extra))


if __name__ == "__main__":
    main()
