# 阿里云 ECS 部署

2026-10-26 部署。入口：https://papermind.47.237.109.221.sslip.io/ ，无需账号密码。该域名由 sslip.io 将服务器 IP 映射成可签发证书的主机名；将来有自有域名时可替换。

服务器应用在 `/opt/papermind`，数据在 `/opt/papermind/data`，运行密钥在 `/opt/papermind/.env.production`。现有 1Panel OpenResty 接收 80/443 请求，并以主机名转发至仅绑定 `127.0.0.1:18001` 的容器。代理配置在 `/opt/1panel/apps/openresty/openresty/conf/conf.d/papermind.conf`。该应用目前没有内建账户或多人隔离，公开入口让所有访问者使用同一份数据；个人文档、阅读记录与概念库也会对访问者开放。

最初从本机复制 13 篇文档、已发布的阅读版本、PDF、阅读记录和概念库；随后按要求删除 CNNIC 文档，目前保留 12 篇。迁移时使用 SQLite 在线备份获得一致的数据库快照，再将数据库内的 Windows 数据路径转换为容器路径。两端从此独立写入，不会自动同步。原始迁移包在 `/opt/papermind/backups/data-windows-original-20261026.tar.gz`；恢复前需要重新运行 `deploy/migrate_windows_data.py`。正式备份应另存到其他机器或存储服务。

服务器只有 896 MB 内存。部署前已出现 MySQL 因内存不足被系统终止；增加了 2 GB 交换空间（`/swapfile-papermind`），并将本应用限制为 512 MB 内存、1 GB 额外交换空间及单路模型并发。长篇 PDF 的解析或页面生成仍可能达到资源上限，此时需要扩容内存。

HTTPS 证书由 Let's Encrypt 签发，存放于 1Panel OpenResty 的挂载配置目录。`papermind-cert-renew.timer` 每天尝试续期并在成功后重载 OpenResty。

## 状态与日志

在服务器运行：

```sh
cd /opt/papermind
docker compose -p papermind -f deploy/compose.aliyun.yaml ps
docker compose -p papermind -f deploy/compose.aliyun.yaml logs --tail 100
curl -fsS http://127.0.0.1:18001/api/health
systemctl status papermind-cert-renew.timer
```

## 更新

构建上下文只包含后端、已构建的前端、KaTeX 数学排版脚本与任务规范。镜像不包含数据库、PDF 或密钥。更新前备份数据；保留 `.env.production` 和 `data/`。已有镜像保存在 `papermind:20261026-3`。

```sh
cd /opt/papermind
docker tag papermind:latest papermind:previous
docker compose -p papermind -f deploy/compose.aliyun.yaml build
docker compose -p papermind -f deploy/compose.aliyun.yaml up -d --wait --wait-timeout 90
```

## 备份

停写后一起备份数据库、上传 PDF 和生成产物：

```sh
cd /opt/papermind
umask 077
docker compose -p papermind -f deploy/compose.aliyun.yaml stop
trap 'docker compose -p papermind -f deploy/compose.aliyun.yaml start' EXIT
tar -czf "backups/data-$(date +%Y%m%d-%H%M%S).tar.gz" -C data .
docker compose -p papermind -f deploy/compose.aliyun.yaml start
trap - EXIT
```

发布检查包括：前端类型检查与构建、47 项后端测试、匿名访问成功、12 篇文档和两条概念库记录、原 PDF 下载、默认交互阅读页及公式渲染、容器内百炼请求、证书验证和重建后数据保留。完整的新文档生成仍取决于模型权限、PDF 内容、外部服务及服务器内存。
