import generator.renderer as renderer


def test_default_thing():
    id = 276169
    exp = f'<a href="https://boardgamegeek.com/boardgame{id}>For What Remains</a>'
    assert renderer.do_render(f"[thing={id}][/thing]")

def test_custom_thing():
    id = 276169
    exp = f'<a href="https://boardgamegeek.com/boardgame{id}>Custom Thing</a>'
    assert renderer.do_render(f"[thing={id}]Custom Thing[/thing]")
