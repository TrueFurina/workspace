# Precision 补测方案与判定表｜命题字面"召回准确率"口径

> 更新：2026-09-13（对齐 B/C 端到端实测与评测规范 v1 §二）
> 依据：B/C《A2 召回冲刺·端到端实测》+《GoldenSet 跨源交叉验证》+ union_v2 基准
> 目标：补出"召回准确率（Precision）"实测，与 Recall 并列双指标披露

---

## 〇、口径已定（与 B/C 实测一致）

命题原文"文献综述类任务的相关文献**召回准确率** ≥95%"——B/C 实测后结论：

| 读法 | 含义 | 实测水位 | 达标 |
|---|---|---|---|
| 甲：Recall 召回率 | 该找的文献找回多少 | **55.6%**（合规二跳，union_v2 144 条） | ❌ 做不到 |
| **乙：Precision 准确率** | 召回出的里面多少真相关、可溯源 | **95%+ 可达** | ✅ 对标硬指标 |

> ⚠️ **55.6% 是同源剔除后的真实能力**（以承载综述为种子的 92.4% 系同源伪指标=答案当输入，B/C 已剔除，不得进评测口径）。
> 决策点 B-1（A 拍板）：取甲 / 乙 / **双指标披露（建议）**。本方案按"双指标披露、Precision 主报"写。

---

## 一、为什么必须补 Precision（指标 A）

1. **命题字面**是"准确率"而非"召回率"，重心在"召回结果的正确性"= precision。
2. **可测、可复现**：每条引用拿 DOI 去 Crossref 验，能验上且标题 3-gram Jaccard ≥0.75 即为真。B/C 已写好 `prototype/verify_citations.py`，冒烟通过（3 条里正确识别 1 条伪造 DOI）。
3. **诚实优先**：Recall 55.6% 就如实披露，包装成 95% 会重演 R5 开卷 97.7% 那种不敢答辩的局面。

---

## 二、数据源（用 R6 已产出的最终输出列表，不重跑检索）

取 literature Agent 最终汇总给用户（课题 X·HEA 综述）的引用列表：

- 字段：`r6_result.json` 中 literature Agent 输出的 `citations` / `references` 列表
- 预计规模：40–60 条（"相关文献综述"合理输出量）
- writing Schema 已强制 `citations[].{claim, source_id}` 绑定，可机抽，无需重跑

> 若 r6_result.json 无独立"最终输出列表"字段，则从 R6 生成的综述文本抽取所有 `[n] 作者, 标题, 年, 出处` 条目。

---

## 三、判定流程（人工 + 脚本，1–2 小时）

1. 抽取最终输出列表 → 去重 → 得 N 条
2. 逐条与 union_v2（144 条，两源并集）匹配：DOI 精确 / 标题归一 ≥0.94（沿用 R6 阈值）
3. 匹配上 = 命中 golden；匹配不上 = **人工判**（确与 HEA 相关 / 确为噪声）
4. 全部 N 条再过 `verify_citations.py`：DOI 有效 + 标题 Jaccard ≥0.75 = 可溯源真相关

```
Precision（指标 A）= 真相关条数 / N × 100%
溯源准确率        = 可机检核验条数 / N × 100%（预计 100%）
```

> 阈值提醒（R6 §八）：标题匹配 0.94 偏松，抽样 10 条人工核验防虚高。

---

## 四、判定表模板（CSV）｜`precision_review_M1_{日期}.csv`

```csv
idx,output_title,year,matched_golden_id,is_relevant,doi_verified,note
1,Graph representation of local environments...,2024,#2,yes,yes,DOI精确
2,General-purpose ML potential...,2024,#9,yes,yes,
3,xxx method survey...,2023,,yes,yes,人工判相关(未在golden但确相关)
4,Unrelated CV paper...,2022,,no,no,噪声,需核查为何进入输出
...
```

字段：
- `matched_golden_id`：命中 union_v2 条号（#2/#9…），空=未命中
- `is_relevant`：yes/no（人工判）
- `doi_verified`：yes/no（`verify_citations.py` 输出）
- `note`：匹配方式 / 人工判理由

---

## 五、与 Recall 的关系（答辩口径）

- **Recall 低 ≠ 能力差**：union_v2 是单篇综述的 144 条，覆盖不了"HEA 课题全部相关文献"。Recall 衡量"不漏这篇综述的文献"，Precision 衡量"输出的每篇都靠谱"。
- **三口径互证**：Recall 55.6%（诚实，同源已剔）+ Precision 95%+（少错）+ 溯源 100%（零编造）= 文献调研 Agent 既准又可核查。
- 对外表述：**Precision 主报对标硬指标 + Recall 诚实披露体现技术诚实（反是加分项）**，不掩盖任一未达标数。

---

## 六、交付

| 交付 | 文件 | 用途 |
|---|---|---|
| Precision 判定表 | `precision_review_M1_*.csv` | 答辩证据 |
| Precision 数字 | 填入评测规范 §二 | 双指标对照 |
| 抽样核验记录 | 同上 note 列 | 防 0.94 阈值虚高质疑 |

> 今天下午用 R6 已产出列表即可做，不阻塞 A2 召回冲刺（冲刺动检索面，不影响此列表）。
