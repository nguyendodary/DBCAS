import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import api from '../api'
import AdminAccountsPage from '../pages/admin/AdminAccountsPage'
import AdminCandidatesPage from '../pages/admin/AdminCandidatesPage'

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
  apiMessage: (e, fb) => e?.response?.data?.error?.message || e?.message || fb,
}))

const renderPage = (el) => render(<MemoryRouter>{el}</MemoryRouter>)

beforeEach(() => vi.clearAllMocks())

describe('AdminAccountsPage', () => {
  const ACCOUNTS = [
    {
      account_id: 1,
      email: 'admin@test.dev',
      full_name: 'Admin One',
      roles: ['Administrator'],
      status: 'active',
    },
    {
      account_id: 2,
      email: 'new@test.dev',
      full_name: 'New Person',
      roles: ['Administrator'],
      status: 'disabled',
    },
    {
      account_id: 3,
      email: 'learner@test.dev',
      full_name: 'Learner One',
      roles: ['Learner'],
      status: 'active',
    },
  ]

  const mockRoleManager = () => api.get.mockImplementation((url) => Promise.resolve({
    data: url === '/admin/role-management/capability'
      ? { account_id: 99, can_manage_roles: true }
      : ACCOUNTS,
  }))

  it('offers only the Administrator role accepted by the provisioning API', async () => {
    mockRoleManager()
    renderPage(<AdminAccountsPage />)
    const role = await screen.findByRole('combobox', { name: 'Account role' })
    expect([...role.options].map((o) => o.value)).toEqual(['Administrator'])
    await screen.findByText('new@test.dev')
  })

  it('lists accounts with their status and the right toggle', async () => {
    mockRoleManager()
    renderPage(<AdminAccountsPage />)
    const row = (await screen.findByText('new@test.dev')).closest('tr')
    expect(within(row).getByText('Disabled')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Activate' })).toBeInTheDocument()
    const adminRow = screen.getByText('admin@test.dev').closest('tr')
    expect(within(adminRow).getByRole('button', { name: 'Disable' })).toBeInTheDocument()
  })

  it('provisions a new account through the admin endpoint', async () => {
    mockRoleManager()
    api.post.mockResolvedValue({ data: {} })
    renderPage(<AdminAccountsPage />)
    await screen.findByText('new@test.dev')
    await userEvent.type(screen.getByPlaceholderText('Full name'), 'Second Admin')
    await userEvent.type(screen.getByPlaceholderText('email@example.com'), 'two@test.dev')
    await userEvent.type(screen.getByPlaceholderText('Temporary password'), 'pass-1234')
    await userEvent.click(screen.getByRole('button', { name: 'Provision' }))
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/admin/accounts', {
        name: 'Second Admin',
        email: 'two@test.dev',
        password: 'pass-1234',
        role: 'Administrator',
      })
    )
    expect(await screen.findByRole('status')).toHaveTextContent(/Provisioned two@test.dev/)
  })

  it('activates a disabled account', async () => {
    mockRoleManager()
    api.patch.mockResolvedValue({ data: {} })
    renderPage(<AdminAccountsPage />)
    await userEvent.click(await screen.findByRole('button', { name: 'Activate' }))
    await waitFor(() =>
      expect(api.patch).toHaveBeenCalledWith('/admin/accounts/2', { status: 'active' })
    )
  })

  it('requires confirmation before granting Administrator access and refreshes the list', async () => {
    mockRoleManager()
    api.patch.mockResolvedValue({ data: { changed: true } })
    renderPage(<AdminAccountsPage />)
    const row = (await screen.findByText('learner@test.dev')).closest('tr')
    await userEvent.click(within(row).getByRole('button', { name: 'Grant Administrator Access' }))
    const dialog = screen.getByRole('dialog', { name: 'Grant Administrator access to this user?' })
    expect(dialog).toHaveTextContent('They will be able to access administrative features.')
    expect(api.patch).not.toHaveBeenCalled()
    await userEvent.click(within(dialog).getByRole('button', { name: 'Grant Administrator Access' }))
    await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/admin/accounts/3/role', {
      role: 'Administrator', expected_role: 'Learner',
    }))
    expect(await screen.findByRole('status')).toHaveTextContent('Administrator access granted to learner@test.dev.')
  })

  it('warns and confirms before revoking Administrator access', async () => {
    mockRoleManager()
    api.patch.mockResolvedValue({ data: { changed: true } })
    renderPage(<AdminAccountsPage />)
    const row = (await screen.findByText('admin@test.dev')).closest('tr')
    await userEvent.click(within(row).getByRole('button', { name: 'Revoke Administrator Access' }))
    const dialog = screen.getByRole('dialog', { name: 'Revoke Administrator access?' })
    expect(dialog).toHaveTextContent('This user will lose access to administrative features.')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Revoke Administrator Access' }))
    await waitFor(() => expect(api.patch).toHaveBeenCalledWith('/admin/accounts/1/role', {
      role: 'Learner', expected_role: 'Administrator',
    }))
  })

  it('hides role operations from an ordinary administrator', async () => {
    api.get.mockImplementation((url) => Promise.resolve({ data: url === '/admin/role-management/capability'
      ? { account_id: 1, can_manage_roles: false } : ACCOUNTS }))
    renderPage(<AdminAccountsPage />)
    expect(await screen.findByText('learner@test.dev')).toBeInTheDocument()
    expect(screen.getByText('Role assignment and Administrator provisioning are restricted to designated role managers.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Grant Administrator Access' })).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Provision an account' })).not.toBeInTheDocument()
  })

  it('keeps the confirmation open on a stale role conflict without duplicate requests', async () => {
    mockRoleManager()
    api.patch.mockRejectedValueOnce({ response: { data: { error: {
      code: 'role_changed_concurrently',
      message: "This account's role changed. Refresh the account list and try again.",
    } } } })
    renderPage(<AdminAccountsPage />)
    const row = (await screen.findByText('learner@test.dev')).closest('tr')
    await userEvent.click(within(row).getByRole('button', { name: 'Grant Administrator Access' }))
    const dialog = screen.getByRole('dialog', { name: 'Grant Administrator access to this user?' })
    await userEvent.click(within(dialog).getByRole('button', { name: 'Grant Administrator Access' }))
    expect(await within(dialog).findByRole('alert')).toHaveTextContent("This account's role changed. Refresh the account list and try again.")
    expect(dialog).toBeInTheDocument()
    expect(api.patch).toHaveBeenCalledTimes(1)
  })
})

