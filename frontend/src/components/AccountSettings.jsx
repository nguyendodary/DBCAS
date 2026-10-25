import { useRef, useState } from 'react'
import { t, resolveMessage, message } from '../i18n'
import { useAuth } from '../auth'
import api, { apiMessage } from '../api'
import { Card, CardTitle, inputCls, btnPrimary, btnGhost } from './SharedComponents'
import AccountAvatar from './AccountAvatar'

export function prepareAvatar(file) {
  return new Promise((resolve, reject) => {
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) return reject(new Error('image'))
    const url = URL.createObjectURL(file)
    const image = new Image()
    image.onload = () => {
      URL.revokeObjectURL(url)
      if (!image.naturalWidth || !image.naturalHeight || image.naturalWidth * image.naturalHeight > 25000000) return reject(new Error('image'))
      const canvas = document.createElement('canvas')
      canvas.width = canvas.height = 256
      const side = Math.min(image.naturalWidth, image.naturalHeight)
      canvas.getContext('2d').drawImage(image, (image.naturalWidth - side) / 2, (image.naturalHeight - side) / 2, side, side, 0, 0, 256, 256)
      resolve(canvas.toDataURL('image/png'))
    }
    image.onerror = () => { URL.revokeObjectURL(url); reject(new Error('image')) }
    image.src = url
  })
}

function Notice({ error, success }) {
  return <div aria-live="polite">{error && <p role="alert" className="mt-3 text-sm text-rose-500">{resolveMessage(error)}</p>}{success && <p role="status" className="mt-3 text-sm text-emerald-500">{resolveMessage(success)}</p>}</div>
}

export function AvatarSettings() {
  const { account, updateAccount } = useAuth()
  const input = useRef(null)
  const [preview, setPreview] = useState(undefined)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  async function choose(event) {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    setBusy(true); setError(null); setSuccess(null)
    try { setPreview(await prepareAvatar(file)) }
    catch { setError(message('accountSettings.imageError')) }
    finally { setBusy(false) }
  }
  async function save(value) {
    setBusy(true); setError(null); setSuccess(null)
    try {
      const result = await api.put('/auth/avatar', { avatar_data_url: value })
      updateAccount(result.data); setPreview(undefined); setSuccess(message('accountSettings.avatarSaved'))
    } catch (err) { setError(apiMessage(err, message('errors.unknown'))) }
    finally { setBusy(false) }
  }
  return <div>
    <div className="flex flex-wrap items-center gap-4">
      <AccountAvatar account={{ ...account, avatar_url: preview === undefined ? account?.avatar_url : preview }} className="h-20 w-20 text-2xl" />
      <div className="min-w-0 flex-1">
        <p className="break-words text-base font-semibold text-ink">{account?.full_name || t('settings.noName')}</p>
        <p className="break-all text-sm text-mute">{account?.email}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button type="button" className={btnGhost} disabled={busy} onClick={() => input.current?.click()}>{t('accountSettings.chooseImage')}</button>
          {preview !== undefined && <button type="button" className={btnPrimary} disabled={busy} onClick={() => save(preview)}>{t('accountSettings.saveImage')}</button>}
          {(account?.avatar_url || preview) && <button type="button" className={btnGhost} disabled={busy} onClick={() => save(null)}>{t('accountSettings.removeImage')}</button>}
        </div>
        <p className="mt-2 text-xs text-mute">{t('accountSettings.imageHint')}</p>
      </div>
      <input ref={input} type="file" accept="image/png,image/jpeg,image/webp" aria-label={t('accountSettings.chooseImage')} className="hidden" onChange={choose} disabled={busy} />
    </div>
    <Notice error={error} success={success} />
  </div>
}

export function PasswordSettings() {
  const { changePassword } = useAuth()
  const [values, setValues] = useState({ current_password: '', new_password: '', new_password_confirm: '' })
  const [busy, setBusy] = useState(false)
  const [visible, setVisible] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  async function submit(event) {
    event.preventDefault(); setError(null); setSuccess(null)
    if (values.new_password !== values.new_password_confirm) { setError(message('accountSettings.mismatch')); return }
    setBusy(true)
    try {
      await changePassword(values)
      setValues({ current_password: '', new_password: '', new_password_confirm: '' })
      setSuccess(message('accountSettings.passwordSaved'))
    } catch (err) { setError(apiMessage(err, message('errors.unknown'))) }
    finally { setBusy(false) }
  }
  return <Card>
    <CardTitle title={t('accountSettings.passwordTitle')} />
    <form className="space-y-4 p-5" onSubmit={submit}>
      <div className="grid gap-4 md:grid-cols-3">
        {['current_password', 'new_password', 'new_password_confirm'].map((key) => <label key={key} className="block text-sm text-sub">
          <span className="mb-2 block">{t(`accountSettings.${key}`)}</span>
          <input className={inputCls} type={visible ? 'text' : 'password'} autoComplete={key === 'current_password' ? 'current-password' : 'new-password'} required minLength={key === 'current_password' ? 1 : 8} maxLength={72} value={values[key]} disabled={busy} onChange={(event) => setValues({ ...values, [key]: event.target.value })} />
        </label>)}
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-2 text-xs text-mute"><p>{t('accountSettings.passwordHint')}</p><label className="flex cursor-pointer items-center gap-2"><input type="checkbox" checked={visible} onChange={(e) => setVisible(e.target.checked)} />{t('accountSettings.showPassword')}</label></div>
        <button type="submit" className={btnPrimary} disabled={busy}>{t(busy ? 'accountSettings.saving' : 'accountSettings.passwordTitle')}</button>
      </div>
      <Notice error={error} success={success} />
    </form>
  </Card>
}
