import bbcode
from icecream import ic
import requests
import time
from xml.sax.saxutils import escape
from generator import renderer
import base64


def item_body(body, auction_title, game_link="", game_title="", wishlist_level=-1):
    rendered_body = renderer.do_render(body)
    ic(game_title)
    return "".join(
        [
            f"{rendered_body}<br/><br/>",
            f"<hr><b>Auction Source:</b> {auction_title}<br/>",
            f"<b>Game Link:</b> <a href='{game_link}'>{game_title}</a><br/>"
            if game_link
            else "",
            f"<b>Wishlist Level:</b> {wishlist_level}" if wishlist_level else "",
            f"<div class='original_body' style='display: none;'>{base64.b64encode(body.encode())}</div>",
        ]
    )


def item(id, title, link, author, item_body, pub_date, site_url):
    return f"""
        <item>
            <id>{id}</id>
            <title>{title}</title>
            <link>{link}</link>
            <author>{author}</author>
            <description>{escape(item_body)}</description>
            <pubDate>{pub_date}</pubDate>
            <site_url>{site_url}</site_url>
        </item>"""


def feed(title, link, description, items):
    return f"""<?xml version='1.0' encoding='UTF-8' ?>
        <rss version='2.0'>
            <channel>
            <title>{title}</title>
            <link>{link}</link>
            <description>{description}</description>
            {''.join(items)}
            </channel>
        </rss>"""
