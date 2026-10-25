import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { AuthProvider } from '../auth'
import LoginPage from '../pages/LoginPage'
import RegisterPage from '../pages/RegisterPage'
import Layout from '../components/Layout'
import { StatusBadge, TypeBadge } from '../components/ui'
import { i18n, setLocale, resolveMessage, statusLabel } from '../i18n'
import api, { apiMessage } from '../api'

vi.mock('../api', async (original) => ({ ...(await original()), default: { get: vi.fn(), post: vi.fn() } }))
beforeEach(async () => {
  vi.clearAllMocks(); localStorage.clear()
  await i18n.changeLanguage('en')
  api.get.mockResolvedValue({ data: { providers: [{ name: 'google', configured: true }, { name: 'github', configured: true }] } })
})
afterEach(async () => { await act(() => i18n.changeLanguage('en')); localStorage.clear() })
function mount(path = '/login') {
  return render(<MemoryRouter initialEntries={[path]}><AuthProvider><Routes>
    <Route path="/login" element={<LoginPage />} /><Route path="/register" element={<RegisterPage />} />
  </Routes></AuthProvider></MemoryRouter>)
}
it('keeps typed credentials and OAuth links when switching languages and navigating', async () => {
  mount()
  await userEvent.type(screen.getByLabelText('Email', { exact: true }), 'learner@test.dev')
  await userEvent.type(screen.getByLabelText('Password', { exact: true }), 'NotSubmitted123!')
  const calls = api.get.mock.calls.length
  await userEvent.click(screen.getByRole('button', { name: 'Language' }))
  await userEvent.click(screen.getByRole('menuitemradio', { name: 'Tiếng Việt' }))
  expect(screen.getByRole('heading', { name: 'Đăng nhập DBCAS' })).toBeInTheDocument()
  expect(screen.getByLabelText('Mật khẩu', { exact: true })).toHaveValue('NotSubmitted123!')
  expect(screen.getByLabelText('Email', { exact: true })).toHaveValue('learner@test.dev')
  expect(screen.getByRole('link', { name: 'Tiếp tục với Google' })).toHaveAttribute('href', '/api/v1/auth/oauth/google/start')
  expect(api.get).toHaveBeenCalledTimes(calls)
  await userEvent.click(screen.getByRole('link', { name: 'Đăng ký học viên' }))
  expect(screen.getByRole('heading', { name: 'Tạo tài khoản' })).toBeInTheDocument()
  expect(screen.getByLabelText('Xác nhận mật khẩu', { exact: true })).toBeInTheDocument()
  expect(document.documentElement.lang).toBe('vi')
})
it('updates an already visible authentication error without retrying the request', async () => {
  api.post.mockRejectedValue({ response: { data: { error: { code: 'invalid_credentials', message: 'private untrusted provider details' } } } })
  mount()
  await userEvent.type(screen.getByLabelText('Email', { exact: true }), 'learner@test.dev')
  await userEvent.type(screen.getByLabelText('Password', { exact: true }), 'wrong')
  await userEvent.click(screen.getByRole('button', { name: 'Sign in', exact: true }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password.')
  await userEvent.click(screen.getByRole('button', { name: 'Language' }))
  await userEvent.click(screen.getByRole('menuitemradio', { name: 'Tiếng Việt' }))
  expect(screen.getByRole('alert')).toHaveTextContent('Email hoặc mật khẩu chưa đúng.')
  expect(screen.queryByText(/private untrusted/)).not.toBeInTheDocument()
  expect(api.post).toHaveBeenCalledTimes(1)
})
it('localizes OAuth callback errors and rejects unknown error text', async () => {
  mount('/login?oauth_error=state')
  await userEvent.click(screen.getByRole('button', { name: 'Language' }))
  await userEvent.click(screen.getByRole('menuitemradio', { name: 'Tiếng Việt' }))
  expect(screen.getByRole('alert')).toHaveTextContent('Yêu cầu đăng nhập đã hết hạn.')
  expect(resolveMessage(apiMessage({ response: { data: { error: { code: 'unknown', message: 'secret server details' } } } }))).not.toContain('secret')
  expect(resolveMessage(apiMessage(new Error('internal stack trace')))).not.toContain('stack')
})
it('localizes the real role-aware shell without exposing admin navigation to learners', async () => {
  localStorage.setItem('dbcas_token', 'test-only-token')
  api.get.mockResolvedValue({ data: { full_name: 'Original name', email: 'learner@test.dev', roles: ['Learner'] } })
  render(<MemoryRouter initialEntries={['/dashboard']}><AuthProvider><Layout><h1>Domain content</h1></Layout></AuthProvider></MemoryRouter>)
  await waitFor(() => expect(screen.getAllByRole('link', { name: 'My Competency' })).toHaveLength(2))
  await act(() => setLocale('vi'))
  expect(screen.getAllByRole('link', { name: 'Tổng quan' })).toHaveLength(2)
  expect(screen.queryByRole('link', { name: 'Tài khoản' })).not.toBeInTheDocument()
  expect(screen.getByText('Original name')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Chuyển đến nội dung' })).toHaveAttribute('href', '#main-content')
})
it('localizes known presentation enums without changing their values', async () => {
  const status = 'in_progress'
  render(<><StatusBadge status={status} /><TypeBadge type="essay" /></>)
  expect(screen.getByText('In progress')).toBeInTheDocument()
  await act(() => setLocale('vi'))
  expect(screen.getByText('Đang làm')).toBeInTheDocument()
  expect(screen.getByText('Tự luận')).toBeInTheDocument()
  expect(status).toBe('in_progress')
  expect(statusLabel('unrecognized_status')).toBe('Không xác định')
})
