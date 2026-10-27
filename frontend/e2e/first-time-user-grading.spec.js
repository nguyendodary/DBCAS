import { test, expect, request as apiRequest } from './browser-fixture.js'
import AxeBuilder from '@axe-core/playwright'

const API = 'http://127.0.0.1:8100'
const PASSWORD = 'ReleaseTest123!'
const DIFFICULTY_LABEL = { EASY: 'Easy', MEDIUM: 'Medium', HARD: 'Hard' }

async function json(api, path, { token, method = 'GET', data } = {}) {
  const response = await api.fetch(`${API}${path}`, {
    method,
    data,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  expect(response.ok(), `${method} ${path}: ${await response.text()}`).toBeTruthy()
  return response.status() === 204 ? null : response.json()
}

async function registerViaApi(api, email, name = 'First-time learner') {
  return json(api, '/api/v1/auth/register', {
    method: 'POST', data: { name, email, password: PASSWORD, password_confirm: PASSWORD },
  })
}

async function tokenViaApi(api, email) {
  return (await json(api, '/api/v1/auth/login', {
    method: 'POST', data: { email, password: PASSWORD },
  })).access_token
}

async function adminToken(api) {
  return tokenViaApi(api, 'release-admin@test.dev')
}

async function login(page, email) {
  await page.addInitScript(() => localStorage.setItem('dbcas_locale', 'en'))
  await page.goto('/login')
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL(/\/dashboard$/)
  await expect(page.getByRole('heading', { name: 'My competency', exact: true })).toBeVisible()
  return page.evaluate(() => localStorage.getItem('dbcas_token'))
}

async function adminLogin(page) {
  await page.addInitScript(() => localStorage.setItem('dbcas_locale', 'en'))
  await page.goto('/login')
  await page.getByLabel('Email', { exact: true }).fill('release-admin@test.dev')
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL(/\/admin$/)
  await expect(page.getByRole('heading', { name: 'Cohort Overview', exact: true })).toBeVisible()
  return page.evaluate(() => localStorage.getItem('dbcas_token'))
}

async function openOptions(page) {
  const details = page.locator('details').filter({ hasText: 'Assessment options' })
  if (!(await details.evaluate((node) => node.open))) {
    await page.getByText('Assessment options', { exact: true }).click()
  }
}

async function startViaUi(page, { assessmentId, area, difficulty, mode = 'FORMAL', count, concepts }) {
  await page.goto('/assessments')
  await expect(page.getByRole('heading', { name: 'Assess your database skills', exact: true })).toBeVisible()
  await openOptions(page)
  await page.getByLabel('Assessment rules', { exact: true }).selectOption(String(assessmentId))
  if (area) await page.getByRole('button', { name: area, exact: true }).click()
  for (const name of concepts || []) {
    await page.getByRole('checkbox', { name, exact: true }).check()
  }
  await page.getByRole('radio', { name: DIFFICULTY_LABEL[difficulty], exact: true }).check()
  await page.getByLabel('Assessment format', { exact: true }).selectOption(mode)
  if (count) await page.getByLabel('Number of questions', { exact: true }).selectOption(String(count))
  const response = page.waitForResponse((r) => r.request().method() === 'POST'
    && new URL(r.url()).pathname.endsWith(`/assessments/${assessmentId}/sessions`))
  await page.getByRole('button', { name: 'Start assessment', exact: true }).click()
  return response
}

async function finishViaUi(page) {
  await page.getByRole('button', { name: 'Finish assessment', exact: true }).first().click()
  await page.getByRole('button', { name: 'Yes, finish', exact: true }).click()
  await expect(page).toHaveURL(/\/history\/\d+$/)
  return Number(page.url().split('/').at(-1))
}

async function openHelp(page) {
  await page.getByRole('button', { name: /^(Help|Hướng dẫn)$/ }).click()
  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  return dialog
}

async function currentState(api, sid, learner) {
  return json(api, `/api/v1/sessions/${sid}`, { token: learner })
}

async function questionKey(api, admin, questionId) {
  return json(api, `/api/v1/admin/questions/${questionId}`, { token: admin })
}

function answerPayload(question, key, { essaySuffix = '' } = {}) {
  if (question.question_type === 'mcq') {
    return { selected_option_id: key.options.find((option) => option.is_correct).option_id }
  }
  if (question.question_type === 'sql') return { sql_answer: key.reference_answer }
  return { essay_answer: `${key.reference_answer}${essaySuffix}` }
}

async function fillAnswer(page, question, key, { essaySuffix = '' } = {}) {
  const payload = answerPayload(question, key, { essaySuffix })
  if (question.question_type === 'mcq') {
    await page.locator(`input[value="${payload.selected_option_id}"]`).locator('..').click()
  } else if (question.question_type === 'sql') {
    await page.getByLabel('Your query', { exact: true }).fill(payload.sql_answer)
  } else {
    await page.getByLabel('Your answer', { exact: true }).fill(payload.essay_answer)
  }
  return payload
}

async function submitViaUi(page, sid) {
  const submitted = page.waitForResponse((r) => r.request().method() === 'POST'
    && new URL(r.url()).pathname.endsWith(`/sessions/${sid}/submit`))
  await page.getByRole('button', { name: 'Submit answer & continue', exact: true }).click()
  const response = await submitted
  expect(response.status()).toBe(200)
  return response.json()
}

async function pollRelease(api, tid, sid, status, timeout = 30_000) {
  await expect.poll(async () => (await json(api, `/api/v1/sessions/${sid}`, { token: tid })).release_status, {
    timeout, intervals: [250, 500, 1_000],
  }).toBe(status)
}

test('practice: mode switching, resume, in-exam help, bilingual state, sandbox safety and official exclusion', async ({ page }) => {
  test.setTimeout(300_000)
  const api = await apiRequest.newContext({ baseURL: API, timeout: 60_000 })
  const unique = `ftu-practice-${Date.now()}`
  const email = `${unique}@test.dev`
  const errors = []
  page.on('pageerror', (error) => errors.push(error.message))
  let closedAssessmentId
  try {
    const admin = await adminToken(api)
    await registerViaApi(api, email, 'Practice learner')
    const learner = await login(page, email)

    // A closed rule stays unavailable to learners even through the visible start form.
    const bankAssessment = await json(api, '/api/v1/admin/assessments/4', { token: admin })
    const areaConcepts = bankAssessment.concepts.filter((c) => c.subject_area === 'SQL Querying')
    const closed = await json(api, '/api/v1/admin/assessments', { token: admin, method: 'POST', data: {
      title: `${unique} closed rule`, result_release_policy: 'IMMEDIATE',
      concepts: areaConcepts.map((c) => ({ concept_id: c.concept_id, min_difficulty: 1, max_difficulty: 5, target_pct: 60 })),
    } })
    closedAssessmentId = closed.assessment_id
    await json(api, `/api/v1/admin/assessments/${closed.assessment_id}`, { token: admin, method: 'PATCH', data: { status: 'published' } })
    await json(api, `/api/v1/admin/assessments/${closed.assessment_id}`, { token: admin, method: 'PATCH', data: { status: 'closed' } })
    const unavailable = await api.fetch(`${API}/api/v1/assessments/${closed.assessment_id}/sessions`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${learner}` },
      data: { concept_ids: areaConcepts.map((c) => c.concept_id), difficulty: 'MEDIUM', request_id: crypto.randomUUID(), mode: 'FORMAL' },
    })
    expect(unavailable.status()).toBe(409)
    expect((await unavailable.json()).error.code).toBe('assessment_not_active')

    await page.goto('/assessments')
    await expect(page.getByRole('heading', { name: 'Assess your database skills', exact: true })).toBeVisible()
    await openOptions(page)
    await expect(page.getByLabel('Assessment rules', { exact: true }).locator('option').filter({ hasText: `${unique} closed rule` })).toHaveCount(0)
    // Mode switching exposes only the controls that apply to the chosen format.
    await page.getByLabel('Assessment rules', { exact: true }).selectOption('4')
    await page.getByRole('button', { name: 'SQL Querying', exact: true }).click()
    await page.getByLabel('Assessment format', { exact: true }).selectOption('PRACTICE')
    await expect(page.getByLabel('Number of questions', { exact: true })).toBeVisible()
    await page.getByLabel('Assessment format', { exact: true }).selectOption('FORMAL')
    await expect(page.getByLabel('Number of questions', { exact: true })).toHaveCount(0)
    await page.getByLabel('Assessment format', { exact: true }).selectOption('PRACTICE')

    // A missing blueprint is reported without creating a session.
    await page.getByLabel('Assessment rules', { exact: true }).selectOption('2')
    await page.getByRole('button', { name: 'Performance', exact: true }).click()
    await page.getByRole('radio', { name: 'Hard', exact: true }).check()
    await page.getByLabel('Assessment format', { exact: true }).selectOption('FORMAL')
    const rejected = page.waitForResponse((r) => r.request().method() === 'POST'
      && new URL(r.url()).pathname.endsWith('/assessments/2/sessions'))
    await page.getByRole('button', { name: 'Start assessment', exact: true }).click()
    const rejection = await rejected
    expect(rejection.status()).toBe(422)
    // The assessment's configured skill ranges and its approved blueprint both
    // make this combination unavailable; either actionable code is valid.
    expect(['blueprint_not_available', 'insufficient_question_pool']).toContain((await rejection.json()).error.code)
    await expect(page).toHaveURL(/\/assessments$/)
    await expect(page.getByText(/The approved bank has too few eligible questions|No approved assessment blueprint/)).toBeVisible()

    const started = await startViaUi(page, { assessmentId: 4, area: 'SQL Querying', difficulty: 'MEDIUM', mode: 'PRACTICE', count: 3 })
    expect(started.status()).toBe(201)
    const sid = (await started.json()).session_id
    await expect(page).toHaveURL(new RegExp(`/exam/${sid}$`))
    const plan = await json(api, `/__test/sessions/${sid}/assembly`, { token: learner })
    expect(plan.assembly_mode).toBe('PRACTICE')
    expect(plan.max_questions).toBe(3)

    let wrongSelection
    for (let i = 0; i < 3; i++) {
      const state = await currentState(api, sid, learner)
      const q = state.current_question
      expect(q, `question ${i + 1}`).toBeTruthy()
      // Correctness is never disclosed before the attempt is submitted.
      expect((q.options || []).every((option) => option.is_correct === undefined)).toBe(true)
      await expect(page.getByText(q.prompt, { exact: true })).toBeVisible()
      const key = await questionKey(api, admin, q.question_id)
      const payload = await fillAnswer(page, q, key, { essaySuffix: q.question_type === 'essay' ? '\nPractice response.' : '' })

      if (i === 0) {
        // Drafts survive a reload and the auto-saved revision is authoritative.
        await page.getByRole('button', { name: 'Save draft', exact: true }).click()
        await expect.poll(async () => (await json(api, `/api/v1/sessions/${sid}/draft?question_id=${q.question_id}`, { token: learner })).revision).toBeGreaterThan(0)
        await page.reload()
        await expect(page.getByText(q.prompt, { exact: true })).toBeVisible()
        if (q.question_type === 'mcq') {
          await expect(page.locator(`input[value="${payload.selected_option_id}"]`)).toBeChecked()
        } else if (q.question_type === 'sql') {
          await expect(page.getByLabel('Your query', { exact: true })).toHaveValue(payload.sql_answer)
        } else {
          await expect(page.getByLabel('Your answer', { exact: true })).toHaveValue(payload.essay_answer)
        }

        // Opening the guide must not pause the clock or discard the answer.
        const beforeClock = await page.locator('.timer-value strong').innerText()
        const drawer = await openHelp(page)
        await expect(drawer.getByText('During an assessment', { exact: true })).toBeVisible()
        const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()
        expect(scan.violations).toEqual([])
        await page.waitForTimeout(1_600)
        await page.keyboard.press('Escape')
        await expect(drawer).toHaveCount(0)
        await expect(page.getByText(q.prompt, { exact: true })).toBeVisible()
        const afterClock = await page.locator('.timer-value strong').innerText()
        const seconds = (value) => Number(value.split(':')[0]) * 60 + Number(value.split(':')[1])
        expect(seconds(afterClock)).toBeLessThan(seconds(beforeClock))
        if (q.question_type === 'mcq') {
          await expect(page.locator(`input[value="${payload.selected_option_id}"]`)).toBeChecked()
        } else if (q.question_type === 'sql') {
          await expect(page.getByLabel('Your query', { exact: true })).toHaveValue(payload.sql_answer)
        } else {
          await expect(page.getByLabel('Your answer', { exact: true })).toHaveValue(payload.essay_answer)
        }

        // The session locale and timer stay fixed while the display language changes.
        const expiresAt = state.expires_at
        const translated = await json(api, `/api/v1/sessions/${sid}?display_locale=vi`, { token: learner })
        await page.getByRole('button', { name: 'Language', exact: true }).click()
        await page.getByRole('menuitemradio', { name: 'Tiếng Việt', exact: true }).click()
        await expect(page.getByText(translated.current_question.prompt, { exact: true })).toBeVisible()
        await expect(page.locator('html')).toHaveAttribute('lang', 'vi')
        const viState = await currentState(api, sid, learner)
        expect(viState.expires_at).toBe(expiresAt)
        expect(viState.locale).toBe('en')
        expect(viState.current_question.question_id).toBe(q.question_id)
        if (q.question_type === 'mcq') {
          await expect(page.locator(`input[value="${payload.selected_option_id}"]`)).toBeChecked()
        } else if (q.question_type === 'sql') {
          await expect(page.getByLabel('Truy vấn của bạn', { exact: true })).toHaveValue(payload.sql_answer)
        } else {
          await expect(page.getByLabel('Câu trả lời của bạn', { exact: true })).toHaveValue(payload.essay_answer)
        }
        await page.getByRole('button', { name: 'Ngôn ngữ', exact: true }).click()
        await page.getByRole('menuitemradio', { name: 'English', exact: true }).click()
        await expect(page.getByText(q.prompt, { exact: true })).toBeVisible()
      }

      // Change the saved draft to a wrong option; the latest choice is graded.
      if (q.question_type === 'mcq' && !wrongSelection) {
        const wrong = key.options.find((option) => !option.is_correct)
        expect(wrong).toBeTruthy()
        await page.locator(`input[value="${wrong.option_id}"]`).locator('..').click()
        wrongSelection = { questionId: q.question_id, optionId: wrong.option_id }
      }

      const result = await submitViaUi(page, sid)
      expect(result.state.answered_count).toBe(i + 1)

      if (i === 0) {
        // Leaving and re-entering the same selection resumes the live session.
        const resumed = await startViaUi(page, { assessmentId: 4, area: 'SQL Querying', difficulty: 'MEDIUM', mode: 'PRACTICE', count: 3 })
        expect(resumed.status()).toBe(201)
        expect((await resumed.json()).session_id).toBe(sid)
        await expect(page).toHaveURL(new RegExp(`/exam/${sid}$`))
        const after = await currentState(api, sid, learner)
        expect(after.expires_at).toBe(state.expires_at)
        expect(after.answered_count).toBe(1)
      }
    }

    const finished = await finishViaUi(page)
    expect(finished).toBe(sid)
    await pollRelease(api, learner, sid, 'published')
    const evidence = await json(api, `/api/v1/sessions/${sid}/evidence`, { token: learner })
    expect(evidence.items).toHaveLength(3)
    expect(evidence.items.every((item) => item.score !== null)).toBe(true)
    expect(wrongSelection, 'practice selection must include an MCQ').toBeTruthy()
    if (wrongSelection) {
      const item = evidence.items.find((row) => row.question_id === wrongSelection.questionId)
      expect(item.selected_option_id).toBe(wrongSelection.optionId)
      expect(Number(item.score)).toBe(0)
      expect(item.options.find((option) => option.option_id === wrongSelection.optionId).is_correct).toBe(false)
      expect(item.options.filter((option) => option.is_correct)).toHaveLength(1)
    }
    const history = (await json(api, '/api/v1/sessions', { token: learner })).find((row) => row.session_id === sid)
    expect(history.assembly_mode).toBe('PRACTICE')
    expect(history.release_status).toBe('published')
    await page.goto('/history')
    await expect(page.getByText(/Topic practice/).first()).toBeVisible()
    await page.goto('/competency')
    await expect(page.getByText('0 published assessments', { exact: true })).toBeVisible()
    const cumulative = await json(api, '/api/v1/sessions/competency/cumulative', { token: learner })
    expect(cumulative.concepts).toEqual([])
    expect(cumulative.summary.finalized_assessments).toBe(0)
    expect(errors).toEqual([])
  } finally {
    if (closedAssessmentId) {
      const admin = await adminToken(api)
      await api.patch(`${API}/api/v1/admin/assessments/${closedAssessmentId}`, {
        headers: { Authorization: `Bearer ${admin}` }, data: { status: 'closed' },
      })
    }
    await api.dispose()
  }
})

test('easy and hard practice completions grade fully and stay out of official competency', async ({ page }) => {
  test.setTimeout(300_000)
  const api = await apiRequest.newContext({ baseURL: API, timeout: 60_000 })
  const email = `ftu-bands-${Date.now()}@test.dev`
  const errors = []
  page.on('pageerror', (error) => errors.push(error.message))
  try {
    const admin = await adminToken(api)
    await registerViaApi(api, email, 'Band coverage learner')
    const learner = await login(page, email)
    // Practice must cover every selected skill with the requested count, so a
    // whole subject area is not always feasible for a short EASY/HARD run.
    // Pick a skill whose band inventory has at least two version families.
    const assessment = await json(api, '/api/v1/admin/assessments/4', { token: admin })
    const areaConceptIds = new Set(assessment.concepts
      .filter((c) => c.subject_area === 'SQL Querying').map((c) => c.concept_id))
    const validated = await json(api, '/api/v1/admin/questions?status=validated', { token: admin })
    const bands = { EASY: [1, 2], HARD: [4, 5] }
    for (const difficulty of ['EASY', 'HARD']) {
      const [low, high] = bands[difficulty]
      const concept = assessment.concepts.find((c) => areaConceptIds.has(c.concept_id)
        && new Set(validated.filter((q) => q.difficulty_level >= low && q.difficulty_level <= high
          && q.concepts.some((tag) => tag.concept_id === c.concept_id && tag.confirmed))
          .map((q) => q.family_id || q.question_id)).size >= 2)
      expect(concept, `${difficulty} needs a skill with two graded questions`).toBeTruthy()
      const started = await startViaUi(page, {
        assessmentId: 4, difficulty, mode: 'PRACTICE', count: 2, concepts: [concept.concept_name],
      })
      expect(started.status()).toBe(201)
      const sid = (await started.json()).session_id
      const plan = await json(api, `/__test/sessions/${sid}/assembly`, { token: learner })
      expect(plan.assembly_mode).toBe('PRACTICE')
      expect(plan.max_questions).toBe(2)
      expect(plan.selected_concept_ids).toEqual([concept.concept_id])
      for (let i = 0; i < 2; i++) {
        const state = await currentState(api, sid, learner)
        const q = state.current_question
        expect(q, `${difficulty} question ${i + 1}`).toBeTruthy()
        await expect(page.getByText(q.prompt, { exact: true })).toBeVisible()
        const key = await questionKey(api, admin, q.question_id)
        await fillAnswer(page, q, key)
        const result = await submitViaUi(page, sid)
        expect(result.state.answered_count).toBe(i + 1)
      }
      expect(await finishViaUi(page)).toBe(sid)
      // Practice shells can still include an essay; drain the same controlled
      // provider path the formal journeys use before asserting publication.
      await json(api, '/__test/grading-jobs/drain?max_attempts=5&include_essay=true', { token: admin, method: 'POST' })
      await pollRelease(api, learner, sid, 'published')
      const evidence = await json(api, `/api/v1/sessions/${sid}/evidence`, { token: learner })
      expect(evidence.items).toHaveLength(2)
      expect(evidence.items.every((item) => item.score !== null)).toBe(true)
      const record = (await json(api, '/api/v1/sessions', { token: learner })).find((row) => row.session_id === sid)
      expect(record.assembly_mode).toBe('PRACTICE')
      expect(record.release_status).toBe('published')
    }
    const cumulative = await json(api, '/api/v1/sessions/competency/cumulative', { token: learner })
    expect(cumulative.concepts).toEqual([])
    expect(cumulative.summary.finalized_assessments).toBe(0)
    await page.goto('/competency')
    await expect(page.getByText('0 published assessments', { exact: true })).toBeVisible()
    expect(errors).toEqual([])
  } finally {
    await api.dispose()
  }
})

test('formal immediate: full submission, persistence, duplicate replay, history and competency', async ({ page }) => {
  test.setTimeout(600_000)
  const api = await apiRequest.newContext({ baseURL: API, timeout: 60_000 })
  const unique = `ftu-formal-${Date.now()}`
  const email = `${unique}@test.dev`
  const errors = []
  page.on('pageerror', (error) => errors.push(error.message))
  try {
    const admin = await adminToken(api)
    await registerViaApi(api, email, 'Formal learner')
    const learner = await login(page, email)
    const started = await startViaUi(page, { assessmentId: 3, area: 'Database Design', difficulty: 'MEDIUM', mode: 'FORMAL' })
    expect(started.status()).toBe(201)
    const sid = (await started.json()).session_id
    await expect(page).toHaveURL(new RegExp(`/exam/${sid}$`))
    const plan = await json(api, `/__test/sessions/${sid}/assembly`, { token: learner })
    expect(plan.assembly_mode).toBe('FORMAL')
    expect(plan.type_mix).toEqual({ mcq: 10, sql: 2, essay: 1 })

    const seen = new Set()
    let firstPayload
    let sandboxChecked = false
    for (let i = 0; i < 13; i++) {
      const state = await currentState(api, sid, learner)
      const q = state.current_question
      expect(q, `question ${i + 1}`).toBeTruthy()
      expect(seen.has(q.question_id)).toBe(false)
      seen.add(q.question_id)
      await expect(page.getByText(q.prompt, { exact: true })).toBeVisible()
      const key = await questionKey(api, admin, q.question_id)
      const payload = await fillAnswer(page, q, key)

      if (i === 0) {
        firstPayload = { question: q, payload }
        await page.getByRole('button', { name: 'Save draft', exact: true }).click()
        await expect.poll(async () => (await json(api, `/api/v1/sessions/${sid}/draft?question_id=${q.question_id}`, { token: learner })).revision).toBeGreaterThan(0)
        await page.reload()
        await expect(page.getByText(q.prompt, { exact: true })).toBeVisible()
        if (q.question_type === 'mcq') {
          await expect(page.locator(`input[value="${payload.selected_option_id}"]`)).toBeChecked()
        } else if (q.question_type === 'sql') {
          await expect(page.getByLabel('Your query', { exact: true })).toHaveValue(payload.sql_answer)
        } else {
          await expect(page.getByLabel('Your answer', { exact: true })).toHaveValue(payload.essay_answer)
        }
      }

      if (q.question_type === 'sql' && !sandboxChecked) {
        sandboxChecked = true
        const editor = page.getByLabel('Your query', { exact: true })
        const run = page.getByRole('button', { name: 'Run in sandbox', exact: true })

        await editor.fill('SELEC * FORM students')
        await run.click()
        await expect(page.getByText(/Check your SQL syntax|Only a single read-only SELECT/)).toBeVisible()

        await editor.fill('DELETE FROM students')
        await run.click()
        await expect(page.getByText(/Only read-only SELECT queries are allowed|Only a single read-only SELECT/)).toBeVisible()

        await editor.fill('SELECT count(*) FROM generate_series(1, 100000) a CROSS JOIN generate_series(1, 100000) b')
        await run.click()
        await expect(page.getByText('The query exceeded the execution time limit.', { exact: true })).toBeVisible({ timeout: 15_000 })
        await expect(page.getByText(q.prompt, { exact: true })).toBeVisible()
        await editor.fill(payload.sql_answer)
      }

      if (i === 1) {
        let aborted = false
        const handler = async (route) => {
          if (!aborted) {
            aborted = true
            await route.abort('failed')
          } else {
            await route.continue()
          }
        }
        await page.route(`**/api/v1/sessions/${sid}/submit`, handler)
        await page.getByRole('button', { name: 'Submit answer & continue', exact: true }).click()
        await expect(page.getByText('Cannot connect to DBCAS. Check your connection and retry.', { exact: true })).toBeVisible()
        await expect(page.getByRole('button', { name: 'Submit answer & continue', exact: true })).toBeEnabled()
        const recovered = await submitViaUi(page, sid)
        expect(recovered.state.answered_count).toBe(2)
        await page.unroute(`**/api/v1/sessions/${sid}/submit`, handler)
      } else {
        const result = await submitViaUi(page, sid)
        expect(result.state.answered_count).toBe(i + 1)
      }

      if (i === 0) {
        const repeat = await api.fetch(`${API}/api/v1/sessions/${sid}/submit`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${learner}` },
          data: { question_id: firstPayload.question.question_id, ...firstPayload.payload },
        })
        expect(repeat.status()).toBe(200)
        const changed = firstPayload.question.question_type === 'mcq'
          ? { selected_option_id: key.options.find((option) => option.option_id !== firstPayload.payload.selected_option_id)?.option_id }
          : firstPayload.question.question_type === 'sql'
            ? { sql_answer: 'SELECT 1' }
            : { essay_answer: `${firstPayload.payload.essay_answer} changed` }
        const conflict = await api.fetch(`${API}/api/v1/sessions/${sid}/submit`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${learner}` },
          data: { question_id: firstPayload.question.question_id, ...changed },
        })
        expect(conflict.status()).toBe(409)
        expect((await conflict.json()).error.code).toBe('already_submitted')
        const after = await currentState(api, sid, learner)
        expect(after.answered_count).toBe(1)
      }
    }

    const finished = await finishViaUi(page)
    expect(finished).toBe(sid)
    await pollRelease(api, learner, sid, 'published', 60_000)
    const evidence = await json(api, `/api/v1/sessions/${sid}/evidence`, { token: learner })
    expect(evidence.items).toHaveLength(13)
    expect(evidence.items.every((item) => item.score !== null)).toBe(true)
    expect(evidence.items.filter((item) => item.question_type === 'sql')).toHaveLength(2)
    expect(evidence.items.filter((item) => item.question_type === 'essay')).toHaveLength(1)
    const record = (await json(api, '/api/v1/sessions', { token: learner })).find((row) => row.session_id === sid)
    expect(record.assembly_mode).toBe('FORMAL')
    expect(record.release_status).toBe('published')
    expect(Number(record.overall_result_pct)).toBe(100)
    await page.goto('/history')
    await expect(page.getByText(/Formal assessment/).first()).toBeVisible()
    await page.goto(`/history/${sid}`)
    await expect(page.getByRole('heading', { name: 'Assessment evidence', exact: true })).toBeVisible()
    const evidenceHelp = await openHelp(page)
    await expect(evidenceHelp.getByText('Assessment evidence', { exact: true })).toBeVisible()
    await page.keyboard.press('Escape')
    await page.goto('/competency')
    await expect(page.getByText('1 published assessment', { exact: true })).toBeVisible()
    await page.getByText('Scores and supporting evidence', { exact: true }).click()
    await expect(page.getByRole('table')).toBeVisible()
    await page.getByRole('table').getByRole('row').nth(1).getByRole('button').first().click()
    await expect(page.getByText('What does this mean?', { exact: true })).toBeVisible()
    await expect(page.getByText('Next step', { exact: true })).toBeVisible()
    await page.getByRole('searchbox', { name: 'Search concepts' }).fill('zzzz-no-concept')
    await expect(page.getByText('No concepts match these filters.', { exact: true })).toBeVisible()
    await expect(page.getByRole('table')).toHaveCount(0)
    await page.getByRole('searchbox', { name: 'Search concepts' }).fill('')
    await expect(page.getByRole('table')).toBeVisible()
    const cumulativeScan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()
    expect(cumulativeScan.violations.map(violation => violation.id)).toEqual([])
    const cumulative = await json(api, '/api/v1/sessions/competency/cumulative', { token: learner })
    expect(cumulative.summary.finalized_assessments).toBe(1)
    expect(cumulative.concepts.length).toBeGreaterThan(0)
    expect(cumulative.concepts.every((concept) => concept.contributing_sessions.includes(sid))).toBe(true)
    expect(sandboxChecked).toBe(true)
    expect(errors).toEqual([])
  } finally {
    await api.dispose()
  }
})

test('human verification: AI failure, retry, unauthorized access, adjusted review and publication', async ({ page, browser }) => {
  test.setTimeout(900_000)
  const api = await apiRequest.newContext({ baseURL: API, timeout: 60_000 })
  const adminContext = await browser.newContext()
  const adminPage = await adminContext.newPage()
  const errors = []
  page.on('pageerror', (error) => errors.push(error.message))
  adminPage.on('pageerror', (error) => errors.push(error.message))
  const unique = `ftu-human-${Date.now()}`
  const email = `${unique}@test.dev`
  let assessmentId
  try {
    const admin = await adminLogin(adminPage)
    const bankAssessment = await json(api, '/api/v1/admin/assessments/4', { token: admin })
    const concepts = bankAssessment.concepts.filter((c) => c.subject_area === 'SQL Querying')
    const created = await json(api, '/api/v1/admin/assessments', { token: admin, method: 'POST', data: {
      title: `${unique} HUMAN_VERIFIED`, description: 'Disposable acceptance assessment',
      result_release_policy: 'HUMAN_VERIFIED',
      concepts: concepts.map((c) => ({ concept_id: c.concept_id, min_difficulty: 1, max_difficulty: 5, target_pct: 60 })),
    } })
    assessmentId = created.assessment_id
    await json(api, `/api/v1/admin/assessments/${assessmentId}`, { token: admin, method: 'PATCH', data: { status: 'published' } })

    await registerViaApi(api, email, 'Human verification learner')
    const learner = await login(page, email)
    const started = await startViaUi(page, { assessmentId, area: 'SQL Querying', difficulty: 'MEDIUM', mode: 'FORMAL' })
    expect(started.status()).toBe(201)
    const sid = (await started.json()).session_id
    await expect(page).toHaveURL(new RegExp(`/exam/${sid}$`))
    const plan = await json(api, `/__test/sessions/${sid}/assembly`, { token: learner })
    expect(plan.type_mix).toEqual({ mcq: 10, sql: 2, essay: 1 })

    const seen = new Set()
    for (let i = 0; i < 13; i++) {
      const state = await currentState(api, sid, learner)
      const q = state.current_question
      expect(q, `question ${i + 1}`).toBeTruthy()
      expect(seen.has(q.question_id)).toBe(false)
      seen.add(q.question_id)
      await expect(page.getByText(q.prompt, { exact: true })).toBeVisible()
      const key = await questionKey(api, admin, q.question_id)
      await fillAnswer(page, q, key, { essaySuffix: q.question_type === 'essay' ? '\n[[AI_FAIL_2]]' : '' })
      const result = await submitViaUi(page, sid)
      expect(result.state.answered_count).toBe(i + 1)
      if (q.question_type === 'essay') expect(result.answer.score).toBeNull()
    }

    const finished = await finishViaUi(page)
    expect(finished).toBe(sid)
    await pollRelease(api, learner, sid, 'auto_grading')
    await expect(page.getByRole('heading', { name: 'We’re grading your assessment', exact: true })).toBeVisible()

    // One bounded provider retry reaches a terminal failure without a live provider.
    await json(api, '/__test/grading-jobs/drain?max_attempts=1&include_essay=true', { token: admin, method: 'POST' })
    await pollRelease(api, learner, sid, 'grading_failed')
    await page.goto(`/history/${sid}`)
    await expect(page.getByRole('heading', { name: 'Your submission needs grading attention', exact: true })).toBeVisible()

    // Learners cannot reach administrator grading or mutate this session.
    await page.goto('/admin/grading')
    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(page.getByRole('heading', { name: 'My competency', exact: true })).toBeVisible()
    const forbiddenDetail = await api.fetch(`${API}/api/v1/admin/grading-reviews/${sid}`, { headers: { Authorization: `Bearer ${learner}` } })
    expect(forbiddenDetail.status()).toBe(403)
    const forbiddenPublish = await api.fetch(`${API}/api/v1/admin/grading-reviews/${sid}/publish`, {
      method: 'POST', headers: { Authorization: `Bearer ${learner}` }, data: { revision: 0 },
    })
    expect(forbiddenPublish.status()).toBe(403)
    const outsiderEmail = `${unique}-outsider@test.dev`
    await registerViaApi(api, outsiderEmail, 'Unrelated learner')
    const outsider = await tokenViaApi(api, outsiderEmail)
    expect((await api.fetch(`${API}/api/v1/sessions/${sid}/evidence`, { headers: { Authorization: `Bearer ${outsider}` } })).status()).toBe(404)

    await adminPage.goto('/admin')
    await expect(adminPage.getByRole('heading', { name: 'Cohort Overview', exact: true })).toBeVisible()
    const adminHelp = await openHelp(adminPage)
    await expect(adminHelp.getByText('Administration', { exact: true })).toBeVisible()
    await adminPage.keyboard.press('Escape')
    await adminPage.goto('/admin/grading')
    const queueRow = adminPage.getByRole('button', { name: new RegExp(`${unique} HUMAN_VERIFIED`) })
    await expect(queueRow).toBeVisible()
    await queueRow.click()
    await expect(adminPage.getByRole('button', { name: 'Publish verified results' })).toBeDisabled()
    const retried = adminPage.waitForResponse((r) => r.request().method() === 'POST' && r.url().endsWith(`/grading-reviews/${sid}/retry`))
    await adminPage.getByRole('button', { name: 'Retry failed grading' }).click()
    expect((await retried).status()).toBe(200)
    await expect(adminPage.getByRole('status')).toHaveText('Grading in progress')
    await json(api, '/__test/grading-jobs/drain?max_attempts=3&include_essay=true', { token: admin, method: 'POST' })
    await pollRelease(api, learner, sid, 'pending_review', 60_000)

    await page.goto(`/history/${sid}`)
    await expect(page.getByRole('heading', { name: 'Your submission is received', exact: true })).toBeVisible()
    let evidenceAborted = false
    const evidenceRoute = async (route) => {
      if (!evidenceAborted) {
        evidenceAborted = true
        await route.abort('failed')
      } else {
        await route.continue()
      }
    }
    await page.route(`**/api/v1/sessions/${sid}/evidence*`, evidenceRoute)
    await page.getByRole('button', { name: 'Refresh status' }).click()
    await expect(page.getByText('We couldn’t check the latest status just now. Your submission is still recorded; please try again.', { exact: true })).toBeVisible()
    await page.getByRole('button', { name: 'Refresh status' }).click()
    await expect(page.getByRole('heading', { name: 'Your submission is received', exact: true })).toBeVisible()
    await page.unroute(`**/api/v1/sessions/${sid}/evidence*`, evidenceRoute)

    const refresh = adminPage.getByRole('button', { name: 'Refresh results', exact: true })
    await refresh.click()
    await expect(adminPage.getByRole('status')).toHaveText('Awaiting human verification')
    const review = await json(api, `/api/v1/admin/grading-reviews/${sid}`, { token: admin })
    const required = review.items.filter((item) => ['sql', 'essay'].includes(item.question_type))
    expect(required).toHaveLength(3)
    const essayItem = required.find((item) => item.question_type === 'essay')
    expect(essayItem.automated_score).not.toBeNull()
    for (const item of required) {
      const card = adminPage.getByRole('heading', { name: item.prompt, exact: true }).locator('..')
      await expect(card).toBeVisible()
      if (item.question_type === 'essay') {
        await card.getByLabel('Approved score', { exact: true }).fill('2.5')
        await card.getByLabel('Grader comments', { exact: true }).fill('Adjusted against the rubric during browser verification')
      } else {
        await card.getByLabel('Grader comments', { exact: true }).fill('Executable SQL evidence verified')
      }
      const approved = adminPage.waitForResponse((r) => r.request().method() === 'POST' && r.url().endsWith(`/attempts/${item.attempt_id}`))
      await card.getByRole('button', { name: 'Approve score', exact: true }).click()
      expect((await approved).status()).toBe(200)
    }
    await expect(adminPage.getByRole('button', { name: 'Publish verified results' })).toBeEnabled()
    await expect(adminPage.getByRole('status')).toHaveText('Verified — ready to publish')
    const help = await openHelp(adminPage)
    await expect(help.getByText('Grading review', { exact: true })).toBeVisible()
    await adminPage.keyboard.press('Escape')
    const published = adminPage.waitForResponse((r) => r.request().method() === 'POST' && r.url().endsWith(`/grading-reviews/${sid}/publish`))
    await adminPage.getByRole('button', { name: 'Publish verified results' }).click()
    const publication = await published
    expect(publication.status()).toBe(200)
    const detail = await publication.json()
    expect(detail.release_status).toBe('published')
    const publishedEvent = detail.events.find((event) => event.new_status === 'published')
    expect(publishedEvent.previous_status).toBe('reviewed')
    expect(publishedEvent.reviewer_id).toBeTruthy()
    expect(detail.events.some((event) => event.new_status === 'reviewed')).toBe(true)
    expect(detail.events.some((event) => event.new_status === 'grading_failed')).toBe(true)

    await page.goto(`/history/${sid}`)
    await expect(page.getByRole('heading', { name: 'Assessment evidence', exact: true })).toBeVisible()
    await expect(page.getByText('2.50 / 5.00 pts', { exact: true })).toBeVisible()
    await expect(page.getByText('Adjusted against the rubric during browser verification', { exact: true })).toBeVisible()
    const evidence = await json(api, `/api/v1/sessions/${sid}/evidence`, { token: learner })
    const essay = evidence.items.find((item) => item.question_type === 'essay')
    expect(Number(essay.score)).toBe(2.5)
    expect(essay.grading_detail.grader).toBe('human_verified')
    expect(essay.grading_detail.reviewer_comments).toContain('Adjusted against the rubric')
    const record = (await json(api, '/api/v1/sessions', { token: learner })).find((row) => row.session_id === sid)
    expect(record.release_status).toBe('published')
    expect(Number(record.overall_result_pct)).toBeLessThan(100)
    await page.goto('/competency')
    await expect(page.getByText('1 published assessment', { exact: true })).toBeVisible()
    await page.getByText('Scores and supporting evidence', { exact: true }).click()
    await expect(page.getByRole('table')).toBeVisible()
    await page.getByRole('table').getByRole('row').nth(1).getByRole('button').first().click()
    await expect(page.getByText('What does this mean?', { exact: true })).toBeVisible()
    await expect(page.getByText('Next step', { exact: true })).toBeVisible()
    await page.getByRole('searchbox', { name: 'Search concepts' }).fill('zzzz-no-concept')
    await expect(page.getByText('No concepts match these filters.', { exact: true })).toBeVisible()
    await expect(page.getByRole('table')).toHaveCount(0)
    await page.getByRole('searchbox', { name: 'Search concepts' }).fill('')
    await expect(page.getByRole('table')).toBeVisible()
    const cumulativeScan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()
    expect(cumulativeScan.violations.map(violation => violation.id)).toEqual([])
    const cumulative = await json(api, '/api/v1/sessions/competency/cumulative', { token: learner })
    expect(cumulative.summary.finalized_assessments).toBe(1)
    expect(cumulative.concepts.length).toBeGreaterThan(0)
    expect(errors).toEqual([])
  } finally {
    if (assessmentId) {
      const admin = await adminToken(api)
      await api.patch(`${API}/api/v1/admin/assessments/${assessmentId}`, {
        headers: { Authorization: `Bearer ${admin}` }, data: { status: 'closed' },
      })
    }
    await adminContext.close()
    await api.dispose()
  }
})
