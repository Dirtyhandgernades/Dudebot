# Actual artifact intake

Added CLI backtest.obsidian_board_intake. Verifies ZIP expected hash, unique packet/board members, exact packet-byte binding, unique complete roster and source<=board<=receipt clock before exclusive receipt write. Five synthetic tests passed including altered hash, source binding, incomplete roster, duplicate ZIP member and future clock. Expected duplicate-member warning from adversarial fixture.

Actually ran against retained artifact14691123325/run44864611244, independently matched ZIP eb91a26b2bd3baa63d7f12e92e34b92d2a98f51ac1019f696f8a38455d64daa5. Packet hash75aa868f9496ac808a4e904e4f63fbb592154dc36450e3ec5745fe5e29c803f5 and board a760c97e5f6158141f196a737732e273a298192faa1ddfb7e501b6b31ad33aab.139 roster entries verified. Actual receipt2026-11-22T03:38:49.392273Z (Nov21 21:38 CT); packet age84590.252369 seconds. It is stale research, not a current decision. decision_review_completed=false and submission_authorized=false.

Installed Windows dispatcher still lacks a scheduled download/intake/decision consumer; this CLI verifies one local intake only. Next connect verified run identity to download and intake using bounded polling and explicit deadline freshness, retaining failure receipts. No duplicate automation, account data or order action introduced. Full goal remains incomplete.
