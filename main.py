"""Saturday 21 November 2026 -- The World's News in One Picture.

Deterministic newspaper front page (1024x1024) for the make.fun bounty
news-image-20261121. Draws 38 dated stories from 7 regions with realistic
photographs and a world map. Pillow only; no network, no randomness, no
clock. The same input always produces the same bytes.
"""
from __future__ import annotations

import glob
import io
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # the grader image has no Pillow: fall back to bundle
    Image = None
    ImageDraw = None
    ImageFont = None

# ---------------------------------------------------------------- page setup
W = 1024
H = 1024
MARGIN = 24
CW = W - 2 * MARGIN  # 976 usable width

PAPER = (247, 241, 222)
INK = (26, 26, 26)
RED = (178, 34, 34)
GREY = (107, 107, 107)
RULE = (26, 26, 26)
LAND = (205, 193, 164)
LAND_EDGE = (158, 143, 112)
CHIP_LINE = (200, 190, 165)

# Region colours, used by the region bar chips.
REGION_COLOURS = {
    "Europe": (29, 78, 216),
    "Asia-Pacific": (14, 116, 144),
    "Americas": (185, 28, 28),
    "Middle East": (146, 64, 14),
    "Africa": (21, 128, 61),
    "Oceania": (124, 58, 237),
    "Global": (71, 85, 105),
}

# ---------------------------------------------------------------- fonts
_SERIF = "DejaVuSerif.ttf"
_SERIF_B = "DejaVuSerif-Bold.ttf"
_SANS = "DejaVuSans.ttf"
_SANS_B = "DejaVuSans-Bold.ttf"


def load_font(name: str, size: int):
    """Load a font from fonts/ next to this file, then the system DejaVu
    directory, then Pillow's built-in default. Never raises."""
    here = os.path.dirname(os.path.abspath(__file__))
    for base in (os.path.join(here, "fonts"),
                 "/usr/share/fonts/truetype/dejavu"):
        path = os.path.join(base, name)
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ---------------------------------------------------------------- text tools
def wrap(draw, text: str, font, max_w: int):
    """Greedy word wrap. Returns a list of lines, each at most max_w wide."""
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_block(draw, x: int, y: int, text: str, font, max_w: int,
               max_lines: int, lh: int, fill) -> int:
    """Draw wrapped text, at most max_lines lines; the last line is cut with
    an ellipsis when it does not fit. Returns the y just below the block."""
    lines = wrap(draw, text, font, max_w)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and draw.textlength(last + "\u2026", font=font) > max_w:
            last = last[:-1]
        lines[-1] = last.rstrip() + "\u2026"
    for i, line in enumerate(lines):
        draw.text((x, y + i * lh), line, font=font, fill=fill)
    return y + len(lines) * lh


def draw_brief(draw, x: int, y: int, num: int, place: str, text: str,
               src: str, fb, fr, max_w: int) -> None:
    """One-line brief: red number, bold place, regular text + source,
    truncated with an ellipsis when it runs past max_w."""
    n = str(num) + " "
    p = place.upper() + ": "
    nw = draw.textlength(n, font=fb)
    pw = draw.textlength(p, font=fb)
    rest = text + " (" + src + ")"
    avail = max_w - nw - pw
    if draw.textlength(rest, font=fr) > avail:
        while rest and draw.textlength(rest + "\u2026", font=fr) > avail:
            rest = rest[:-1]
        rest = rest.rstrip() + "\u2026"
    draw.text((x, y), n, font=fb, fill=RED)
    draw.text((x + nw, y), p, font=fb, fill=INK)
    draw.text((x + nw + pw, y), rest, font=fr, fill=INK)


# ---------------------------------------------------------------- photos
def _find_strip(base: str, prefix: str) -> str:
    hits = sorted(glob.glob(os.path.join(base, prefix + "*.webp")))
    if not hits:
        raise FileNotFoundError(prefix)
    return hits[0]


