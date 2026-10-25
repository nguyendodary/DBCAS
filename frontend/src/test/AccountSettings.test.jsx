import { beforeEach, expect, it, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PasswordSettings, AvatarSettings } from '../components/AccountSettings'
import { setLocale } from '../i18n'

const mock = vi.hoisted(() => ({ changePassword: vi.fn(), updateAccount: vi.fn(), put: vi.fn() }))
vi.mock('../auth', () => ({ useAuth: () => ({ account: { email: 'student@example.test', full_name: 'Student', avatar_url: 'data:image/png;base64,test' }, ...mock }) }))
vi.mock('../api', () => ({ default: { put: mock.put }, apiMessage: (_, fallback) => fallback }))

beforeEach(async () => { vi.clearAllMocks(); await setLocale('vi') })

it('validates confirmation before sending passwords', async () => {
  render(<PasswordSettings />)
  fireEvent.change(screen.getByLabelText('Mật khẩu hiện tại'), { target: { value: 'old-password' } })
  fireEvent.change(screen.getByLabelText('Mật khẩu mới'), { target: { value: 'new-password' } })
  fireEvent.change(screen.getByLabelText('Nhập lại mật khẩu mới'), { target: { value: 'different-password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Đổi mật khẩu' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('chưa khớp')
  expect(mock.changePassword).not.toHaveBeenCalled()
})

it('sends all password fields and clears them after success', async () => {
  mock.changePassword.mockResolvedValue({})
  render(<PasswordSettings />)
  for (const [label, value] of [['Mật khẩu hiện tại', 'old-password'], ['Mật khẩu mới', 'new-password'], ['Nhập lại mật khẩu mới', 'new-password']]) {
    fireEvent.change(screen.getByLabelText(label), { target: { value } })
  }
  fireEvent.click(screen.getByRole('button', { name: 'Đổi mật khẩu' }))
  await waitFor(() => expect(mock.changePassword).toHaveBeenCalledWith({ current_password: 'old-password', new_password: 'new-password', new_password_confirm: 'new-password' }))
  expect(await screen.findByRole('status')).toHaveTextContent('thành công')
  expect(screen.getByLabelText('Mật khẩu hiện tại')).toHaveValue('')
})

it('persists photo removal and updates the authenticated account', async () => {
  const account = { email: 'student@example.test', avatar_url: null }
  mock.put.mockResolvedValue({ data: account })
  render(<AvatarSettings />)
  fireEvent.click(screen.getByRole('button', { name: 'Xoá ảnh' }))
  await waitFor(() => expect(mock.put).toHaveBeenCalledWith('/auth/avatar', { avatar_data_url: null }))
  expect(mock.updateAccount).toHaveBeenCalledWith(account)
  expect(await screen.findByRole('status')).toHaveTextContent('Đã cập nhật')
})

it('does not announce success or clear passwords when the request fails', async () => {
  mock.changePassword.mockRejectedValue(new Error('network'))
  render(<PasswordSettings />)
  for (const [label, value] of [['Mật khẩu hiện tại', 'old-password'], ['Mật khẩu mới', 'new-password'], ['Nhập lại mật khẩu mới', 'new-password']]) {
    fireEvent.change(screen.getByLabelText(label), { target: { value } })
  }
  fireEvent.click(screen.getByRole('button', { name: 'Đổi mật khẩu' }))
  expect(await screen.findByRole('alert')).toBeInTheDocument()
  expect(screen.queryByRole('status')).not.toBeInTheDocument()
  expect(screen.getByLabelText('Mật khẩu hiện tại')).toHaveValue('old-password')
})
