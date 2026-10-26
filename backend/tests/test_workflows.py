import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ["PAPERMIND_DATA_DIR"] = tempfile.mkdtemp(prefix="papermind-tests-")
os.environ['PAPERMIND_MODE']='fixture'
from fastapi.testclient import TestClient
from backend.main import app
from backend import store

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        store.DATA = Path(tempfile.mkdtemp(prefix="papermind-case-"))
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()

    def tearDown(self):
        self.client_context.__exit__(None, None, None)

    def send(self, text="为什么范围缩小会漏掉目标？", node="mechanism"):
        response=self.client.post("/api/documents/adaptive-search/messages",json={"text":text,"node_id":node})
        self.assertEqual(response.status_code,201,response.text)
        return response.json()

    def preview(self, message, revision=1):
        response=self.client.post("/api/documents/adaptive-search/patches",json={"message_id":message["assistant"]["id"],"base_revision":revision})
        self.assertEqual(response.status_code,201,response.text)
        return response.json()

    def test_live_database_does_not_inject_teaching_samples(self):
        with tempfile.TemporaryDirectory() as location,patch.object(store,'DATA',Path(location)),patch.dict(os.environ,{'PAPERMIND_MODE':'live'}):
            store.initialize()
            with store.connection() as db:self.assertEqual(store.items(db,'documents'),[])

    def test_production_bootstrap_does_not_leak_teaching_concepts(self):
        with store.connection(write=True) as db:
            db.execute('DELETE FROM documents')
        value=self.client.get('/api/bootstrap').json()
        self.assertEqual(value['documents'],[])
        self.assertEqual(value['concepts'],{})
        self.assertEqual(value['concept_sources'],[])

    def test_seed_and_health_are_explicitly_demo(self):
        self.assertFalse(self.client.get('/api/health').json()['llm_connected'])
        d=self.client.get('/api/documents/adaptive-search').json()
        self.assertEqual(len(d['nodes']),5)
        self.assertEqual(d['status'],'demo_ready')

    def test_context_anchor_and_scope_action(self):
        result=self.send('把范围缩小演示一下')
        self.assertEqual(result['user']['node_id'],'mechanism')
        self.assertEqual(result['assistant']['action']['scope'],'narrow')
        self.assertEqual(len(self.client.get('/api/documents/adaptive-search').json()['messages']),2)

    def test_reject_foreign_node(self):
        r=self.client.post('/api/documents/adaptive-search/messages',json={'text':'解释','node_id':'does-not-exist'})
        self.assertEqual(r.status_code,422)

    def test_patch_preview_apply_undo_does_not_save_concept(self):
        patch=self.preview(self.send())
        self.assertEqual(self.client.get('/api/documents/adaptive-search').json()['supplements'],[])
        path=f"/api/documents/adaptive-search/patches/{patch['id']}"
        self.assertEqual(self.client.post(path+'/apply',json={'base_revision':1}).status_code,200)
        self.assertEqual(self.client.get('/api/bootstrap').json()['library'],[])
        self.assertEqual(self.client.post(path+'/undo',json={'base_revision':2}).status_code,200)
        doc=self.client.get('/api/documents/adaptive-search').json()
        self.assertEqual(doc['revision'],3)
        self.assertEqual(doc['supplements'],[])

    def test_stale_preview_rejected_and_revision_monotonic(self):
        message=self.send()
        p1=self.preview(message); p2=self.preview(message)
        base='/api/documents/adaptive-search/patches/'
        self.client.post(base+p1['id']+'/apply',json={'base_revision':1})
        self.assertEqual(self.client.post(base+p2['id']+'/apply',json={'base_revision':1}).status_code,409)
        self.client.post(base+p1['id']+'/undo',json={'base_revision':2})
        self.assertEqual(self.client.post(base+p2['id']+'/apply',json={'base_revision':3}).status_code,409)

    def test_concept_save_is_layered_and_separate(self):
        self.client.put('/api/library',json={'document_id':'adaptive-search','concept_id':'candidate'})
        b=self.client.get('/api/bootstrap').json()
        self.assertEqual(b['library'][0]['id'],'candidate:definition')
        self.assertEqual(b['library'][0]['declaration'],'self_reported')
        self.assertEqual(self.client.get('/api/documents/adaptive-search').json()['supplements'],[])
        self.client.delete('/api/library/candidate:definition')
        self.assertEqual(self.client.get('/api/bootstrap').json()['library'],[])

    def test_memory_undo_tombstone_prevents_recreation(self):
        result=self.send('请解释公式符号')
        memory=result['new_memory']
        self.assertIsNotNone(memory)
        self.client.delete('/api/memories/'+memory['id'])
        self.assertIsNone(self.send('解释公式符号')['new_memory'])
        self.assertEqual(self.client.get('/api/bootstrap').json()['library'],[])

    def test_compare_requires_attached_source(self):
        self.assertFalse(self.send('比较两篇方法')['assistant']['can_patch'])
        self.client.post('/api/documents/adaptive-search/attachments',json={'document_id':'global-search'})
        response=self.send('比较两篇方法')
        self.assertIn('compare-method',response['assistant']['source_ids'])

    def test_unhandled_question_not_fabricated(self):
        result=self.send('某个未支持的请求')
        self.assertIn('暂不具备自由问答',result['assistant']['text'])
        self.assertFalse(result['assistant']['can_patch'])

    def test_invalid_pdf_and_cross_document_mutation(self):
        self.assertEqual(self.client.post('/api/documents',files={'file':('bad.pdf',b'not pdf','application/pdf')}).status_code,415)
        patch=self.preview(self.send())
        self.assertEqual(self.client.post(f"/api/documents/global-search/patches/{patch['id']}/apply",json={'base_revision':1}).status_code,404)

    def test_real_pdf_upload_incomplete_and_deduplicated(self):
        import pymupdf
        with pymupdf.open() as pdf:
            pdf.new_page().insert_text((72,72),'Local PDF extraction test. Not a generated explanation.')
            payload=pdf.tobytes()
        r=self.client.post('/api/documents',files={'file':('test.pdf',payload,'application/pdf')})
        self.assertEqual(r.status_code,201,r.text)
        doc_id=r.json()['id']
        doc=self.client.get('/api/documents/'+doc_id).json()
        self.assertEqual(doc['status'],'incomplete')
        self.assertIn('Local PDF extraction',doc['nodes'][0]['paragraphs'][0])
        self.assertEqual(self.client.get(f'/api/documents/{doc_id}/file').headers['content-type'],'application/pdf')
        self.assertEqual(self.client.get(f'/api/documents/{doc_id}/pages/1/image').headers['content-type'],'image/png')
        r2=self.client.post('/api/documents',files={'file':('again.pdf',payload,'application/pdf')})
        self.assertTrue(r2.json()['deduplicated'])
        response=self.client.post(f'/api/documents/{doc_id}/messages',json={'text':'请解释','node_id':'extracted'}).json()
        self.assertFalse(response['assistant']['can_patch'])

    def test_product_has_no_node_scene_or_quality_acceptance_routes(self):
        for path in ['/api/documents/adaptive-search/checks','/api/documents/adaptive-search/presentations']:
            self.assertEqual(self.client.get(path).status_code,404)

if __name__ == '__main__':
    unittest.main()
