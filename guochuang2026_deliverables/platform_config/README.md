# 平台配置包（A-1 路径）

> 2026-09-14 ｜ 状态：**真机已跑通**
> 平台：多智能体协同高校科研助理平台
> 编排层：WorkBuddy / CodeBuddy 原生 `--agents` + `--agent orchestrator`

---

## 1. 目录结构

```
platform_config/
├── agents_official.json      # 【主力】8 角色配置，--agents 直接吃
├── agents_md/                # 【交付】文件式 8 角色，落 .codebuddy/agents/
│   ├── orchestrator.md       #   编排中枢
│   ├── literature.md         #   ① 文献调研
│   ├── data.md               #   ② 数据处理
│   ├── experiment.md         #   ③ 代码实验
│   ├── writing.md            #   ④ 论文写作
│   ├── evaluation.md         #   ⑤ 成果评估
│   ├── catfish.md            #   ⑥ 鲶鱼对抗式复核
│   └── topic_eval.md         #   ⑦ 课题选择评估器（离线）
├── run_platform.sh           # 一键启动（自动 Triage / 强制 L·M·H）
├── smoke/                    # 冒烟记录
│   ├── smoke_agents.json     #   最小冒烟（验证分派链路）
│   ├── agents_real.json      #   正式配置去注释版
│   └── H档全链路_20260914.log
└── config/                   # ⚠️ 旧草案，字段结构不符合官方规范，已作废
```

---

## 2. 三种启动方式

### 方式 A：命令行 `--agents`（最快，适合演示与录屏）

```bash
./run_platform.sh "检索高熵合金形成能预测的代表性文献"
./run_platform.sh -l "..."   # 强制 L 档
./run_platform.sh -m "..."   # 强制 M 档
./run_platform.sh -h "..."   # 强制 H 档（含鲶鱼，约 16 分钟）
./run_platform.sh --check    # 只校验配置
```

### 方式 B：文件式（推荐交付形态，随仓库提交）

```bash
cp agents_md/*.md <你的项目>/.codebuddy/agents/     # 项目级，团队共用
# 或
cp agents_md/*.md ~/.codebuddy/agents/              # 用户级，仅本机
```

优势：支持 `memory: project`（**Agent 级持久记忆**，跨会话记住科研上下文）、`displayName` 中文名、`maxTurns` 等 CLI 版没有的字段。

### 方式 C：等价裸命令（写进技术文档/论文用）

```bash
codebuddy -p \
  --agents "$(cat agents_official.json)" \
  --agent orchestrator \
  --max-turns 40 \
  "你的自然语言科研任务"
```

---

## 3. `--agents` 官方字段规范（实测校准，勿改结构）

```jsonc
{
  "<name>": {
    "description": "必填 — 编排中枢靠它判断何时分派，写太短会导致分派不准",
    "prompt":     "必填 — 角色系统提示词，防编造约束写在这里",
    "tools":           ["可选 工具白名单"],
    "disallowedTools": ["可选 工具黑名单"],
    "model":           "可选 指定模型",
    "mcpServers":      ["可选 连接器，字符串引用或 {name: config}"]
  }
}
```

| 坑 | 说明 |
|---|---|
| 顶层是**扁平 map**，不是 `{"agents":[...]}` | 写错会整体不生效 |
| 是 `description` / `prompt`，**不是** `role` / `instruction` | 字段名错了会被忽略 |
| **没有** `output_schema` / `required_fields` | 结构化输出约束只能写进 `prompt`（这反而符合 R5：不做应用层校验器） |
| `_` 开头的键会被当作 agent 解析并跳过 | `run_platform.sh` 已自动剔除 |

---

## 4. Triage 分档规则（写在 orchestrator prompt 里，非外部规则引擎）

| 档 | 触发条件 | 链路 | 参考耗时 |
|---|---|---|---|
| **L** | 事实查询 / 单一数据源 / 无统计推断 | 只调度必要 Agent，**跳过 evaluation** | ~15s–3min |
| **M** | 统计分析 / 多源数据 / 需方法学把关 | 完整链路 + evaluation | — |
| **H** | 实验设计 / 因果主张 / 需外推 | 完整链路 + evaluation + **强制鲶鱼** | ~16min |

---

## 5. 防编造字段（全部内嵌在各角色 prompt 中）

| 字段 | 作用 |
|---|---|
| `insufficient_evidence[]` | 证据不足的论述，明列不隐瞒 |
| `missing_handling` | 缺失值处理方式，**禁静默填充** |
| `not_obtained[]` | 跑不出的部分据实列，不得估算冒充实测 |
| `rewrite_tool_used` | **恒 false** — 不得用改写工具规避查重 |
| `self_reviewed_previous` | 鲶鱼必须自审上一轮，不得自我背书 |
| `metrics_verified[].{claimed, recomputed, match}` | 独立复算，不采信上游自报 |
| `queries[]` | 检索式留痕，供他人复算 |
| `citations[].doi` | 可解析 DOI，校验失败须标 `verified=false` |

---

## 6. R5 红线自检

| 项 | 状态 |
|---|---|
| 编排走平台原生 `--agents` / `--agent orchestrator` | ✅ |
| Triage 规则在 **prompt 内**由 Agent 自主判定，非外部规则引擎 | ✅ |
| 无任何自研 Agent 调度内核 / 应用层校验器 | ✅ |
| 工具调用走平台连接器（MCP/CLI） | ✅ |
| A-2 后端（若做）仅透传渲染，不自编排 | ⏸ 待 6.3/6.4 定案 |

---

## 7. 冒烟记录（2026-09-14）

| 项 | 结果 |
|---|---|
| 最小冒烟：orchestrator 分派 librarian_smoke 并回收 | ✅ 通过 |
| L 档真实链路：Triage 判 L → 只跑 ① → 5 篇文献 | ✅ 通过，3m13s |
| DOI 独立复算（Crossref，不采信 Agent 自报） | ✅ **5/5 真实** |
| 8 角色全部注册成功 | ✅ |
| H 档全链路（①→⑥ 含鲶鱼） | ⏳ 运行中 |

详见 `/workspace/平台启动实录_20260914.md`。
