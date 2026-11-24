# Kusama Vision runway

The planner behind [birdbrain.wtf/tools/runway](https://birdbrain.wtf/tools/runway): how long a
dollar budget lasts if it is paid from Kusama's Vision pots, what DOT price the plan needs, and
the monthly spend that survives 9 in 10 replays of DOT's real price history.

The first Kusama Vision runway calculator (February 2026) assumed 10M DOT paid out evenly and a
straight-line price guess. This one starts from what is really in the pots and from the price
moves DOT has actually made.

## Run it yourself

Python 3, nothing to install.

```sh
git clone https://github.com/Birdbrain-wtf/runway && cd runway
python3 serve.py              # then open http://localhost:8000/tools/runway
python3 market.py market.json # optional: take your own order-book snapshot, which serve.py then uses
```

`serve.py` serves the page and fetches its three data files from birdbrain.wtf. All of the
sums run in your browser, in the `<script>` at the bottom of `index.html`.

## What is here

| File | What it does |
| --- | --- |
| `index.html` | The whole page. No libraries, nothing stored, nothing sent anywhere |
| `market.py` | Order-book snapshot for DOT on Kraken (DOT/USDC, DOT/USD, DOT/USDT), Coinbase (DOT/USD) and Binance (DOT/USDT, DOT/USDC): bids within 25% of the best, 24-hour volume, 30-day median daily volume. Birdbrain's server runs it every 15 minutes. A market that fails is left out. Binance refuses some regions (HTTP 451) |
| `serve.py` | A local server for the page |
| `og-card.html`, `social.png` | The link preview card |

## What the page reads

| Path | What | Source |
| --- | --- | --- |
| `/api/treasury` | Bounty balances in DOT, the current block, open referenda | Polkadot Asset Hub, `bounties` pallet |
| `/tools/ksm-dot/data.json` | DOT daily closes since August 2020 | [Birdbrain-wtf/ksm-dot](https://github.com/Birdbrain-wtf/ksm-dot) |
| `/tools/runway/market.json` | Order books and volumes | `market.py` |

## How the numbers are made

- **Each month** the plan pays from dollars first, then sells DOT at that month's price.
- **Selling to dollars.** The default sells all of the DOT to USDC on day one. A smaller share
  sells that share on day one and the same share of any later DOT when it lands.
- **Cost of selling** walks the chosen market's bids down from the mid price and adds the taker
  fee: Kraken Pro's tiered table, Coinbase a flat 0.50% (its UK and EU entry rate, so a large
  Coinbase sale is overstated), Binance a flat 0.10%. Past the 25% floor of the book the rest
  fills at the floor, and the page says an over-the-counter desk is needed. Deposit and
  withdrawal fees, maker orders and price drift during a sale spread over time are not counted.
- **Today's price** is the Kraken DOT/USDC mid when the snapshot is under three hours old,
  otherwise the last daily close.
- **Replays.** 1,000 paths. Each month takes a random 30-day log return from real closes in the
  chosen window (since 2020, two years or one year). "Swings only" removes the window's average
  drift. The random generator is seeded, so a shared link gives the same numbers.
- **The price the plan needs** and **the spend that fits** are found by bisection. The 9-in-10
  spend uses every fourth path (250) for speed.

## Facts typed into the page

- 10,000,000 DOT under [referendum 498](https://polkadot.subsquare.io/referenda/498) (submitted
  21 February 2025, executed 8 March 2025, "for the sole benefit of Kusama"). The page offers it
  only as a hypothetical.
- [Referendum 680](https://polkadot.subsquare.io/referenda/680), the Cypherpunk Vision Fund,
  moves the Art and ZK bounties' DOT into one Cypherpunk bounty. The default balance counts those
  bounties once each. It is a gross scenario, not a confirmed transfer or free budget.

Everything else is read live.

## Licence

Apache 2.0. Birdbrain is an experiment by [Decent](https://www.decent.partners).
