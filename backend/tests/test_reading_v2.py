import unittest
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
from backend.reading_v2 import frame_html
from backend.tests.reading_checks import validate_artifact
from backend import reading_v2 as reading,store
from backend.reading_v2_markup import normalize

class ReadingV2Tests(unittest.TestCase):
    def setUp(self):
        self.doc={'nodes':[{'id':'mechanism'}]}
        self.data={'nodes':[{'id':'mechanism','concepts':[]}],'sources':{'S001':{'id':'real','page':1,'quote':'Source <script> text'}},'tables':[]}
        self.artifact={'title':'Test <title>','description':'test','html':'<section id="mechanism"><input type="range" id="q"><canvas id="plot"></canvas><button data-source="S001">来源</button></section>','css':'body{color:#123}','javascript':'(()=>{document.getElementById("q").addEventListener("input",()=>{});})();','teaching_assumptions':[],'limitations':[]}
    def test_runtime_boundary_is_separate_from_offline_quality_checks(self):
        missing={**self.artifact,'html':'<section>Generated content without a reading anchor</section>','javascript':''}
        reading.enforce_execution_boundary(missing)
        with self.assertRaises(ValueError):validate_artifact(missing,self.doc,self.data)
        with self.assertRaises(ValueError):reading.enforce_execution_boundary({**missing,'javascript':'fetch("https://example.com")'})

    def test_accepts_local_computation(self):
        self.assertEqual(validate_artifact(self.artifact,self.doc,self.data)['status'],'pass')
    def test_accepts_numeric_canonical_html5_ids_without_accepting_unsafe_ids(self):
        doc={'nodes':[{'id':'4g-limitations'}]}
        html='<section id="4g-limitations"><button data-source="S001">原文</button></section>'
        self.assertEqual(validate_artifact({**self.artifact,'html':html},doc,self.data)['status'],'pass')
        for invalid in ['4g limitations','4g/limitations','pm-local-source']:
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                validate_artifact({**self.artifact,'html':html.replace('4g-limitations',invalid)}, {'nodes':[{'id':invalid}]},self.data)
    def test_rejects_network_and_host_access(self):
        for code in ['fetch("https://x")','window.parent.document','new Worker("x")','eval("x")','localStorage.setItem("a","b")']:
            with self.subTest(code=code),self.assertRaises(ValueError):validate_artifact({**self.artifact,'javascript':code},self.doc,self.data)
    def test_rejects_markup_resource_and_event(self):
        for html in ['<img src="https://x">','<button onclick="alert(1)">x</button>','<iframe></iframe>','<a href="https://x">go</a>']:
            with self.subTest(html=html),self.assertRaises(ValueError):validate_artifact({**self.artifact,'html':self.artifact['html']+html},self.doc,self.data)
    def test_rejects_unmapped_source_and_missing_anchor(self):
        for html in ['<section id="mechanism"><button data-source="fake">来源</button></section>','<button data-source="S001">来源</button>']:
            with self.subTest(html=html),self.assertRaises(ValueError):validate_artifact({**self.artifact,'html':html},self.doc,self.data)
    def test_compile_escapes_evidence_and_unique_nonces(self):
        a=frame_html(self.artifact,self.data,{'id':'e','document_id':'d'},'test-channel')
        b=frame_html(self.artifact,self.data,{'id':'e','document_id':'d'},'test-channel')
        self.assertNotEqual(a,b)
        self.assertIn("connect-src 'none'",a)
        self.assertNotIn('Source <script>',a)
        self.assertIn('Test &lt;title&gt;',a)
    def test_rejects_unknown_dynamically_created_source(self):
        bad={**self.artifact,'javascript':'const sourceIds=["S0011"]; button.setAttribute("data-source",sourceIds[0]);'}
        with self.assertRaises(ValueError):validate_artifact(bad,self.doc,self.data)

    def test_accepts_local_svg_definitions_but_rejects_external_paint(self):
        svg='<svg><defs><pattern id="grid"></pattern><linearGradient id="shade"><stop offset="0"/></linearGradient></defs><rect fill="url(\'#grid\')"/></svg><pre><code>local</code></pre>'
        self.assertEqual(validate_artifact({**self.artifact,'html':self.artifact['html']+svg},self.doc,self.data)['status'],'pass')
        for paint in ['url(https://example.com/paint.svg)', 'url("https://example.com/paint.svg")']:
            with self.subTest(paint=paint),self.assertRaises(ValueError):
                validate_artifact({**self.artifact,'html':self.artifact['html']+f"<svg><rect fill='{paint}'/></svg>"},self.doc,self.data)

    def test_semantic_anchor_wraps_real_attributed_content_without_breaking_author_selector(self):
        original={**self.artifact,'html':'<section id="local" data-node="mechanism"><p>This is the actual complete mechanism explanation with sufficient context.</p><button data-source="S001">source</button></section>',
                  'javascript':'document.getElementById("local").dataset.ready="yes";'}
        result=normalize(original,['mechanism'],'chapter-a')
        self.assertIn('<section id="mechanism" data-node="mechanism"',result['html'])
        self.assertIn('id="chapter-a--local"',result['html'])
        self.assertIn('getElementById("chapter-a--local")',result['javascript'])
        self.assertEqual(validate_artifact(result,self.doc,self.data)['status'],'pass')

    def test_missing_content_is_not_replaced_with_a_hidden_anchor(self):
        original={**self.artifact,'html':'<div id="local">Unattributed content</div><button data-source="S001">source</button>'}
        with self.assertRaisesRegex(ValueError,'锚点'):
            validate_artifact(normalize(original,['mechanism'],'chapter-a'),self.doc,self.data)

    def test_private_identifiers_and_svg_relations_do_not_collide_across_chapters(self):
        original={**self.artifact,'html':self.artifact['html']+'<svg><defs><marker id="arrow"/></defs><path id="edge" marker-end="url(#arrow)"/></svg><label for="q">Q</label>',
                  'css':'#q{color:#123} #edge{marker-end:url("#arrow")}',
                  'javascript':'document.querySelector("#edge");document.getElementById("q");'}
        first=normalize(original,['mechanism'],'first');second=normalize(original,['other'],'second')
        self.assertIn('url(#first--arrow)',first['html'])
        self.assertIn('for="first--q"',first['html'])
        self.assertIn('#second--edge',second['javascript'])
        self.assertNotIn('id="q"',first['html']+second['html'])

    def test_math_markup_cache_reuses_the_same_render_without_skipping_new_content(self):
        from backend.reading_math import render_math
        from types import SimpleNamespace
        render_math.cache_clear()
        with patch('backend.reading_math.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='["<math><mi>x</mi></math>"]')) as process:
            a=render_math('<p>$x$</p>');b=render_math('<p>$x$</p>')
            self.assertEqual(a,b);self.assertEqual(process.call_count,1)
            render_math('<article>$x$</article>');self.assertEqual(process.call_count,2)
        render_math.cache_clear()


class ReadingDefaultTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.patcher=patch.object(store,'DATA',Path(self.temp.name));self.patcher.start()
        store.initialize()
        self.doc={'id':'reading-test','status':'ready','is_demo':False,'nodes':[], 'sources':[],'file_path':None}
        with store.connection(write=True) as db:store.put_document(db,self.doc)
        self.edition=reading.create(self.doc['id'])
        f=reading.folder(self.edition['id'])
        artifact={'title':'T','description':'D','html':'<section></section>','css':'','javascript':'','teaching_assumptions':[],'limitations':[]}
        (f/'artifact.json').write_text(json.dumps(artifact),encoding='utf-8');(f/'data.json').write_text('{}',encoding='utf-8')

    def tearDown(self):
        self.patcher.stop();self.temp.cleanup()

    def complete(self):
        reading.update(self.edition['id'],status='running')
        return reading.publish(self.edition['id'])

    def test_completion_publishes_without_quality_acceptance(self):
        with self.assertRaises(ValueError):reading.publish(self.edition['id'])
        self.complete()
        self.assertEqual(reading.get(self.edition['id'])['status'],'completed')
        reading.create(self.doc['id'])
        self.assertEqual(reading.default_edition(self.doc['id'])['id'],self.edition['id'])
        with store.connection() as db:self.assertEqual(store.get_document(db,self.doc['id']),self.doc)

    def test_runtime_change_does_not_hide_completed_page_but_missing_file_falls_back(self):
        self.complete()
        self.assertIsNotNone(reading.default_edition(self.doc['id']))
        (reading.folder(self.edition['id'])/'artifact.json').unlink()
        self.assertIsNone(reading.default_edition(self.doc['id']))

    def test_default_route_and_cross_document_ownership(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from backend.reading_v2_routes import router
        app=FastAPI();app.include_router(router)
        client=TestClient(app)
        self.assertEqual(client.get('/api/documents/reading-test/reading-v2/default').json(),None)
        self.complete()
        self.assertEqual(client.get('/api/documents/reading-test/reading-v2/default').json()['id'],self.edition['id'])
        self.assertEqual(client.get(f'/api/documents/foreign/reading-v2/{self.edition["id"]}').status_code,409)
        self.assertEqual(client.get(f'/api/documents/reading-test/reading-v2/{self.edition["id"]}/export').status_code,200)
        self.assertEqual(client.post(f'/api/documents/reading-test/reading-v2/{self.edition["id"]}/publish').status_code,404)

    def test_successful_generation_immediately_exposes_default_without_review_calls(self):
        artifact=json.loads((reading.folder(self.edition['id'])/'artifact.json').read_text())
        pack={'nodes':[],'sources':{},'pages':[],'concepts':{},'title':'Test'}
        with patch.object(reading,'evidence',return_value=pack),patch.object(reading.gateway,'structured',return_value={'chapters':[],'visual_pages':[]}) as model,patch('backend.reading_v2_author.compose',return_value=artifact):
            result=reading.generate(self.edition['id'])
        self.assertEqual(result['status'],'completed')
        self.assertEqual(reading.default_edition(self.doc['id'])['id'],result['id'])
        self.assertEqual([c.args[0] for c in model.call_args_list],['planner'])
        self.assertNotIn('checks',result)

    def test_failed_or_cancelled_regeneration_preserves_last_published_page(self):
        self.complete()
        for cancelled in [False,True]:
            edition=reading.create(self.doc['id'])
            if cancelled:reading.cancel(edition['id'],self.doc['id'])
            with patch.object(reading,'evidence',side_effect=RuntimeError('failed generation')):
                with self.assertRaises((RuntimeError,InterruptedError)):reading.generate(edition['id'])
            self.assertEqual(reading.get(edition['id'])['status'],'cancelled' if cancelled else 'failed')
            self.assertEqual(reading.default_edition(self.doc['id'])['id'],self.edition['id'])

    def test_existing_generated_draft_is_published_on_startup_without_models(self):
        reading.update(self.edition['id'],status='draft')
        with patch.object(reading.settings,'live_enabled',return_value=False):
            reading.startup()
        reading.shutdown()
        self.assertEqual(reading.default_edition(self.doc['id'])['id'],self.edition['id'])

    def test_repeated_request_reuses_active_generation(self):
        with patch.object(reading,'POOL') as pool:
            result=reading.enqueue(self.doc['id'])
        self.assertEqual(result['id'],self.edition['id'])
        pool.submit.assert_not_called()

if __name__=='__main__':unittest.main()
