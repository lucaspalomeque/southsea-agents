# Scout — Learnings

## Feed Health (as of March 2026)

### Working
- **CoinDesk** (`coindesk`): Reliable, ~25 items per fetch. Primary news source.
- **a16z YouTube** (`yt_a16z`): Consistent, ~15 items. Good for tech/VC perspective.
- **Y Combinator YouTube** (`yt_ycombinator`): Consistent, ~15 items. Startup/tech focus.

### Broken
- **Bankless** (`bankless`): SSL certificate invalid — domain changed. Needs URL update.
- **Coin Bureau** (`coin_bureau`): Returns HTML instead of XML. Feed URL may have changed.
- **Network State YouTube** (`yt_network_state`): XML malformed. Channel ID may need verification.

## Discard Patterns
- Items without any valid topic are discarded (zero topic match)
- To be populated with recurring discard patterns as the pipeline runs
