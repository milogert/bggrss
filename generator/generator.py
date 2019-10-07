#!/usr/bin/env python

import datetime
import math
import requests
import xmltodict
import json
import time
from xml.sax.saxutils import escape
import sqlite3
import os
from icecream import ic

from generator import renderer
from generator import bgg
from generator import wishlist
from generator import auctions

# from generator import renderer, bgg

debugging = True


class Generator:
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__))
    )

    username = None
    users_dir = os.path.join(__location__, "users")
    old = None
    feed = None

    db = None
    k_table_dict = {"tn": "timer", "username": "username", "time": "last_request_time"}
    k_username = 0
    k_time = 1

    def __init__(self, username, link=""):
        self.username = username
        self.link = link
        self.old = os.path.join(self.users_dir, self.username + "_old")
        self.feed = os.path.join(self.users_dir, self.username + ".xml")
        db_path = os.path.join(self.users_dir, "db.sqlite")
        ic(db_path)
        self.db = sqlite3.connect(db_path)

        # Create the table if it does not exist.
        c = self.db.cursor()
        c.execute(
            (
                "CREATE TABLE IF NOT EXISTS {tn} ("
                "{username} TEXT UNIQUE NOT NULL,"
                "{time} INTEGER"
                ")"
            ).format(**self.k_table_dict)
        )
        self.db.commit()

    def _update_last_time(self):
        # Check last request time.
        c = self.db.cursor()
        c.execute(
            'SELECT * FROM {tn} WHERE {username}="{username_q}"'.format(
                username_q=self.username, **self.k_table_dict
            )
        )
        row = c.fetchone()
        if not row:
            ic("no row found, inserting")
            c.execute(
                (
                    "INSERT INTO {tn} ({username}, {time})"
                    'VALUES ("{username_n}", {time_n})'
                ).format(
                    username_n=self.username,
                    time_n=math.ceil(time.time()),
                    **self.k_table_dict,
                )
            )
            self.db.commit()
        else:
            ic("row found")
            # Get the date from the row.
            prev_time = datetime.datetime.fromtimestamp(row[self.k_time])
            minimum_next_time = prev_time + datetime.timedelta(minutes=5)
            if datetime.datetime.now() < minimum_next_time:
                with open(self.feed) as fd:
                    ic("returning cached feed")
                    ic(self.feed)
                    return fd.read()

            ic("updating row")
            c.execute(
                (
                    "UPDATE {tn}\n"
                    "SET {time} = {time_n}\n"
                    'WHERE {username} = "{username_q}"'
                ).format(
                    time_n=math.ceil(time.time()),
                    username_q=self.username,
                    **self.k_table_dict,
                )
            )
            self.db.commit()

    def _get_metalist(self):
        while True:
            metalist_url = bgg.apiv1 + "geeklist/66420"
            ic(metalist_url)
            metalist_request = requests.get(metalist_url)
            if metalist_request.status_code != 200:
                time.sleep(1)
                continue

            return xmltodict.parse(metalist_request.text)["geeklist"]

    def _convert_item(self, game):
        site_url = f"https://boardgamegeek.com/geeklist/{game['auction_id']}"
        item_url = site_url + f"/item/{game['@id']}#item{game['@id']}"
        description = (
            f"{renderer.do_render(game['body'])}<br/><br/>"
            f"<hr><b>Auction Source:</b> {game['auction_title']}<br/>"
            f"<b>Wishlist Level:</b> {game['wishlist_status']}"
        )
        title = game["@objectname"]
        author = game["@username"]
        pubDate = game["@postdate"]
        return f"""
            <item>
                <id>{game["auction_id"] + "_" + game["@id"]}</id>
                <title>{title}</title>
                <link>{item_url}</link>
                <author>{author}</author>
                <description>{escape(description)}</description>
                <pubDate>{pubDate}</pubDate>
                <site_url>{site_url}</site_url>
            </item>
        """

    def generate(self):
        self._update_last_time()

        # Get metalist.
        metalist_json = self._get_metalist()

        # Create datastructure for auctions.
        old = []
        try:
            with open(self.old) as old_fd:
                old = json.load(old_fd)
            ic(old_fd, old)
        except (IOError, TypeError) as e:
            ic("new `old` array", e.strerror)
        to_post = {}

        # Get new auctions (just one to start).
        counter = 0
        counter_limit = 10 if debugging else len(metalist_json["item"])
        ic("checking auctions... ")
        while counter < counter_limit:
            item = metalist_json["item"][counter]
            auction_id = item["@objectid"]
            ic(auction_id)

            # Skip this auction if we have already looked at it.
            is_old = auction_id in old
            is_closed = "closed" in item["@objectname"].lower()
            if (is_old or is_closed) and not debugging:
                label = "other"
                if is_old:
                    label = "old"
                elif is_closed:
                    label = "closed"
                ic(label)
                counter = counter + 1
                continue

            # Get games in new auctions.
            auction_url = bgg.apiv1 + "geeklist/" + auction_id
            ic(auction_url)
            auction_request = requests.get(auction_url)

            # Move to the next loop if we are accepted but processing.
            if auction_request.status_code == 202:
                ic(auction_id)
                continue

            auction_data = auction_request.text
            try:
                auction_json = xmltodict.parse(auction_data)["geeklist"]
                # ic(auction_json)
                ic(f"processed {auction_id}\t {auction_json['title']}")
            except Exception as e:
                ic("failure to process auction", auction_request.status_code, e)
                counter = counter + 1
                continue

            # Increment the counter.
            counter = counter + 1

            # Pull and parse the text.
            # Pull all the games in from this auction into a specific dict.
            if not debugging:
                old.append(auction_id)
            to_post[auction_id] = auction_json
            time.sleep(0.25)

        # Write out the old ids.
        if not debugging:
            ic("writing processed auctions to", self.old)
            json.dump(old, open(self.old, "w"))

        ic("going to post:", len(to_post.keys()))

        # Get games in wishlist.
        wishlist_json = wishlist.get()

        # Intersection between new auctions and wishlist.
        games = []

        # Loop through all auctions to post.
        for auction_id, auction_data in to_post.items():
            # Loop through all items in the auction.
            games += auctions.wishlist_intersection(
                wishlist_json, auction_id, auction_data
            )

        # List of items.
        item_list = [self._convert_item(game) for game in games]

        title = self.username + "'s Wishlist-Auction Matches"
        description = "Aggregates auctions for " + self.username
        link = self.link
        items = "\n".join(item_list)
        feed_final = f"""<?xml version='1.0' encoding='UTF-8' ?>
            <rss version='2.0'>
            <channel>
            <title>{title}</title>
            <link>{link}</link>
            <description>{description}</description>
            {items}
            </channel>
            </rss>"""

        with open(self.feed, "w") as fd:
            ic(fd.name)
            fd.write(feed_final)

        return feed_final


if __name__ == "__main__":
    ic(Generator("miloshot").generate())
