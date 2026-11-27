"""Brand shell: kit header, icons, theme, and the operator flag."""

from __future__ import annotations

BOOKING_URL = (
    "https://calendar.google.com/calendar/appointments/schedules/"
    "AcZssZ3r5LJ7bPLsMMNRH2fcH9DkzDNTf8oA8XIg0NX9aNpoKezPGMN2Z2OTD-baqG9XoB5vfehzJnzt"
    "?gv=true"
)
BOOKING_LINK = f'href="{BOOKING_URL}" target="_blank" rel="noopener noreferrer"'


def _exit_tag(html: str) -> str:
    """Return the opening tag of the header exit link."""
    start = html.find('id="demo-exit"')
    assert start != -1
    open_at = html.rfind("<a", 0, start)
    return html[open_at:html.find(">", start) + 1]


def test_page_links_the_three_icons_and_no_google_fonts(client) -> None:
    html = client.get("/").text
    assert 'rel="icon"' in html
    assert 'type="image/svg+xml"' in html
    assert "demo-kit/favicon.svg" in html
    assert 'type="image/png"' in html
    assert 'sizes="32x32"' in html
    assert "demo-kit/favicon-32.png" in html
    assert 'rel="apple-touch-icon"' in html
    assert "demo-kit/apple-touch-icon.png" in html
    assert 'name="theme-color"' in html
    assert "fonts.googleapis.com" not in html
    assert "fonts.gstatic.com" not in html
    assert "fonts.google.com" not in html
    for name in ("favicon.svg", "favicon-32.png", "apple-touch-icon.png"):
        icon = client.get(f"/demo-kit/{name}")
        assert icon.status_code == 200


def test_header_uses_the_wordmark_product_and_footer(client) -> None:
    html = client.get("/").text
    assert "RoxanaTapia" in html
    assert 'class="dk-wordmark-dev">.dev' in html
    assert 'class="dk-product">Receipt Intelligence' in html
    assert "Portfolio demo · fictional shops · demo currency (DC)" in html
    assert 'id="demo-exit" href="https://roxanatapia.dev/"' in html
    assert 'class="dk-exit-visitor">Back to portfolio</span>' in html
    assert 'class="dk-exit-ops">Log out</span>' in html
    assert "Exit demo" not in html
    assert "/invite/exit" not in html
    assert "/ops/logout" not in html
    exit_tag = _exit_tag(html)
    assert "target=" not in exit_tag
    assert "btn-primary" not in exit_tag
    css = client.get("/demo-kit/demo-kit.css").text
    assert ".dk-exit-ops {\n  display: none;" in css
    assert 'html[data-operator="true"] .dk-exit-visitor {\n  display: none;' in css
    assert 'html[data-operator="true"] .dk-exit-ops {\n  display: inline;' in css
    assert 'html[data-operator="true"] .dk-exit {\n  padding: 0 14px;' in css
    footer = html.split('class="dk-footer-slot"', 1)[1].split("</div>", 1)[0]
    assert footer.count("<a ") == 3
    assert footer.index("Built by Roxana Tapia") < footer.index("How it's built")
    assert footer.index("How it's built") < footer.index("Book a call")
    assert 'href="https://roxanatapia.dev/">Built by Roxana Tapia</a>' in footer
    assert 'href="https://roxanatapia.dev/cases/receipts">How it\'s built</a>' in footer
    assert f"{BOOKING_LINK}>Book a call</a>" in footer
    assert 'href="https://roxanatapia.dev/cases/receipts" target=' not in html
    assert html.count('href="https://roxanatapia.dev/"') == 3
    assert "demo-kit/theme-init.js" in html
    assert "demo-kit/theme.js" in html
    assert "demo-kit/motion.js" in html
    assert "demo-kit/demo-kit.css" in html
    assert "demo-kit/ops-heartbeat.js" not in html
    assert "data-operator" not in html
    assert 'class="dk-enter"' in html


def test_end_card_book_a_call_opens_the_booking_page(client) -> None:
    html = client.post(
        "/ask",
        data={
            "question": "How much did I spend on snacks in August?",
            "start": "2026-07-01",
            "end": "2026-08-31",
        },
    ).text
    assert 'id="end-card"' in html
    assert f'<a class="btn-secondary" {BOOKING_LINK}>Book a call</a>' in html
    assert html.count(BOOKING_LINK) == 2
    assert 'href="https://roxanatapia.dev/">Book a call</a>' not in html
    assert "Exit demo" not in html
    assert "/invite/exit" not in html
    assert "or leave the demo" not in html


def test_operator_header_sets_the_flag_and_loads_the_heartbeat(client) -> None:
    html = client.get("/", headers={"X-Ops-Ok": "1"}).text
    assert 'data-operator="true"' in html
    assert 'id="demo-exit" href="/ops/logout"' in html
    assert 'class="dk-exit-ops">Log out</span>' in html
    assert 'class="dk-exit-visitor">Back to portfolio</span>' in html
    assert "demo-kit/ops-heartbeat.js" in html
    assert "Exit demo" not in html
    assert html.count('href="https://roxanatapia.dev/"') == 2
    theme = client.get("/demo-kit/theme.js")
    assert theme.status_code == 200
    assert 'link.setAttribute("href", "/ops/logout")' in theme.text


def test_operator_header_ignores_an_explicit_no(client) -> None:
    html = client.get("/", headers={"X-Ops-Ok": "false"}).text
    assert "data-operator" not in html
    assert "ops-heartbeat.js" not in html
    assert 'id="demo-exit" href="https://roxanatapia.dev/"' in html
    assert 'href="/invite/exit"' not in html
    assert "/ops/logout" not in html


def test_kit_fonts_are_same_origin(client) -> None:
    css = client.get("/demo-kit/demo-kit.css")
    assert css.status_code == 200
    text = css.text
    assert 'url("fonts/plus-jakarta-sans-latin.woff2")' in text
    assert 'url("fonts/bricolage-grotesque-latin.woff2")' in text
    assert "fonts.googleapis.com" not in text
    assert "fonts.gstatic.com" not in text
    for name in (
        "fonts/plus-jakarta-sans-latin.woff2",
        "fonts/bricolage-grotesque-latin.woff2",
    ):
        font = client.get(f"/demo-kit/{name}")
        assert font.status_code == 200
        assert font.headers["content-type"].startswith("font/woff2")
        assert len(font.content) > 100
