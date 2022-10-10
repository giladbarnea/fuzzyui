#!/usr/bin/env python3
import functools
import re
from typing import NoReturn

from blessed import Terminal
from fuzzywuzzy import process as fuzzyprocess


class fuzzyui:

    def __init__(self, items=None):
        self.items = items or []
        self.term = None
        self.echo = functools.partial(print, end='', flush=True)
        self.fuzzysorted = []

    def is_within_bounds(self, idx) -> bool:
        return len(self.fuzzysorted) > idx >= 0

    def render(self, idx, input_string: str) -> NoReturn:
        self.fuzzysorted = fuzzyprocess.extract(input_string, self.items, limit=len(self.items))
        # Clear screen
        self.echo(self.term.home + self.term.clear)
        # Set bottom height for list to be displayed
        #   idx is set to 0 for the bottom item in find(), incremented + when going up
        #   which keeps this functional and reasonably sanely implemented
        self.echo(self.term.move_xy(0, self.term.height - 3))

        # fuzzysorted reutrns an array of tuples: [('one', 45), ('three', 45), ('two', 0)]
        displayed_items_count = 0
        for index, item in enumerate(self.fuzzysorted):
            # If there's no input_string filter, output everything
            if item[1] >= 30 or input_string == "":
                displayed_items_count += 1
                if index == idx:
                    self.echo(self.term.red_on_grey30("> "))
                    self.highlight_input_characters(item[0], input_string, is_idx=True)
                else:
                    self.echo(self.term.snow_on_grey30(" ") + " ")
                    self.highlight_input_characters(item[0], input_string)
                self.echo(self.term.move_x(0) + self.term.move_up(1))

        # Count of how many displayed vs total passed in
        self.echo(self.term.move_xy(0, self.term.height - 2) + f"{displayed_items_count}/{len(self.items)}")
        # Bottom display prompt
        self.echo(self.term.move_xy(0, self.term.height - 1) + f"> {input_string}\u2588")

    def highlight_input_characters(self, item, input_string, is_idx=False) -> NoReturn:
        """Make the letters that match input_string stand out a bit more"""
        if input_string:
            pattern = re.compile(fr'[{input_string}]')
            for elem in map(str, item):
                pattern_matches = pattern.match(elem)
                if is_idx:  # Index pattern match
                    if pattern_matches:
                        self.echo(self.term.snow_on_grey30(elem))
                    else:
                        self.echo(self.term.grey60_on_grey30(elem))
                else:  # Non-index pattern match
                    if pattern_matches:
                        self.echo(self.term.grey60(elem))
                    else:
                        self.echo(elem)
        else:  # No input_string
            if is_idx:
                self.echo(self.term.on_grey30(str(item)))
            else:
                self.echo(str(item))

    def find(self, items, searchtext: str = ""):
        self.term = Terminal()
        self.items = items
        with self.term.fullscreen(), self.term.hidden_cursor(), self.term.cbreak():
            idx = 0
            input_string = searchtext
            selected_value = None
            dirty = True
            inp = None
            while True:
                inp = self.term.inkey(timeout=.05)

                if dirty:
                    self.render(idx, input_string)

                if inp.code == self.term.KEY_DOWN:
                    if self.is_within_bounds(idx - 1):
                        idx -= 1
                        dirty = True
                elif inp.code == self.term.KEY_UP:
                    if self.is_within_bounds(idx + 1):
                        idx += 1
                        dirty = True
                elif inp.code == self.term.KEY_ESCAPE:
                    selected_value = None
                    break
                elif inp.code == self.term.KEY_ENTER:
                    selected_value = self.fuzzysorted[idx][0]
                    break
                elif re.match(r'^[a-zA-z-_. ]{1}$', inp):
                    dirty = True
                    input_string += inp
                    idx = 0
                elif inp.code == self.term.KEY_BACKSPACE:
                    dirty = True
                    input_string = input_string[:-1]
                    idx = 0
                else:
                    dirty = False

        self.term.exit_fullscreen()
        self.term = None
        return selected_value


if __name__ == "__main__":
    fzf = fuzzyui()
    return_value = fzf.find(['one', 'two', 'three'], 'tw')
    print(return_value)
