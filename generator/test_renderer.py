import generator.renderer as renderer
import pytest


@pytest.mark.parametrize(
    "id, name, title",
    [(276169, "", "For What Remains"), (276169, "Custom Title", "Custom Title")],
)
def test_thing(id, name, title):
    exp = f'<a href="https://boardgamegeek.com/boardgame/{id}">{title}</a>'
    assert renderer.do_render(f"[thing={id}]{name}[/thing]") == exp


def test_size():
    size = 1
    value = "test"
    exp = f'<span style="font-size: 1.4px">{value}</span>'
    assert renderer.do_render(f"[size={size}]{value}[/size]") == exp


@pytest.mark.parametrize("tag, id", [("ImageID", 100), ("imageid", 1000)])
def test_image(tag, id):
    exp = f'<a href="https://boardgamegeek.com/image/{id}">Image {id}</a>'
    assert renderer.do_render(f"[{tag}={id}]") == exp


def test_quote():
    value = "test"
    style = "background-color: lightgray; padding: 1rem; border: 1px solid gray;"
    exp = f'<blockquote style="{style}">{value}</blockquote>'
    assert renderer.do_render(f"[q]{value}[/q]") == exp


def test_strike():
    value = "test"
    exp = f"<s>{value}</s>"
    assert renderer.do_render(f"[-]{value}[/-]") == exp


@pytest.mark.parametrize("color", [("red"), ("#FFFFFF"), ("#aaa")])
def test_bgcolor(color):
    value = "test"
    exp = f"<span style='background-color: {color};'>{value}</span>"
    assert renderer.do_render(f"[bgcolor={color}]{value}[/bgcolor]") == exp
