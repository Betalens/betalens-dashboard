# Betalens Dashboard

在线研究工作台和离线实验前端源码。两套前端共用本仓库中的展示组件；Python 后端通过显式目录加载研究脚本。

```bash
uv sync --python 3.11 --extra test
export BETALENS_FACTOR_ROOT=/absolute/path/betalens-factor
export BETALENS_RUNTIME_DIR=/absolute/path/runtime
uv run betalens-dashboard serve --port 8000
```

另开终端，在 `dashboard/frontend` 执行 `npm ci && npm run dev`，浏览器打开 `http://127.0.0.1:5173`。
前端要求 Node.js 22。Windows 使用根目录 `.venv` 及 `dashboard/run.bat`，同样先设置环境变量。
核心依赖固定到公开兼容提交；运行研究脚本需为核心准备仓库外的数据库配置。

## 构建和离线资源

两个前端各执行一次 `npm ci`；随后在 `dashboard/frontend` 执行 `npm run build`，构建在线前端和 `dist/experiment-viewer`。
普通构建不写入其他仓库。提交 UI 源码后，显式导出离线资源：

```bash
uv run python scripts/export-viewer.py --core-dir /absolute/path/betalens
```

导出生成来源提交及 SHA-256 清单；在核心单独审阅、提交后，其 wheel 继续提供安装即用的离线看板。
UI 本地源码开发可在 `experiment-dashboard` 使用 `npm run dev`，API 代理到核心离线服务的 8020 端口。

## 验证

```bash
uv run pytest -q
uv run npm --prefix experiment-dashboard run test:e2e
```

浏览器测试使用本仓库的合成归档和已构建资源。运行前安装 Playwright Chromium。
真实研究仓库的接口集成测试位于 `tests/integration`；需显式设置 `BETALENS_FACTOR_ROOT`，并在 UI 环境 editable 安装研究运行器。
核心的工作目录初始化脚本会完成该安装。常规 CI 使用合成因子，无需访问其他私有仓库。
