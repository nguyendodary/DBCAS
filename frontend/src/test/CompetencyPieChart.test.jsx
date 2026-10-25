import { render, screen, fireEvent } from '@testing-library/react'
import { expect, it } from 'vitest'
import CompetencyPieChart from '../components/CompetencyPieChart'

it('only shows actual data without a preview control', () => {
  const { container } = render(<CompetencyPieChart concepts={[
    { concept_id: 1, concept_name: 'Original concept', competency_pct: 83, target_pct: 70 },
  ]} />)
  expect(screen.queryByRole('button', { name: 'Preview 20 concepts' })).not.toBeInTheDocument()
  expect(screen.getByRole('img')).toHaveAccessibleName('Original concept: 83%')
  expect(container.querySelectorAll('.reference-concept-legend li')).toHaveLength(1)
})

it('shows one slice per concept and preserves the original scores', () => {
  const { container } = render(<CompetencyPieChart concepts={[
    { concept_id: 1, concept_name: 'SELECT', competency_pct: 83, target_pct: 70, below_target: false },
    { concept_id: 2, concept_name: 'JOIN', competency_pct: 47, target_pct: 80, below_target: true },
    { concept_id: 3, concept_name: 'WHERE', competency_pct: 65, target_pct: null },
  ]} />)
  expect(container.querySelectorAll('.reference-slice path')).toHaveLength(3)
  expect(container.querySelectorAll('.reference-concept-legend strong')[0]).toHaveTextContent('83%')
  expect(container.querySelectorAll('.reference-concept-legend strong')[1]).toHaveTextContent('47%')
  expect(container.querySelectorAll('.reference-concept-legend strong')[2]).toHaveTextContent('65%')
  expect(screen.getByRole('img')).toHaveAccessibleName(/3/)
})

it.each([0, 100])('renders a single group without a degenerate arc at score %s', value => {
  const { container } = render(<CompetencyPieChart concepts={[
    { concept_id: 1, concept_name: 'SELECT', competency_pct: value, target_pct: 70, below_target: value < 70 },
  ]} />)
  expect(container.querySelectorAll('.reference-slice circle')).toHaveLength(value === 100 ? 1 : 0)
  expect(container.querySelectorAll('.reference-slice path')).toHaveLength(0)
  expect(container.querySelector('.reference-concept-legend strong')).toHaveTextContent(`${value}%`)
})

it('does not draw invented segments without assessed concepts', () => {
  render(<CompetencyPieChart concepts={[]} />)
  expect(screen.queryByRole('img')).not.toBeInTheDocument()
})

it('highlights and separates the matching slice when hovering a concept', () => {
  const { container } = render(<CompetencyPieChart concepts={[
    { concept_id: 1, concept_name: 'SELECT', competency_pct: 83, target_pct: 70 },
    { concept_id: 2, concept_name: 'JOIN', competency_pct: 47, target_pct: 80 },
  ]} />)
  expect(container.querySelector('.reference-slice-percent')).toBeNull()
  const choice = screen.getByRole('button', { name: /JOIN/ })
  fireEvent.mouseEnter(choice)
  const slices = container.querySelectorAll('.reference-slice')
  expect(slices[1]).toHaveClass('is-active')
  expect(slices[1].style.transform).not.toBe('translate(0px, 0px)')
  expect(slices[0].style.opacity).toBe('0.3')
  expect(container.querySelector('.reference-active-value')).toHaveTextContent('JOIN47%')
  fireEvent.mouseLeave(choice)
  expect(slices[1]).not.toHaveClass('is-active')
})
