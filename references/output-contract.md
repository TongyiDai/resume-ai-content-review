# 机器可读输出协议

需要批处理、审计记录或交给下游 Agent 时输出 JSON；普通对话默认使用 `SKILL.md` 的 Markdown 模板。

## 顶层字段

```json
{
  "schema_version": "1.0",
  "subject": {},
  "conclusion": {},
  "signals": [],
  "counter_evidence": [],
  "verification_plan": [],
  "fairness_checks": {},
  "hiring_action": {}
}
```

### `subject`

- `anonymous_id`: 不含姓名、邮箱、电话的本地匿名标识；
- `sections_reviewed`: 实际审阅的章节列表；
- `job_context_provided`: 是否提供岗位描述；
- `text_limitations`: OCR、长度、缺页、翻译等限制。

### `conclusion`

- `ai_attribution`: `insufficient_evidence`、`assistance_compatible_signals` 或 `provenance_confirmed`；
- `verification_need`: `normal`、`targeted`、`enhanced` 或 `insufficient_information`；
- `summary`: 一句话说明已知、未知和决策边界，不得出现 AI 百分比或概率。

### `signals[]`

每项包含：

- `id`: 如 `S1`；
- `evidence_level`: `E1`、`E2` 或 `E3`；
- `excerpt`: 去除个人信息后的短引；
- `observation`: 可观察事实；
- `why_relevant`: 为什么值得关注；
- `alternative_explanations`: 至少一项；
- `implication`: `style_only`、`verify_claim` 或 `provenance`；
- `provenance_basis`: 仅 E3 必填，值为 `explicit_disclosure`、`documented_edit_history` 或 `verifiable_watermark_or_metadata`。

### `counter_evidence[]`

每项包含 `excerpt`、`observation` 和 `why_it_matters`。允许为空，但分析时必须主动搜索。

### `verification_plan[]`

每项包含：

- `target_signal_ids`: 对应信号；
- `primary_question`: 中性主问题；
- `follow_up`: 深挖问题；
- `good_evidence`: 什么回答或材料能澄清。

每个 E2 信号必须至少被一个问题覆盖。

### `fairness_checks`

以下字段都必须为 `true`：

- `no_automatic_rejection`
- `no_candidate_ranking`
- `no_protected_attribute_inference`
- `language_background_considered`
- `template_and_editor_alternatives_considered`
- `pii_minimized`

### `hiring_action`

- `next_step`: `standard_process`、`structured_verification` 或 `manual_review_due_to_insufficient_text`；
- `prohibited_use_acknowledged`: 必须为 `true`；
- `note`: 说明最终决定由人类招聘决策者作出。

## 校验

```bash
python3 scripts/validate_review.py path/to/report.json
```

退出码 `0` 表示结构和关键护栏通过；退出码 `1` 表示存在阻断错误。校验器不会判断分析质量，仍需人工确认原文证据、替代解释与问题是否合理。
