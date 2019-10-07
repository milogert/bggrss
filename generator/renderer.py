import bbcode
from icecream import ic
import requests
import time
import xmltodict
from generator import bgg
from generator import bgg_request


def thing_renderer(tag_name, value, options, parent, context):
    ic(tag_name, value, options, parent, context)
    thing_text = bgg_request.get(bgg.apiv2 + f"thing?id={options['thing']}")
    things_json = xmltodict.parse(thing_text)
    thing_json = things_json["items"]["item"]
    thing_type = thing_json["@type"]
    thing_id = thing_json["@id"]
    if value:
        thing_name = value
    else:
        name = thing_json["name"]
        if isinstance(name, list):
            name = name[0]
        thing_name = name["@value"]

    return (
        f'<a href="https://boardgamegeek.com/{thing_type}/{thing_id}>{thing_name}</a>'
    )


def size_renderer(tag_name, value, options, parent, context):
    return f'<span style="font-size: {int(options["size"]) * 1.4}px>{value}</span>'


def image_renderer(tag_name, value, options, parent, context):
    return f'<a href="https://boardgamegeek.com/image/{options["imageid"]}">Image {options["imageid"]}</a>'


def quote_renderer(tag_name, value, options, parent, context):
    style = "background-color: lightgray; padding: 1rem; border: 1px solid gray;"
    return f'<blockquote style="{style}">{value}</blockquote>'


def strike_renderer(tag_name, value, options, parent, context):
    return f"<s>{value}</s>"


def do_render(input_text, **context):
    # Installing simple formatters.
    parser = bbcode.Parser()
    # parser.add_simple_formatter('hr', '<hr />', standalone=True)
    # parser.add_simple_formatter('thing', '<a>%(value)s</sub>')

    # A custom render function.
    parser.add_formatter("thing", thing_renderer)
    parser.add_formatter("size", size_renderer)
    parser.add_formatter("imageid", image_renderer, standalone=True)
    parser.add_formatter("q", quote_renderer)
    parser.add_formatter("-", strike_renderer)

    # Calling format with context.
    return parser.format(input_text, **context)
