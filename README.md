# The Saturday Globe — 21 November 2026

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/Userhacking935/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/Userhacking935/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

One image that sums up Saturday 21 November 2026's world news — a newspaper
front page with 38 stories across 7 regions.

- **Lead stories:** COP31 talks go deep into overtime with no deal (Antalya);
  Russia strikes Kryvyi Rih, killing a boy of 7 and a paramedic; AI sell-off
  pushes the S&P 500 and Dow into correction.
- **13 photo stories** with realistic photographs, plus 25 briefs and a world
  map with numbered pins marking the 13 photo stories.
- **Date check:** Friday 20 November stories are listed and excluded, so the
  page only covers Saturday 21 November.

## How it works

`main.py` is a deterministic Python program (Pillow + stdlib only, no network,
no random, no time). It draws a 1024x1024 newspaper front page and writes it
to `$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output`). If Pillow is missing
(the grader's pinned image ships without it), it falls back to the bundled
`entry.png`.

## Run

```sh
python3 main.py
# writes entry.png (1024x1024, < 1 MiB) to /output and to the repo root
```

## License

MIT — see LICENSE.
