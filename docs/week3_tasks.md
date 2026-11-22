# 第 3 周分工（11/16 – 11/22 23:59）

**本周唯一目标**：把 L2 从「三个抽取模型跑通」推进到「能在**完整应用**上给出可与论文对照的覆盖率」，并让报告的结论从 partially reproduced 走到能对论文下判断。

**当前状态（截至 11/21 12:30）**
- 第 2 周的活已全部并入 `main`：A 的逐格核对、C 的三个抽取模型复现器（症状 3/3、修复对照 3/3、检测器结论已记录）、B 在 CI 上实测的环境
- 报告已写入 C 的三个抽取模型结果，并明确标注它们**不能**代表论文 Table 8 的应用级覆盖率
- 距周检（周日 11/22 23:59）还有约 35 小时

---

## 一、本周最容易出错的地方：三个层次别混

| 层次 | 当前状态 | 能否与论文对照 |
|---|---|---|
| L1 表格（Table 5/6/7/9/10） | 已复现，论文模型下逐格全对 | 是 |
| L2 **抽取模型**（extracted_model） | 3 个模型跑通（grpc-793 / docker-256 / grpc-1424） | **否** |
| L2 **完整应用**（original_application） | 0 个 | 是 ← 本周目标 |
| Extension（Go 1.21 vs 1.22） | 只有协议 | 是 |

上周最有价值的一点是 C 主动标注了「抽取模型 ≠ 完整应用」。本周不要把这个边界弄丢：**任何写进报告的数字，都要标明它属于哪一层。**

---

## 二、A — 数据与统计（辛相天）

**目标**：把「逐格核对」从 Table 5 补到 Table 6/7/9/10，并把每处 ⚠️ 的原因换成可验证的说法。

当前 `tables_check.md` 只有 Table 5，且里面两句原因与我们已验证的归因不一致：

| 现在写的 | 应改成 |
|---|---|
| "Missing 2 BoltDB patches" | 这两行**在**工作簿里（blocking 行 90 / 92），只是 commit 列存的是 issue ID 而非 hash，所以无法绑定 commit |
| "Double-labeled kubernetes#11298 offset issue" | 该记录同时带 shared+message 标签与 Wait+ChanWith 两个 cause；论文只赋一个 cause，我们保留两个 —— 按论文模型这两处差异会**完全抵消** |
| "Two errors cancel each other out" | 成立，但要说清是哪两处：+1（k8s 双标签）与 −1（BoltDB issue-only 行） |

**交付**
- `tables_check.md` 补齐 Table 6/7/9/10 的逐格对照（用 `scripts/parse_dataset.py` 的输出，论文值从论文 Table 抄）
- 写明「论文模型」结论：纳入那 2 行 + k8s 单 cause ⇒ Table 5/6/7 逐格全对（我已独立复算过，可复核）
- `deviations.md`（仓库根目录）补一条：**抽取模型 ≠ 完整应用**

**提交**
```
dataset: complete the cell-by-cell check for tables 6/7/9/10 (<学号> 辛相天)
dataset: correct the deviation wording to match the verified attribution (<学号> 辛相天)
```

---

## 三、B — 环境与可复现（张歆海）

**目标**：为「完整应用复现」扫清环境障碍，并提供可复现的应用级构建路径。

当前 `b-env` 分支还停在第 1 周（6d6f855），本周第 2 周的环境工作是通过合并进 main 的。**请把自己本周的提交推回 `b-env`**，否则 B 的第 2 周提交在分支历史里看不到。

**交付**
- `b-env` 分支推上本周提交
- 为「2016–2018 的上游 revision」准备一条可复现的构建路径：这些 revision 早于 Go modules，用 Go 1.22 构建需要一层依赖固定 —— 请把这层的**版本与来源**写成脚本并纳入镜像，不要手工 patch
- 若完整应用复现需要额外镜像（例如特定 Go 版本 + 特定依赖），请给 digest

**提交**
```
env: pin the dependency-compatibility layer for pre-modules upstream revisions (<学号> 张歆海)
env: publish the week-three environment measurement (<学号> 张歆海)
```

---

## 四、C — 复现实验（谢昊桐）

**目标**：把抽取模型的成功，迁移到一个**完整应用**上；这是本周唯一能把 Claim 3 从「inconclusive」变成「可下判断」的活。

