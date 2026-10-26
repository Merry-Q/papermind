# data 目录清理说明

2026-10-26，基于当前数据库引用核对。两个预置教学文档和下列旧测试数据均已从项目移除。

## 已清理的旧测试/图解数据

| 路径 | 大小 MiB | 用途 |
|---|---:|---|
| data/benchmark-live | 0.77 | 旧跨领域测试结果 |
| data/benchmark-after-fixes | 0.12 | 旧复测结果 |
| data/presentation-benchmarks | 0.65 | 旧节点图解测试报告 |
| data/presentation-runs | 33.89 | 已移除的节点图解链路产物，当前后端不再读取 |
| data/test-corpus | 15.07 | 11 份下载测试 PDF，均有 SHA256 一致的 uploads 副本 |
| data/live-probe.json | 0.00 | 一次性接入探测记录 |

合计 50.51 MiB。旧测试报告链接、复测输入路径已失效；产品现有 PDF 和交互阅读不受影响。再次运行语料测试需先重新准备语料。

## 必须保留或按引用清理

| 路径 | 当前大小 MiB | 说明 |
|---|---:|---|
| data/uploads | 17.73 | 必须保留：13 份实际文档的原 PDF，全部被 documents.file_path 引用。 |
| data/papermind.db | 6.68 | 必须保留：文档、对话、个人概念库、页面补充与默认页面指针。 |
| data/reading-v2 | 58.74 | 不要整目录删除：包含 12 个默认整篇页面、事实数据和中间生成文件。 |
| data/runs | 7.65 | 不要整目录删除：13 份文档的 document-ir.json 正在被引用。 |
| data/parsed | 5.12 | 可重建缓存，但再次生成/OCR可能增加耗时和模型费用。 |
| data/papermind.db-wal | 0.00 | 数据库运行期间不要手动删除；关闭服务并由 SQLite 正常 checkpoint。 |
| data/papermind.db-shm | 0.03 | 数据库运行期间不要手动删除。 |

## 可进一步整理的历史生成目录

runs 中有 7 个目录未被当前文档 IR 或活动任务引用，合计 1.90 MiB。可按下面清单单独清理，不能整目录删除。

- `data/runs/3ba7ac8d-26b2-4e2c-b57b-4d1f6023640b/`（0.25 MiB）
- `data/runs/73d852ff-4a35-41af-9a67-818881a87398/`（0.13 MiB）
- `data/runs/a2c8a579-b81e-4507-bd98-c7bfad5b1907/`（0.27 MiB）
- `data/runs/c74b987f-c691-4643-84e7-f5e410699c71/`（0.12 MiB）
- `data/runs/c83b8d3d-4c6d-4bb4-bf52-0b7445c1e750/`（0.85 MiB）
- `data/runs/ce388335-f12c-45d3-8ec0-073b157cdf1f/`（0.24 MiB）
- `data/runs/cf125175-7cbc-4ebb-a5b6-67ee86d02213/`（0.03 MiB）

reading-v2 中有 16 个非默认、非活动版本目录，合计 29.76 MiB。删除会失去旧版本、定向修订和续跑缓存；如决定清理，建议同时维护对应 reading_editions 记录，避免历史版本链接指向缺失文件。

- `data/reading-v2/00f64620-2440-4231-a559-459d6a9f2382/`（completed，2.51 MiB）
- `data/reading-v2/1835a7ff-9894-4cc5-b4bd-058dd5df005c/`（failed，0.57 MiB）
- `data/reading-v2/1ca47681-7aa7-4b81-917b-7442ee2f155c/`（completed，1.06 MiB）
- `data/reading-v2/1e811d20-657e-4bc5-a6d1-6f835ac675bc/`（failed，1.23 MiB）
- `data/reading-v2/278f8557-f0da-4d9a-a83c-2abaf814a67d/`（failed，1.51 MiB）
- `data/reading-v2/284336eb-c194-44fe-a682-3cc691048b9d/`（failed，4.01 MiB）
- `data/reading-v2/3ea2996d-d812-488e-ae72-6f73eb7a6e61/`（failed，0.12 MiB）
- `data/reading-v2/5f0ec9e7-5228-4faa-89c1-9149cf37a2e3/`（completed，5.17 MiB）
- `data/reading-v2/5f13bf8d-0478-401c-a32a-236136c8485f/`（failed，0.44 MiB）
- `data/reading-v2/84e43ad0-3286-4487-b87d-edb348858dd3/`（failed，4.05 MiB）
- `data/reading-v2/92c47ac1-5693-439a-9140-944c5c0b2ce0/`（completed，1.53 MiB）
- `data/reading-v2/9732739c-3568-4c59-8701-d03e133a2c80/`（failed，0.17 MiB）
- `data/reading-v2/a4c1ebd3-7957-446b-99cc-200182278139/`（failed，1.40 MiB）
- `data/reading-v2/ae090d55-b8ff-4fa4-bcb4-d450f89db345/`（failed，1.98 MiB）
- `data/reading-v2/f409fae8-7e5c-403d-8ca7-5eeacb9fa007/`（draft，1.50 MiB）
- `data/reading-v2/ff61987b-4552-40e5-ab3d-2015e77d6774/`（completed，2.51 MiB）

## 当前默认页面：这些版本不能删

- `pdf-473e344b1814e453` → `data/reading-v2/b243eb08-a78f-4fda-bd23-01090970a1c9/`
- `pdf-bdfaa68d8984f0dc` → `data/reading-v2/079275a4-bac5-4953-b1ff-e449a44ef573/`
- `pdf-23e3249e9a1e7541` → `data/reading-v2/011ba157-97bb-47c1-91e2-2d4a759e49ca/`
- `pdf-b4deafe808239771` → `data/reading-v2/5b4b2f49-c50c-40e0-9d93-833782eb4350/`
- `pdf-be823e12764a35cd` → `data/reading-v2/fbc90b04-29cf-482a-9ec4-0dbcf25b9f5e/`
- `pdf-b0183405d850db11` → `data/reading-v2/dbbf5b7d-dbc8-4903-aac0-6960596fcc64/`
- `pdf-6e4e3411984f3edf` → `data/reading-v2/65692414-669d-4c7d-a1f8-45902c79136d/`
- `pdf-59c4f6158add045b` → `data/reading-v2/a9958210-2077-4f59-b9e3-28e28dcbe47c/`
- `pdf-66fe209b72eb93c6` → `data/reading-v2/68d7a680-5a5c-42ce-b5fc-3b34cea683c5/`
- `pdf-1a02a680ff1cd6e0` → `data/reading-v2/5df55aad-2051-4bb2-87f5-ae0d98db8ca6/`
- `pdf-ac0a4e183aa6f936` → `data/reading-v2/917662fc-a4e6-4bcb-ac7f-f9cbe992a034/`
- `pdf-fe9119a9c453151a` → `data/reading-v2/c67cefb0-eec6-4cb5-a977-c4cdf634405e/`
