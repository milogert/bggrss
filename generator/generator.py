#!/usr/bin/env python

import bbcode
import requests
import xmltodict
import json
import time
import collections
from xml.sax.saxutils import escape

debugging = False

class Generator:
    root = 'http://www.boardgamegeek.com/xmlapi/'
    root2 = 'https://www.boardgamegeek.com/xmlapi2/'

    wishlist_root = root2 + 'collection?'
    wishlist_args = 'username={username}&wishlist=1'
    wishlist_url = wishlist_root + wishlist_args

    username = None
    old = None
    feed = None

    def __init__(self, username):
        self.username = username
        self.old = self.username + '_old'
        self.feed = self.username + '.xml'

    def generate(self):
        # Get metalist.
        metalist_json = {}
        while True:
            metalist_request = requests.get(self.root + 'geeklist/66420')
            print(metalist_request.status_code)
            if metalist_request.status_code != 200:
                time.sleep(1)
                continue

            metalist_json = xmltodict.parse(metalist_request.text)['geeklist']
            break

        # Create datastructure for auctions.
        old = []
        try:
            with open(self.username) as fd:
                old = json.load(fd)
            print('read in old file: ' + len(old))
        except:
            print('new `old` array')
        to_post = {}

        # Get new auctions (just one to start).
        counter = 0
        counter_limit = 10 if debugging else len(metalist_json['item'])
        while counter < counter_limit:
            item = metalist_json['item'][counter]
            auction_id = item['@objectid']
            print('checking auction', auction_id)
            
            # Skip this auction if we have already looked at it.
            if auction_id in old and not debugging:
                print('skip auction')
                counter = counter + 1
                continue

            # Get games in new auctions.
            auction_request = requests.get(self.root + 'geeklist/' + auction_id)

            # Move to the next loop if we are accepted but processing.
            if auction_request.status_code == 202:
                print('processing ' + auction_id)
                continue

            auction_data = auction_request.text
            try:
                auction_json = xmltodict.parse(auction_data)['geeklist']
                print('\tprocessed {}\t {}'.format(auction_id, auction_json['title']))
            except:
                print(auction_data)
                print(auction_request.status_code)
                import sys
                sys.exit()

            # Increment the counter.
            counter = counter + 1

            # Pull and parse the text.
            # Pull all the games in from this auction into a specific dict.
            if not debugging:
                old.append(auction_id)
            to_post[auction_id] = auction_json
            time.sleep(.25)

        # Write out the old ids.
        if not debugging:
            json.dump(old, open(self.old, 'w'))

        print('going to post:', len(to_post.keys()))

        wishlist_json = {}
        # Get games in wishlist.
        while True:
            wishlist_request = requests.get(self.wishlist_url.format(
                username=self.username
            ))
            print(wishlist_request.status_code)
            if wishlist_request.status_code != 200:
                time.sleep(1)
                continue

            wishlist_json = xmltodict.parse(wishlist_request.text)['items']['item']
            break

        # Intersection between new auctions and wishlist.
        wishlist_ids = [i['@objectid'] for i in wishlist_json]
        wishlist_map = {i['@objectid']: i for i in wishlist_json}
        games = []

        # Loop through all auctions to post.
        for auction_id, auction_data in to_post.items():
            # Loop through all items in the auction.
            for item in auction_data['item']:
                try:
                    item_id = item['@objectid']
                    if item_id in wishlist_map.keys():
                        # Get the wishlist status.
                        wishlist_status = wishlist_map[item_id]['status']['@wishlistpriority']
                        print(item_id, wishlist_status)
                        item.update({
                            'auction_id': auction_id,
                            'wishlist_status': wishlist_status
                        })
                        games.append(item)
                except:
                    continue

        feed = """<?xml version="1.0" encoding="UTF-8" ?>
        <rss version="2.0">

        <channel>
          <title>{title}</title>
          <link>{link}</link>
          <description>{description}</description>
          {items}
        </channel>

        </rss>"""

        item_tmpl = """
          <item>
            <id>{id}</id>
            <title>{title}</title>
            <link>{link}</link>
            <author>{author}</author>
            <description>{description}</description>
            <pubDate>{pubDate}</pubDate>
            <site_url>{site_url}</site_url>
          </item>"""

        site_fmt = 'https://www.boardgamegeek.com/geeklist/{geeklist}'
        link_fmt = site_fmt + '/item/{item}#item{item}'
        item_list = []
        for game in games:
            site_url = site_fmt.format(geeklist=game['auction_id'])
            item_link = link_fmt.format(
                geeklist=game['auction_id'],
                item=game['@id']
            )
            description = '{body}<br/><br/><hr>Wishlist Level: {wishlist_status}'.format(
                body=bbcode.render_html(game['body']),
                wishlist_status=game['wishlist_status']
            )
            item_list.append(item_tmpl.format(
                id=game['auction_id'] + '_' + game['@id'],
                title=game['@objectname'],
                link=item_link,
                author=game['@username'],
                description=escape(description),
                pubDate=game['@postdate'],
                site_url=site_url
            ))

        feed_final = feed.format(
            title='BGG Auction Aggregator',
            description='Aggregates auctions.',
            link='http://pig/bggrss/{feed}'.format(feed=self.feed),
            items='\n'.join(item_list)
        )

        with open(self.feed, 'w') as fd:
            fd.write(feed_final)

        return feed_final

if __name__ == '__main__':
    print(Generator('miloshot').generate())
