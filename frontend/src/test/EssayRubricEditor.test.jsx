import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { vi } from 'vitest'
import EssayRubricEditor, { rubricRows } from '../components/EssayRubricEditor'

it.each([0.03, 0.5, 1, 2, 10])('covers every cent without gaps or overlap for %s points', points => {
  const rows = rubricRows('[]', points)
  expect(rows).toHaveLength(4)
  expect(rows[0].min_score).toBe(0)
  expect(rows[3].max_score).toBe(points)
  rows.forEach((row, i) => {
    expect(row.max_score).toBeGreaterThanOrEqual(row.min_score)
    if (i) expect(Math.round(row.min_score * 100)).toBe(Math.round(rows[i - 1].max_score * 100) + 1)
  })
})

it('preserves saved custom ranges and criteria, and retains criteria when redistributing points', () => {
  const saved = rubricRows('[]', 1).map((row, i) => ({ ...row, criteria: `Criterion ${i}` }))
  saved[0].max_score = 0.19
  saved[1].min_score = 0.2
  expect(rubricRows(JSON.stringify(saved), 1)).toEqual(saved)
  const changed = rubricRows(JSON.stringify(saved), 2, true)
  expect(changed.map(row => row.criteria)).toEqual(saved.map(row => row.criteria))
  expect(changed[3].max_score).toBe(2)
})

it('lets an administrator enter criteria in four ordinary text fields', async () => {
  const changed = vi.fn()
  function Harness() {
    const [value, setValue] = useState('[]')
    return <EssayRubricEditor value={value} points="1" onChange={next => { setValue(next); changed(next) }} />
  }
  render(<Harness />)
  const fields = screen.getAllByRole('textbox')
  expect(fields).toHaveLength(4)
  expect(fields.every(field => field.required && field.value === '')).toBe(true)
  await userEvent.type(fields[0], 'Incorrect explanation')
  await userEvent.type(fields[3], 'Correct explanation with examples')
  const saved = JSON.parse(changed.mock.lastCall[0])
  expect(saved[0].criteria).toBe('Incorrect explanation')
  expect(saved[3].criteria).toBe('Correct explanation with examples')
  expect(saved[3].level_name).toBe('Complete')
})
