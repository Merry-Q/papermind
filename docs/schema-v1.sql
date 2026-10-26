-- Proposed normalized local-production schema, NOT used by the current JSON demo store.
-- Migration requires an explicit converter for data/papermind.db; do not execute over it.
PRAGMA foreign_keys = ON;

CREATE TABLE documents (
  id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE document_versions (
  id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id),
  file_hash TEXT NOT NULL, file_path TEXT NOT NULL, page_count INTEGER NOT NULL CHECK(page_count>0),
  parser_version TEXT NOT NULL, ir_path TEXT,
  status TEXT NOT NULL CHECK(status IN ('uploaded','parsing','parsed','incomplete','failed')),
  UNIQUE(document_id,file_hash,parser_version)
);
CREATE TABLE source_anchors (
  id TEXT PRIMARY KEY, document_version_id TEXT REFERENCES document_versions(id),
  kind TEXT NOT NULL CHECK(kind IN ('paper','external','teaching')),
  physical_page INTEGER CHECK(physical_page>=1), printed_page TEXT, block_id TEXT,
  bbox_json TEXT CHECK(bbox_json IS NULL OR json_valid(bbox_json)), rotation INTEGER NOT NULL DEFAULT 0,
  quote TEXT NOT NULL, quote_hash TEXT NOT NULL, url TEXT, retrieved_at TEXT,
  locator_status TEXT NOT NULL CHECK(locator_status IN ('located','unresolved','not_applicable'))
);
CREATE TABLE claims (
  id TEXT PRIMARY KEY, document_version_id TEXT NOT NULL REFERENCES document_versions(id),
  statement TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('paper','external','teaching')),
  critical INTEGER NOT NULL CHECK(critical IN (0,1)), conditions_json TEXT NOT NULL CHECK(json_valid(conditions_json)),
  verification TEXT NOT NULL CHECK(verification IN ('pending','supported','contradicted','insufficient'))
);
CREATE TABLE claim_evidence (
  claim_id TEXT NOT NULL REFERENCES claims(id), source_id TEXT NOT NULL REFERENCES source_anchors(id),
  relation TEXT NOT NULL CHECK(relation IN ('supports','contradicts','context')),
  PRIMARY KEY(claim_id,source_id)
);
CREATE TABLE lessons (
  id TEXT PRIMARY KEY, document_version_id TEXT NOT NULL REFERENCES document_versions(id),
  revision INTEGER NOT NULL DEFAULT 1 CHECK(revision>=1), coverage_plan_json TEXT NOT NULL CHECK(json_valid(coverage_plan_json)),
  status TEXT NOT NULL CHECK(status IN ('draft','incomplete','ready'))
);
CREATE TABLE lesson_nodes (
  id TEXT PRIMARY KEY, lesson_id TEXT NOT NULL REFERENCES lessons(id), sort_order INTEGER NOT NULL,
  title TEXT NOT NULL, required INTEGER NOT NULL CHECK(required IN (0,1)), revision INTEGER NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('planned','draft','verifying','readable','blocked')),
  blocks_json TEXT NOT NULL CHECK(json_valid(blocks_json)), UNIQUE(lesson_id,sort_order)
);
CREATE TABLE node_claims (
  node_id TEXT NOT NULL REFERENCES lesson_nodes(id), claim_id TEXT NOT NULL REFERENCES claims(id),
  PRIMARY KEY(node_id,claim_id)
);
CREATE TABLE concept_explanations (
  id TEXT PRIMARY KEY, canonical_key TEXT NOT NULL, domain TEXT NOT NULL,
  definition_version TEXT NOT NULL, layer TEXT NOT NULL, conditions_json TEXT NOT NULL CHECK(json_valid(conditions_json)),
  body_json TEXT NOT NULL CHECK(json_valid(body_json)), sources_json TEXT NOT NULL CHECK(json_valid(sources_json)),
  UNIQUE(canonical_key,domain,definition_version,layer)
);
CREATE TABLE conversations (
  id TEXT PRIMARY KEY, document_id TEXT NOT NULL UNIQUE REFERENCES documents(id)
);
CREATE TABLE messages (
  id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES conversations(id),
  document_version_id TEXT NOT NULL REFERENCES document_versions(id), node_id TEXT REFERENCES lesson_nodes(id),
  role TEXT NOT NULL CHECK(role IN ('user','assistant','tool')), body_json TEXT NOT NULL CHECK(json_valid(body_json)),
  selection_json TEXT CHECK(selection_json IS NULL OR json_valid(selection_json)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE attachments (
  conversation_id TEXT NOT NULL REFERENCES conversations(id), document_version_id TEXT NOT NULL REFERENCES document_versions(id),
  attached_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, detached_at TEXT,
  PRIMARY KEY(conversation_id,document_version_id)
);
CREATE TABLE page_patches (
  id TEXT PRIMARY KEY, lesson_id TEXT NOT NULL REFERENCES lessons(id), message_id TEXT NOT NULL REFERENCES messages(id),
  base_revision INTEGER NOT NULL, applied_revision INTEGER, reverted_revision INTEGER,
  operations_json TEXT NOT NULL CHECK(json_valid(operations_json)), source_ids_json TEXT NOT NULL CHECK(json_valid(source_ids_json)),
  status TEXT NOT NULL CHECK(status IN ('preview','applied','undone','conflicted'))
);
CREATE TABLE concept_library (
  id TEXT PRIMARY KEY, explanation_id TEXT NOT NULL UNIQUE REFERENCES concept_explanations(id),
  source_document_version_id TEXT NOT NULL REFERENCES document_versions(id),
  declaration TEXT NOT NULL DEFAULT 'self_reported' CHECK(declaration='self_reported'),
  saved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE preference_memories (
  id TEXT PRIMARY KEY, stable_key TEXT NOT NULL UNIQUE, body TEXT NOT NULL,
  source_message_id TEXT NOT NULL REFERENCES messages(id), created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT, deleted_at TEXT
);
CREATE TABLE jobs (
  id TEXT PRIMARY KEY, document_version_id TEXT NOT NULL REFERENCES document_versions(id),
  status TEXT NOT NULL, stage TEXT NOT NULL, lease_owner TEXT, lease_until TEXT,
  checkpoint_json TEXT NOT NULL CHECK(json_valid(checkpoint_json)), config_hash TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0, cancelled_at TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE job_events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL REFERENCES jobs(id),
  event_type TEXT NOT NULL, payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE stage_results (
  idempotency_key TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(id),
  node_id TEXT, stage TEXT NOT NULL, skill_version TEXT NOT NULL, model_config_hash TEXT NOT NULL,
  output_path TEXT NOT NULL, usage_json TEXT NOT NULL CHECK(json_valid(usage_json))
);
CREATE TABLE verification_runs (
  id TEXT PRIMARY KEY, lesson_id TEXT NOT NULL REFERENCES lessons(id), lesson_revision INTEGER NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN ('fact','structure','browser')),
  status TEXT NOT NULL CHECK(status IN ('pending','pass','fail','not_run')),
  report_path TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_message_conversation ON messages(conversation_id,created_at);
CREATE INDEX idx_source_document_page ON source_anchors(document_version_id,physical_page);
CREATE INDEX idx_job_status_lease ON jobs(status,lease_until);
CREATE INDEX idx_event_job ON job_events(job_id,event_id);

-- Additional service invariants (cross-table, not guaranteed by this draft DDL):
-- 1. A message node and its document_version must belong to the same document.
-- 2. A ready lesson must have all required nodes readable and no unresolved core claims.
-- 3. Patch apply atomically compares lessons.revision, writes overlay, and increments revision.
-- 4. Sources on an answer must belong to its authorized document/attachment scope.
-- 5. Components, URLs, bbox coordinates and JSON block shapes use application validators.
