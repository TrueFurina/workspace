# 国创赛2026 · 多智能体协同高校科研助理平台 · 交付物归档包

> 命题：腾讯科技《基于 WorkBuddy / LearnBuddy 的多智能体协同高校科研助理平台》（产业命题赛道·新工科）
> 归档日期：2026-09-25
> 打包人：A（技术总负责）／WorkBuddy 沙箱整理

## ⚠️ 本包用途与来源说明

本包由 **WorkBuddy 沙箱**整理生成。沙箱环境**无法直连 GitHub 公网**（已实测：`github.com` 被 DNS 黑洞到 `198.18.0.14`，全端口不可达；代理超时；GitHub MCP 未激活），因此**无法在沙箱内直接 push**。

本包采用「**沙箱整理 + 你本机一键收尾**」方案：文件已按项目结构备齐，配套 `push_to_github.sh`，你在本机解压后运行脚本即可推送到 `TrueFurina/workspace`。

## 📁 目录结构

```
交付物归档_20260925/
├── README.md                        本说明
├── push_to_github.sh                本机一键推送脚本（你运行它）
├── platform_config/                 8 Agent 专家团配置 + 一键启动脚本（核心代码）
│   ├── agents_official.json         8 角色：orchestrator + literature/data/experiment/writing/evaluation/catfish/topic_eval
│   ├── run_platform.sh              一键启动（--agents / --agent / --check）
│   ├── agents_md/                   各角色详细 prompt
│   ├── config/                      角色 schema
│   ├── portal/                      展示页 index.html
│   └── smoke/                       冒烟测试日志
├── 实测产出_H档全链路_20260914/      H 档 10 任务全链路产物（含鲶鱼复核 7.5→4.5）
├── 实测产出_真数据实验_20260916/     JARVIS-DFT 真数据实验（RF R²=0.9158、成分熵 r=+0.3394、ablation）
├── HEA_data_clean.csv               清洗后数据集（15,783 行 × 11 列）
├── 成分熵vs形成能_20260919.png      成分熵 vs 形成能散点图
├── 成分熵vs形成能_metrics.json      相关指标（Pearson r / R² / n）
└── *.md                             方案书 / 指标证据 / 红线清单 / 盲测 SOP / 可行性评估 / 全记录（真实版）等
```

> 完整 file_id 索引见 `资产盘归档主索引_20260921.md`（含 netdrive 资产盘已归档的 19 份权威 file_id）。

## 🔴 红线口径（评审一票否决项，务必守住）

| 类别 | 数字 / 表述 | 处置 |
|---|---|---|
| 禁用 | `R²=0.947`（无真 CSV 的 demo 值） | 任何交付物不得出现 |
| 禁用 | "硬度预测"（旧题面） | 一律改为"形成能预测" |
| 限用 | XGBoost `R²=0.9260` | 不可称"高熵合金"，须带数据子集限定 |
| 限用 | 评估分 `7.5→4.5` | 须引全过程，不得只引 4.5 |
| 引用边界 | 公开数据集描述 | 不可称"高熵合金"整体，须限定 JARVIS-DFT 子集 |

所有数字均来自本会话真实测试，无一条编造。详见 `禁用数字与证据红线清单_20260915.md`。

## 🚀 本机推送步骤（3 步）

```bash
# 1. 解压本包
unzip 交付物归档_20260925.zip
cd 交付物归档_20260925

# 2. 鉴权（二选一）
#    方式A：用 PAT（无需本机登录，推荐）——把下面的 ghp_xxx 换成你的 Token
export GITHUB_TOKEN=ghp_你的PAT
#    方式B：或本机已登录 GitHub
#    gh auth status          # 或 git credential / ssh 已配置

# 3. 运行一键推送（默认推到 TrueFurina/workspace 的默认分支）
bash push_to_github.sh
```

> ⚠️ 安全提醒：本次用于推送的 PAT 已出现在对话上下文中，推送完成后请到
> GitHub → Settings → Developer settings → Personal access tokens 将其**撤销/重建**，
> 避免凭据泄露。

脚本会把本包内容推送到 `TrueFurina/workspace` 仓库下的 `国创赛2026交付物/` 子目录（**不覆盖你仓库根目录已有文件**）。如需改目标仓库 / 分支，编辑脚本顶部变量即可。

## 📌 三大约束回顾

1. 文献综述召回准确率 ≥95%（方法学达标：Precision 34/34=100%，Recall 89/133=66.9% 诚实披露）
2. 多 Agent 协同自动完成率 ≥80%（代码就绪，待真机 8 Agent 部署 + 舍友盲测录屏实测）
3. ≥4 类科研 Agent（实际 8 类，原生 WorkBuddy 编排，不自研 Agent OS）

> 指标②正式证据需在你真机部署 8 Agent 后重跑（见 `真机加载与盲测SOP_指标②_20260921.md`）；当前 `#1–#6` 舍友盲测产物为**能力演示素材**，不作实测完成率。
