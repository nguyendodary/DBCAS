import { expect, test } from '@playwright/test'
import { register, vi } from './practice-harness'

const QUESTION = (seq) => ({
  seq_no: seq,
  question_id: 100 + seq,
  question_type: 'mcq',
  content_locale: 'en',
  prompt: `Question ${seq}`,
  options: [
    { option_id: seq * 10, option_label: 'A', option_text: 'First option' },
    { option_id: seq * 10 + 1, option_label: 'B', option_text: 'Second option' },
  ],
  draft: null,
  draft_revision: 0,
  answered: false,
  flagged: false,
  flag_revision: 0,
  first_opened_at: null,
})

// The FIXED endpoints are additive and the local demo stack may predate them.
// Mocking them at the route level keeps this spec deterministic (no bank
// seeding, no sleeps) while exercising the real browser UI end to end.
async function mockFixedPaper(page, sid, { expired = false } = {}) {
  const now = new Date(expired ? Date.now() - 60_000 : Date.now()).toISOString()
  const end = new Date(expired ? Date.now() - 60_000 : Date.now() + 1_800_000).toISOString()
  const drafts = new Map()
  const flags = new Map()
  let lastOpened = 1
  let submits = 0

  const meta = () => ({
    session_id: sid,
    runner_mode: 'fixed',
    status: 'in_progress',
    assessment_title: 'Free navigation paper',
    started_at: now,
    expires_at: end,
    server_now: now,
    remaining_seconds: expired ? 0 : 1800,
    question_count: 3,
    answered_count: drafts.size,
    flagged_count: [...flags.values()].filter(Boolean).length,
    last_opened_seq: lastOpened,
    questions: [1, 2, 3].map((seq) => ({
      seq_no: seq,
      question_id: 100 + seq,
      question_type: 'mcq',
      answered: drafts.has(seq),
      flagged: Boolean(flags.get(seq)),
      opened: seq <= lastOpened,
      draft_revision: 0,
    })),
  })
  const json = (body) => ({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })

  await page.route('**/api/v1/sessions/**', async (route) => {
    const url = new URL(route.request().url())
    const path = url.pathname
    if (path === `/api/v1/sessions/${sid}`) {
      await route.fulfill(
        json({
          session_id: sid,
          assessment_id: null,
          assessment_title: 'Free navigation paper',
          status: 'in_progress',
          runner_mode: 'fixed',
          locale: 'en',
          server_now: now,
          expires_at: end,
          remaining_seconds: expired ? 0 : 1800,
          current_question: null,
        }),
      )
      return
    }
    if (path === `/api/v1/sessions/${sid}/paper`) {
      await route.fulfill(json(meta()))
      return
    }
    if (path === `/api/v1/sessions/${sid}/paper/submit`) {
      submits += 1
      await route.fulfill(
        json({
          status: 'completed',
          submitted_at: now,
          answered_count: drafts.size,
          unanswered_count: 3 - drafts.size,
          flagged_count: [...flags.values()].filter(Boolean).length,
          final: true,
          next: `/evaluations/${sid}`,
        }),
      )
      return
    }
    const draftMatch = /^\/api\/v1\/sessions\/\d+\/paper\/(\d+)\/draft$/.exec(path)
    if (draftMatch && route.request().method() === 'PUT') {
      const seq = Number(draftMatch[1])
      const body = route.request().postDataJSON()
      const answer = body.selected_option_id ? { selected_option_id: body.selected_option_id } : {}
      drafts.set(seq, answer)
      await route.fulfill(
        json({ seq_no: seq, revision: body.revision, saved_at: now, answered: true }),
      )
      return
    }
    const flagMatch = /^\/api\/v1\/sessions\/\d+\/paper\/(\d+)\/flag$/.exec(path)
    if (flagMatch && route.request().method() === 'PUT') {
      const seq = Number(flagMatch[1])
      const body = route.request().postDataJSON()
      flags.set(seq, body.flagged)
      await route.fulfill(json({ seq_no: seq, flagged: body.flagged, revision: body.revision + 1 }))
      return
    }
    const questionMatch = /^\/api\/v1\/sessions\/\d+\/paper\/(\d+)$/.exec(path)
    if (questionMatch) {
      const seq = Number(questionMatch[1])
      lastOpened = seq
      const base = QUESTION(seq)
      await route.fulfill(
        json({
          ...base,
          draft: drafts.get(seq) ?? null,
          draft_revision: drafts.has(seq) ? 1 : 0,
          answered: drafts.has(seq),
          flagged: Boolean(flags.get(seq)),
          flag_revision: flags.has(seq) ? 1 : 0,
          first_opened_at: now,
          remaining_seconds: expired ? 0 : 1800,
          server_now: now,
        }),
      )
      return
    }
    await route.continue()
  })
  return () => submits
}

test.describe('FIXED free navigation', () => {
  test('jumps, flags, autosaves, resumes and submits once', async ({ page }) => {
    await register(page)
    const sid = 424242
    await mockFixedPaper(page, sid)

    await page.goto(`/exam/${sid}`)
    const palette = page.locator('.ex-question-grid button')
    await expect(palette).toHaveCount(3)
    await expect(palette.first()).toHaveAttribute('aria-current', 'step')

    // Free navigation: every question is open, including ones never served.
    await palette.nth(2).click()
    await expect(page.locator('.question-top h2')).toHaveText(/3\/3/)
    await palette.first().click()
    await expect(page.locator('.question-top h2')).toHaveText(/1\/3/)

    // Flag for review with its own revision, and confirm the palette state.
    await page.getByRole('button', { name: vi.paper.flag, exact: true }).click()
    await expect(palette.first()).toHaveAttribute(
      'aria-label',
      vi.paper.paletteLabel
        .replace('{{number}}', '1')
        .replace(
          '{{state}}',
          `${vi.paper.stateCurrent}, ${vi.paper.stateUnanswered}, ${vi.paper.stateFlagged}`,
        ),
    )

    // Answer and wait for the debounced server save.
    await page.locator('.answer-option input').first().check()
    await expect(page.getByText(vi.paper.draftSaved, { exact: true })).toBeVisible()

    // Reload resumes the last opened question with its saved answer and flag.
    await page.reload()
    await expect(page.locator('.answer-option input').first()).toBeChecked()
    await expect(page.getByRole('button', { name: vi.paper.unflag, exact: true })).toBeVisible()

    // Final submit shows the answer/flag counts and opens the result page once.
    await page.getByRole('button', { name: vi.paper.finish, exact: true }).click()
    const dialog = page.getByRole('dialog')
    await expect(dialog).toContainText(vi.paper.finishTitle)
    await dialog.getByRole('button', { name: vi.paper.confirm, exact: true }).click()
    await expect(page).toHaveURL(/\/evaluations\/\d+$/)
  })

  test('finalizes automatically when the server clock has expired', async ({ page }) => {
    await register(page)
    const sid = 424243
    const submits = await mockFixedPaper(page, sid, { expired: true })
    await page.goto(`/exam/${sid}`)
    await expect(page).toHaveURL(/\/evaluations\/\d+$/)
    expect(submits()).toBe(1)
  })
})
