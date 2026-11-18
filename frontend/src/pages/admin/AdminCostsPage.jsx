import { useEffect, useMemo, useState } from 'react'
import api, { apiMessage } from '../../api'
import { useLocale } from '../../i18n'

const COST_TEXT = {
  admin: { vi: 'Quản trị', en: 'Administration' },
  title: { vi: 'Quản lý chi phí & gói dịch vụ', en: 'Costs & Subscription Management' },
  intro: {
    vi: 'Xem doanh thu, chi phí và trạng thái gói tài khoản.',
    en: 'View revenue, costs and account plans.',
  },
  overview: { vi: 'Tổng quan', en: 'Overview' },
  accounts: { vi: 'Tổng tài khoản', en: 'Total accounts' },
  accountsHint: { vi: 'Từ API tài khoản Admin', en: 'From the Admin accounts API' },
  proAccounts: { vi: 'Tài khoản gói Pro', en: 'Pro accounts' },
  proHint: {
    vi: 'Chỉ đếm khi API có thông tin gói',
    en: 'Counted only if the API provides plan details',
  },
  freeAccounts: { vi: 'Tài khoản gói Free', en: 'Free accounts' },
  freeHint: {
    vi: 'Chỉ đếm khi API có thông tin gói',
    en: 'Counted only if the API provides plan details',
  },
  unknownAccounts: { vi: 'Chưa có dữ liệu gói', en: 'No plan data' },
  unknownHint: { vi: 'Không tự mặc định là Free', en: 'Not assumed to be Free' },
  reportError: { vi: 'Không tải được báo cáo thu chi.', en: 'Could not load the financial report.' },
  unpriced: { vi: 'lượt gọi AI chưa tính được giá', en: 'AI calls without a price' },
  usersTitle: { vi: 'Danh sách người dùng & gói đang sử dụng', en: 'Users & Current Plans' },
  reload: { vi: 'Tải lại', en: 'Reload' },
  searchLabel: { vi: 'Tìm người dùng', en: 'Search users' },
  searchPlaceholder: { vi: 'Tìm tên hoặc email...', en: 'Search name or email...' },
  filterLabel: { vi: 'Lọc theo gói', en: 'Filter by plan' },
  allPlans: { vi: 'Tất cả gói', en: 'All plans' },
  noData: { vi: 'Chưa có dữ liệu', en: 'No data' },
  loading: { vi: 'Đang tải người dùng...', en: 'Loading users...' },
  loadError: { vi: 'Không tải được danh sách tài khoản.', en: 'Could not load account list.' },
  user: { vi: 'Người dùng', en: 'User' },
  currentPlan: { vi: 'Gói hiện tại', en: 'Current plan' },
  subscriptionStatus: { vi: 'Trạng thái thuê bao', en: 'Subscription status' },
  notUpdated: { vi: 'Chưa cập nhật', en: 'Not updated' },
  noPurchaseData: { vi: 'Chưa có dữ liệu mua gói', en: 'No purchase data' },
  noMatches: { vi: 'Không có tài khoản phù hợp.', en: 'No matching accounts.' },
}

function knownPlan(account) {
  const raw =
    account.subscription?.plan ?? account.subscription_plan ?? account.plan_name ?? account.plan
  if (typeof raw !== 'string') return null
  const value = raw.trim().toLowerCase()
  return value === 'pro' || value === 'free' ? value : null
}

function money(value, locale, currency = 'VND') {
  const amount = Number(value)

  if (value == null || !Number.isFinite(amount)) {
    return '—'
  }

  return new Intl.NumberFormat(locale === 'en' ? 'en-US' : 'vi-VN', {
    style: 'currency', currency, maximumFractionDigits: currency === 'VND' ? 0 : 8,
  }).format(amount)
}

function currentVietnamMonth() {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit',
  }).formatToParts(new Date())
  const get = (type) => parts.find((part) => part.type === type)?.value
  return `${get('year')}-${get('month')}`
}

function knownSubscriptionStatus(account, locale = 'vi') {
  const isEnglish = locale === 'en'

  if (account.plan === 'free') {
    return isEnglish ? 'Free plan active' : 'Đang sử dụng gói Free'
  }

  if (account.plan === 'pro') {
    if (!account.pro_expires_at) {
      return isEnglish ? 'No expiry information' : 'Chưa có thông tin hết hạn'
    }

    const expiresAt = new Date(account.pro_expires_at)

    return expiresAt.getTime() > Date.now()
      ? isEnglish
        ? 'Pro active'
        : 'Pro còn hiệu lực'
      : isEnglish
        ? 'Pro expired'
        : 'Pro đã hết hạn'
  }

  return isEnglish ? 'No plan data' : 'Chưa có dữ liệu gói'
}

const panel = 'rounded-2xl border border-edge bg-surface/90 p-5 shadow-sm'
const field =
  'w-full rounded-lg border border-edge2 bg-abyss px-3 py-2 text-ink outline-none focus:border-cyan-400'

