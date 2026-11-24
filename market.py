#!/usr/bin/env python3
"""DOT market snapshot for birdbrain.wtf/tools/runway.

Writes market.json: for each market below, the bid side of the order book (within 25% of
the best bid), the 24-hour volume and the median daily volume over the last 30 days.
Public endpoints only, stdlib only, atomic write. A market that fails is left out and the
rest are written. If Kraken DOT/USDC fails (the page's price source) the old file stays.
Runs on Birdbrain's box from /etc/cron.d/runway-market.
"""
import json, os, statistics, sys, tempfile, time, urllib.request

OUT = sys.argv[1] if len(sys.argv) > 1 else "/var/www/birdbrain-static/tools/runway/market.json"
UA = {"User-Agent": "birdbrain-runway/2"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        return json.load(r)


def trim(bids):
    best = bids[0][0]
    return [b for b in bids if b[0] >= best * 0.75]


def kraken(pair):
    api = "https://api.kraken.com/0/public/"
    def k(path):
        d = get(api + path)
        if d.get("error"):
            raise RuntimeError(d["error"])
        return next(v for key, v in d["result"].items() if key != "last")
    t = k("Ticker?pair=" + pair)
    book = k(f"Depth?pair={pair}&count=500")
    days = k(f"OHLC?pair={pair}&interval=1440")[-31:-1]
    vols = [float(d[6]) for d in days]
    return {"bids": trim([[float(p), float(q)] for p, q, _ in book["bids"]]), "bestAsk": float(book["asks"][0][0]),
            "last": float(t["c"][0]), "vol24h": float(t["v"][1]), "vwap24h": float(t["p"][1]), "days": vols}


def coinbase(product):
    api = "https://api.exchange.coinbase.com/products/" + product
    st = get(api + "/stats")
    book = get(api + "/book?level=2")
    days = get(api + "/candles?granularity=86400")[1:31]  # newest first, skip today
    vols = [float(d[5]) for d in days]
    return {"bids": trim([[float(p), float(q)] for p, q, *_ in book["bids"]]), "bestAsk": float(book["asks"][0][0]),
            "last": float(st["last"]), "vol24h": float(st["volume"]), "vwap24h": float(st["last"]), "days": vols}


def binance(symbol):
    api = "https://api.binance.com/api/v3/"
    t = get(api + "ticker/24hr?symbol=" + symbol)
    book = get(api + f"depth?symbol={symbol}&limit=5000")
    days = get(api + f"klines?symbol={symbol}&interval=1d&limit=31")[:-1]
    vols = [float(d[5]) for d in days]
    return {"bids": trim([[float(p), float(q)] for p, q in book["bids"]]), "bestAsk": float(book["asks"][0][0]),
            "last": float(t["lastPrice"]), "vol24h": float(t["volume"]), "vwap24h": float(t["weightedAvgPrice"]), "days": vols}


MARKETS = [
    ("kraken-USDC", "Kraken", "USDC", lambda: kraken("DOTUSDC")),
    ("kraken-USD", "Kraken", "USD", lambda: kraken("DOTUSD")),
    ("kraken-USDT", "Kraken", "USDT", lambda: kraken("DOTUSDT")),
    ("coinbase-USD", "Coinbase", "USD", lambda: coinbase("DOT-USD")),
    ("binance-USDT", "Binance", "USDT", lambda: binance("DOTUSDT")),
    ("binance-USDC", "Binance", "USDC", lambda: binance("DOTUSDC")),
]


def main():
    out = {"source": "Kraken, Coinbase and Binance public APIs", "fetchedAt": int(time.time()), "pairs": {}}
    for key, ex, quote, fn in MARKETS:
        try:
            p = fn()
            if not p["bids"] or len(p["days"]) < 20:
                raise RuntimeError("short data")
        except Exception as e:  # noqa: BLE001 - one market failing must not blank the others
            print(time.strftime("%FT%TZ", time.gmtime()), "skip", key, e, file=sys.stderr)
            continue
        vols = p.pop("days")
        p.update(exchange=ex, quote=quote, bestBid=p["bids"][0][0],
                 medianDay30=statistics.median(vols), meanDay30=sum(vols) / len(vols))
        out["pairs"][key] = p
        time.sleep(0.5)
    if "kraken-USDC" not in out["pairs"]:
        raise SystemExit("no Kraken DOT/USDC, keeping the old file")
    d = os.path.dirname(OUT)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".market.")
    with os.fdopen(fd, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    os.chmod(tmp, 0o644)
    os.replace(tmp, OUT)
    print(time.strftime("%FT%TZ", time.gmtime()), "ok", {k: len(p["bids"]) for k, p in out["pairs"].items()})


if __name__ == "__main__":
    main()
