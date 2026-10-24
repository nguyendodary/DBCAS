import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import api from '../api'
import AdminCurriculumPage from '../pages/admin/AdminCurriculumPage'

vi.mock('../api', () => ({
  default: { get: vi.fn(), put: vi.fn(), patch: vi.fn(), post: vi.fn(), delete: vi.fn() },
  apiMessage: (e) => e.message,
}))
const concept = { concept_id: 2, concept_code: 'SQL-JOIN', concept_name: 'Joins', subject_area: 'SQL Querying', difficulty_level: 2, description: 'Combine tables' }
const clo = { clo_id: 4, clo_code: 'CLO2', title: 'Write joins', description: 'Use relational queries', concepts: [
  { concept_id: 2, concept_code: 'SQL-JOIN', concept_name: 'Joins', status: 'confirmed', mapping_source: 'admin' },
  { concept_id: 3, concept_code: 'SQL-GROUP', concept_name: 'Grouping', status: 'pending', mapping_source: 'ai' },
] }
beforeEach(() => {
  vi.resetAllMocks()
  api.get.mockImplementation((url) => Promise.resolve({ data: url === '/admin/concepts' ? [{ ...concept, concept_id: 1, concept_code: 'SQL-SELECT', concept_name: 'Projection' }, concept, { ...concept, concept_id: 3, concept_code: 'SQL-GROUP', concept_name: 'Grouping' }] : url === '/admin/clos' ? [clo] : { nodes: [{ concept_id: 2, prerequisites: [1] }] } }))
  api.put.mockResolvedValue({ data: {} })
  api.patch.mockResolvedValue({ data: {} })
})

async function openPrerequisites() {
  await userEvent.click(await screen.findByRole('button', { name: 'Prerequisites' }))
  await userEvent.click(screen.getByText('Prerequisites for SQL-JOIN', { selector: 'summary' }))
  const group = screen.getByRole('group', { name: 'Prerequisites for SQL-JOIN' })
  return { group, row: group.closest('li') }
}

it('loads named prerequisites and CLO values and preserves untouched saves', async () => {
  render(<AdminCurriculumPage />)
  const { group, row } = await openPrerequisites()
  expect(within(group).getByRole('checkbox', { name: 'Projection (SQL-SELECT)' })).toBeChecked()
  expect(within(group).queryByRole('checkbox', { name: 'Joins (SQL-JOIN)' })).not.toBeInTheDocument()
  await userEvent.click(within(row).getByRole('button', { name: 'Save', exact: true }))
  await waitFor(() => expect(api.put).toHaveBeenCalledWith('/admin/concepts/2/prerequisites', { prerequisite_concept_ids: [1] }))
  await userEvent.click(await screen.findByRole('button', { name: /Learning outcomes/ }))
  await userEvent.click(screen.getByText('Confirmed concepts for CLO2', { selector: 'summary' }))
  const mapping = screen.getByRole('group', { name: 'Confirmed concepts for CLO2' })
  expect(within(mapping).getByRole('checkbox', { name: 'Joins (SQL-JOIN)' })).toBeChecked()
  expect(within(mapping).queryByRole('checkbox', { name: 'Grouping (SQL-GROUP)' })).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Save set' }))
  await waitFor(() => expect(api.put).toHaveBeenCalledWith('/admin/clos/4/concepts', { concept_ids: [2] }))
})

it('adds and removes prerequisites by name without numeric input', async () => {
  render(<AdminCurriculumPage />)
  const { group, row } = await openPrerequisites()
  await userEvent.click(within(group).getByRole('checkbox', { name: 'Grouping (SQL-GROUP)' }))
  await userEvent.click(within(row).getByRole('button', { name: 'Save', exact: true }))
  await waitFor(() => expect(api.put).toHaveBeenCalledWith('/admin/concepts/2/prerequisites', { prerequisite_concept_ids: [1, 3] }))
  await userEvent.click(within(group).getByRole('checkbox', { name: 'Projection (SQL-SELECT)' }))
  await userEvent.click(within(row).getByRole('button', { name: 'Save', exact: true }))
  await waitFor(() => expect(api.put).toHaveBeenCalledWith('/admin/concepts/2/prerequisites', { prerequisite_concept_ids: [] }))
})

it('surfaces a cycle rejection without losing named selections', async () => {
  render(<AdminCurriculumPage />)
  const { group, row } = await openPrerequisites()
  await userEvent.click(within(group).getByRole('checkbox', { name: 'Grouping (SQL-GROUP)' }))
  api.put.mockRejectedValueOnce(new Error('This prerequisite would create a dependency cycle'))
  await userEvent.click(within(row).getByRole('button', { name: 'Save', exact: true }))
  expect(await screen.findByRole('alert')).toHaveTextContent('dependency cycle')
  expect(within(group).getByRole('checkbox', { name: 'Grouping (SQL-GROUP)' })).toBeChecked()
})

it('edits a concept with loaded values while keeping its code stable', async () => {
  render(<AdminCurriculumPage />)
  const row = (await screen.findByText('Joins', { exact: true })).closest('li')
  await userEvent.click(within(row).getByRole('button', { name: 'Edit' }))
  await userEvent.click(screen.getByText('Reference code (optional)', { exact: true }))
  expect(screen.getByRole('textbox', { name: 'Concept code' })).toBeDisabled()
  const name = screen.getByRole('textbox', { name: 'Concept name' })
  expect(name).toHaveValue('Joins')
  await userEvent.clear(name)
  await userEvent.type(name, 'Relational joins')
  await userEvent.click(screen.getByRole('button', { name: 'Save concept' }))
  await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/admin/concepts/2', { concept_name: 'Relational joins', subject_area: 'SQL Querying', description: 'Combine tables', difficulty_level: 2 }))
})

it('edits a CLO without implicitly approving pending mappings', async () => {
  render(<AdminCurriculumPage />)
  await userEvent.click(await screen.findByRole('button', { name: /Learning outcomes/ }))
  const row = (await screen.findByText('CLO2 — Write joins')).closest('li')
  await userEvent.click(within(row).getByRole('button', { name: 'Edit' }))
  expect(screen.getByRole('textbox', { name: 'CLO title' })).toHaveValue('Write joins')
  await userEvent.click(screen.getByRole('button', { name: 'Save CLO' }))
  await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/admin/clos/4', { title: 'Write joins', description: 'Use relational queries' }))
  expect(api.post).not.toHaveBeenCalled()
  expect(await screen.findByText('Pending')).toBeInTheDocument()
})
