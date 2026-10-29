"""Local-only Lattice review UI; launch with `python app.py`."""
import argparse, json, secrets, sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse
import lattice

TOKEN=secrets.token_urlsafe(32)
HTML=Path(__file__).with_name('index.html').read_text(encoding='utf-8')

def make_handler(db_path):
 class Handler(BaseHTTPRequestHandler):
  def reply(self,status,data,content_type='application/json; charset=utf-8'):
   body=data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False).encode('utf-8')
   self.send_response(status); self.send_header('Content-Type',content_type); self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(body)
  def valid_host(self):
   return self.headers.get('Host') == '127.0.0.1:'+str(self.server.server_port)
  def do_GET(self):
   if not self.valid_host(): self.reply(403,{'error':'Invalid host'}); return
   if self.path=='/': self.reply(200,HTML.replace('__TOKEN__',TOKEN).encode('utf-8'),'text/html; charset=utf-8'); return
   if self.path=='/api/state':
    db=lattice.connect(db_path)
    try:
     state={'queue':lattice.queue(db),'sources':[dict(r) for r in db.execute('SELECT s.name, v.id, v.text FROM sources s JOIN versions v ON v.id=(SELECT max(id) FROM versions WHERE source_id=s.id) ORDER BY s.name')]}
     self.reply(200,state)
    finally: db.close()
    return
   if self.path=='/api/export':
    db=lattice.connect(db_path)
    try: self.reply(200,{'format':'lattice-evidence','version':1,**{t:[dict(r) for r in db.execute('SELECT * FROM '+t)] for t in ('sources','versions','cards','edges','reviews','card_revisions')},'queue':lattice.queue(db)})
    finally: db.close()
    return
   self.reply(404,{'error':'Not found'})
  def do_POST(self):
   if not self.valid_host(): self.reply(403,{'error':'Invalid host'}); return
   if self.headers.get('X-Lattice-Token')!=TOKEN: self.reply(403,{'error':'Invalid session'}); return
   try:
    n=int(self.headers.get('Content-Length','0'))
    if n<1 or n>2_000_000: raise ValueError('Request is empty or too large (2 MB limit)')
    data=json.loads(self.rfile.read(n)); db=lattice.connect(db_path)
    try:
     if self.path=='/api/import':
      name=data['name'].strip(); text=data['text']
      if not name or not text.strip(): raise ValueError('Source name and text are required')
      lattice.add_source(db,name,text)
     elif self.path=='/api/card':
      if not data['title'].strip() or not data['body'].strip(): raise ValueError('Title and card text are required')
      lattice.add_card(db,data['source'],data['title'].strip(),data['body'].strip(),data['passage'])
     elif self.path=='/api/edit':
      title=data['title'].strip(); body=data['body'].strip(); edge=int(data['edge'])
      if not title or not body: raise ValueError('Title and card text are required')
      row=db.execute('SELECT c.* FROM cards c JOIN edges e ON e.card_id=c.id WHERE e.id=?',(edge,)).fetchone()
      if not row: raise ValueError('Unknown card')
      with db:
       db.execute('INSERT INTO card_revisions(card_id,title,body) VALUES (?,?,?)',(row['id'],row['title'],row['body']))
       db.execute('UPDATE cards SET title=?,body=? WHERE id=?',(title,body,row['id']))
     elif self.path=='/api/review':
      edge=int(data['edge']); note=data['note'].strip(); expected=int(data['version'])
      if not note: raise ValueError('Review note is required')
      row=next((r for r in lattice.queue(db) if r['edge']==edge),None)
      if not row: raise ValueError('Unknown edge')
      if row['latest_version']!=expected: raise ValueError('Source changed while reviewing; refresh and inspect the new version')
      with db: db.execute('INSERT INTO reviews(edge_id,version_id,status,note) VALUES (?,?,?,?)',(edge,expected,row['status'],note))
     else: self.reply(404,{'error':'Not found'}); return
     self.reply(200,{'ok':True})
    finally: db.close()
   except (ValueError,KeyError,TypeError,json.JSONDecodeError,sqlite3.Error) as exc: self.reply(400,{'error':str(exc)})
  def log_message(self,*args): pass
 return Handler

def main():
 p=argparse.ArgumentParser(); p.add_argument('--db',default='lattice.sqlite3'); p.add_argument('--port',type=int,default=8765); a=p.parse_args()
 server=HTTPServer(('127.0.0.1',a.port),make_handler(a.db)); print(f'Lattice: http://127.0.0.1:{server.server_port} (Ctrl+C to stop)',flush=True)
 try: server.serve_forever()
 except KeyboardInterrupt: pass
 finally: server.server_close()
if __name__=='__main__': main()