export default function AdminCostsPage() {
  const { locale } = useLocale()
  const tx = (key) => COST_TEXT[key][locale === 'en' ? 'en' : 'vi']
  const [accounts, setAccounts] = useState([])
  const [financialReport, setFinancialReport] = useState(null)
  const [financialError, setFinancialError] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('all')

  async function loadAccounts() {
    setLoading(true)
    setError('')
    try {
      const response = await api.get('/admin/accounts')
      setAccounts(Array.isArray(response.data) ? response.data : [])
    } catch (err) {
      setError(apiMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAccounts()
  }, [])
  useEffect(() => {
    async function loadFinancialReport() {
      try {
        const response = await api.get('/admin/financial-report', {
          params: { month: currentVietnamMonth() },
        })

        setFinancialReport(response.data)
      } catch (error) {
        setFinancialError(apiMessage(error))
      }
    }

    loadFinancialReport()
  }, [])

  const summary = useMemo(() => {
    const plans = accounts.map(knownPlan)
    return {
      pro: plans.filter((p) => p === 'pro').length,
      free: plans.filter((p) => p === 'free').length,
      unknown: plans.filter((p) => p === null).length,
    }
  }, [accounts])

  const filteredAccounts = accounts.filter((account) => {
    const q = query.trim().toLowerCase()
    const text = `${account.full_name || ''} ${account.email || ''}`.toLowerCase()
    const plan = knownPlan(account)
    return (
      (!q || text.includes(q)) &&
      (filter === 'all' || (filter === 'unknown' ? !plan : plan === filter))
    )
  })

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-cyan-300">
          Skill Analytics · {tx('admin')}
        </p>
        <h1 className="mt-2 text-3xl font-bold text-ink">{tx('title')}</h1>
        <p className="mt-2 text-sm text-sub">{tx('intro')}</p>
      </div>
      {financialError && <p role="alert" className="text-rose-300">{tx('reportError')} {financialError}</p>}
      {financialReport && (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[
              [locale === 'en' ? 'Revenue' : 'Doanh thu', financialReport.revenue],
              [locale === 'en' ? 'Estimated AI cost' : 'Chi phí AI ước tính', financialReport.ai_cost],
              [locale === 'en' ? 'Hosting cost' : 'Chi phí Hosting', financialReport.hosting_cost],
              [locale === 'en' ? 'Remaining' : 'Số dư còn lại', financialReport.balance],
            ].map(([label, value]) => (
              <div className={panel} key={label}>
                <p className="text-sm text-sub">{label}</p>
                <p className="mt-2 text-3xl font-bold text-cyan-300">{money(value, locale, financialReport.currency)}</p>
              </div>
            ))}
          </section>
          <p className="text-xs text-mute">
            {locale === 'en' ? 'Demo purchase data; no real payment is collected.' : 'Dữ liệu mua gói trong môi trường demo; không thu tiền thật.'}
          </p>
          {financialReport.unpriced_ai_calls > 0 && (
            <p role="status" className="text-sm text-amber-300">
              {financialReport.unpriced_ai_calls} {tx('unpriced')}. {locale === 'en' ? 'The AI total does not include these calls.' : 'Tổng chi phí AI chưa gồm các lượt này.'}
            </p>
          )}
        </>
      )}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label={tx('overview')}>
        {[
          [tx('accounts'), loading || error ? '—' : accounts.length, tx('accountsHint')],
          [tx('proAccounts'), loading || error ? '—' : summary.pro, tx('proHint')],
          [tx('freeAccounts'), loading || error ? '—' : summary.free, tx('proHint')],
          [tx('unknownAccounts'), loading || error ? '—' : summary.unknown, tx('unknownHint')],
        ].map(([label, value, hint]) => (
          <div className={panel} key={label}>
            <p className="text-sm text-sub">{label}</p>
            <p className="mt-2 text-3xl font-bold text-cyan-300">{value}</p>
            <p className="mt-2 text-xs text-mute">{hint}</p>
          </div>
        ))}
      </section>

      <section className={panel}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-ink">{tx('usersTitle')}</h2>
          </div>
          <button
            type="button"
            onClick={loadAccounts}
            className="rounded-lg border border-edge2 px-4 py-2 text-sm text-ink hover:bg-surface-hover"
          >
            {tx('reload')}
          </button>
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <input
            aria-label={tx('searchLabel')}
            placeholder={tx('searchPlaceholder')}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className={`${field} max-w-sm`}
          />
          <select
            aria-label={tx('filterLabel')}
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className={`${field} max-w-xs`}
          >
            <option value="all">{tx('allPlans')}</option>
            <option value="pro">Pro</option>
            <option value="free">Free</option>
            <option value="unknown">{tx('noData')}</option>
          </select>
        </div>
        {loading ? (
          <p className="mt-4 text-sm text-sub">{tx('loading')}</p>
        ) : error ? (
          <p role="alert" className="mt-4 text-sm text-rose-300">
            {tx('loadError')} {String(error)}
          </p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[650px] text-left text-sm">
              <thead className="border-b border-edge text-sub">
                <tr>
                  <th className="px-3 py-3">{tx('user')}</th>
                  <th className="px-3 py-3">Email</th>
                  <th className="px-3 py-3">{tx('currentPlan')}</th>
                  <th className="px-3 py-3">{tx('subscriptionStatus')}</th>
                </tr>
              </thead>
              <tbody>
                {filteredAccounts.map((account) => (
                  <tr className="border-b border-edge/60" key={account.account_id ?? account.email}>
                    <td className="px-3 py-3 text-ink">{account.full_name || tx('notUpdated')}</td>
                    <td className="px-3 py-3 text-sub">{account.email}</td>
                    <td className="px-3 py-3">
                      <span className="rounded-md border border-edge2 px-2 py-1 text-ink">
                        {knownPlan(account)?.toUpperCase() || tx('noData')}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-sub">
                      {knownSubscriptionStatus(account, locale)}
                    </td>
                  </tr>
                ))}
                {!filteredAccounts.length && (
                  <tr>
                    <td colSpan={4} className="px-3 py-6 text-center text-sub">
                      {tx('noMatches')}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
