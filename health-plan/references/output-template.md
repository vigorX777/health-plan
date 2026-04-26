# Output Template

Use these staged templates. Do not output all sections at once unless the conversation has already reached that stage.

## Stage 1: 信息收集

After receiving physiological data, acknowledge receipt and collect missing context before analysis.

Prefer Codex built-in parameter selection components. If the UI component is unavailable, use Chinese text options. Ask in small batches, normally 2-3 items per message.

Required fields:

- 训练目标：体态重组 / 减脂优先 / 增肌优先 / 力量表现 / 恢复改善 / 其他。
- 训练经验：新手 / 规律训练 3-12 个月 / 规律训练 1-3 年 / 训练 3 年以上。
- 器械条件：健身房 / 居家无器械 / 哑铃弹力带 / 混合训练 / 其他。
- 每日可用时间：20-30 分钟 / 30-45 分钟 / 45-60 分钟 / 60-75 分钟。
- 伤病史：无明显伤病 / 膝踝不适 / 腰背不适 / 肩颈不适 / 心血管或医生限制 / 其他。
- 睡眠：稳定 7 小时以上 / 6-7 小时 / 少于 6 小时 / 作息不规律。
- 饮食限制：无 / 素食 / 乳糖不耐 / 控糖或低碳 / 外食为主 / 其他。

Example wording:

```text
我已收到你的生理数据。先不直接分析，需要先补齐训练上下文，否则计划会不准确。

请先选择这 3 项：
1. 训练目标：体态重组 / 减脂优先 / 增肌优先 / 力量表现 / 恢复改善 / 其他
2. 训练经验：新手 / 规律训练 3-12 个月 / 规律训练 1-3 年 / 训练 3 年以上
3. 器械条件：健身房 / 居家无器械 / 哑铃弹力带 / 混合训练 / 其他
```

## Stage 2: 上下文确认

Only output this after all seven required fields are collected. Do not analyze yet.

Use this summary card:

```text
训练上下文摘要
- 训练目标：...
- 训练经验：...
- 器械条件：...
- 每日可用时间：...
- 伤病史/疼痛限制：...
- 睡眠状态：...
- 饮食限制：...

请确认以上信息是否准确。确认后我再开始身体状态分析；如果有任何一项需要修改，请直接指出。
```

## Stage 3: 状态分析输出

Only output this after required context is complete.

### 0. 前置说明

State:

- This is fitness/health education, not medical diagnosis.
- Which physiological data and training-context fields are available.
- Which fields remain uncertain or need retesting.

### 1. 身体状态分析报告

#### 总体结论

Give a concise classification:

- `体态重组`
- `减脂优先`
- `增肌优先`
- `恢复优先`
- `医学复核优先`

Explain the top 3 reasons from the data.

#### 体重体型

Discuss weight, height, BMI, standard/healthy range, and whether weight change should be a primary goal.

#### 脂肪状态

Discuss body-fat percentage, fat mass, visceral fat, waist-hip ratio, and whether the user should reduce fat, maintain, or focus on composition.

#### 肌肉状态

Discuss muscle mass, skeletal muscle mass, fat-free mass, FFMI if calculable, and training implications.

#### 代谢与恢复

Discuss BMR, water/protein/bone indicators if provided, confirmed sleep/recovery context, and HRV trend if available.

#### 心率与 HRV

Discuss resting heart rate, smart-scale heart rate, baseline, annual min/max if provided, and HRV. Clearly flag values that need repeat measurement.

#### 风险与不确定项

List:

- inconsistent or blurry fields.
- device-dependent fields.
- missing fields that would improve personalization.

### 2. 异常数据与调整建议

Use this table:

| 优先级 | 指标 | 当前表现 | 可能原因 | 复测/确认方式 | 调整建议 | 何时就医 |
|---|---|---|---|---|---|---|

Rules:

- Include only relevant abnormal, borderline, uncertain, or high-impact items.
- If no clear abnormal data exists, say so and list optimization opportunities instead.
- Do not diagnose.

### 3. 分析确认

End Stage 3 by asking for confirmation:

```text
请确认：以上分析是否符合你的实际情况？如果有训练经验、伤病、睡眠、饮食或身体状态需要修正，请直接指出；如果分析没问题，请回复“进入规划”，我会直接生成 7 天训练日程，不再重复确认。
```

## Stage 4: 规划询问

Use this stage only if the user's reply after Stage 3 is ambiguous. If the user says `进入规划`, `开始规划`, `继续`, `可以`, `没问题`, `确认`, or equivalent forward-intent wording, skip this stage and generate the 7-day plan directly.

```text
我理解你已确认分析。是否现在进入 7 天健身规划？如果进入，我会基于刚才确认过的身体状态和训练条件生成每天的训练日程。
```

## Stage 5: 7 天健身规划

Before the table, state the confirmed context:

- Goal.
- Training level.
- Equipment/location.
- Available time.
- Injury constraints.
- Nutrition baseline.

Use this daily format:

### Day [N]：[训练主题]

- 目标：...
- 热身：...
- 主训练：动作、组数、次数、RPE、休息时间。
- 辅助训练：动作、组数、次数、RPE、休息时间。
- 有氧：类型、时长、强度。
- 拉伸/恢复：...
- 营养重点：...
- 睡眠/恢复重点：...
- 调整规则：如果当天静息心率明显高于基线或 HRV 明显低于基线，则...

Use varied daily themes:

- Upper body push/pull.
- Lower body strength.
- Zone-2 cardio.
- Mobility/recovery.
- Full-body resistance.
- Core/posture.
- Rest or active recovery.

End Stage 5 by asking for confirmation:

```text
请确认：这份 7 天规划是否可执行？如果需要调整训练天数、器械、时间、动作难度或恢复安排，我会先修改。确认没问题后，我会生成 7 条 OpenAI gpt-image-2 兼容的每日训练示意图提示词；如果你明确要实际出图，我会优先使用 OpenAI gpt-image-2 API 并发生成，缺少 API 配置时自动降级到 Codex 内置 imagegen。
```

## Stage 6: 图片提示词与可选出图

After the user confirms the plan:

- Generate exactly one OpenAI gpt-image-2-compatible prompt per day, for seven total prompts.
- Display the prompts by default as reusable deliverables.
- If the user explicitly asks to generate images, resolve the provider first.
- Default provider: `openai_gpt_image_2`, using `POST /v1/images/generations`, model `gpt-image-2`, size `1536x1024`, and seven concurrent day jobs.
- Fallback provider: `codex_builtin_imagegen`, using the Codex built-in `imagegen` skill and `image_gen` tool when `OPENAI_API_KEY` is missing or the official API path is unavailable.
- Generate Day 1 through Day 7 as seven independent daily images if actual generation is requested.
- In the official API path, submit all seven daily jobs concurrently. In Codex built-in fallback mode, use sequential generation only if the available image tool cannot parallelize.
- Do not combine the week into one overview image unless the user explicitly requests an extra overview image.
- If a day fails during actual image generation, retry only that failed day. Do not regenerate successful days.
- If the user provides a reference image, use it as the visual layout template for all seven daily images. Match its canvas size and aspect ratio when supported by the generation backend. The current default reference style is a 1536x1024 landscape poster with a 3:2 aspect ratio.

Provider status card:

```text
图片生成通道
- 首选通道：OpenAI gpt-image-2 API
- 当前通道：OpenAI gpt-image-2 API / Codex 内置 imagegen 兜底
- 触发原因：用户确认实际出图
- 降级原因：无 / 缺少 OPENAI_API_KEY / 官方 API 不可用 / 用户指定 Codex 预览
- 并发策略：官方 API 并发 7 个任务；Codex 兜底按工具能力逐日生成
```

Use one consistent layout system for every daily image:

- Top-left: large `DAY N` and training title.
- Top summary row: `当天目标`, `核心动作`, `目标肌群`.
- Top-right or right-side info cards: `姿势要点`, `组数次数/RPE`, `安全提醒`.
- Main body: three numbered exercise panels. Use the day's three most important movements; for recovery/rest days, use three recovery actions or tracking actions.
- Muscle inset: include target-muscle diagrams or simplified highlighted muscle insets where appropriate.
- Bottom section: action cues, training tip, and estimated duration.
- Visual consistency: same typography hierarchy, navy/white color system, icon style, card borders, spacing, and panel proportions across Day 1-Day 7.

Each daily image must include:

- 当天目标.
- 核心动作.
- 目标肌群.
- 动作姿势要点.
- 组数次数/RPE.
- 安全提醒.

Parallel job status contract:

| Day | Job ID | Status | Image reference | Retry policy |
|---|---|---|---|---|
| Day 1 | `day_1` | `queued/generating/succeeded/failed/retrying` | only after success | retry only Day 1 if failed |
| Day 2 | `day_2` | `queued/generating/succeeded/failed/retrying` | only after success | retry only Day 2 if failed |
| Day 3 | `day_3` | `queued/generating/succeeded/failed/retrying` | only after success | retry only Day 3 if failed |
| Day 4 | `day_4` | `queued/generating/succeeded/failed/retrying` | only after success | retry only Day 4 if failed |
| Day 5 | `day_5` | `queued/generating/succeeded/failed/retrying` | only after success | retry only Day 5 if failed |
| Day 6 | `day_6` | `queued/generating/succeeded/failed/retrying` | only after success | retry only Day 6 if failed |
| Day 7 | `day_7` | `queued/generating/succeeded/failed/retrying` | only after success | retry only Day 7 if failed |

User-facing result format:

```text
训练示意图生成结果
- 当前通道：OpenAI gpt-image-2 API / Codex 内置 imagegen 兜底
- Day 1：成功，[图片]
- Day 2：生成中
- Day 3：失败重试中
- Day 4：成功，[图片]
- Day 5：成功，[图片]
- Day 6：成功，[图片]
- Day 7：成功，[图片]

失败项只会重试对应日期，不会重新生成已成功图片。
```

Daily prompt structure:

`生成一张 OpenAI gpt-image-2 兼容的专业健身海报，与参考训练海报同尺寸、同结构、同排版系统，默认 1536x1024 横向 3:2；[Day N 当天训练主题]；顶部左侧使用大号 DAY N 和训练标题；顶部摘要区包含 当天目标[...], 核心动作[...], 目标肌群[...]；右上信息卡包含 姿势要点[...], 组数次数/RPE[...], 安全提醒[...]；主体为三个编号动作面板，分别展示[动作1], [动作2], [动作3]，每个面板包含动作照片/示意、目标肌群小图、动作要点；底部包含训练小贴士和预计用时；统一海军蓝与白色配色、清晰中文标签、真实人体比例、居家/健身训练场景、高质感运动摄影与信息图结合；避免夸张肌肉、避免医疗诊断文字、避免危险姿势、避免前后对比承诺。`

Rules:

- Keep prompts aligned with each day's actual plan.
- Mention safety cues when the day includes loaded movements.
- Do not include medical claims.
- Do not include unrealistic instant transformation language.

## Stage 7: 追踪指标

Include a compact checklist after either the analysis or planning stage:

- 7 日平均体重.
- 腰围 or 腰臀比.
- 训练动作重量/次数.
- 静息心率.
- HRV vs baseline.
- 睡眠时长/质量.
- 主观疲劳 and soreness.