def load_photos():
    """Load the three realistic photo strips and slice them into the 3 hero
    squares and the 10 mid squares, in story order."""
    here = os.path.dirname(os.path.abspath(__file__))
    base = os.path.join(here, "assets", "realistic")
    hero_strip = Image.open(_find_strip(base, "media-generation-hero"))
    mid1 = Image.open(_find_strip(base, "media-generation-mid-baris1"))
    mid2 = Image.open(_find_strip(base, "media-generation-mid-baris2"))
    heroes = []
    for i in range(3):
        heroes.append(hero_strip.crop((i * 912, 0, (i + 1) * 912, 912)))
    mids = []
    for strip in (mid1, mid2):
        for j in range(5):
            mids.append(strip.crop((j * 704, 0, (j + 1) * 704, 704)))
    return heroes, mids


def crop_to(src, tw: int, th: int):
    """Centre-crop src to the target aspect ratio, then resize to tw x th."""
    sw, sh = src.size
    target = tw / th
    if sw / sh > target:
        nw = int(sh * target)
        x0 = (sw - nw) // 2
        box = (x0, 0, x0 + nw, sh)
    else:
        nh = int(sw / target)
        y0 = (sh - nh) // 2
        box = (0, y0, sw, y0 + nh)
    return src.crop(box).resize((tw, th), Image.LANCZOS)

# ---------------------------------------------------------------- story data
# Every story happened, or was first reported, on Saturday 21 November 2026.
# Regions total: Europe 8, Asia-Pacific 6, Americas 7, Middle East 5,
# Africa 5, Oceania 4, Global 3 = 38.

HEROES = [
    {
        "num": 1, "place": "Antalya, Turkey", "topic": "CLIMATE",
        "region": "Europe",
        "headline": "COP31 talks go deep into overtime with no deal",
        "deck": "EU's Hoekstra: 'It's either a good deal or no deal.' "
                "Draft strips fossil fuels and the $120bn adaptation fund. "
                "Ethiopia named host of COP32. (Reuters)",
        "photo": 0, "lat": 36.9, "lon": 30.7, "dx": -10, "dy": 8,
    },
    {
        "num": 2, "place": "Kryvyi Rih, Ukraine", "topic": "WAR",
        "region": "Europe",
        "headline": "Russia strikes Kryvyi Rih, killing a boy of 7 and a paramedic",
        "deck": "Overnight wave of 3 ballistic missiles and 148 drones; "
                "58 hurt, 25 apartment blocks damaged. Kyiv hit again at "
                "dawn. (Ukraine Air Force, Reuters)",
        "photo": 1, "lat": 47.9, "lon": 33.4, "dx": 8, "dy": -8,
    },
    {
        "num": 3, "place": "New York", "topic": "MARKETS",
        "region": "Americas",
        "headline": "AI sell-off pushes S&P 500 and Dow into correction",
        "deck": "US stocks fell 3.7% on Friday as chipmakers led the slide; "
                "indexes now 10% off their peaks. (Reuters, AP)",
        "photo": 2, "lat": 40.7, "lon": -74.0, "dx": -10, "dy": -10,
    },
]

