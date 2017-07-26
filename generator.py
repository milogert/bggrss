#!/usr/bin/env python

import requests
import xmltodict
import json
import time
import collections

root = 'http://www.boardgamegeek.com/xmlapi/'
root2 = 'https://www.boardgamegeek.com/xmlapi2/'

wishlist_root = root2 + 'collection?'
wishlist_args = 'username={username}&wishlist=1'
wishlist_url = wishlist_root + wishlist_args

# Get metalist.
metalist_json = {}
while True:
    metalist_request = requests.get(root + 'geeklist/66420')
    print(metalist_request.status_code)
    if metalist_request.status_code != 200:
        time.sleep(1)
        continue

    metalist_json = xmltodict.parse(metalist_request.text)['geeklist']
    break

# Create datastructure for auctions.
old = []
try:
    with open('old') as fd:
        old = json.load(fd)
    print('read in old file: ' + len(old))
except:
    print('new `old` array')
print('old: ' + json.dumps(old, indent=2))
to_post = {}

# Get new auctions (just one to start).
counter = 0
while counter < 10:#len(metalist_json['item']):
    time.sleep(.25)
    item = metalist_json['item'][counter]
    auction_id = item['@objectid']
    print('checking auction', auction_id)
    
    # Skip this auction if we have already looked at it.
    if auction_id in old:
        print('skip auction')
        counter = counter + 1
        continue

    # Get games in new auctions.
    #print(requests.get(root + 'geeklist/' + auction_id).textdd)
    auction_request = requests.get(root + 'geeklist/' + auction_id)

    # Move to the next loop if we are accepted but processing.
    if auction_request.status_code == 202:
        print('processing ' + auction_id)
        continue

    # Increment the counter.
    counter = counter + 1

    # Pull and parse the text.
    auction_data = auction_request.text
    try:
        auction_json = xmltodict.parse(auction_data)['geeklist']
        print('\tprocessed {}\t {}'.format(auction_id, auction_json['title']))
    except:
        print(auction_data)
        print(auction_request.status_code)
        import sys
        sys.exit()

    # Pull all the games in from this auction into a specific dict.
    old.append(auction_id)
    to_post[auction_id] = auction_json

# Write out the old ids.
print('old: ' + json.dumps(old, indent=2))
json.dump(old, open('./old', 'w'))

wishlist_json = {}
# Get games in wishlist.
while True:
    wishlist_request = requests.get(wishlist_url.format(
        username='miloshot'
    ))
    print(wishlist_request.status_code)
    if wishlist_request.status_code != 200:
        time.sleep(1)
        continue

    wishlist_json = xmltodict.parse(wishlist_request.text)['items']['item']
    break

# Intersection between new auctions and wishlist.
wishlist_ids = [i['@objectid'] for i in wishlist_json]
games = []
for auction_id, auction_data in to_post.items():
    for item in auction_data['item']:
        try:
            item.update({'auction_id': auction_id})
            item_id = item['@objectid']
            if item_id in wishlist_ids:
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
    <content>{content}</content>
    <updated>{updated}</updated>
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
    item_list.append(item_tmpl.format(
        id=game['auction_id'] + '_' + game['@id'],
        title=game['@objectname'],
        link=item_link,
        author=game['@username'],
        content=game['body'],
        updated=game['@postdate'],
        site_url=site_url
    ))

feed_final = feed.format(
    title='BGG Auction Aggregator',
    description='Aggregates auctions.',
    link='http://pig/bggrss/feed.xml',
    items='\n'.join(item_list)
)

with open('feed.xml', 'w') as fd:
    fd.write(feed_final)
