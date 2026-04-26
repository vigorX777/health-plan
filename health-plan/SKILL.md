---
name: health-plan
description: Guide a staged health and fitness planning flow from user-provided physiological, body-composition, wearable, or smart-scale data. Use when the user asks to analyze body status, identify abnormal health/fitness indicators, collect training context, create a 7-day fitness plan, generate OpenAI gpt-image-2-compatible training guidance prompts, or create daily training guidance images via the official gpt-image-2 API with Codex imagegen fallback. Outputs Chinese by default, uses non-diagnostic health language, asks for context confirmation before analysis, asks for confirmation before planning, and only triggers actual image generation when the user explicitly confirms image creation.
---

# Health Plan

Use this skill to run a staged health-planning conversation from user-provided physiological data to analysis, optional 7-day training planning, OpenAI gpt-image-2-compatible image prompts, and optional daily image generation through the official gpt-image-2 API or the Codex built-in imagegen fallback.

This is a pure prompt-template skill. Do not run deterministic calculation scripts unless the user explicitly asks. Perform simple calculations and consistency checks directly in reasoning.

## Required References

Read these files when using this skill:

- `references/evidence.md` for stable reference ranges and training/nutrition anchors.
- `references/safety.md` for red flags, medical boundaries, and intensity downgrade rules.
- `references/output-template.md` for the required output structure.

If the user asks about latest medical guidelines, controversial claims, high-risk symptoms, drugs, disease treatment, or current tool recommendations, browse the web and cite authoritative sources.

## Data Handling Workflow

1. Parse the uploaded data.
   Identify available fields, but do not produce the full analysis yet. Fields include: sex, age, height, weight, BMI, body score, body-fat percentage, fat mass, visceral fat level, muscle mass, muscle rate, skeletal muscle mass, fat-free mass, water mass/rate, protein mass/rate, bone mass/rate, basal metabolic rate, body age, waist-hip ratio, smart-scale heart rate, resting heart rate, HRV, and trend/baseline values.

2. Normalize units and calculate sanity checks.
   Calculate BMI if height and weight exist. Calculate fat mass, fat-free mass, and FFMI when possible. Compare calculated values with user-provided values. Mark inconsistent, blurry, impossible, or single-device uncertain values as `需复测/需确认`. Keep these checks internal until the required user context is collected.

3. Check safety first.
   Apply `references/safety.md`. If red flags are present, immediately provide a short safety triage and avoid high-intensity planning until the issue is clarified.

4. Collect required context before analysis.
   Prefer Codex built-in parameter selection components for training goal, training experience, equipment/location, daily available time, injury or pain history, sleep status, and dietary restrictions. If built-in selection components are unavailable, fall back to concise Chinese text options. Do not output the body status report until these fields are collected, summarized, and confirmed, or until the user explicitly refuses to provide them.

5. Analyze and classify only after context collection.
   Choose one primary classification:
   - `体态重组`: normal BMI, moderate body fat, room to gain muscle or improve composition.
   - `减脂优先`: elevated BMI/body fat/visceral fat or waist-risk indicators.
   - `增肌优先`: low BMI, low muscle mass, or user goal is muscle gain.
   - `恢复优先`: elevated resting heart rate, low HRV, poor sleep, pain, excessive fatigue, or recent illness.
   - `医学复核优先`: red flags, abnormal repeated resting values, or symptoms needing clinician evaluation.

## Conversation State Machine

Follow this order. Do not skip ahead.

1. `信息收集`
   After receiving physiological data, do not provide the full analysis immediately. First collect required training context. Prefer Codex built-in parameter selection components; use text options only as fallback:
   - Training goal.
   - Training experience.
   - Equipment/location.
   - Daily available time.
   - Injury or pain history.
   - Sleep status.
   - Dietary restrictions.
   Ask in small batches if needed. Keep each question concise and provide practical options. Only do immediate safety triage if the uploaded data contains red flags.

2. `上下文确认`
   After all seven fields are collected, show a concise training-context summary card and ask the user to confirm or correct it. Do not analyze until the user confirms the context.

3. `状态分析`
   Once required context is complete, generate the body status report and abnormal-data suggestions. Do not generate the 7-day plan yet.

4. `分析确认`
   Ask the user to confirm whether the analysis is accurate enough and invite them to enter planning in the same reply. If the user corrects data or context, revise the analysis first. If the user reply contains a clear forward intent such as `进入规划`, `开始规划`, `继续`, `可以`, `没问题`, `确认`, or equivalent, treat it as both analysis confirmation and planning authorization; go directly to `健身规划` without asking `规划询问`.

5. `规划询问`
   Use this only when the user's analysis-confirmation reply is ambiguous and does not clearly authorize planning.

6. `健身规划`
   If the user agrees, generate the 7-day training plan. Do not display GPT-Imagine 2 prompts yet.

7. `规划确认`
   Ask the user to confirm whether the plan is acceptable. If the user requests changes, revise the plan before image generation.

