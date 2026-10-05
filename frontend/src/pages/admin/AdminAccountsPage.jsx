import { useCallback, useEffect, useState } from 'react'
import api, { apiMessage } from '../../api'
import AdminNav from '../../components/AdminNav'
import { EmptyState, ErrorState, Loading } from '../../components/States'

// UC04 — provision accounts (start disabled) and activate verified ones.
export default function AdminAccountsPage() {
  const [accounts, setAccounts] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'Administrator' })
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    setError('')
    api
      .get('/admin/accounts')
      .then((r) => setAccounts(r.data))
      .catch((e) => {
        setError(apiMessage(e))
        setAccounts([])
      })
  }, [])

  useEffect(load, [load])

  async function provision(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await api.post('/admin/accounts', form)
      setNotice(`Provisioned ${form.email} — activate it after verifying the person.`)
      setForm({ name: '', email: '', password: '', role: 'Administrator' })
      load()
    } catch (e2) {
      setError(apiMessage(e2))
    } finally {
      setBusy(false)
    }
  }

  async function setStatus(account, status) {
    setError('')
    try {
      await api.patch(`/admin/accounts/${account.account_id}`, { status })
      load()
    } catch (e) {
      setError(apiMessage(e))
    }
  }

  return (
    <div>
      <AdminNav />
      <h1 className="text-xl font-semibold text-gray-900">Accounts</h1>
      <p className="mt-1 text-sm text-gray-500">
        Provisioned accounts start <strong>disabled</strong> and cannot log in
        until you activate them after verifying the intended person.
      </p>

      <form onSubmit={provision} className="mt-4 grid gap-2 rounded-md border bg-white p-4 sm:grid-cols-5">
        <input
          required
          placeholder="Full name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
        <input
          required
          type="email"
          placeholder="email@example.com"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
        <input
          required
          type="password"
          placeholder="Temporary password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
        <select
          value={form.role}
          onChange={(e) => setForm({ ...form, role: e.target.value })}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        >
          <option>Administrator</option>
          <option>Learner</option>
        </select>
        <button
          type="submit"
          disabled={busy}
          className="rounded bg-blue-600 px-3 py-1 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {busy ? 'Provisioning…' : 'Provision'}
        </button>
      </form>

      {notice && <p role="status" className="mt-3 rounded bg-green-50 p-2 text-sm text-green-700">{notice}</p>}
      {error && <div className="mt-3"><ErrorState message={error} /></div>}

      {accounts === null ? (
        <Loading />
      ) : accounts.length === 0 ? (
        <div className="mt-4"><EmptyState title="No accounts" /></div>
      ) : (
        <table className="mt-4 w-full border-collapse overflow-hidden rounded-md border bg-white text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th className="px-3 py-2">Name</th>
              <th className="px-3 py-2">Email</th>
              <th className="px-3 py-2">Roles</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody className="divide-y">
            {accounts.map((a) => (
              <tr key={a.account_id}>
                <td className="px-3 py-2">{a.full_name || '—'}</td>
                <td className="px-3 py-2">{a.email}</td>
                <td className="px-3 py-2">{(a.roles || []).join(', ')}</td>
                <td className="px-3 py-2">
                  <span
                    className={`rounded px-2 py-0.5 text-xs font-medium ${
                      a.status === 'active'
                        ? 'bg-green-50 text-green-700'
                        : 'bg-amber-50 text-amber-700'
                    }`}
                  >
                    {a.status}
                  </span>
                </td>
                <td className="px-3 py-2 text-right">
                  {a.status === 'active' ? (
                    <button
                      type="button"
                      onClick={() => setStatus(a, 'disabled')}
                      className="text-sm text-red-600 hover:underline"
                    >
                      Disable
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setStatus(a, 'active')}
                      className="text-sm text-blue-600 hover:underline"
                    >
                      Activate
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
