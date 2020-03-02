import base64
import bbcode
from icecream import ic
import requests
import time
from xml.sax.saxutils import escape

from generator import renderer


def item_body(
    body,
    auction_title,
    game_link="",
    game_title="",
    wishlist_level=-1,
    include_hashed_content=False,
):
    rendered_body = renderer.do_render(body)
    ic(game_title)
    return "".join(
        [
            f"{rendered_body}<br/><br/>",
            f"<hr>",
            f"<div><b>Auction Source:</b> {auction_title}</div>",
            f"<div><b>Game Link:</b> <a href='{game_link}'>{game_title}</a></div>"
            if game_link
            else "",
            f"<div><b>Wishlist Level:</b> {wishlist_level}</div>"
            if wishlist_level
            else "",
            f"<hr><h3>Original Content</h3><pre>{base64.b64encode(body.encode())}</pre>"
            if include_hashed_content
            else "",
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