当前状态（`repro/week2-results.md`）：3 个抽取模型、症状 3/3、修复对照 3/3、检测器 1/3 报死锁；并且你自己已写明这些**不能**估计论文 Table 8 的覆盖率。

**建议顺序**
1. 挑 **1 个** 抽取模型，把它的完整上游应用构建出来（依赖固定交给 B），在同一 pinned 镜像里跑
2. 完整应用上跑：症状 3/3 + 修复对照 3/3 + 检测器结论
3. 关键对照：同一模型、**完整应用 vs 抽取模型**的检测器结论是否一致 —— 这直接回答「抽取模型能代替完整应用吗」，即使只有 1 个模型也很有价值
4. 若完整应用构建不通（依赖太老），**记录失败原因并给最小可复现的替代路径**，这本身是可发表的负结果

**交付**
- `repro/<bug-id>/` 下新增一个 `original_application` 工作负载（沿用现有 metadata/notes 契约，加 `workload_kind` 字段区分）
- `repro/week3-results.md`：应用级 vs 抽取模型并排
- `docs/claims.md` 的 Claim 3 判定更新（应用级数据到位就改成 supported / partially supported，不足就保持 inconclusive 但写清差在哪）

**提交**
```
repro: run the full application build for one blocking bug (<学号> 谢昊桐)
docs: compare application-level and extracted-model detector outcomes (<学号> 谢昊桐)
```

---

## 五、D — 报告与统筹（郭子嘉）

**目标**：让报告能顶住「你的结论有证据吗」的追问，并把四个人的工作汇成一个可提交的整体。

**本周已完成**
- 把 A 的 `a-dataset` 和 C 的 `c-repro` 合并进 `main`（两个分支基线不同、但都能干净合并，已验证无冲突）
- 把 C 的三个抽取模型结果写进 `report/main.tex`：L2 新增实测表 + 「这些测量覆盖不到什么」的边界说明；Claim 3 判定改为「论文成立、我们尚不成立」；摘要、结论、局限性同步
- 更新 `docs/discrepancy_analysis.md` 的 D4 节：给出实测表 + 为什么不能外推到 Table 8
- 统一行尾（A 的两个文件是 CRLF，已按仓库 `.gitattributes` 规范化为 LF）

**本周还要做**
- 把 `results/tables/*.csv`、`scripts/parse_dataset.py`、`tests/` 接进 `make tables` 流程（现在这些在 `c-repro` 上，合并后已在 main，需确认 `make tables` 一键可跑）
- 报告补一张「三层证据强度」表：L1 / 抽取模型 / 完整应用，让阅卷人一眼看到每个数字属于哪一层
- 每周至少一条提交（周检 23:59 硬性要求）

**提交**
```
report: fold the measured week-two reproducer results into the report (<学号> 郭子嘉)
docs: add the week-three plan and update the weekly log (<学号> 郭子嘉)
```

---

## 六、时间线与风险

| 时间 | 动作 |
|---|---|
| 今天（周六 11/21） | 各自认领上面的任务；C 先定 1 个目标 bug；B 确认依赖固定方案 |
| 周日 11/22 12:00 | 全部 push（先 `git pull --rebase`）；`main` 上能看到四个人的提交 |
| 周日 11/22 21:30 | 开 PR / 合并；D 出报告定稿 |
| 周日 11/22 23:59 | 助教检查 |

**风险与预案**
1. **完整应用构建不通**（最可能）—— 预案：记录失败原因 + 最小替代路径，这仍是有效负结果；Claim 3 保持 inconclusive 但把「差在哪一步」写具体
2. **四人提交撞车** —— 分支已按角色分开（`a-dataset`/`b-env`/`c-repro`/`d-report`），各自只在自己的分支提交，D 只做合并
3. **周检只有一次机会** —— 漏周不可补，宁可早交；每晚 22:00 群里同步一次进度
4. **数字被误读** —— 报告里任何 L2 数字必须带「抽取模型 / 完整应用」标注，claims.md 与 main.tex 保持同一口径

---

## 七、本周的判定标准（写完就能自检）

- [ ] `main` 上能看到 A/B/C/D 四个人的提交，且都带学号与姓名
- [ ] 报告里每个 L2 数字都标了它属于抽取模型还是完整应用
- [ ] Claim 3 的判定与证据一致：有应用级数据就下判断，没有就写清差在哪一步
- [ ] `make tables` 一键跑通并重新生成五张表
- [ ] `docs/weekly-log.md` 与 `git log` 逐条对得上