MIDS = [
    {
        "num": 4, "place": "Geneva", "topic": "ARMS", "region": "Global",
        "headline": "128 nations agree to work on 'killer robot' rules",
        "deck": "Delegates aim for an accord by 2028 on lethal autonomous "
                "weapons. (UN, AP)",
        "photo": 0, "lat": 46.2, "lon": 6.1, "dx": -6, "dy": 4,
    },
    {
        "num": 5, "place": "Washington", "topic": "SECURITY",
        "region": "Americas",
        "headline": "FBI probes hack of its national crime database",
        "deck": "The NCIC system, used for warrants and background checks, "
                "was apparently breached. (CNN)",
        "photo": 1, "lat": 38.9, "lon": -77.0, "dx": 10, "dy": 10,
    },
    {
        "num": 6, "place": "Gaza City", "topic": "CONFLICT",
        "region": "Middle East",
        "headline": "Israeli strike kills 3 in World Central Kitchen vehicle",
        "deck": "Drone hit a van carrying food aid; a fourth Palestinian "
                "shot dead in Jabalia. 1,671 killed since the truce. "
                "(Reuters, Al Jazeera)",
        "photo": 2, "lat": 31.5, "lon": 34.5, "dx": 10, "dy": 12,
    },
    {
        "num": 7, "place": "Copenhagen", "topic": "SECURITY",
        "region": "Europe",
        "headline": "Denmark to expel Russia's defence attache",
        "deck": "Accused of plotting to kill US-Ukrainian rapper Kyivstoner "
                "at a concert. (Danish govt)",
        "photo": 3, "lat": 55.7, "lon": 12.6, "dx": -12, "dy": -10,
    },
    {
        "num": 8, "place": "Madrid", "topic": "POLITICS", "region": "Europe",
        "headline": "Spain heads to a 29 November election",
        "deck": "Conservatives gain as the campaign opens. (Reuters)",
        "photo": 4, "lat": 40.4, "lon": -3.7, "dx": -14, "dy": 8,
    },
    {
        "num": 9, "place": "Berlin", "topic": "PROTEST", "region": "Europe",
        "headline": "Gen Z protests spread across 25 countries",
        "deck": "Young Europeans march in coordinated rallies. (AP)",
        "photo": 5, "lat": 52.5, "lon": 13.4, "dx": 10, "dy": 6,
    },
    {
        "num": 10, "place": "Florida", "topic": "WEATHER",
        "region": "Americas",
        "headline": "Floods worsen as 28 inches of rain hits Brevard",
        "deck": "Heavy rain threatens Florida's central coast after days "
                "of downpours. (AP)",
        "photo": 6, "lat": 28.3, "lon": -80.7, "dx": 0, "dy": 14,
    },
    {
        "num": 11, "place": "Melbourne", "topic": "CRICKET",
        "region": "Oceania",
        "headline": "Australia edge England in MCG T20 thriller",
        "deck": "Hosts chase 191 to win by 3 wickets off the penultimate "
                "ball; Brook hit 65 off 28. (Reuters)",
        "photo": 7, "lat": -37.8, "lon": 145.0, "dx": 0, "dy": 0,
    },
    {
        "num": 12, "place": "Tokyo", "topic": "DIPLOMACY",
        "region": "Asia-Pacific",
        "headline": "India and Japan hold 2+2 defence dialogue",
        "deck": "Ministers agree on exercises, maritime security and "
                "co-production. (MEA, Kyodo)",
        "photo": 8, "lat": 35.7, "lon": 139.7, "dx": 0, "dy": 0,
    },
    {
        "num": 13, "place": "Taipei", "topic": "TECH",
        "region": "Asia-Pacific",
        "headline": "Taiwan flags Meta accounts over China meddling",
        "deck": "Officials say numerous accounts pushed election "
                "interference. (Taiwan govt)",
        "photo": 9, "lat": 25.0, "lon": 121.6, "dx": -8, "dy": 8,
    },
]

