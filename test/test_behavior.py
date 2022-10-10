from fuzzyui import fuzzyui


def test_1_match_immediately_returns_no_ui():
    items = ["validator", "field", "config"]
    initial_search = 'validators'
    fzf = fuzzyui()
    found = fzf.find(items, initial_search)
    assert found == 'validator'
