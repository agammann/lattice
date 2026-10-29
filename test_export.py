import contextlib, io, json, tempfile, unittest
from pathlib import Path
import lattice

class ExportSafetyTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name); self.db=self.root/'data.sqlite3'
  db=lattice.connect(self.db); lattice.add_source(db,'course','A sample source.'); db.close()
 def tearDown(self): self.temp.cleanup()
 def run_export(self,path):
  with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
   with self.assertRaises(SystemExit) as error: lattice.main(['--db',str(self.db),'export',str(path)])
  self.assertEqual(error.exception.code,2)
 def test_database_and_relative_alias_are_not_overwritten(self):
  before=self.db.read_bytes()
  for target in (self.db,self.root/'.'/self.db.name):
   self.run_export(target); self.assertEqual(self.db.read_bytes(),before)
 def test_existing_export_is_not_overwritten(self):
  target=self.root/'evidence.json'; target.write_text('existing',encoding='utf-8')
  self.run_export(target); self.assertEqual(target.read_text(encoding='utf-8'),'existing')
 def test_hardlink_alias_is_not_overwritten(self):
  alias=self.root/'alias.sqlite3'
  try: alias.hardlink_to(self.db)
  except OSError as exc: self.skipTest(str(exc))
  before=self.db.read_bytes(); self.run_export(alias); self.assertEqual(self.db.read_bytes(),before)
 def test_new_export_succeeds(self):
  target=self.root/'new.json'
  with contextlib.redirect_stdout(io.StringIO()): lattice.main(['--db',str(self.db),'export',str(target)])
  self.assertEqual(json.loads(target.read_text(encoding='utf-8'))['format'],'lattice-evidence')
if __name__=='__main__': unittest.main()

