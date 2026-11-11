import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import OAuthButtons from '../components/OAuthButtons'
import { setLocale } from '../i18n'
import api from '../api'

vi.mock('../api', () => ({ default: { get: vi.fn() } }))

afterEach(() => {
  document.documentElement.removeAttribute('data-theme')
})

for (const theme of ['light', 'dark']) {
  for (const locale of ['vi', 'en']) {
    for (const configured of [false, true]) {
      it(`keeps both providers visible: ${theme}, ${locale}, configured=${configured}`, async () => {
        await setLocale(locale)
        document.documentElement.dataset.theme = theme
        api.get.mockResolvedValue({
          data: { providers: ['google', 'github'].map((name) => ({ name, configured })) },
        })
        render(<OAuthButtons />)
        const prefix = locale === 'vi' ? 'Tiếp tục với' : 'Continue with'
        for (const [name, label] of [
          ['google', 'Google'],
          ['github', 'GitHub'],
        ]) {
          const control = await screen.findByRole(configured ? 'link' : 'button', {
            name: `${prefix} ${label}`,
          })
          expect(control).toBeVisible()
          expect(control.querySelector('svg')).toBeInTheDocument()
          expect(control).toHaveTextContent(`${prefix} ${label}`)
          if (configured) {
            expect(control).toHaveAttribute('href', `/api/v1/auth/oauth/${name}/start`)
          } else {
            await waitFor(() => expect(control).toBeEnabled())
            await userEvent.click(control)
            expect(screen.getByRole('status')).toHaveTextContent(
              locale === 'vi'
                ? `Chưa cấu hình đăng nhập bằng ${label}. Vui lòng dùng email.`
                : `${label} sign-in is not configured. Please use email.`,
            )
            expect(control).not.toHaveAttribute('href')
          }
        }
        expect(screen.getByText(locale === 'vi' ? 'hoặc' : 'or')).toBeInTheDocument()
      })
    }
  }
}

it('shows safe controls during loading and after unavailable or incomplete metadata', async () => {
  let rejectProviders
  api.get.mockReturnValue(
    new Promise((_, reject) => {
      rejectProviders = reject
    }),
  )
  render(<OAuthButtons />)
  expect(screen.getByRole('button', { name: 'Continue with Google' })).toBeVisible()
  expect(screen.getByRole('button', { name: 'Continue with GitHub' })).toBeDisabled()
  await act(async () => rejectProviders(new Error('offline')))
  const google = screen.getByRole('button', { name: 'Continue with Google' })
  await userEvent.click(google)
  expect(screen.getByRole('status')).toHaveTextContent(
    'Google sign-in is not configured. Please use email.',
  )
  expect(screen.queryByRole('link')).not.toBeInTheDocument()
})
