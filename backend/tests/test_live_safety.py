import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
os.environ['PAPERMIND_MODE']='fixture'
from backend import jobs, parser, retrieval, store
from backend.demo_data import fixture_documents
from backend.live_contracts import Plan,NodeBatch
from backend.tests.reading_checks import ref_issues

class LiveSafetyTests(unittest.TestCase):
    def setUp(self):
        store.DATA=Path(tempfile.mkdtemp(prefix='papermind-live-test-'))
        store.initialize()

    def test_external_fetch_cannot_read_local_files_or_loopback(self):
        for url in ['file:///C:/Windows/win.ini','http://127.0.0.1/private','http://[::1]/','http://localhost:8000/api/bootstrap','https://user:pass@example.com/']:
            with self.subTest(url=url),self.assertRaises(ValueError):retrieval.public_url(url)

    def test_scholarly_filter_rejects_blog_even_if_successfully_downloaded(self):
        self.assertTrue(retrieval.scholarly_source('https://plato.stanford.edu/entries/ethics-ai/'))
        self.assertTrue(retrieval.scholarly_source('https://arxiv.org/pdf/1706.03762'))
        self.assertFalse(retrieval.scholarly_source('https://arxiv.org.attacker.example/blog'))
        self.assertFalse(retrieval.scholarly_source('https://www.cnblogs.com/article'))

    def test_academic_query_preserves_digits_in_technical_terms(self):
        with patch('backend.retrieval.httpx.Client') as client:
            response=client.return_value.__enter__.return_value.get.return_value
            response.text='<feed xmlns="http://www.w3.org/2005/Atom"/>'
            retrieval.academic_index('word2vec negative sampling noise')
            params=client.return_value.__enter__.return_value.get.call_args.kwargs['params']
            self.assertEqual(params['search_query'],'all:word2vec AND all:negative AND all:sampling')

    def test_missing_citation_and_empty_stepper_cannot_pass_structure(self):
        node={'source_ids':['invented'],'claims':[{'source_ids':['original']}],'steps':[],'terms':[],'interaction':'stepper'}
        issues=ref_issues(node,{'original'})
        self.assertTrue(any('invented' in s for s in issues))
        self.assertTrue(any('步骤' in s for s in issues))

    def test_source_only_document_has_explicit_anchor_without_allowing_foreign_nodes(self):
        from backend.main import require_node
        from fastapi import HTTPException
        doc={'is_demo':False,'nodes':[]}
        require_node(doc,'document')
        with self.assertRaises(HTTPException):require_node(doc,'foreign-node')
        with self.assertRaises(HTTPException):require_node({'is_demo':True,'nodes':[]},'document')

    def test_composer_expands_only_known_short_evidence_handles(self):
        node={'id':'n1','title':'Node','summary':'Result','paragraphs':['Result'],'source_ids':['R00001'],'claims':[{'id':'c1','statement':'Result','conditions':[],'source_ids':['R00001']}],'interaction':'none','steps':[],'terms':[],'formula':None,'assumptions':[]}
        def model(role,instruction,evidence,schema,**kwargs):
            self.assertEqual(evidence['sources'][0]['id'],'R00001')
            return {'nodes':[node]}
        payload={'sources':[{'id':'pdf-real-p1-b10','page':1,'quote':'Result'}],'requested_nodes':[{'id':'n1','source_pages':[1]}]}
        with patch('backend.jobs.gateway.structured',side_effect=model):
            value=jobs.compose_nodes(store.DATA/'node.json','Explain',payload,max_tokens=3000,context={})
        self.assertEqual(value['nodes'][0]['claims'][0]['source_ids'],['pdf-real-p1-b10'])

    def test_invalid_batch_retries_individual_nodes_without_filling_fields(self):
        def model(role,instruction,evidence,schema,**kwargs):
            group=evidence['requested_nodes']
            if len(group)>1:raise jobs.gateway.ModelError('strict schema rejected')
            return {'nodes':[{'id':group[0]['id'],'title':'Node','summary':'Result','paragraphs':['Result'],'source_ids':['R00001'],'claims':[{'id':'c1','statement':'Result','conditions':[],'source_ids':['R00001']}],'interaction':'none','steps':[],'terms':[],'formula':None,'assumptions':[]}]}
        payload={'sources':[{'id':'real','page':1,'quote':'Result'}],'requested_nodes':[{'id':f'n{i}','source_pages':[1]} for i in range(2)]}
        with patch('backend.jobs.gateway.structured',side_effect=model) as calls:
            value=jobs.compose_nodes(store.DATA/'nodes.json','Explain',payload,max_tokens=3000,context={})
        self.assertEqual(calls.call_count,3)
        self.assertEqual([n['id'] for n in value['nodes']],['n0','n1'])
        self.assertTrue((store.DATA/'nodes-single-0.json').is_file())

    def test_image_only_page_really_enters_ocr_branch(self):
        import pymupdf
        path=store.DATA/'scan.pdf'
        with pymupdf.open() as original:
            p=original.new_page();p.insert_text((72,72),'A rasterized regression sample')
            pix=p.get_pixmap()
            with pymupdf.open() as scanned:
                scanned.new_page(width=p.rect.width,height=p.rect.height).insert_image(p.rect,pixmap=pix)
                scanned.save(path)
        with patch('backend.parser.gateway.ocr',return_value='Recognized example text from image-only source.') as ocr:
            ir=parser.parse({'id':'scan-test','title':'scan','file_path':str(path)},inspect_visuals=False)
        self.assertEqual(ocr.call_count,1)
        self.assertEqual(ir['ocr_pages'],1)
        self.assertEqual(ir['sources'][0]['status'],'ocr_extracted')
        self.assertTrue(ir['sources'][0]['bbox'])

    def test_generation_continues_to_interactive_page_without_quality_review(self):
        doc=fixture_documents()[0];doc.update(id='live-test',is_demo=False,nodes=[],supplements=[])
        source={'id':'original','kind':'paper','page':1,'quote':'The study reports a bounded result.','title':'source','locator':'p1','status':'located','url':None}
        ir={'sources':[source],'pages':[{'page':1,'text':source['quote'],'source_ids':['original']}],'visuals':[],'gaps':[],'page_count':1,'ocr_pages':0,'two_column_pages':0,'parser_version':'test'}
        plan={'title':'Test','subtitle':'Test','domain':'testing','nodes':[{'id':f'n{i}','title':f'Node {i}','purpose':'explain','source_pages':[1],'required':True} for i in range(3)],'coverage_notes':[],'core_gaps':['核心证据区域无法读取']}
        nodes=[{'id':f'n{i}','title':f'Node {i}','summary':'Bounded result','paragraphs':['The study reports a bounded result.'],'source_ids':['original'],'claims':[{'id':f'c{i}','statement':'A bounded result','source_ids':['original'],'conditions':[]}],'interaction':'none','steps':[],'terms':[],'formula':None,'assumptions':[]} for i in range(3)]
        job={'id':'job-test','document_id':doc['id'],'status':'queued','stage':'queued','force_ocr_pages':[],'cancel_requested':False}
        with store.connection(write=True) as db:
            store.put_document(db,doc);db.execute('INSERT INTO jobs VALUES (?,?,?)',(job['id'],doc['id'],store.encode(job)))
        def model(role,instruction,evidence,schema,**kwargs):
            if schema is Plan:return plan
            if schema is NodeBatch:return {'nodes':nodes}
            self.fail('Unexpected live call contract')
        with patch('backend.jobs.parser.parse',return_value=ir),patch('backend.jobs.gateway.structured',side_effect=model) as calls,patch('backend.reading_v2.generate') as generate:
            jobs.run_job(job['id'])
            generate.assert_called_once()
            self.assertNotIn('reviewer',[c.args[0] for c in calls.call_args_list])
        with store.connection() as db:
            result=store.get_document(db,doc['id']);finished=jobs.get_job(db,job['id'])
        self.assertEqual(finished['status'],'completed')
        self.assertEqual(result['status'],'ready')
        self.assertTrue(result['generation_gaps'])

if __name__=='__main__':unittest.main()
