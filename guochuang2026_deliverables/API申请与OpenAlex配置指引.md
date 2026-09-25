# API Key 申请与 OpenAlex 礼貌池配置｜解锁 A2 冲刺前置

> 目标：提升检索配额，补 2024 分片 + 中子主题，把 Recall 从 90.2% 推到 95%+。
> 全部免费。今天上午办完。

---

## 一、Semantic Scholar API Key（免费）

1. 打开 https://www.semanticscholar.org/product/api
2. 点 "API Key" → 注册/登录（用学校邮箱更易过）
3. 申请 Product API Key（免费档足够文献元数据）
4. 复制 Key，存入本地 `.env`：`S2_API_KEY=xxxx`
5. 调用时 Header 带 `x-api-key`

> 作用：补 2024 文献、中子主题检索，覆盖 golden set 缺口 #2/#9/#53/#56/#65。

---

## 二、OpenAlex 礼貌池（mailto，免费，必须配）

OpenAlex 对带 `mailto` 的请求走"礼貌池"，速率限制更宽松，且能避免 R8 那种同 IP 配额耗尽雪崩。

请求示例：
```
https://api.openalex.org/works?filter=title.search:high%20entropy%20alloy&mailto=你的邮箱@学校.edu.cn
```

Python 片段：
```python
import requests
MAILTO = "你的邮箱@学校.edu.cn"
def oa_search(q, per_page=200):
    url = "https://api.openalex.org/works"
    params = {"filter": f"title.search:{q}", "per-page": per_page, "mailto": MAILTO}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()
```

---

## 三、断点续跑骨架（防 R8 雪崩）

```python
import json, time, os

STATE = "progress_r9.json"

def load_state():
    return json.load(open(STATE)) if os.path.exists(STATE) else {"done": []}

def save_state(s):
    json.dump(s, open(STATE, "w"), ensure_ascii=False, indent=2)

def run_batch(items):
    s = load_state()
    for it in items:
        if it["id"] in s["done"]:
            continue
        try:
            res = oa_search(it["q"])
            s["done"].append(it["id"])
            save_state(s)          # 每完成一个就落盘
        except Exception as e:
            print("FAIL", it["id"], e)
            time.sleep(5)          # 失败退避，不雪崩
            # 单源失败率 >30% 自动切 Crossref 备份
    return s
```

---

## 四、多源互备（你已实测 Crossref 未被限流）

| 源 | 角色 | 备注 |
|---|---|---|
| OpenAlex（mailto） | 主 | 礼貌池提额 |
| Semantic Scholar | 补 2024/中子主题 | 需 Key |
| **Crossref** | **主力备份** | 你的实测：本次未被限流，直接当备份源 |

> 单源失败率 >30% 自动切备份源；每批落盘 + 断点续跑。

---

## 五、冲刺补捞清单（Recall 90.2%→95.5%）

| 优先级 | 补捞项 | 目标 golden 条目 |
|---|---|---|
| 1 | 2024 年份分片 | #2 Graph representation、#9 ML potential |
| 2 | 中子主题（中熵/纳米晶/增材/辐照） | #53 #56 #65 |
| 3 | 材料基因组 / 迁移学习主题词 | #25 #35 |

捞回 7 条 → 127/133 = **95.5%**。
