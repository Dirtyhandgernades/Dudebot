import json,sqlite3
from smg.source_replay import select_sources

def test_source_selection_uses_dated_firm_corpus_and_distinct_issuers(tmp_path):
    path=tmp_path/'sources.sqlite';db=sqlite3.connect(path)
    db.execute('CREATE TABLE hits (id TEXT, source TEXT)')
    for key,cik,form,day in [('a','1','20-F','2024-04-01'),('b','1','8-K','2024-04-02'),('c','2','20-F','2024-05-01'),('future','3','20-F','2026-04-01')]:
        db.execute('INSERT INTO hits VALUES (?,?)',(key,json.dumps(dict(ciks=[cik],form=form,file_date=day))))
    db.commit();db.close()
    assert [i for i,_ in select_sources(path)]==['a','c']