describe('AdminCandidatesPage', () => {
  const QUEUE = [
    {
      candidate_id: 9,
      question_type: 'mcq',
      concept_id: 10,
      concept_code: 'SQL-SELECT',
      validation_status: 'validated',
      created_at: '2026-11-20T10:00:00Z',
    },
  ]
  const DETAIL = {
    candidate_id: 9,
    question_type: 'mcq',
    concept_id: 10,
    concept_code: 'SQL-SELECT',
    validation_status: 'validated',
    promoted_question_id: null,
    payload: { prompt: 'Draft MCQ prompt', options: [] },
    validation_detail: {
      ok: true,
      checks: [
        { check: 'completeness', ok: true, problems: [] },
        { check: 'duplicate', ok: true, matches: [] },
      ],
    },
  }
  const CONCEPTS = [
    { concept_id: 10, concept_code: 'SQL-SELECT', concept_name: 'SELECT', subject_area: 'x', difficulty_level: 1 },
  ]

  function mockApi() {
    api.get.mockImplementation((url) => {
      if (url === '/admin/question-candidates') return Promise.resolve({ data: QUEUE })
      if (url === '/admin/concepts') return Promise.resolve({ data: CONCEPTS })
      if (url === '/admin/question-candidates/9') return Promise.resolve({ data: DETAIL })
      return Promise.reject(new Error(url))
    })
  }

  it('lists the review queue and hides rejected by default', async () => {
    mockApi()
    renderPage(<AdminCandidatesPage />)
    const row = (await screen.findByText('Review')).closest('li')
    expect(within(row).getByText('SQL-SELECT')).toBeInTheDocument()
    expect(api.get).toHaveBeenCalledWith('/admin/question-candidates', { params: {} })
    expect(within(row).getByText('Validated')).toBeInTheDocument()
  })

  it('opens a candidate, shows checks, and approves it into the bank', async () => {
    mockApi()
    api.post.mockResolvedValue({ data: { ...DETAIL, validation_status: 'approved', promoted_question_id: 77 } })
    renderPage(<AdminCandidatesPage />)
    await userEvent.click(await screen.findByRole('button', { name: 'Review' }))
    expect((await screen.findAllByText(/Draft MCQ prompt/)).length).toBeGreaterThan(0)
    expect(screen.getByText('Completeness: Passed')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Approve into bank' }))
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/admin/question-candidates/9/approve')
    )
  })

  it('generates candidates for a chosen concept', async () => {
    mockApi()
    api.post.mockResolvedValue({ data: [DETAIL] })
    renderPage(<AdminCandidatesPage />)
    await screen.findByRole('button', { name: 'Review' })
    await userEvent.selectOptions(screen.getByLabelText(/concept/i), '10')
    await userEvent.click(screen.getByRole('button', { name: 'Generate' }))
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/admin/question-candidates/generate', {
        concept_id: 10,
        question_type: 'mcq',
        count: 1,
      })
    )
  })
})
