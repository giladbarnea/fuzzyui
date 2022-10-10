#!/usr/bin/env python3
import functools
import re
import sys
from typing import NoReturn

from blessed import Terminal

try:
    from rapidfuzz import fuzz
    from rapidfuzz import process as fuzzyprocess
except ModuleNotFoundError:
    from fuzzywuzzy import fuzz
    from fuzzywuzzy import process as fuzzyprocess

SCORE_CUTOFF = 30


class fuzzyui:

    def __init__(self, items: list[str] = None):
        self.items: list[str] = items or []
        self.term = None
        self.echo = functools.partial(print, end='', flush=True)
        self.fuzzysorted: list[tuple[str, int | float, int]] = []  # item, score, key

    def _setup_terminal(self) -> NoReturn:
        if sys.stdin.isatty():
            self.term = Terminal()
        else:
            from unittest.mock import MagicMock
            self.term = MagicMock()

    def _is_within_bounds(self, idx: int) -> bool:
        return len(self.fuzzysorted) > idx >= 0

    def _highlight_input_characters(self, item, input_string: str, is_idx=False) -> NoReturn:
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

    def _render(self, idx, input_string: str) -> NoReturn:
        extracted_matches: list[tuple[str, int | float, int]] = fuzzyprocess.extract(input_string, self.items, limit=len(self.items), scorer=fuzz.token_sort_ratio, score_cutoff=SCORE_CUTOFF)
        self.fuzzysorted = extracted_matches
        # Clear screen
        self.echo(self.term.home + self.term.clear)
        # Set bottom height for list to be displayed
        #   idx is set to 0 for the bottom item in find(), incremented + when going up
        #   which keeps this functional and reasonably sanely implemented
        self.echo(self.term.move_xy(0, self.term.height - 3))

        # fuzzysorted reutrns an array of tuples: [('one', 45), ('three', 45), ('two', 0)]
        displayed_items_count = 0
        for index, (item, score, key) in enumerate(self.fuzzysorted):
            # If there's no input_string filter, output everything
            if score >= SCORE_CUTOFF or input_string == "":
                displayed_items_count += 1
                if index == idx:
                    self.echo(self.term.red_on_grey30("> "))
                    self._highlight_input_characters(item, input_string, is_idx=True)
                else:
                    self.echo(self.term.snow_on_grey30(" ") + " ")
                    self._highlight_input_characters(item, input_string)
                self.echo(self.term.move_x(0) + self.term.move_up(1))

        # Count of how many displayed vs total passed in
        self.echo(self.term.move_xy(0, self.term.height - 2) + f"{displayed_items_count}/{len(self.items)}")
        # Bottom display prompt
        self.echo(self.term.move_xy(0, self.term.height - 1) + f"> {input_string}\u2588")

    def find(self, items: list[str], searchtext: str = ""):
        self._setup_terminal()
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
                    self._render(idx, input_string)

                if len(self.fuzzysorted) == 1:
                    selected_value = self.fuzzysorted[0][0]
                    break
                if inp.code == self.term.KEY_DOWN:
                    if self._is_within_bounds(idx - 1):
                        idx -= 1
                        dirty = True
                elif inp.code == self.term.KEY_UP:
                    if self._is_within_bounds(idx + 1):
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
