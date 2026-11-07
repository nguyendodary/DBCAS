// Separate opt-in acceptance. Never load credentials into browser storage or traces.
import { test, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'
import {
  api,
  login,
  register,
  setFlow,
  start,
  take,
  checkArithmetic,
  checkViewport,
} from './practice-harness.js'

const ledger = () =>
  JSON.parse(
    readFileSync(
      new URL(
        `${process.env.DBCAS_REAL_LEDGER_DIR || './_review/real-provider-20261104'}/ledger.json`,
        new URL('../../', import.meta.url),
      ),
      'utf8',
    ),
  )

test('real provider: validated generation within a single selected concept', async ({
  page,
}, info) => {
  test.skip(!info.config.metadata.live, 'Requires a key and explicit DBCAS_RUN_REAL_PROVIDER=1')
  expect(ledger().calls.length).toBeLessThanOrEqual(78)
  await register(page, 'real-generation')
  const options = await api(page, '/practice/options')
  const concept = options.concepts.find((c) => /SELECT/i.test(c.concept_name))
  expect(concept).toBeTruthy()
  const state = await start(page, 'ai', 1, {
    concept_ids: [concept.concept_id],
    difficulties: ['EASY'],
  })
  await info.attach('generation-diagnostics', {
    body: JSON.stringify(state.generation_diagnostics || []),
    contentType: 'application/json',
  })
  expect(state.max_questions).toBe(1)
  expect(
    state.generation_fallback,
    'The live generated question must pass the shared validator',
  ).toBe(false)
  expect(state.bank_mixed).toBe(false)
  expect(state.template_fallback).toBe(false)
  expect(state.ai_generated_count).toBe(1)
  expect(state.current_question).toBeTruthy()
  await page.screenshot({ path: info.outputPath('validated-live-generation.png'), fullPage: true })
})

test('real provider: exact count keeps SQL on the validated bank', async ({ page }, info) => {
  test.skip(!info.config.metadata.live, 'Requires a key and explicit DBCAS_RUN_REAL_PROVIDER=1')
  await register(page, 'real-mixed')
  const options = await api(page, '/practice/options')
  const concept = options.concepts.find((c) => /SELECT/i.test(c.concept_name))
  expect(concept).toBeTruthy()
  const state = await start(page, 'ai', 3, {
    concept_ids: [concept.concept_id],
    difficulties: ['EASY'],
  })
  await info.attach('generation-diagnostics', {
    body: JSON.stringify(state.generation_diagnostics || []),
    contentType: 'application/json',
  })
  expect(state.max_questions).toBe(3)
  expect(state.question_source).toBe('ai')
  expect(state.ai_generated_count).toBe(2)
  expect(state.bank_mixed).toBe(true)
  expect(state.template_fallback).toBe(false)
  expect(state.selection_notice).toContain('SQL')
  expect(state.current_question).toBeTruthy()
  await page.screenshot({ path: info.outputPath('mixed-bank-sql.png'), fullPage: true })
})

test('real provider: one AI attempt evaluated through Prompt Builder and Evaluator', async ({
  page,
}, info) => {
  test.skip(!info.config.metadata.live, 'Requires a key and explicit DBCAS_RUN_REAL_PROVIDER=1')
  const before = ledger()
  expect(before.maximum_total).toBe(80)
  expect(
    before.maximum_total - before.prior_calls - before.calls.length,
    'Keep at least four meter slots for this targeted run',
  ).toBeGreaterThanOrEqual(4)
  await register(page, 'live-builder-eval')
  const options = await api(page, '/practice/options')
  const concept = options.concepts.find((c) => /SELECT/i.test(c.concept_name))
  expect(concept).toBeTruthy()
  const state = await start(page, 'ai', 3, {
    concept_ids: [concept.concept_id],
    difficulties: ['EASY'],
  })
  await info.attach('generation-diagnostics', {
    body: JSON.stringify(state.generation_diagnostics || []),
    contentType: 'application/json',
  })
  expect(state.max_questions).toBe(3)
  expect(state.question_source).toBe('ai')
  expect(state.bank_mixed, 'SQL must stay on the validated bank').toBe(true)
  expect(state.template_fallback, 'No deterministic template fallback').toBe(false)
  expect(state.ai_generated_count, 'AI must supply both non-SQL questions').toBe(2)
  expect(
    ledger().calls.length - before.calls.length,
    'Generation retries must stay inside the four-call run budget',
  ).toBeLessThanOrEqual(2)
  const { sid } = await take(page, state)
  await expect(page.getByRole('heading', { name: 'Nhận xét từng câu', exact: true })).toBeVisible({
    timeout: 90000,
  })
  const attempt = await api(page, `/evaluations/attempts/${sid}`)
  expect(attempt.result.evaluator_fallback, 'Evaluator must run on the real model').toBe(false)
  expect(attempt.result.prompt_hash).toBeTruthy()
  expect(attempt.result.evaluation.question_comments).toHaveLength(3)
  expect(ledger().calls.length - before.calls.length, 'Targeted run budget').toBeLessThanOrEqual(4)
  await info.attach('evaluated-attempt', {
    body: JSON.stringify({
      session_id: sid,
      evaluator_fallback: attempt.result.evaluator_fallback,
      builder_fallback: attempt.result.builder_fallback,
      prompt_hash: attempt.result.prompt_hash,
      score: attempt.score ?? null,
      question_comments: attempt.result.evaluation.question_comments?.length ?? 0,
    }),
    contentType: 'application/json',
  })
  await page.screenshot({ path: info.outputPath('live-builder-evaluate.png'), fullPage: true })
})

test('real provider: three attempts, automatic release, admin approval and overall evaluation', async ({
  browser,
}, info) => {
  test.skip(!info.config.metadata.live, 'Requires a key and explicit DBCAS_RUN_REAL_PROVIDER=1')
  const before = ledger()
  expect(before.maximum_total).toBe(80)
  expect(Number.isInteger(before.prior_calls)).toBe(true)
  expect(
    before.maximum_total - before.prior_calls - before.calls.length,
    'Reserve at least ten requests before beginning a full scenario',
  ).toBeGreaterThanOrEqual(10)
  const adminContext = await browser.newContext({ baseURL: info.project.use.baseURL })
  const learnerContext = await browser.newContext({ baseURL: info.project.use.baseURL })
  const admin = await adminContext.newPage(),
    learner = await learnerContext.newPage()
  const arithmetic = []
  try {
    await login(admin, 'admin@dbcas.local')
    await register(learner, 'real-acceptance')
    await learner.goto('/competency')
    await expect(learner.getByRole('heading', { name: 'Bắt đầu hành trình của bạn' })).toBeVisible()
    for (let index = 0; index < 3; index++) {
      await setFlow(admin, index === 1 ? 'HUMAN_VERIFIED' : 'IMMEDIATE')
      const cohort = await api(admin, '/admin/analytics/cohort')
      const options = index === 2 ? await api(learner, '/practice/options') : null
      const concept = options?.concepts.find((c) => /SELECT/i.test(c.concept_name))
      if (index === 2) expect(concept).toBeTruthy()
      const state = await start(
        learner,
        index === 2 ? 'ai' : 'bank',
        3,
        index === 2 ? { concept_ids: [concept.concept_id], difficulties: ['EASY'] } : {},
      )
      if (index === 2) {
        await info.attach('generation-diagnostics', {
          body: JSON.stringify(state.generation_diagnostics || []),
          contentType: 'application/json',
        })
        expect(state.generation_fallback, 'AI is mixed with the validated SQL bank').toBe(true)
        expect(state.bank_mixed, 'SQL must come from the validated bank').toBe(true)
        expect(state.template_fallback, 'No deterministic template fallback').toBe(false)
        expect(state.ai_generated_count, 'AI must supply both non-SQL questions').toBe(2)
      }
      const { sid } = await take(learner, state, { refresh: index === 0, sandbox: index === 0 })
      if (index === 1) {
        await expect(
          learner.getByRole('heading', { name: 'Đang chờ giảng viên duyệt', exact: true }),
        ).toBeVisible()
        const hidden = await api(learner, `/evaluations/attempts/${sid}`)
        expect(hidden.status).toBe('awaiting_approval')
        expect(hidden).not.toHaveProperty('score')
        expect(hidden).not.toHaveProperty('result')
        expect(await api(admin, '/admin/analytics/cohort')).toEqual(cohort)
        await admin.goto(`/admin/grading/${sid}`)
        await expect(admin.getByRole('button', { name: 'Duyệt', exact: true })).toBeEnabled({
          timeout: 90000,
        })
        await admin.getByRole('button', { name: 'Chạy SQL kiểm tra', exact: true }).click()
        await expect(admin.getByText(/Thành công/)).toBeVisible()
        const form = admin.locator('form').first()
        await form.getByRole('spinbutton').fill('0.25')
        await form
          .getByLabel('Lý do điều chỉnh')
          .fill('Kiểm thử đối chiếu rubric và đồng bộ điểm đã duyệt.')
        await form.getByRole('button', { name: 'Lưu điểm điều chỉnh' }).click()
        await expect(admin.getByRole('button', { name: 'Duyệt', exact: true })).toBeEnabled({
          timeout: 90000,
        })
        await admin.getByRole('button', { name: 'Duyệt', exact: true }).click()
        await expect(learner.getByText(/Đã được giảng viên duyệt/)).toBeVisible({ timeout: 90000 })
        const review = await api(admin, `/admin/grading-reviews/${sid}`)
        expect(review.score_edits).toHaveLength(1)
        expect(review.score_edits[0].reason).toContain('rubric')
        expect((await api(admin, '/admin/analytics/cohort')).finalized_sessions).toBe(
          cohort.finalized_sessions + 1,
        )
      }
      await expect(
        learner.getByRole('heading', { name: 'Nhận xét từng câu', exact: true }),
      ).toBeVisible({ timeout: 90000 })
      const attempt = await api(learner, `/evaluations/attempts/${sid}`)
      expect(
        attempt.result.evaluator_fallback,
        'Real evaluator must satisfy the full contract',
      ).toBe(false)
      expect(attempt.result.evaluation.question_comments).toHaveLength(3)
      arithmetic.push(await checkArithmetic(learner, sid))
      await learner.screenshot({
        path: info.outputPath(`attempt-${index + 1}.png`),
        fullPage: true,
      })
      await learner.goto('/competency')
      await expect(learner.getByRole('heading', { name: 'Nhận xét', exact: true })).toBeVisible({
        timeout: 90000,
      })
      const overall = await api(learner, '/evaluations/overall')
      expect(overall.attempt_count).toBe(index + 1)
      expect(overall.result.evaluator_fallback).toBe(false)
      const callsBeforeCacheRead = ledger().calls.length
      expect((await api(learner, '/evaluations/overall')).input_hash).toBe(overall.input_hash)
      expect(ledger().calls.length).toBe(callsBeforeCacheRead)
      if (index === 0)
        await expect(
          learner.getByText('Làm thêm bài để xem xu hướng', { exact: true }),
        ).toBeVisible()
      if (index === 2)
        await expect(
          learner.getByRole('heading', { name: 'Xu hướng qua các bài', exact: true }),
        ).toBeVisible()
      await learner.setViewportSize({ width: 390, height: 844 })
      await checkViewport(learner)
      await learner.screenshot({
        path: info.outputPath(`overall-${index + 1}-mobile.png`),
        fullPage: true,
      })
      await learner.setViewportSize({ width: 1440, height: 1000 })
    }
    const after = ledger()
    expect(after.calls.length).toBeGreaterThan(before.calls.length)
    expect(after.prior_calls + after.calls.length).toBeLessThanOrEqual(80)
    await info.attach('arithmetic', {
      body: JSON.stringify(arithmetic),
      contentType: 'application/json',
    })
  } finally {
    await setFlow(admin, 'IMMEDIATE')
    await learnerContext.close()
    await adminContext.close()
  }
})
