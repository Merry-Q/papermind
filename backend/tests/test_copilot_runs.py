import os
import tempfile
import time
import unittest
from pathlib import Path

os.environ['PAPERMIND_MODE']='fixture'
os.environ['PAPERMIND_DATA_DIR']=tempfile.mkdtemp(prefix='papermind-copilot-tests-')

from fastapi.testclient import TestClient
from backend import store
from backend.main import app


class CopilotRunTests(unittest.TestCase):
    def setUp(self):
        store.DATA=Path(tempfile.mkdtemp(prefix='papermind-copilot-case-'))
        self.context=TestClient(app);self.client=self.context.__enter__()

    def tearDown(self):
        self.context.__exit__(None,None,None)

    def wait_for(self,run_id,statuses,timeout=3):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            value=self.client.get(f'/api/copilot/runs/{run_id}').json()
            if value['status'] in statuses:return value
            time.sleep(.03)
        self.fail(f'run {run_id} did not reach {statuses}')

    def test_quick_turn_persists_progress_and_answer(self):
        response=self.client.post('/api/documents/adaptive-search/copilot/runs',json={
            'text':'为什么范围缩小会漏掉目标？','node_id':'mechanism','mode':'auto'})
        self.assertEqual(response.status_code,202,response.text)
        run=self.wait_for(response.json()['id'],{'completed'})
        self.assertEqual(run['mode'],'quick')
        doc=self.client.get('/api/documents/adaptive-search').json()
        self.assertEqual([message['role'] for message in doc['messages']],['user','assistant'])
        self.assertEqual(doc['messages'][-1]['run_id'],run['id'])
        events=self.client.get(f"/api/copilot/runs/{run['id']}/events").json()['events']
        self.assertEqual([event['event_id'] for event in events],sorted(event['event_id'] for event in events))
        self.assertIn('completed',[event['type'] for event in events])

    def test_deep_turn_waits_for_plan_confirmation(self):
        self.client.post('/api/documents/adaptive-search/attachments',json={'document_id':'global-search'})
        response=self.client.post('/api/documents/adaptive-search/copilot/runs',json={
            'text':'深度比较两篇方法的假设与局限','node_id':'mechanism','mode':'deep'})
        run=self.wait_for(response.json()['id'],{'awaiting_user'})
        self.assertTrue(run['plan']['use_attached_documents'])
        self.assertEqual(len(self.client.get('/api/documents/adaptive-search').json()['messages']),1)
        approved=self.client.post(f"/api/copilot/runs/{run['id']}/decision",json={'action':'approve_plan'}).json()
        self.assertEqual(approved['status'],'queued')
        finished=self.wait_for(run['id'],{'completed'})
        self.assertEqual(finished['status'],'completed')
        self.assertIn('compare-method',self.client.get('/api/documents/adaptive-search').json()['messages'][-1]['source_ids'])

    def test_plan_can_be_cancelled_without_assistant_claim(self):
        response=self.client.post('/api/documents/adaptive-search/copilot/runs',json={
            'text':'请深度研究这个方法','node_id':'mechanism','mode':'deep'})
        run=self.wait_for(response.json()['id'],{'awaiting_user'})
        stopped=self.client.post(f"/api/copilot/runs/{run['id']}/cancel").json()
        self.assertEqual(stopped['status'],'cancelled')
        messages=self.client.get('/api/documents/adaptive-search').json()['messages']
        self.assertEqual([message['role'] for message in messages],['user'])

    def test_plan_revision_and_single_active_run(self):
        response=self.client.post('/api/documents/adaptive-search/copilot/runs',json={
            'text':'深度研究这个方法','node_id':'mechanism','mode':'deep'})
        run=self.wait_for(response.json()['id'],{'awaiting_user'})
        conflict=self.client.post('/api/documents/adaptive-search/copilot/runs',json={
            'text':'另一个问题','node_id':'mechanism','mode':'quick'})
        self.assertEqual(conflict.status_code,409)
        revised=self.client.post(f"/api/copilot/runs/{run['id']}/decision",json={
            'action':'revise_plan','comment':'只分析候选覆盖条件，不使用外部来源'})
        self.assertEqual(revised.status_code,200,revised.text)
        updated=self.wait_for(run['id'],{'awaiting_user'})
        self.assertEqual(updated['plan_revision'],2)
        self.assertIn('不使用外部来源',updated['plan']['objective'])
        self.assertFalse(updated['plan']['use_external_sources'])


if __name__=='__main__':unittest.main()
