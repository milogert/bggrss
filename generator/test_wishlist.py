from generator import wishlist
from icecream import ic


def test_wishlist():
    wl = wishlist.get()
    assert len(wl) > 0
    assert all(v == '1' for v in [i['status']['@wishlist'] for i in wl])

