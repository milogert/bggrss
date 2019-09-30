import bbcode
from icecream import ic
import requests
import time
import xmltodict


root2 = "https://boardgamegeek.com/xmlapi2/"


def thing_renderer(tag_name, value, options, parent, context):
    ic(tag_name, value, options, parent, context)
    thing_request = {}
    while True:
        thing_url = root2 + f"thing?id={options['thing']}"
        ic(thing_url)
        thing_request = requests.get(thing_url)
        if thing_request.status_code != 200:
            time.sleep(1)
            continue
        break

    things_json = xmltodict.parse(thing_request.text)
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


def do_render(input_text, **context):
    # Installing simple formatters.
    parser = bbcode.Parser()
    # parser.add_simple_formatter('hr', '<hr />', standalone=True)
    # parser.add_simple_formatter('thing', '<a>%(value)s</sub>')

    # A custom render function.
    parser.add_formatter("thing", thing_renderer)

    # Calling format with context.
    return parser.format(input_text, **context)
