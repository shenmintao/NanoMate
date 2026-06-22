# NanoMate Life Assistant Docker

这个 compose 文件面向 `life-assistant` 分支：默认启动 gateway/WebUI，启用生活数据、审批、skill 管理、skill curator 和中国生活服务查询工具。

## 启动

```bash
cp .env.life-assistant.example .env.life-assistant
# 编辑 .env.life-assistant，至少填一个 LLM API key，例如 DEEPSEEK_API_KEY
docker compose --env-file .env.life-assistant -f docker-compose.life-assistant.yml up -d
```

访问：

- WebUI/gateway: `http://127.0.0.1:18790`
- OpenAI-compatible API profile: `http://127.0.0.1:8900/v1/chat/completions`

默认镜像来自 GitHub Container Registry：

```text
ghcr.io/shenmintao/nanomate-life-assistant:life-assistant
```

如果 GitHub Packages 里还没有这个镜像，先在 GitHub Actions 手动运行 `Build and Push Life Assistant Docker Image`，或者推送 `life-assistant` 分支触发自动构建。首次发布后如果需要公开拉取，需要在 GitHub Packages 页面把 package visibility 改成 public。

本地构建镜像时加上 override 文件：

```bash
docker compose --env-file .env.life-assistant -f docker-compose.life-assistant.yml -f docker-compose.life-assistant.build.yml up -d --build
```

启动 API profile：

```bash
docker compose --env-file .env.life-assistant -f docker-compose.life-assistant.yml --profile api up -d
```

启动 WhatsApp bridge profile：

```bash
docker compose --env-file .env.life-assistant -f docker-compose.life-assistant.yml --profile whatsapp up -d
```

## 数据位置

默认使用 Docker named volume `nanomate-life-data`，避免 Linux/NAS 上 bind mount 权限问题。里面包含：

- `config.json`
- `workspace/`
- `workspace/life/`
- `workspace/skills/`
- `approvals/`

如果你想把数据放到仓库旁边的 `./data/life-assistant`，把 compose 里的 volume 改成：

```yaml
volumes:
  - ./data/life-assistant:/home/nanobot/.nanobot
```

Linux/NAS 上如果目录不可写，执行：

```bash
sudo chown -R 1000:1000 ./data/life-assistant
```

## 配置 key

推荐先通过 `.env.life-assistant` 提供一个 LLM key，让 NanoMate 能启动。启动后，其他 key 可以通过对话审批配置，例如：

```text
把高德地图 key 配成 xxxxx
批准
```

容器启动时会自动启用这些生活助手相关工具：

- `life_data`
- `life_action`
- `config_manage`
- `skill_manage`
- `skill_curator`
- `china_life`
- `web`

高风险动作仍然只会进入审批，不会在没有确认的情况下订票、付款、发消息或改第三方账号。
