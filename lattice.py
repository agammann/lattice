import argparse, html.parser, json, sqlite3
from pathlib import Path

SCHEMA = '''
CREATE TABLE IF NOT EXISTS sources(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS versions(id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL REFERENCES sources(id), text TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS cards(id INTEGER PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS edges(id INTEGER PRIMARY KEY, card_id INTEGER NOT NULL REFERENCES cards(id), version_id INTEGER NOT NULL REFERENCES versions(id), start INTEGER NOT NULL, end INTEGER NOT NULL, quote TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY, edge_id INTEGER NOT NULL REFERENCES edges(id), version_id INTEGER NOT NULL REFERENCES versions(id), status TEXT NOT NULL, note TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS card_revisions(id INTEGER PRIMARY KEY, card_id INTEGER NOT NULL REFERENCES cards(id), title TEXT NOT NULL, body TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP);
'''
class TextHTML(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.hidden=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.hidden+=1
        elif tag in ('p','div','br','li','h1','h2','h3'): self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script','style') and self.hidden: self.hidden-=1
        elif tag in ('p','div','li','h1','h2','h3'): self.parts.append('\n')
    def handle_data(self, data):
        if not self.hidden: self.parts.append(data)

def read_source(path):
    p=Path(path)
    if p.suffix.lower() == '.pdf': raise ValueError('PDF is not supported; extract text yourself first')
    text=p.read_text(encoding='utf-8')
    if p.suffix.lower() in ('.html','.htm'):
        parser=TextHTML(); parser.feed(text); text=''.join(parser.parts)
    if not text.strip(): raise ValueError('source is empty')
    return text

def connect(path):
    db=sqlite3.connect(path); db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON'); db.executescript(SCHEMA); return db

def add_source(db,name,text):
    db.execute('INSERT OR IGNORE INTO sources(name) VALUES (?)',(name,))
    sid=db.execute('SELECT id FROM sources WHERE name=?',(name,)).fetchone()['id']
    with db: return db.execute('INSERT INTO versions(source_id,text) VALUES (?,?)',(sid,text)).lastrowid

def add_card(db,source,title,body,quote):
    v=db.execute('SELECT v.* FROM versions v JOIN sources s ON s.id=v.source_id WHERE s.name=? ORDER BY v.id DESC LIMIT 1',(source,)).fetchone()
    if not v: raise ValueError('unknown source')
    if not quote or v['text'].count(quote)!=1: raise ValueError('passage must occur exactly once in the latest source')
    start=v['text'].index(quote)
    with db:
        card=db.execute('INSERT INTO cards(title,body) VALUES (?,?)',(title,body)).lastrowid
        return db.execute('INSERT INTO edges(card_id,version_id,start,end,quote) VALUES (?,?,?,?,?)',(card,v['id'],start,start+len(quote),quote)).lastrowid

def classify(old,new,start,end):
    # Map only a contiguous equal region; ambiguous repeated exact quotes cannot be relocated safely.
    quote=old[start:end]
    if old==new: return 'unchanged', quote
    if new.count(quote)==1: return 'unchanged', quote
    if new.count(quote)>1: return 'unresolvable', None

    # Use equal text on both sides as boundaries. Only unique boundaries permit a changed candidate.
    left=next((old[start-n:start] for n in range(1,min(start,32)+1) if new.count(old[start-n:start])==1), ""); right=next((old[end:end+n] for n in range(1,min(len(old)-end,32)+1) if new.count(old[end:end+n])==1), "")
    if left and right and new.count(left)==1 and new.count(right)==1:
        a=new.index(left)+len(left); b=new.index(right)
        if a<=b: return 'changed', new[a:b]
    return 'unresolvable', None

def queue(db):
    rows=db.execute('''SELECT e.*,c.title,c.body,v.text old,s.name source,
      (SELECT id FROM versions WHERE source_id=s.id ORDER BY id DESC LIMIT 1) latest_id,
      (SELECT text FROM versions WHERE source_id=s.id ORDER BY id DESC LIMIT 1) latest
      FROM edges e JOIN cards c ON c.id=e.card_id JOIN versions v ON v.id=e.version_id JOIN sources s ON s.id=v.source_id ORDER BY e.id''').fetchall()
    result=[]
    for r in rows:
        state,candidate=classify(r['old'],r['latest'],r['start'],r['end'])
        review=db.execute('SELECT status,note,created FROM reviews WHERE edge_id=? AND version_id=? ORDER BY id DESC LIMIT 1',(r['id'],r['latest_id'])).fetchone()
        result.append(dict(edge=r['id'],title=r['title'],body=r['body'],source=r['source'],baseline_version=r['version_id'],latest_version=r['latest_id'],status=state,old_passage=r['quote'],candidate=candidate,review=dict(review) if review else None))
    return result

def main(argv=None):
    p=argparse.ArgumentParser(description='Track source passages used by authored cards.')
    p.add_argument('--db',default='lattice.sqlite3'); sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('import'); a.add_argument('source'); a.add_argument('file')
    a=sub.add_parser('card'); a.add_argument('source'); a.add_argument('title'); a.add_argument('body'); a.add_argument('passage')
    sub.add_parser('queue')
    a=sub.add_parser('review'); a.add_argument('edge',type=int); a.add_argument('note')
    a=sub.add_parser('export'); a.add_argument('file')
    args=p.parse_args(argv); db=connect(args.db)
    try:
        if args.cmd=='import': print('version',add_source(db,args.source,read_source(args.file)))
        elif args.cmd=='card': print('edge',add_card(db,args.source,args.title,args.body,args.passage))
        elif args.cmd=='queue': print(json.dumps(queue(db),indent=2,ensure_ascii=False))
        elif args.cmd=='review':
            if not args.note.strip(): raise ValueError('review note cannot be empty')
            row=next((r for r in queue(db) if r['edge']==args.edge),None)
            if not row: raise ValueError('unknown edge')
            with db: db.execute('INSERT INTO reviews(edge_id,version_id,status,note) VALUES (?,?,?,?)',(args.edge,row['latest_version'],row['status'],args.note))
            print('review recorded; baseline evidence retained')
        else:
            data={'format':'lattice-evidence','version':1,'sources':[dict(r) for r in db.execute('SELECT * FROM sources')], 'versions':[dict(r) for r in db.execute('SELECT * FROM versions')], 'cards':[dict(r) for r in db.execute('SELECT * FROM cards')], 'edges':[dict(r) for r in db.execute('SELECT * FROM edges')], 'reviews':[dict(r) for r in db.execute('SELECT * FROM reviews')], 'card_revisions':[dict(r) for r in db.execute('SELECT * FROM card_revisions')], 'queue':queue(db)}
            with Path(args.file).open('x',encoding='utf-8') as output:
                json.dump(data,output,indent=2,ensure_ascii=False); output.write('\n')
            print('exported',args.file)
    except (ValueError,OSError,sqlite3.Error) as e: p.exit(2,f'error: {e}\n')
    finally: db.close()
if __name__=='__main__': main()





