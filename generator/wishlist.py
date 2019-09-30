import requests
import xmltodict
from icecream import ic
from generator import bgg
from generator import bgg_request


def get(username="miloshot"):
    wishlist_text = bgg_request.get(bgg.apiv2 + f"collection?username={username}&wishlist=1")
    wishlist_items = xmltodict.parse(wishlist_text)["items"]
    if "item" not in wishlist_items:
        ic("not a real wishlist item set", wishlist_items)
        return {}

    return wishlist_items["item"]
