#!/usr/bin/env python

import datetime
import math
import requests
import xmltodict
import json
import time
import sqlite3
import os
from icecream import ic

from generator import bgg
from generator import wishlist
from generator import auctions
from generator import templates


class Generator:
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__))
    )

    username = None
    users_dir = os.path.join(__location__, "users")
    old = None
    feed = None

    db = None
    k_tables = {
        "timer": {"tn": "timer", "username": "username", "time": "last_request_time"},
        "old_auctions": {
            "tn": "old_auctions",
            "username": "username",
            "auction_id": "auction_id",
        },
    }
    k_table_dict = {"tn": "timer", "username": "username", "time": "last_request_time"}
    k_username = 0
    k_time = 1

    debugging = False
    feed_debugging = False

    def __init__(self, username, link="", debugging=False, feed_debugging=False):
        ic("generator init", username, link, debugging, feed_debugging)
        self.username = username
        self.link = link
        self.old = os.path.join(self.users_dir, self.username + "_old")
        self.feed = os.path.join(self.users_dir, self.username + ".xml")
        db_path = os.path.join(self.users_dir, "db.sqlite")
        ic(db_path)
        self.db = sqlite3.connect(db_path)
        self.debugging = debugging
        self.feed_debugging = feed_debugging

        # Create the table if it does not exist.
        c = self.db.cursor()
        c.execute(
            (
                "CREATE TABLE IF NOT EXISTS {tn} ("
                "{username} TEXT UNIQUE NOT NULL,"
                "{time} INTEGER"
                ")"
            ).format(**self.k_tables["timer"])
        )
        c.execute(
            (
                "CREATE TABLE IF NOT EXISTS {tn} ("
                "{username} TEXT NOT NULL,"
                "{auction_id} TEXT NOT NULL"
                ")"
            ).format(**self.k_tables["old_auctions"])
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
        if ic(row):
            # Get the date from the row.
            prev_time = datetime.datetime.fromtimestamp(row[self.k_time])
            minimum_next_time = prev_time + datetime.timedelta(minutes=5)
            if datetime.datetime.now() < minimum_next_time:
                try:
                    with open(self.feed) as fd:
                        ic("returning cached feed")
                        ic(self.feed)
                        return fd.read()
                except FileNotFoundError:
                    id("FILE IS MISSING")

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
        else:
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
        ic(game)
        site_url = f"https://boardgamegeek.com/geeklist/{game['auction_id']}"
        item_url = site_url + f"/item/{game['@id']}#item{game['@id']}"
        title = game["@objectname"]
        item_body = templates.item_body(
            game["body"],
            game["auction_title"],
            game_link=f'https://boardgamegeek.com/boardgame/{game["game_object_id"]}',
            game_title=title,
            wishlist_level=game["wishlist_status"],
            include_hashed_content=self.feed_debugging,
        )
        author = game["@username"]
        pubDate = game["@postdate"]
        return templates.item(
            game["auction_id"] + "_" + game["@id"],
            title,
            item_url,
            author,
            item_body,
            pubDate,
            site_url,
        )

    def _get_old_auctions(self):
        c = self.db.cursor()
        c.execute(
            'SELECT {auction_id} FROM {tn} WHERE {username}="{username_q}"'.format(
                username_q=self.username, **self.k_tables["old_auctions"]
            )
        )
        return [i[0] for i in c.fetchall()]

    def _update_old_auctions(self, old_auctions):
        c = self.db.cursor()
        for auction_id in old_auctions:
            c.execute(
                "INSERT INTO {tn} values (?, ?)".format(
                    **self.k_tables["old_auctions"]
                ),
                (self.username, auction_id),
            )
        self.db.commit()

    def generate(self):
        self._update_last_time()

        # Get metalist.
        metalist_json = self._get_metalist()

        # Create datastructure for auctions.
        old = ic(self._get_old_auctions())
        to_post = {}

        # Get new auctions (just one to start).
        for item in metalist_json["item"]:
            auction_id = item["@objectid"]

            if item["@objecttype"] != "geeklist":
                ic(auction_id, "skipping item", item["@objecttype"])
                continue

            # Skip this auction if we have already looked at it.
            is_old = auction_id in old
            is_closed = "closed" in item["@objectname"].lower()
            if (is_old or is_closed) and not self.debugging:
                label = "other"
                if is_old:
                    label = "old"
                elif is_closed:
                    label = "closed"
                ic(auction_id, label)
                continue

            # Get games in new auctions.
            auction_url = bgg.apiv1 + "geeklist/" + auction_id
            ic(auction_id, auction_url)

            # Get the auction and wait for a good status code.
            auction_request = requests.get(auction_url)
            while auction_request.status_code == 202:
                auction_request = requests.get(auction_url)
                ic(auction_id, auction_request.status_code)

            auction_data = auction_request.text
            try:
                auction_json = xmltodict.parse(auction_data)["geeklist"]
                ic(auction_id, f"processed", auction_json["title"])
            except Exception as e:
                ic(
                    auction_id,
                    "failure to process auction",
                    auction_request.status_code,
                    e,
                )
                continue

            # Pull and parse the text.
            # Pull all the games in from this auction into a specific dict.
            to_post[auction_id] = auction_json
            time.sleep(0.25)

        # Write out the old ids.
        if not self.debugging:
            self._update_old_auctions(to_post.keys())

        ic("going to post:", len(to_post.keys()))

        # Get games in wishlist.
        wishlist_json = wishlist.get(self.username)

        # Intersection between new auctions and wishlist.
        games = []

        # Loop through all auctions to post.
        for auction_id, auction_data in to_post.items():
            # Loop through all items in the auction.
            games += auctions.wishlist_intersection(
                wishlist_json, auction_id, auction_data
            )

        # List of items.
        items = [self._convert_item(game) for game in games]

        title = self.username + "'s Wishlist-Auction Matches"
        description = "Aggregates auctions for " + self.username
        link = self.link
        feed_final = templates.feed(title, link, description, items)
        if self.feed_debugging:
            with open(self.feed, "w") as fd:
                ic(fd.name)
                fd.write(feed_final)

        return feed_final


if __name__ == "__main__":
    ic(Generator("miloshot").generate())
