#!/usr/bin/env python
from fuzzyui import fuzzyui

items = ["validator", "validator", "field", "config"]
initial_search = 'validators'

fui = fuzzyui()
found = fui.find(items, initial_search)
print(found)
assert found == 'validator'
