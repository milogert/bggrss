def wishlist_intersection(wishlist_json, auction_id, auction_data):
    wishlist_map = {i["@objectid"]: i for i in wishlist_json}
    games_matched = []
    for item in auction_data["item"]:
        try:
            item_id = item["@objectid"]
            if item_id in wishlist_map.keys():
                # Get the wishlist status.
                wishlist_status = wishlist_map[item_id]["status"]["@wishlistpriority"]
                item.update(
                    {
                        "auction_id": auction_id,
                        "wishlist_status": wishlist_status,
                        "auction_title": auction_data["title"],
                    }
                )
                games_matched.append(item)
        except:
            continue

    return games_matched
