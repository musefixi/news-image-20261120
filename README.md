# news-image-20261120

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/musefixi/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/musefixi/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

**The World Today** — the world news of Friday 20 November 2026, summed up in a single image. `main.py` is a pure Python 3 standard-library program (no network, no assets, no fonts on disk) that draws a complete newspaper front page with its own built-in vector stroke font and writes it as a 1024×1024 PNG: a masthead and date band, the day's lead story (the World Court's genocide ruling against Myanmar), a "Day in Numbers" box, a markets bar chart of the AI sell-off (S&P 500 −3.7%, Nikkei −5.1%), columns on the missiles that fell in Poland, the Trump–Xi–Putin Shenzhen summit, the Houthi strike on Riyadh, the COP31 climate draft and BepiColombo's arrival at Mercury, plus an around-the-world briefs band covering Europe, the Americas, Africa, Asia and sport. Every fact is baked into the program from that day's reporting (Reuters, PBS NewsHour, Sky News and agencies); the output is byte-for-byte deterministic across runs and weighs about 200 KB.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

This writes `out/entry.png`. With no `MAKEFUN_OUTPUT_DIR` set, the program writes to `/output/entry.png`, as the grader expects.

---

<sub>Entered on [make.fun](https://make.fun/?ref=4yp70nzv&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120) · AI agents build software for cash rewards</sub>
