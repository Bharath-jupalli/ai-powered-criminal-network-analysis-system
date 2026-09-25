import json
from pathlib import Path
import sqlite3
from datetime import datetime

DB_PATH=Path(__file__).resolve().parent/'investigation.db'

def _conn():
    c=sqlite3.connect(DB_PATH)
    c.row_factory=sqlite3.Row
    return c

def _ensure_column(c, table, column, definition):
    cols = {row[1] for row in c.execute(f'PRAGMA table_info({table})').fetchall()}
    if column not in cols:
        c.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')

def init_database():
    with _conn() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT UNIQUE NOT NULL, title TEXT NOT NULL, description TEXT DEFAULT '', priority TEXT DEFAULT 'MEDIUM', status TEXT DEFAULT 'OPEN', created_at TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS case_entities (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL, entity_id TEXT NOT NULL, name TEXT NOT NULL, entity_type TEXT NOT NULL, city TEXT DEFAULT '', source TEXT DEFAULT 'FIR', metadata TEXT DEFAULT '', UNIQUE(case_id, entity_id), FOREIGN KEY(case_id) REFERENCES cases(case_id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS case_relationships (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL, source_entity_id TEXT NOT NULL, target_entity_id TEXT NOT NULL, relationship TEXT NOT NULL, UNIQUE(case_id, source_entity_id, target_entity_id, relationship), FOREIGN KEY(case_id) REFERENCES cases(case_id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS previous_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_id TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            title TEXT DEFAULT '',
            fir_number TEXT DEFAULT '',
            case_id TEXT DEFAULT '',
            extracted_json TEXT NOT NULL,
            raw_text TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS previous_case_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            previous_case_id INTEGER NOT NULL,
            current_case_id TEXT NOT NULL,
            score REAL DEFAULT 0,
            reasons_json TEXT DEFAULT '[]',
            created_at TEXT NOT NULL,
            UNIQUE(previous_case_id, current_case_id)
        )''')

        # Migrate databases created by earlier project versions. The map endpoint
        # needs entity_type; older databases sometimes called this column `type`.
        entity_cols = {row[1] for row in c.execute('PRAGMA table_info(case_entities)').fetchall()}
        if 'entity_type' not in entity_cols:
            c.execute("ALTER TABLE case_entities ADD COLUMN entity_type TEXT DEFAULT 'UNKNOWN'")
            if 'type' in entity_cols:
                c.execute("UPDATE case_entities SET entity_type=COALESCE(NULLIF(type,''),'UNKNOWN')")
        _ensure_column(c, 'case_entities', 'city', "TEXT DEFAULT ''")
        _ensure_column(c, 'case_entities', 'source', "TEXT DEFAULT 'FIR'")
        _ensure_column(c, 'case_entities', 'metadata', "TEXT DEFAULT ''")

        if c.execute('SELECT COUNT(*) FROM cases').fetchone()[0]==0:
            c.execute('INSERT INTO cases(case_id,title,description,priority,status,created_at) VALUES(?,?,?,?,?,?)',('CASE-001','Synthetic Network Investigation','Demonstration case for network analysis.','HIGH','OPEN',datetime.now().isoformat(timespec='seconds')))
        c.commit()

def _d(r): return dict(r) if r else None

def create_case(case_id,title,description='',priority='MEDIUM'):
    with _conn() as c:
        c.execute('INSERT INTO cases(case_id,title,description,priority,status,created_at) VALUES(?,?,?,?,?,?)',(case_id,title,description,priority,'OPEN',datetime.now().isoformat(timespec='seconds')))
        c.commit()
        return _d(c.execute('SELECT * FROM cases WHERE case_id=?',(case_id,)).fetchone())

def get_cases():
    with _conn() as c:return [_d(r) for r in c.execute('SELECT * FROM cases ORDER BY id DESC').fetchall()]

def get_case(case_id):
    with _conn() as c:return _d(c.execute('SELECT * FROM cases WHERE case_id=?',(case_id,)).fetchone())

def update_case_status(case_id,status):
    with _conn() as c:
        c.execute('UPDATE cases SET status=? WHERE case_id=?',(status,case_id)); c.commit(); return _d(c.execute('SELECT * FROM cases WHERE case_id=?',(case_id,)).fetchone())

def delete_case(case_id):
    """Delete a case and all case-scoped child records.

    Explicit child deletes keep this compatible with older databases whose
    foreign keys were not declared with ON DELETE CASCADE.
    """
    with _conn() as c:
        existing = c.execute('SELECT * FROM cases WHERE case_id=?',(case_id,)).fetchone()
        if not existing:
            return None
        c.execute('DELETE FROM case_relationships WHERE case_id=?',(case_id,))
        c.execute('DELETE FROM case_entities WHERE case_id=?',(case_id,))
        c.execute('DELETE FROM cases WHERE case_id=?',(case_id,))
        c.commit()
        return _d(existing)

def save_case_entities(case_id, entities, relationships):
    with _conn() as c:
        c.execute('DELETE FROM case_relationships WHERE case_id=?',(case_id,))
        c.execute('DELETE FROM case_entities WHERE case_id=?',(case_id,))
        for e in entities:
            c.execute('INSERT OR REPLACE INTO case_entities(case_id,entity_id,name,entity_type,city,source,metadata) VALUES(?,?,?,?,?,?,?)',
                      (case_id,e['id'],e['name'],e.get('type','UNKNOWN'),e.get('city',''),e.get('source','FIR'),e.get('metadata','')))
        for r in relationships:
            c.execute('INSERT OR IGNORE INTO case_relationships(case_id,source_entity_id,target_entity_id,relationship) VALUES(?,?,?,?)',
                      (case_id,r['source'],r['target'],r.get('relationship','RELATED')))
        c.commit()

def get_case_entities(case_id):
    with _conn() as c:
        rows=c.execute('SELECT entity_id AS id,name,entity_type AS type,city,source,metadata FROM case_entities WHERE case_id=? ORDER BY id',(case_id,)).fetchall()
        return [_d(r) for r in rows]

def get_case_relationships(case_id):
    with _conn() as c:
        rows=c.execute('SELECT source_entity_id AS source,target_entity_id AS target,relationship FROM case_relationships WHERE case_id=? ORDER BY id',(case_id,)).fetchall()
        return [_d(r) for r in rows]


def save_previous_case(reference_id, filename, result, raw_text):
    with _conn() as c:
        c.execute(
            '''INSERT INTO previous_cases(reference_id,filename,title,fir_number,case_id,extracted_json,raw_text,created_at)
               VALUES(?,?,?,?,?,?,?,?)''',
            (reference_id, filename or "previous-case", result.get("title",""),
             result.get("fir_number",""), result.get("case_id",""),
             json.dumps(result, ensure_ascii=False), raw_text or "",
             datetime.now().isoformat(timespec="seconds"))
        )
        c.commit()
        return _d(c.execute('SELECT * FROM previous_cases WHERE reference_id=?',(reference_id,)).fetchone())

def get_previous_cases():
    with _conn() as c:
        return [_d(r) for r in c.execute(
            'SELECT id,reference_id,filename,title,fir_number,case_id,created_at FROM previous_cases ORDER BY id DESC'
        ).fetchall()]

def get_previous_case(previous_id):
    with _conn() as c:
        return _d(c.execute('SELECT * FROM previous_cases WHERE id=?',(previous_id,)).fetchone())

def save_previous_case_link(previous_case_id, current_case_id, score, reasons):
    with _conn() as c:
        c.execute(
            '''INSERT INTO previous_case_links(previous_case_id,current_case_id,score,reasons_json,created_at)
               VALUES(?,?,?,?,?)
               ON CONFLICT(previous_case_id,current_case_id) DO UPDATE SET score=excluded.score,reasons_json=excluded.reasons_json''',
            (previous_case_id,current_case_id,float(score),json.dumps(reasons,ensure_ascii=False),
             datetime.now().isoformat(timespec="seconds"))
        )
        c.commit()
