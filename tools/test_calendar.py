#!/usr/bin/env python3
"""Check the arithmetic that turns a date into a day's readings.

The other tests hold the rules that judge a verse or a paragraph to cases a
reader ruled on. This one holds the plumbing around those rules to cases in
code: what a week's title says about its dates and its chapters, which day of
the Book of Mormon calendar lands on which verse, which manual and which
conference a date reaches for, which of a conference's links are talks, how
its quotes are spaced, how a passage is cited and linked.

None of it is hard, and all of it is the kind of thing that is right until
somebody touches it. The day index in `bom_for` is the plainest example: the
ordinary days are numbered with the mastery days taken out, so the tier is
walked straight through rather than skipping an entry every fortnight, and the
line that does it is one subtraction away from being wrong in a way nothing
else would notice for a year.

Run it:

    python tools/test_calendar.py

It needs no network and no cache. Standard library only, like the builder, so
CI installs nothing.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_daily as builder  # noqa: E402


# Each case is a label, a callable that computes something, and what it should
# come to. A callable rather than the value, so a case that raises is a failure
# with a name on it rather than a traceback with none.
CASES: list[tuple[str, object, object]] = []


def case(label: str, want: object):
    def register(fn):
        CASES.append((label, fn, want))
        return fn
    return register


# ---------- a week's title: its dates ----------

@case("a week inside one month", (dt.date(2026, 1, 5), dt.date(2026, 1, 11)))
def _():
    return builder.parse_week_range('January 5–11. "Title": Genesis 1', 2026)


@case("the opening week straddles the new year",
      (dt.date(2026, 12, 28), dt.date(2027, 1, 3)))
def _():
    return builder.parse_week_range("December 28–January 3. Title: Matthew 1", 2027)


@case("a December week at the far end stays in its year",
      (dt.date(2026, 12, 21), dt.date(2026, 12, 27)))
def _():
    return builder.parse_week_range("December 21–27. Title: Malachi", 2026)


@case("a week crossing a month boundary", (dt.date(2026, 3, 30), dt.date(2026, 4, 5)))
def _():
    return builder.parse_week_range("March 30–April 5. Easter", 2026)


@case("a title with no dates is no opinion", None)
def _():
    return builder.parse_week_range("Easter. He Is Risen", 2026)


# ---------- a week's title: its assignment ----------

@case("two chapters of two books", [("matt", 2), ("luke", 2)])
def _():
    return builder.parse_reading_block(
        'January 4–10. "We Have Come to Worship Him": Matthew 2; Luke 2')


@case("ranges and lists of chapters",
      [("job", n) for n in (1, 2, 3, 12, 13, 14, 19, 21, 22, 23, 24, 38, 39, 40, 42)])
def _():
    return builder.parse_reading_block(
        "August 3–9. Title: Job 1–3; 12–14; 19; 21–24; 38–40; 42")


@case("a book named without chapters means all of it", [("esth", None)])
def _():
    return builder.parse_reading_block("June 1–7. Title: Esther")


@case("numbered books stated together", [("1-thes", None), ("2-thes", None)])
def _():
    return builder.parse_reading_block("Title: 1 and 2 Thessalonians")


@case("a numbered range of books", [("1-jn", None), ("2-jn", None), ("3-jn", None)])
def _():
    return builder.parse_reading_block("Title: 1–3 John")


@case("a book with an em dash in its name, cited with verses", [("js-h", 1)])
def _():
    return builder.parse_reading_block("Title: Joseph Smith—History 1:1–26")


@case("Psalms cited as a list", [("ps", n) for n in (102, 103, 110, 116, 117, 118, 119)])
def _():
    return builder.parse_reading_block("Title: Psalms 102–103; 110; 116–119")


@case("a title with no colon is no opinion", None)
def _():
    return builder.parse_reading_block("January 4–10. Just a title")


@case("a chapter is in the block by number or by whole book", (True, True, False))
def _():
    block = [("matt", 2), ("esth", None)]
    return (builder.in_block(block, "matt", 2), builder.in_block(block, "esth", 9),
            builder.in_block(block, "matt", 3))


@case("a chapter's rank is where the week's reading reaches it", (0, 1, 1, 2))
def _():
    block = [("matt", 2), ("esth", None)]
    return (builder.block_rank(block, "matt", 2), builder.block_rank(block, "esth", 1),
            builder.block_rank(block, "esth", 9), builder.block_rank(block, "luke", 2))


# ---------- a citation's verses ----------

@case("verse ids: a range and a single", [12, 13, 14, 20])
def _():
    return builder.parse_verse_ids("?lang=eng&id=p12-p14,p20#p12")


@case("verse ids: html-escaped, as found in a page body", [4, 6])
def _():
    return builder.parse_verse_ids("?lang=eng&amp;id=p4%2Cp6")


@case("verse ids: an absurd range is refused", [])
def _():
    return builder.parse_verse_ids("?lang=eng&id=p1-p99")


@case("a passage's verses are cited as runs", ("45, 47–48", "p45,p47-p48"))
def _():
    return (builder.format_verses([45, 47, 48]), builder.passage_anchor([48, 45, 47]))


@case("a passage of one verse", ("7", "p7"))
def _():
    return (builder.format_verses([7]), builder.passage_anchor([7]))


# ---------- the Book of Mormon calendar ----------

TIER = [{"reference": f"tier {n}"} for n in range(100)]
MASTERY = [{"reference": f"mastery {n}"} for n in range(25)]


@case("the middle of every fortnight is a mastery passage",
      ["mastery 0", "mastery 1", "mastery 2", "mastery 0"])
def _():
    return [builder.bom_for(i, TIER, MASTERY)["reference"]
            for i in (7, 21, 35, 7 + 14 * 25)]


@case("the ordinary days walk the tier without skipping or repeating", True)
def _():
    seen = [int(builder.bom_for(i, TIER, MASTERY)["reference"].split()[1])
            for i in range(1400) if i % 14 != 7]
    return all(b == (a + 1) % len(TIER) for a, b in zip(seen, seen[1:]))


@case("the first fortnight, day by day",
      [f"tier {n}" for n in range(7)] + ["mastery 0"]
      + [f"tier {n}" for n in range(7, 14)])
def _():
    return [builder.bom_for(i, TIER, MASTERY)["reference"] for i in range(15)]


@case("with no mastery passages every day is ordinary", ["tier 6", "tier 7", "tier 8"])
def _():
    return [builder.bom_for(i, TIER, [])["reference"] for i in (6, 7, 8)]


@case("spreading a pool keeps neighbours apart and loses nothing", (True, True, True))
def _():
    pool = [{"ref": f"{book} {n}"} for book in "abc" for n in range(4)]

    def key(verse):
        return verse["ref"].split()[0]

    out = builder.spread(pool, seed=1, key=key)
    again = builder.spread(pool, seed=1, key=key)
    apart = all(key(x) != key(y) for x, y in zip(out, out[1:]))
    same_verses = sorted(v["ref"] for v in out) == sorted(v["ref"] for v in pool)
    return (apart, out == again, same_verses)


def _speaker(quote):
    return quote["ref"].split()[0]


def _apart_all_round(out):
    """No two neighbours share a speaker -- the last and the first included,
    since the calendar deals the list out as a circle."""
    return all(_speaker(x) != _speaker(y) for x, y in zip(out, out[1:] + out[:1]))


@case("spacing out the quotes keeps speakers apart all the way round", (True, True, True))
def _():
    pool = [{"ref": f"{who} {n}"} for who in "abc" for n in range(4)]
    out = builder.space_out(pool, seed=1, key=_speaker)
    again = builder.space_out(pool, seed=1, key=_speaker)
    same_quotes = sorted(q["ref"] for q in out) == sorted(q["ref"] for q in pool)
    return (_apart_all_round(out), out == again, same_quotes)


@case("one speaker far ahead of the rest still never runs two days", (True, True))
def _():
    # The shape of April 2026: thirteen quotes from one speaker, seven from a
    # few, three from many. Dealt round-robin, the end of the list was the
    # thirteen alone, seven days running, and the start was them again.
    sizes = {"p": 13, "a": 7, "b": 7, "c": 7} | {f"s{n}": 3 for n in range(30)}
    pool = [{"ref": f"{who} {n}"} for who, count in sizes.items() for n in range(count)]
    results = [builder.space_out(pool, seed=seed, key=_speaker) for seed in range(50)]
    whole = all(sorted(q["ref"] for q in out) == sorted(q["ref"] for q in pool)
                for out in results)
    return (all(_apart_all_round(out) for out in results), whole)


# ---------- which manual, which conference ----------

@case("the four-year cycle from its epoch",
      ["come-follow-me-for-home-and-church-old-testament-2026",
       "come-follow-me-for-home-and-church-new-testament-2027",
       "come-follow-me-for-home-and-church-book-of-mormon-2028",
       "come-follow-me-for-home-and-church-doctrine-and-covenants-2029",
       "come-follow-me-for-home-and-church-old-testament-2030"])
def _():
    return [builder.cfm_manual_for(y) for y in range(2026, 2031)]


@case("conference candidates from a September", [(2026, 4), (2025, 10), (2025, 4)])
def _():
    return list(builder.conference_candidates(dt.date(2026, 9, 3), depth=3))


@case("conference candidates from a February reach back a year", [(2025, 10), (2025, 4)])
def _():
    return list(builder.conference_candidates(dt.date(2026, 2, 1), depth=2))


@case("the month conference is held already counts", [(2026, 10), (2026, 4)])
def _():
    return list(builder.conference_candidates(dt.date(2026, 10, 1), depth=2))


@case("a conference's talks are counted without its session pages",
      ["/general-conference/2026/10/11christofferson",
       "/general-conference/2026/10/12gong",
       "/general-conference/2026/10/210rasband"])
def _():
    # Cut down from the October 2026 index: a session's own tile, the business
    # item and two talks inside it, and a talk linked twice.
    body = (
        '<li data-content-type="general-conference-session"><ul class="doc-map"><li>'
        '<a href="/study/general-conference/2026/10/saturday-morning-session?lang=eng">'
        '</a></li><li data-content-type="general-conference-business">'
        '<a href="/study/general-conference/2026/10/11christofferson?lang=eng"></a></li>'
        '<li data-content-type="general-conference-talk">'
        '<a href="/study/general-conference/2026/10/12gong?lang=eng"></a></li>'
        '<li data-content-type="general-conference-talk">'
        '<a href="/study/general-conference/2026/10/210rasband?lang=eng"></a>'
        '<a href="/study/general-conference/2026/10/210rasband?lang=eng"></a></li>'
        '<a href="/study/general-conference/2026/04/12oaks?lang=eng"></a>')
    return builder.talk_uris_in(body, 2026, 10)


# ---------- rendering ----------

@case("the date as the masthead prints it", "Monday, August 31, 2026")
def _():
    return builder.human_date(dt.date(2026, 8, 31))


@case("a long reading is set a step smaller", ("scripture", "scripture scripture--long"))
def _():
    return (builder.scripture_class("x" * 420), builder.scripture_class("x" * 421))


@case("a long quote is set a step smaller too", ("quote", "quote quote--long"))
def _():
    return (builder.quote_class("x" * 420), builder.quote_class("x" * 421))


# ---------- how many quotes a talk gives ----------

def _quote(name, score, closing=False):
    return {"text": name, "score": score, "closing": closing}


def _names(quotes):
    return [q["text"] for q in quotes]


@case("a talk takes its best, up to its quota, closing last", ["b", "a", "amen"])
def _():
    candidates = [_quote("amen", 9, closing=True), _quote("a", 2), _quote("b", 5)]
    return _names(builder.take_quotes(candidates, [], quota=7))


@case("a talk short of the minimum is made up from its long paragraphs",
      ["short", "long best", "long next"])
def _():
    at_length = [_quote("long next", 3), _quote("long best", 6), _quote("long last", 1)]
    return _names(builder.take_quotes([_quote("short", 1)], at_length, quota=9))


@case("a talk with enough never reaches for a long paragraph", ["a", "b", "c"])
def _():
    candidates = [_quote("a", 5), _quote("b", 4), _quote("c", 3)]
    return _names(builder.take_quotes(candidates, [_quote("long", 99)], quota=3))


@case("a share block is the reading, the credit, the link", "text\n\nAlma 32:21\n\nhttps://x")
def _():
    return builder.share_text("text", "Alma 32:21", "https://x")


@case("a share block with nothing to credit leaves no gap", "text\n\nhttps://x")
def _():
    return builder.share_text("text", "", "https://x")


@case("a speaker photo is named for its talk", "assets/speakers/2026-04-53hall.jpg")
def _():
    path = builder.portrait_path("/general-conference/2026/04/53hall")
    return path.relative_to(builder.ROOT).as_posix()


@case("a portrait is asked for at the width the card serves",
      "https://example.org/iiif/abc/full/%21480%2C/0/default")
def _():
    return builder.portrait_url(
        {"ogTagImageUrl": "https://example.org/iiif/abc/full/1200%2C/0/default"})


@case("no portrait when the talk has no image", None)
def _():
    return builder.portrait_url({})


# ---------- the month slices ----------

@case("months are sliced from the calendar and stale ones removed", (2, 1, ["2026-08", "2026-09"]))
def _():
    import json
    import tempfile
    days = {"2026-08-30": {"a": 1}, "2026-08-31": {"a": 2}, "2026-09-01": {"a": 3}}
    real = builder.MONTH_DIR
    try:
        with tempfile.TemporaryDirectory() as tmp:
            builder.MONTH_DIR = Path(tmp) / "months"
            builder.MONTH_DIR.mkdir()
            (builder.MONTH_DIR / "2026-07.json").write_text("{}", encoding="utf-8")
            written, removed = builder.write_months(days)
            names = sorted(p.stem for p in builder.MONTH_DIR.glob("*.json"))
            august = json.loads((builder.MONTH_DIR / "2026-08.json").read_text(encoding="utf-8"))
            assert august == {"days": {"2026-08-30": {"a": 1}, "2026-08-31": {"a": 2}}}
            return (written, removed, names)
    finally:
        builder.MONTH_DIR = real


def run() -> int:
    failures = []
    for label, fn, want in CASES:
        try:
            got = fn()
            ok = got == want
        except Exception as err:  # noqa: BLE001 -- a raise is a failure with a name
            got, ok = f"raised {err!r}", False
        if not ok:
            failures.append((label, want, got))
        print(f"  {'ok  ' if ok else 'FAIL'} {label}")

    print(f"\n{len(CASES)} cases, {len(failures)} failures")
    for label, want, got in failures:
        print(f"\n  {label}\n    wanted: {want!r}\n    got:    {got!r}")
    return len(failures)


if __name__ == "__main__":
    raise SystemExit(1 if run() else 0)
