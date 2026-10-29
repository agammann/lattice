import io, json, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
import app

class HTTPTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.db=str(Path(self.temp.name)/'test.sqlite3')
 def tearDown(self): self.temp.cleanup()
 def request(self,path,data=None,token=True,host='127.0.0.1:8765'):
  handler=object.__new__(app.make_handler(self.db)); handler.server=SimpleNamespace(server_port=8765); handler.path=path
  raw=json.dumps(data).encode() if data is not None else b''
  handler.headers={'Host':host,'Content-Length':str(len(raw)),'X-Lattice-Token':app.TOKEN if token else 'invalid'}; handler.rfile=io.BytesIO(raw); handler.wfile=io.BytesIO(); result={}
  handler.reply=lambda status,payload,content_type=None: result.update(status=status,payload=payload)
  (handler.do_POST if data is not None else handler.do_GET)(); return result
 def test_full_api_workflow_and_history(self):
  old='Introduction: abc.\nFirst fact: red.\nSecond fact: blue.\nThird fact: green.\nConclusion: done.'
  self.assertEqual(self.request('/api/import',{'name':'course','text':old})['status'],200)
  for word in ('red','blue','green','Introduction'):
   self.assertEqual(self.request('/api/card',{'source':'course','title':word,'body':'lesson','passage':word})['status'],200)
  self.request('/api/import',{'name':'course','text':old.replace('red','amber').replace('blue','cyan').replace('green','lime')})
  q=self.request('/api/state')['payload']['queue']; self.assertEqual([r['status'] for r in q],['changed','changed','changed','unchanged'])
  self.assertEqual(self.request('/api/edit',{'edge':1,'title':'Edited','body':'revised'})['status'],200)
  self.assertEqual(self.request('/api/review',{'edge':1,'version':2,'note':'checked'})['status'],200)
  evidence=self.request('/api/export')['payload']; self.assertEqual(evidence['card_revisions'][0]['title'],'red'); self.assertEqual(evidence['reviews'][0]['note'],'checked')
  self.request('/api/import',{'name':'course','text':old+' red'})
  self.assertEqual(self.request('/api/state')['payload']['queue'][0]['status'],'unresolvable')
  self.assertEqual(self.request('/api/review',{'edge':1,'version':2,'note':'stale'})['status'],400)
 def test_rejects_invalid_session_and_host(self):
  self.assertEqual(self.request('/api/import',{'name':'a','text':'b'},token=False)['status'],403)
  self.assertEqual(self.request('/api/state',host='evil.example')['status'],403)
if __name__=='__main__': unittest.main()