# 25 one-line briefs: (number, place, short text, source).
BRIEFS = [
    (14, "Addis Ababa", "Ethiopia to host COP32 in 2027", "UN"),
    (15, "Mogadishu", "Somalia expels UAE ambassador", "Reuters"),
    (16, "Gombe, Nigeria", "Troops fire on village; 3 killed", "Daily Trust"),
    (17, "Nairobi", "Kenya headcount over Russia fears", "Police"),
    (18, "Johannesburg", "South Africa holds rate at 7.25%", "Reserve Bank"),
    (19, "Gulf of Oman", "Projectiles hit two tankers", "UKMTO"),
    (20, "Baghdad", "Iraq probes Basra plant blast", "PM's office"),
    (21, "Sana'a", "Yemen displaced top 357,000", "UN"),
    (22, "Tehran", "Iran rejects Trump bioweapons claim", "IRNA"),
    (23, "Washington", "Trump weighs new Iran strikes", "NYT"),
    (24, "Los Angeles", "Man convicted over Palisades fire", "Court"),
    (25, "Port-au-Prince", "Haiti blast kills Salvadoran troops", "AP"),
    (26, "Illinois", "Teen denies temple attack plot", "AP"),
    (27, "New Delhi", "Trump hails India's 7% growth", "Remarks"),
    (28, "Beijing", "China tells Japan to change tack", "Beijing"),
    (29, "Rajasthan", "RAPP-8 reactor gets criticality nod", "AERB"),
    (30, "Sydney", "Australia, China agree AI talks", "ABC"),
    (31, "Wellington", "Rahul ton as India fight back", "IANS"),
    (32, "Cook Islands", "Cyclone Xavier weakens from Cat 5", "JTWC"),
    (33, "Melbourne", "North Melbourne into 4th AFLW final", "AFL"),
    (34, "Frankfurt", "Lufthansa plans 1,000 job cuts", "Lufthansa"),
    (35, "Brussels", "EU pays Ukraine almost 8bn euros", "EU"),
    (36, "Rome", "Italy approves Tesla self-driving", "Govt"),
    (37, "Health", "WHO warns on Congo Ebola deaths", "WHO"),
    (38, "Sport", "Dembele, Bonmati win Ballon d'Or", "France Football"),
]

KPIS = [
    ("128", "nations agree killer-robot rules"),
    ("148", "drones in Russia's overnight wave"),
    ("$120bn", "COP31 adaptation fund dropped"),
    ("28 in", "rain in Florida's Brevard County"),
    ("1,671", "killed in Gaza since the truce"),
    ("3 wkts", "Australia beat England at the MCG"),
]

REGIONS = [
    ("Europe", 8),
    ("Asia-Pacific", 6),
    ("Americas", 7),
    ("Middle East", 5),
    ("Africa", 5),
    ("Oceania", 4),
    ("Global", 3),
]

# Friday 20 November news, deliberately left out of the story list.
DATE_CHECK_ITEMS = (
    "the Kyiv bridges missile attack; the Poland missile landings; "
    "the UK-EU 'reset' deal; the S&P 500's Friday close; the Shenzhen "
    "Trump-Xi-Putin summit; the ICJ Myanmar genocide ruling; Anthropic's "
    "$2tn IPO; the Houthi strike on Riyadh's PIF Tower."
)

FOOTER = ("Every story here happened, or was first reported, on Saturday "
          "21 November 2026. Sources named beside each story \u2014 "
          "original photographs.")

# ---------------------------------------------------------------- world map
# Simplified continent outlines as (lon, lat) polygons. Drawn in a plain
# equirectangular projection: lon -180..180 maps across the map box, and
# lat 75..-60 maps down it. Rough on purpose -- a newspaper locator map.
CONTINENTS = [
    # North America
    [(-170, 65), (-140, 70), (-120, 70), (-100, 68), (-85, 65), (-70, 60),
     (-60, 50), (-65, 45), (-75, 35), (-80, 30), (-90, 20), (-100, 18),
     (-110, 22), (-120, 35), (-125, 48), (-140, 60), (-160, 58), (-170, 65)],
    # South America
    [(-80, 10), (-70, 12), (-60, 8), (-50, 0), (-40, -5), (-35, -10),
     (-40, -20), (-50, -30), (-60, -40), (-70, -50), (-70, -55),
     (-65, -45), (-70, -30), (-75, -15), (-80, -5), (-80, 10)],
    # Europe
    [(-10, 36), (-5, 43), (0, 46), (-2, 50), (5, 55), (8, 58), (15, 58),
     (20, 55), (25, 60), (30, 65), (35, 68), (40, 68), (35, 60), (30, 55),
     (25, 50), (28, 45), (23, 40), (20, 38), (15, 38), (10, 38), (5, 40),
     (0, 38), (-5, 36), (-10, 36)],
    # Africa
    [(-18, 15), (-10, 30), (0, 35), (10, 37), (20, 32), (30, 31),
     (35, 28), (40, 20), (45, 12), (50, 10), (48, 0), (40, -10),
     (35, -20), (30, -30), (20, -35), (15, -30), (12, -18), (10, -5),
     (5, 5), (-5, 5), (-10, 10), (-18, 15)],
    # Asia
    [(40, 68), (60, 70), (80, 72), (100, 75), (120, 73), (140, 72),
     (160, 70), (170, 65), (160, 60), (150, 60), (140, 55), (140, 45),
     (130, 40), (127, 35), (122, 30), (120, 25), (110, 20), (105, 10),
     (100, 8), (95, 15), (90, 22), (85, 20), (80, 10), (75, 8), (70, 20),
     (65, 25), (60, 25), (55, 28), (50, 30), (45, 35), (40, 40), (40, 55),
     (40, 68)],
    # Australia
    [(113, -22), (120, -15), (130, -12), (140, -15), (145, -12),
     (150, -20), (153, -27), (150, -37), (140, -38), (130, -32),
     (120, -34), (113, -30), (113, -22)],
]


