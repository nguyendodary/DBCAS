import { useState } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import SqlDatasetsEditor from '../components/SqlDatasetsEditor'

vi.mock('../components/SqlTableBuilder', () => ({ default: ({ value, onChange }) => <textarea aria-label="Table setup" value={value} onChange={event => onChange(event.target.value)} /> }))

function Editor({ initial, changed }) {
  const [value, setValue] = useState(JSON.stringify(initial))
  return <SqlDatasetsEditor value={value} onChange={next => { setValue(next); changed(JSON.parse(next)) }} />
}

it('hides scenario inputs and edge flags while preserving existing data', async () => {
  const changed = vi.fn()
  render(<Editor initial={[{ dataset_name: 'existing name', is_edge_case: true, setup_sql: 'SELECT 1;', expected_result: { columns: ['id'], rows: [[1]] } }]} changed={changed} />)
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
  expect(screen.getAllByRole('textbox')).toHaveLength(1)
  await userEvent.type(screen.getByRole('textbox', { name: 'Table setup' }), ' ')
  const updated = changed.mock.lastCall[0][0]
  expect(updated.dataset_name).toBe('existing name')
  expect(updated.is_edge_case).toBe(true)
  expect(updated.expected_result).not.toHaveProperty('rows')
})

it('assigns unique dataset names automatically without asking the admin', async () => {
  const changed = vi.fn()
  render(<Editor initial={[{ dataset_name: 'dataset_2', setup_sql: '', expected_result: {}, is_edge_case: false }]} changed={changed} />)
  await userEvent.click(screen.getByRole('button', { name: '+ Add dataset (optional)' }))
  const datasets = changed.mock.lastCall[0]
  expect(datasets.map(dataset => dataset.dataset_name)).toEqual(['dataset_2', 'dataset_3'])
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
})
