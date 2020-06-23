import requests
import bs4

from bs4 import BeautifulSoup
from dateparser import parse as parse_date
from icalendar import Calendar, Event, vUri, vText

URL = "https://www.cnvill.net/mfperfs.htm"


def get_page_content():
    r = requests.get(URL)
    assert r.status_code == 200
    return r.text


def is_text(p):
    return type(p) == bs4.element.NavigableString


def parse_event(p):
    texts = list(p.children)
    line1 = texts[0].text.strip()
    content = list(texts[-1].children)
    date, location = line1.split("*")
    date = parse_date(date)
    location = location.strip()
    programme = [p.strip() for p in content[0].contents if is_text(p)]
    performer = None
    venue = None
    source = None
    for line in content[1:]:
        if is_text(line) and len(line.strip()) > 0:
            if performer is None:
                performer = line.strip()
                continue
            if venue is None:
                venue = line.strip()
                continue
        if line.name == "a":
            source = content[8].attrs["href"]

    return {
        "uid": "%s-%s" % (str(date.date()), location.lower().replace(" ", "/")),
        "date": date,
        "performer": performer,
        "venue": venue,
        "location": location,
        "programme": programme,
        "source": source,
    }


def parse_events_from_html(body):
    soup = BeautifulSoup(body, "html.parser")
    events = []
    for child in soup.body.children:
        if child.name == "p":
            try:
                event = parse_event(child)
                events.append(event)
            except Exception as e:
                print(e)
    return events


def get_event_desc(event):
    return """
Source: %s

Performers: %s

Programme:
%s

Venue: %s
""" % (
        event["performer"],
        "\n".join(event["programme"]),
        event["venue"],
        event["source"],
    )


def gen_calendar_data(events):
    c = Calendar()
    c.add("prodid", "-//Morton Feldman Forthcoming Performances//notimportant.org//")
    c.add("version", "2.0")
    c.add("X-WR-CALNAME", "Morton Feldman Forthcoming Performances")
    c.add("x-original-url", "http://feldman.notimportant.org/")
    c.add("method", "PUBLISH")

    for event in events:
        e = Event()
        e.add("summary", "Morton Feldman: %s" % event["location"])
        e.add("location", event["location"])
        e.add("dtstart", event["date"].date())
        e.add("url", vUri(event["source"]))
        e.add("uid", event["uid"])
        e.add("description", get_event_desc(event))
        c.add_component(e)
    return c


def get_latest_calendar():
    body = get_page_content()
    events = parse_events_from_html(body)
    return gen_calendar_data(events)


if __name__ == "__main__":
    c = get_latest_calendar()
    with open("Feldman.ics", "w") as f:
        f.write(c.to_ical().decode("utf-8"))