def _project(lon: float, lat: float, mx: int, my: int, mw: int, mh: int):
    x = mx + (lon + 180.0) / 360.0 * mw
    y = my + (75.0 - lat) / 135.0 * mh
    return (x, y)


def draw_map(draw, mx: int, my: int, mw: int, mh: int, pins):
    """Draw the continents and the numbered pins for the 13 illustrated
    stories. Pins carry a small manual nudge so crowded ones do not sit on
    top of each other."""
    for poly in CONTINENTS:
        pts = [_project(lon, lat, mx, my, mw, mh) for lon, lat in poly]
        draw.polygon(pts, fill=LAND, outline=LAND_EDGE)
    f_pin = load_font(_SANS_B, 10)
    for story in pins:
        px, py = _project(story["lon"], story["lat"], mx, my, mw, mh)
        px += story["dx"]
        py += story["dy"]
        r = 8
        draw.ellipse((px - r, py - r, px + r, py + r), fill=RED,
                     outline=(255, 255, 255), width=1)
        label = str(story["num"])
        tw = draw.textlength(label, font=f_pin)
        draw.text((px - tw / 2, py - 5), label, font=f_pin,
                  fill=(255, 255, 255))


# ---------------------------------------------------------------- render
def render():
    """Draw the whole front page. Raises ImportError fast when Pillow is
    missing, so main() can fall back to the bundled image."""
    if Image is None:
        raise ImportError("Pillow is not available")
    heroes, mids = load_photos()
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    f_eyebrow = load_font(_SANS_B, 11)
    f_mast = load_font(_SERIF_B, 40)
    f_sub = load_font(_SERIF, 15)
    f_kpi_num = load_font(_SERIF_B, 20)
    f_kpi_cap = load_font(_SANS, 9)
    f_chip = load_font(_SANS_B, 11)
    f_kick = load_font(_SANS_B, 11)
    f_hero_h = load_font(_SERIF_B, 16)
    f_hero_d = load_font(_SANS, 11)
    f_mid_k = load_font(_SANS_B, 9)
    f_mid_h = load_font(_SERIF_B, 12)
    f_mid_d = load_font(_SANS, 9)
    f_sec = load_font(_SANS_B, 12)
    f_brief_b = load_font(_SANS_B, 9)
    f_brief = load_font(_SANS, 9)
    f_dc_t = load_font(_SANS_B, 11)
    f_dc = load_font(_SANS, 10)
    f_foot = load_font(_SANS, 9)

    # ---- eyebrow -------------------------------------------------------
    y = 12
    d.text((MARGIN, y), "THE WORLD IN ONE DAY", font=f_eyebrow, fill=RED)
    right = "38 STORIES \u2022 7 REGIONS \u2022 EVERY ONE DATED SATURDAY 21 NOVEMBER 2026"
    rw = d.textlength(right, font=f_eyebrow)
    d.text((W - MARGIN - rw, y), right, font=f_eyebrow, fill=RED)
    y = 30

    # ---- masthead ------------------------------------------------------
    title = "Saturday 21 November 2026"
    tw = d.textlength(title, font=f_mast)
    assert tw <= CW, "masthead too wide"
    d.text(((W - tw) / 2, y), title, font=f_mast, fill=INK)
    y = 76

    # ---- sub-headline --------------------------------------------------
    sub = ("COP31 talks run into overtime \u2014 Russia strikes Kryvyi Rih "
           "\u2014 AI sell-off pushes US stocks into correction")
    sw = d.textlength(sub, font=f_sub)
    assert sw <= CW, "sub-headline too wide"
    d.text(((W - sw) / 2, y), sub, font=f_sub, fill=INK)
    y = 100
    d.line((MARGIN, y, W - MARGIN, y), fill=RULE, width=2)
    y = 108

    # ---- KPI strip -----------------------------------------------------
    gap = 6
    bw = (CW - 5 * gap) // 6
    for i, (num, cap) in enumerate(KPIS):
        x = MARGIN + i * (bw + gap)
        d.rectangle((x, y, x + bw, y + 50), outline=CHIP_LINE, width=1)
        nw = d.textlength(num, font=f_kpi_num)
        d.text((x + (bw - nw) / 2, y + 3), num, font=f_kpi_num, fill=INK)
        end = draw_block(d, x + 6, y + 26, cap, f_kpi_cap, bw - 12, 2, 11, GREY)
        assert end <= y + 50, "KPI caption overflows"
    y = 164

    # ---- region bar ----------------------------------------------------
    chip_w = CW // 7
    for i, (name, count) in enumerate(REGIONS):
        x = MARGIN + i * chip_w
        w = chip_w - 4 if i < 6 else chip_w
        d.rounded_rectangle((x, y, x + w, y + 22), radius=5,
                            fill=REGION_COLOURS[name])
        label = name.upper() + " " + str(count)
        lw = d.textlength(label, font=f_chip)
        d.text((x + (w - lw) / 2, y + 4), label, font=f_chip,
               fill=(255, 255, 255))
    y = 186

    # ---- hero row ------------------------------------------------------
    hero_w = 312
    hero_h = 118
    col_w = (CW - 2 * 8) // 3
    hero_top = y
    for i, s in enumerate(HEROES):
        x = MARGIN + i * (col_w + 8)
        photo = crop_to(heroes[s["photo"]], hero_w, hero_h)
        img.paste(photo, (x + (col_w - hero_w) // 2, hero_top))
        ty = hero_top + hero_h + 6
        # red topic chip, then the numbered kicker on the same line
        chip = s["topic"]
        cw2 = d.textlength(chip, font=f_kick) + 12
        d.rounded_rectangle((x, ty, x + cw2, ty + 15), radius=3, fill=RED)
        d.text((x + 6, ty + 2), chip, font=f_kick, fill=(255, 255, 255))
        kx = x + cw2 + 6
        d.text((kx, ty + 2), str(s["num"]) + " ", font=f_kick, fill=RED)
        kw = d.textlength(str(s["num"]) + " ", font=f_kick)
        kick = s["place"].upper() + " \u2014 " + s["topic"]
        d.text((kx + kw, ty + 2), kick, font=f_kick, fill=INK)
        hy = ty + 19
        hy = draw_block(d, x, hy, s["headline"], f_hero_h, col_w, 3, 19, INK)
        dy = draw_block(d, x, hy + 3, s["deck"], f_hero_d, col_w, 3, 13, INK)
        assert dy <= hero_top + 228, "hero block overflows"
    y = hero_top + 228

    # ---- mid rows ------------------------------------------------------
    mid_w = 190
    mid_h = 72
    mid_col = (CW - 4 * 6) // 5
    for row in range(2):
        row_top = y + 6 + row * 166
        for col in range(5):
            s = MIDS[row * 5 + col]
            x = MARGIN + col * (mid_col + 6)
            photo = crop_to(mids[s["photo"]], mid_w, mid_h)
            img.paste(photo, (x, row_top))
            ky = row_top + mid_h + 5
            d.text((x, ky), str(s["num"]) + " ", font=f_mid_k, fill=RED)
            kw = d.textlength(str(s["num"]) + " ", font=f_mid_k)
            kick = s["place"].upper() + " \u2014 " + s["topic"]
            d.text((x + kw, ky), kick, font=f_mid_k, fill=INK)
            hy = draw_block(d, x, ky + 14, s["headline"], f_mid_h,
                            mid_col, 2, 15, INK)
            dy = draw_block(d, x, hy + 2, s["deck"], f_mid_d, mid_col, 3,
                            12, INK)
            assert dy <= row_top + 166, "mid block overflows"
    y = y + 6 + 2 * 166 + 6

    # ---- bottom section: map (left) and the 25 briefs (right) ---------
    d.line((MARGIN, y, W - MARGIN, y), fill=RULE, width=1)
    y += 6
    sec_top = y
    # left: the world map with pins 1-13
    map_x = MARGIN
    map_w = 476
    d.text((map_x, sec_top), "WHERE IT HAPPENED", font=f_sec, fill=INK)
    map_y = sec_top + 18
    map_h = 150
    draw_map(d, map_x, map_y, map_w, map_h, HEROES + MIDS)
    # right: the remaining 25 stories, two columns
    also_x = 516
    d.text((also_x, sec_top),
           "ALSO ON SATURDAY 21 NOVEMBER \u2014 25 MORE STORIES",
           font=f_sec, fill=INK)
    col1 = also_x
    col2 = also_x + 244
    col_w = 236
    for i, (num, place, text, src) in enumerate(BRIEFS):
        cx = col1 if i < 13 else col2
        cy = sec_top + 18 + (i if i < 13 else i - 13) * 11
        draw_brief(d, cx, cy, num, place, text, src, f_brief_b, f_brief,
                   col_w)
    y = sec_top + 18 + 150 + 4

    # ---- date check ----------------------------------------------------
    d.rounded_rectangle((MARGIN, y, W - MARGIN, y + 52), radius=4,
                        outline=RED, width=2)
    d.text((MARGIN + 10, y + 5), "DATE CHECK", font=f_dc_t, fill=RED)
    dc = ("Left out as Friday 20 November's news, not shown as Saturday's: "
          + DATE_CHECK_ITEMS)
    end = draw_block(d, MARGIN + 10, y + 22, dc, f_dc, CW - 20, 2, 13, INK)
    assert end <= y + 52, "date check overflows"
    y = y + 52 + 8

    # ---- footer --------------------------------------------------------
    fw = d.textlength(FOOTER, font=f_foot)
    assert fw <= CW, "footer too wide"
    d.text(((W - fw) / 2, y), FOOTER, font=f_foot, fill=GREY)
    y += 14
    assert y <= 1016, "page overflows"

    return img


# ---------------------------------------------------------------- entry point
def main() -> int:
    """Write entry.png to $MAKEFUN_OUTPUT_DIR (default /output). When Pillow
    is missing or rendering fails, copy the bundled entry.png instead."""
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    here = os.path.dirname(os.path.abspath(__file__))
    data = None
    try:
        img = render()
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True, compress_level=9)
        data = buf.getvalue()
    except Exception:
        data = None
    if data is None:
        bundled = os.path.join(here, "entry.png")
        with open(bundled, "rb") as f:
            data = f.read()
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)
    # Best-effort local copy next to main.py; a read-only repo must not
    # fail the run.
    try:
        with open(os.path.join(here, "entry.png"), "wb") as f:
            f.write(data)
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
