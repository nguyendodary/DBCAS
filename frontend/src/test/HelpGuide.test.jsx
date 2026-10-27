import { act, fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { HelpButton, HelpGuide, HelpProvider } from '../components/HelpGuide'
import { i18n, setLocale } from '../i18n'

const authState = vi.hoisted(() => ({ account: null }))
vi.mock('../auth', () => ({ useAuth: () => ({ account: authState.account }) }))

beforeEach(async () => {
  localStorage.clear()
  authState.account = { roles: ['Learner'] }
  await i18n.changeLanguage('en')
  Element.prototype.scrollIntoView = vi.fn()
})

afterEach(() => {
  document.body.style.overflow = ''
})

function renderHelp(path = '/dashboard', account = { roles: ['Learner'] }) {
  authState.account = account
  return render(
    <MemoryRouter initialEntries={[path]}>
      <HelpProvider>
        <main>Workspace content</main>
        <HelpButton />
        <HelpButton />
      </HelpProvider>
    </MemoryRouter>,
  )
}

it('explains optional adaptive practice and controlled source-grounded drafts', async () => {
  renderHelp('/admin/candidates', { roles: ['Administrator'] })
  await userEvent.click(screen.getAllByRole('button', { name: 'Help' })[0])
  const dialog = screen.getByRole('dialog')
  expect(within(dialog).getByRole('heading', { name: 'Optional adaptive practice' })).toBeInTheDocument()
  expect(dialog).toHaveTextContent('At 80% or above')
  expect(dialog).toHaveTextContent('Drafts never enter assessment assembly automatically')
})

it('stays closed until the compact trigger is used and never auto-opens', async () => {
  const { container } = renderHelp()
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  const triggers = screen.getAllByRole('button', { name: 'Help' })
  expect(triggers).toHaveLength(2)
  expect(triggers[0]).toHaveAttribute('aria-haspopup', 'dialog')
  await userEvent.click(triggers[0])
  const dialogs = screen.getAllByRole('dialog', { name: 'How to use DBCAS' })
  expect(dialogs).toHaveLength(1)
  expect(dialogs[0]).toHaveAccessibleDescription('A quick guide to assessments, grading states and your account.')
  expect(container).toHaveAttribute('inert')
  expect(container).toHaveAttribute('aria-hidden', 'true')
  expect(document.body.style.overflow).toBe('hidden')
  expect(within(dialogs[0]).getByRole('button', { name: 'Close help' })).toHaveFocus()
})

it('closes with Escape, the close button and backdrop while restoring focus and page state', async () => {
  const { container } = renderHelp()
  const trigger = screen.getAllByRole('button', { name: 'Help' })[0]
  await userEvent.click(trigger)
  await userEvent.keyboard('{Escape}')
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(container).not.toHaveAttribute('inert')
  expect(container).not.toHaveAttribute('aria-hidden')
  expect(document.body.style.overflow).not.toBe('hidden')
  expect(trigger).toHaveFocus()

  await userEvent.click(trigger)
  await userEvent.click(screen.getByRole('button', { name: 'Close help' }))
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(trigger).toHaveFocus()

  await userEvent.click(trigger)
  fireEvent.mouseDown(document.querySelector('.help-backdrop'))
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
})

it('traps Tab and Shift+Tab inside the drawer and focuses section headings from the index', async () => {
  renderHelp()
  await userEvent.click(screen.getAllByRole('button', { name: 'Help' })[0])
  const dialog = screen.getByRole('dialog')
  const nav = within(dialog).getByRole('navigation', { name: 'Guide sections' })
  const jumps = within(nav).getAllByRole('button')
  await userEvent.keyboard('{Shift>}{Tab}{/Shift}')
  expect(jumps.at(-1)).toHaveFocus()
  await userEvent.keyboard('{Tab}')
  expect(within(dialog).getByRole('button', { name: 'Close help' })).toHaveFocus()
  await userEvent.click(within(nav).getByRole('button', { name: 'SQL sandbox' }))
  expect(within(dialog).getByRole('heading', { name: 'SQL sandbox' })).toHaveFocus()
  expect(Element.prototype.scrollIntoView).toHaveBeenCalled()
})

it('restores the invoking trigger when pointer activation does not focus the button', () => {
  renderHelp()
  const trigger = screen.getAllByRole('button', { name: 'Help' })[1]
  expect(trigger).not.toHaveFocus()
  // WebKit pointer activation and programmatic click do not focus a button.
  fireEvent.click(trigger)
  expect(screen.getByRole('button', { name: 'Close help' })).toHaveFocus()
  fireEvent.keyDown(document, { key: 'Escape' })
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(trigger).toHaveFocus()
})

it('shows route-aware guidance for the current workspace', async () => {
  const cases = [
    ['/assessments', 'Starting an assessment'],
    ['/exam/42', 'During an assessment'],
    ['/history', 'Your assessment history'],
    ['/history/42', 'Assessment evidence'],
    ['/competency', 'Cumulative competency'],
    ['/admin/grading/8', 'Grading review'],
    ['/admin/questions', 'Question bank'],
    ['/dashboard', 'Your dashboard'],
  ]
  for (const [path, heading] of cases) {
    const { unmount } = renderHelp(path, { roles: ['Learner', 'Administrator'] })
    await userEvent.click(screen.getAllByRole('button', { name: 'Help' })[0])
    expect(screen.getByText(heading)).toBeVisible()
    unmount()
  }
})

it('shows role-specific guidance without exposing the other role guide', async () => {
  const { unmount } = renderHelp('/dashboard', { roles: ['Learner'] })
  await userEvent.click(screen.getAllByRole('button', { name: 'Help' })[0])
  expect(screen.getByRole('heading', { name: 'Learner guide' })).toBeVisible()
  expect(screen.queryByRole('heading', { name: 'Administrator guide' })).not.toBeInTheDocument()
  expect(screen.getAllByRole('button', { name: 'Learner guide' })).toHaveLength(1)
  unmount()

  renderHelp('/admin', { roles: ['Administrator'] })
  await userEvent.click(screen.getAllByRole('button', { name: 'Help' })[0])
  expect(screen.getByRole('heading', { name: 'Administrator guide' })).toBeVisible()
  expect(screen.queryByRole('heading', { name: 'Learner guide' })).not.toBeInTheDocument()
})

it('switches all guide content to Vietnamese and keeps both locales complete', async () => {
  renderHelp()
  const trigger = screen.getAllByRole('button', { name: 'Help' })[0]
  await userEvent.click(trigger)
  expect(screen.getByRole('heading', { name: 'How to use DBCAS' })).toBeVisible()
  await act(async () => { await setLocale('vi') })
  expect(screen.getByRole('dialog', { name: 'Cách sử dụng DBCAS' })).toBeVisible()
  expect(screen.getByRole('button', { name: 'Đóng hướng dẫn' })).toBeVisible()
  const nav = screen.getByRole('navigation', { name: 'Các mục hướng dẫn' })
  expect(within(nav).getByRole('button', { name: 'Sandbox SQL' })).toBeVisible()
  expect(within(nav).getByRole('button', { name: 'Luyện tập và chính thức' })).toBeVisible()
  expect(screen.getByRole('heading', { name: 'Cách sử dụng DBCAS' })).toBeVisible()
  await act(async () => { await setLocale('en') })
  expect(screen.getByRole('dialog', { name: 'How to use DBCAS' })).toBeVisible()
})

it('supports rendering the drawer directly, including no auth context', async () => {
  authState.account = null
  const onClose = vi.fn()
  render(<MemoryRouter><HelpGuide open onClose={onClose} /></MemoryRouter>)
  const dialog = screen.getByRole('dialog')
  expect(within(dialog).getByRole('heading', { name: 'Learner guide' })).toBeVisible()
  expect(within(dialog).getByRole('heading', { name: 'Administrator guide' })).toBeVisible()
  await userEvent.keyboard('{Escape}')
  expect(onClose).toHaveBeenCalledTimes(1)
})
