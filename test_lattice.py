import json, tempfile, unittest
from pathlib import Path
import lattice

class LatticeTests(unittest.TestCase):
 def setUp(self):
  self.db=lattice.connect(':memory:')
  self.old='Introduction: abc.\nFirst fact: red.\nSecond fact: blue.\nThird fact: green.\nConclusion: done.'
  lattice.add_source(self.db,'course',self.old)
 def tearDown(self): self.db.close()
 def add(self,quote): return lattice.add_card(self.db,'course',quote,'Lesson body',quote)
 def test_three_changes_and_unrelated(self):
  for s in ('red','blue','green','Introduction'): self.add(s)
  lattice.add_source(self.db,'course',self.old.replace('red','amber').replace('blue','cyan').replace('green','lime'))
  states=[x['status'] for x in lattice.queue(self.db)]
  self.assertEqual(states,['changed','changed','changed','unchanged'])
 def test_duplicate_and_missing_passage_rejected(self):
  lattice.add_source(self.db,'duplicate','x x')
  for quote in ('x','missing',''):
   with self.assertRaises(ValueError): lattice.add_card(self.db,'duplicate','T','B',quote)
 def test_duplicate_new_passage_is_unresolvable(self):
  self.add('red'); lattice.add_source(self.db,'course',self.old+' red')
  self.assertEqual(lattice.queue(self.db)[0]['status'],'unresolvable')
 def test_deleted_boundaries_unresolvable(self):
  self.add('red'); lattice.add_source(self.db,'course','completely different')
  self.assertEqual(lattice.queue(self.db)[0]['status'],'unresolvable')
 def test_review_is_version_specific_and_history_preserved(self):
  edge=self.add('red'); v=lattice.add_source(self.db,'course',self.old.replace('red','amber'))
  self.db.execute('INSERT INTO reviews(edge_id,version_id,status,note) VALUES (?,?,?,?)',(edge,v,'changed','checked'))
  self.assertEqual(lattice.queue(self.db)[0]['review']['note'],'checked')
  lattice.add_source(self.db,'course',self.old.replace('red','orange'))
  self.assertIsNone(lattice.queue(self.db)[0]['review'])
  self.assertEqual(self.db.execute('SELECT count(*) FROM reviews').fetchone()[0],1)
 def test_html_and_pdf(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.html'; p.write_text('<p>Hello</p><script>secret</script>',encoding='utf8')
   self.assertIn('Hello',lattice.read_source(p)); self.assertNotIn('secret',lattice.read_source(p))
   with self.assertRaises(ValueError): lattice.read_source(Path(d)/'a.pdf')
if __name__=='__main__': unittest.main()
