"""Small diagnostic of cached annual filings; no labels or provider requests."""
import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path

import yaml
from lxml import html as lhtml

from .source_replay import parse_source, select_sources, source_identity

MAX_EVIDENCE = 60
MAX_SECONDS = 150
MAX_BYTES = 300_000


def flattened(node):
    return ' '.join(' '.join(node.itertext()).split())


def identity_evidence(raw):
    tree = lhtml.document_fromstring(raw.encode('utf8'), parser=lhtml.HTMLParser(encoding='utf8', no_network=True))
    text = flattened(tree)
    facts = {}
    for node in tree.xpath('//*[@name]'):
        name = node.get('name', '').lower()
        if name in {'dei:tradingsymbol', 'dei:securityexchangename', 'dei:entityregistrantname'}:
            facts.setdefault(name, [])
            value = flattened(node)
            if value not in facts[name]:
                facts[name].append(value)
    tables = []
    for table in tree.xpath('//table'):
        value = flattened(table)
        match = re.search(r'trading\s+symbols?', value, re.I)
        if match:
            snippet = value[max(0, match.start()-100):match.start()+600]
            if snippet not in tables:
                tables.append(snippet)
            if len(tables) == 2:
                break
    contexts = []
    own = r'\b(?:our|the company[’\']s)\s+[^;]{0,90}?(?:shares|stock|ADSs?)\b[^;]{0,320}'
    for match in re.finditer(own, text, re.I):
        passage = match.group()
        if re.search(r'listed|trading|\btrade[sd]?\b|symbol|ticker', passage, re.I):
            contexts.append(passage[:420])
            if len(contexts) == 2:
                break
    symbols = facts.get('dei:tradingsymbol', [])
    usable = {v for v in symbols if re.fullmatch('[A-Z]{1,6}', v)}
    venues = facts.get('dei:securityexchangename', [])
    reasons = []
    if not symbols:
        reasons.append('NO_INLINE_TRADING_SYMBOL_FACT')
    elif not usable:
        reasons.append('INLINE_SYMBOL_FORMAT_NOT_RECOGNIZED')
    elif len(usable) > 1:
        reasons.append('MULTIPLE_INLINE_TRADING_SYMBOLS')
    if not venues:
        reasons.append('NO_INLINE_EXCHANGE_FACT')
    elif not {v.upper() for v in venues} & {'NASDAQ', 'XNAS', 'NYSE', 'XNYS'}:
        reasons.append('INLINE_EXCHANGE_VALUE_NOT_RECOGNIZED')
    reasons.append('REGISTRATION_TABLE_PRESENT_BUT_UNRESOLVED' if tables else 'NO_REGISTRATION_TABLE_RECOGNIZED')
    reasons.append('ISSUER_LISTING_CONTEXT_PRESENT_BUT_UNRESOLVED' if contexts else 'NO_ISSUER_LISTING_CONTEXT_RECOGNIZED')
    symbol, exchange, _ = source_identity(tree, text)
    return dict(
        subreasons=reasons,
        inline_facts={k: [v[:140] for v in values[:6]] for k, values in facts.items()},
        registration_table_snippets=tables,
        issuer_listing_snippets=contexts,
        current_identity=dict(symbol=symbol, exchange=exchange),
    )


def main():
    started = time.monotonic()
    root = Path.cwd()
    indexes = sorted((root/'backtest/runtime/independent-checkpoint').rglob('firm-search.sqlite'))
    if not indexes:
        raise ValueError('Independent firm-search checkpoint is required')
    selected = [(identifier, src) for identifier, src in select_sources(indexes[0]) if src['form'] in {'10-K', '20-F'}]
    cache = root/'backtest/runtime/source-replay'
    entries = yaml.safe_load((root/'config/entities.yaml').read_text())
    jobs = []
    for identifier, src in selected:
        accession, filename = identifier.split(':', 1)
        url = f"https://www.sec.gov/Archives/edgar/data/{int(src['ciks'][0])}/{accession.replace('-', '')}/{filename}"
        jobs.append((identifier, src, url, cache/(hashlib.sha256(url.encode()).hexdigest()+'.html')))
    cache_absent = sum(not path.is_file() for _, _, _, path in jobs)
    counts, subreasons, errors = Counter(), Counter(), Counter()
    examples = []
    visited = 0
    budget = 0
    stop = 'COMPLETE'
    for identifier, src, url, path in jobs:
        if time.monotonic()-started >= MAX_SECONDS:
            stop = 'DEADLINE'
            break
        if len(examples) >= MAX_EVIDENCE:
            stop = 'EVIDENCE_LIMIT'
            break
        visited += 1
        if not path.is_file():
            counts['CACHE_ABSENT'] += 1
            continue
        try:
            raw = path.read_text(encoding='utf8')
            _, status = parse_source(identifier, src, raw, entries)
            counts[status] += 1
            if status != 'SOURCE_SYMBOL_OR_EXCHANGE_UNRESOLVED':
                continue
            evidence = identity_evidence(raw)
            subreasons.update(evidence['subreasons'])
            row = dict(id=identifier, cik=src['ciks'][0], form=src['form'], filed_at=src['file_date'], source_url=url, **evidence)
            size = len(json.dumps(row, ensure_ascii=False).encode('utf8'))
            if budget+size > MAX_BYTES-20_000:
                stop = 'ARTIFACT_SIZE_LIMIT'
                break
            examples.append(row)
            budget += size
        except Exception as exc:
            errors[type(exc).__name__] += 1
    report = dict(
        status='BOUNDED_CACHED_IDENTITY_AUDIT', stop_reason=stop,
        annual_sources_selected=len(selected), raw_cache_available=len(jobs)-cache_absent,
        raw_cache_absent=cache_absent, sources_visited=visited, sources_not_visited=len(jobs)-visited,
        source_status_counts=dict(counts), processing_error_types=dict(errors),
        processing_errors=sum(errors.values()),
        identity_subreason_counts=dict(subreasons), evidence_records=len(examples),
        elapsed_seconds=round(time.monotonic()-started, 2),
        scope='Independent corpus order; first 60 unresolved annual filings, cached HTML only. No labels or market providers opened.',
        interpretation='Subreasons describe parser evidence gaps, not verified firm negatives or recovered historical identities. Counts apply only to visited sources; cache availability covers all selected annual sources.',
        evidence=examples,
    )
    encoded = json.dumps(report, ensure_ascii=False, separators=(',', ':')).encode('utf8')
    if len(encoded) > MAX_BYTES:
        raise ValueError('Audit artifact exceeded its size limit')
    out = root/'reports/source-identity-audit'
    out.mkdir(parents=True, exist_ok=True)
    (out/'audit.json').write_bytes(encoded)
    print(json.dumps({k: v for k, v in report.items() if k != 'evidence'}))


if __name__ == '__main__':
    main()
