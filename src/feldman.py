import requests
import bs4
from bs4 import BeautifulSoup
from dateparser import parse as parse_date
from ics import Calendar, Event


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
        "date": date,
        "performer": performer,
        "venue": venue,
        "location": location.strip(),
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


def gen_calendar_data(events):
    c = Calendar()

    for event in events:
        e = Event()
        e.name = "Morton feldman performance at %s" % event["location"]
        e.description = "Peformer: %s\n\nProgramme:\n%s\n\nVenue: %s\n\nSource:%s" % (
            event["performer"],
            "\n".join(event["programme"]),
            event["venue"],
            event["source"],
        )
        e.location = event["location"]
        e.begin = event["date"].date()
        e.url = event["source"]
        e.make_all_day()
        c.events.add(e)
        c.events
    return c


def get_latest_calendar():
    body = get_page_content()
    events = parse_events_from_html(body)
    return gen_calendar_data(events)


if __name__ == "__main__":
    c = get_latest_calendar()
    with open('Feldman.ics', 'w') as f:
        f.write(str(c))