8. `图片提示词或图片生成`
   After the plan is confirmed, create one gpt-image-2-compatible prompt per day. By default, display the seven prompts as reusable deliverables. If the user explicitly asks to generate images, resolve the image provider first: use `openai_gpt_image_2` when `OPENAI_API_KEY` is configured and the API is available; otherwise fall back to Codex built-in `imagegen`. Submit Day 1 through Day 7 as seven independent image-generation jobs. The official API path must run jobs concurrently and return per-day status. The Codex built-in fallback may generate sequentially if the available tool path cannot parallelize. Do not merge the week into a weekly overview image unless requested. If the user provides a reference image, match its canvas size, aspect ratio, visual structure, and layout system across all generated daily images.

## Image Provider Resolution

Resolve image generation in this order:

1. `openai_gpt_image_2`
   - Use by default for actual image generation.
   - Required environment: `OPENAI_API_KEY`.
   - Default endpoint: `POST https://api.openai.com/v1/images/generations`.
   - Default model: `gpt-image-2`.
   - Default size: `1536x1024`.
   - Default quality: `medium`.
   - Default concurrency: `7`.
   - Use `scripts/generate_daily_images.py` when an API-backed batch run is appropriate.

2. `codex_builtin_imagegen`
   - Use when `OPENAI_API_KEY` is missing, the official API is unavailable, the user explicitly requests Codex preview generation, or the API script returns `fallback_required=codex_builtin_imagegen`.
   - Follow the `imagegen` skill and use the built-in `image_gen` tool.
   - Keep the same seven daily prompts, 1536x1024 layout target, and per-day job semantics.
   - State that this is a fallback preview path and may generate sequentially.

Do not silently skip image generation if the official API prerequisites are missing. Switch to the Codex built-in imagegen fallback unless the user has explicitly forbidden fallback generation.

## Image Generation Job Contract

When actual image generation is requested, use this behavior:

- Create exactly seven jobs: `day_1` through `day_7`.
- With `openai_gpt_image_2`, submit all seven jobs concurrently after plan confirmation.
- With `codex_builtin_imagegen`, keep seven independent jobs but generate sequentially if the built-in tool path cannot parallelize.
- Track each job independently with states: `queued`, `generating`, `succeeded`, `failed`, `retrying`.
- Return per-day image references only after each job succeeds; do not expose prompts by default.
- If one or more jobs fail, retry only the failed day jobs. Do not regenerate successful days.
- Keep the UI status visible as: `生成中`, `成功`, `失败重试`, `失败`.
- Preserve deterministic mapping: Day N prompt must only produce Day N image.
- If the backend has a concurrency limit lower than seven, enqueue all seven jobs immediately and let the backend worker pool drain them without blocking the conversation on each individual image.

## Planning Rules

- Default cycle: 7 days after analysis is confirmed and the user either explicitly opts into planning or uses a clear forward-intent phrase.
- Default image style: professional fitness poster.
- Default image-prompt output: 7 separate OpenAI gpt-image-2-compatible daily prompts, one for each day of the plan.
- Actual image generation: only after explicit user confirmation. Prefer the official `openai_gpt_image_2` API path when `OPENAI_API_KEY` is configured; otherwise follow the `imagegen` skill and generate one image per daily prompt through Codex built-in fallback.
- Product backend generation: submit seven independent daily jobs concurrently by default through `gpt-image-2`. Sequential generation is only a Codex built-in preview fallback when the available tool path cannot parallelize.
- Image size/layout consistency: if the user uploads a reference image, use that reference as the required visual template for every daily image. Preserve the same aspect ratio, canvas dimensions when supported, header structure, panel grid, typography hierarchy, icon/card style, color system, and footer layout. If no reference image exists, default to a 1536x1024 landscape canvas with a 3:2 aspect ratio.
- Default daily poster structure: top header with large `DAY N` and training title; top summary cards for `当天目标`, `核心动作`, `目标肌群`; right-side or top-right cards for `姿势要点`, `组数次数/RPE`, `安全提醒`; three numbered exercise panels with consistent image composition and muscle insets; bottom area for action cues, training tip, and estimated duration.
- Use RPE for intensity. New users usually stay at RPE 6-7; intermediate users can use RPE 7-8; avoid RPE 9-10 unless the user is experienced and no risk flags exist.
- Prefer sustainable plans over aggressive transformation claims.
- For beginners, avoid prescribing high-risk heavy barbell lifts as mandatory. Offer safer machine, dumbbell, cable, or bodyweight alternatives.
- Include warm-up, main training, accessory work, cardio, cooldown/stretching, nutrition focus, and recovery focus for each day.
- Match each daily image prompt to that day's actual training theme. Each prompt/image must include the day's goal, core exercises, target muscles, posture cues, sets/reps/RPE, and safety reminders. Do not invent unrealistic before/after effects.
- Keep visual structure consistent across Day 1-Day 7. Only change the day number, training title, exercise content, target muscles, cues, and duration.

## Language Rules

- Use non-diagnostic language: `提示`, `可能`, `建议复测`, `建议咨询医生`.
- Do not say: `诊断为`, `治疗`, `治愈`, `保证`, `必然`.
- Clearly separate data-derived findings from user-provided context and any remaining uncertainties.
- When listing file names in the local workspace, show only file names, not full paths.
