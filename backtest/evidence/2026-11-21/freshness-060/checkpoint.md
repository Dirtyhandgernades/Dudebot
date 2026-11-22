# Per-row source age audit

Added obsidian_packet_freshness to preserve original status labels while computing actual source ages at observation for IEX trades/quotes, SIP completed bars and safe-asof cutoffs. Missing/future/unparseable clocks counted explicitly; duplicate/incomplete roster rejects. One focused regression passed: fresh-at-asof label with a31-minute-old bar remains visibly old and never grants execution freshness.

Executed against actual packet44864611244 in verified artifact14691123325. All139 roster rows included;139 IEX trade clocks,139 IEX quote clocks,134 SIP bar-end clocks,5 SIP bar ends missing,139 safe-asof clocks. All139 halt rows SOURCE_UNAVAILABLE. These counts describe available clocks, not fresh or tradable quotes. Packet is historical at current receipt; delayed SIP safe-asof cannot be substituted for actual observation time. No new signals, predictions, outcomes or orders generated.

Next bind freshness audit to intake receipt and inspect exact retained halt-feed raw response to diagnose invalid feed independently of current live source health. The existing packet failure remains retained even if parser is repaired. Full goal active; live Monday runtime, current position review and predictive evidence remain unresolved.
