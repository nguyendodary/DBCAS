import { useEffect, useMemo, useState } from 'react'
import api, { apiMessage } from '../../api'
import { useLocale } from '../../i18n'

// FE-only prototype. Prices are browser-local; the backend remains the source of truth
// for purchases, subscriptions, payment amounts and accounting numbers.
const COST_TEXT = {
  admin: { vi: "Quản trị", en: "Administration" },
  title: { vi: "Quản lý chi phí & gói dịch vụ", en: "Costs & Subscription Management" },
  intro: { vi: "Theo dõi người dùng, xem thông tin gói nếu hệ thống có dữ liệu và thử cấu hình giá trên giao diện.", en: "View users, available subscription details, and test display-only pricing settings." },
  overview: { vi: "Tổng quan", en: "Overview" },
  accounts: { vi: "Tổng tài khoản", en: "Total accounts" },
  accountsHint: { vi: "Từ API tài khoản Admin", en: "From the Admin accounts API" },
  proAccounts: { vi: "Tài khoản gói Pro", en: "Pro accounts" },
  proHint: { vi: "Chỉ đếm khi API có thông tin gói", en: "Counted only if the API provides plan details" },
  freeAccounts: { vi: "Tài khoản gói Free", en: "Free accounts" },
  freeHint: { vi: "Chỉ đếm khi API có thông tin gói", en: "Counted only if the API provides plan details" },
  unknownAccounts: { vi: "Chưa có dữ liệu gói", en: "No plan data" },
  unknownHint: { vi: "Không tự mặc định là Free", en: "Not assumed to be Free" },
  pricing: { vi: "Bảng giá", en: "Pricing" },
  freePackage: { vi: "Gói Free", en: "Free plan" },
  proPackage: { vi: "Gói Pro", en: "Pro plan" },
  freeNote: { vi: "3 lượt dùng thử theo yêu cầu dự án. Việc giới hạn lượt cần backend thực hiện.", en: "Three trial sessions as required by the project. Trial enforcement requires backend support." },
  freeBadge: { vi: "Miễn phí", en: "Free" },
  proNote: { vi: "Giá mặc định minh họa: 99.000đ / 30 ngày.", en: "Illustrative default: VND 99,000 / 30 days." },
  priceLabel: { vi: "Điều chỉnh giá hiển thị (VNĐ)", en: "Adjust displayed price (VND)" },
  savePrice: { vi: "Lưu giá giao diện", en: "Save displayed price" },
  invalidPrice: { vi: "Giá Pro phải là số nguyên không âm.", en: "The Pro price must be a non-negative integer." },
  savedPrice: { vi: "Đã lưu giá HIỂN THỊ trên trình duyệt này. Chưa thay đổi giá thanh toán thật.", en: "DISPLAY price saved in this browser only. The actual checkout price has not changed." },
  usersTitle: { vi: "Danh sách người dùng & gói đang sử dụng", en: "Users & Current Plans" },
  usersHelp: { vi: "Lấy tài khoản thật từ API hiện có; chỉ hiển thị trạng thái mua khi API cung cấp.", en: "Accounts are loaded from the existing API; purchase status appears only when supplied by the API." },
  reload: { vi: "Tải lại", en: "Reload" },
  searchLabel: { vi: "Tìm người dùng", en: "Search users" },
  searchPlaceholder: { vi: "Tìm tên hoặc email...", en: "Search name or email..." },
  filterLabel: { vi: "Lọc theo gói", en: "Filter by plan" },
  allPlans: { vi: "Tất cả gói", en: "All plans" },
  noData: { vi: "Chưa có dữ liệu", en: "No data" },
  loading: { vi: "Đang tải người dùng...", en: "Loading users..." },
  loadError: { vi: "Không tải được danh sách tài khoản.", en: "Could not load account list." },
  user: { vi: "Người dùng", en: "User" },
  currentPlan: { vi: "Gói hiện tại", en: "Current plan" },
  subscriptionStatus: { vi: "Trạng thái thuê bao", en: "Subscription status" },
  notUpdated: { vi: "Chưa cập nhật", en: "Not updated" },
  noPurchaseData: { vi: "Chưa có dữ liệu mua gói", en: "No purchase data" },
  noMatches: { vi: "Không có tài khoản phù hợp.", en: "No matching accounts." },
  footerNote: { vi: "Lưu ý: Trang này chưa có số liệu thu, chi AI, hosting hoặc lợi nhuận vì API hiện tại chưa cung cấp dữ liệu tài chính tương ứng.", en: "Note: Revenue, AI costs, hosting costs, and profit are not shown because the current API does not provide those financial figures." },
}

const STORAGE_KEY = 'dbcas_admin_ui_plan_prices_v1'
const DEFAULT_PRICES = { free: 0, pro: 99000 }
const money = (value) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(value)

function readPrices() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
    return {
      free: 0,
      pro: Number.isFinite(value.pro) && value.pro >= 0 ? value.pro : DEFAULT_PRICES.pro,
    }
  } catch {
    return DEFAULT_PRICES
  }
}

function knownPlan(account) {
  // No inference: a learner role or an active account does not prove a purchase.
  const raw = account.subscription?.plan ?? account.subscription_plan ?? account.plan_name ?? account.plan
  if (typeof raw !== 'string') return null
  const value = raw.trim().toLowerCase()
  return value === 'pro' || value === 'free' ? value : null
}

function knownSubscriptionStatus(account) {
  const raw = account.subscription?.status ?? account.subscription_status
  return typeof raw === 'string' && raw.trim() ? raw : null
}

const panel = 'rounded-2xl border border-edge bg-surface/90 p-5 shadow-sm'
const field = 'w-full rounded-lg border border-edge2 bg-abyss px-3 py-2 text-ink outline-none focus:border-cyan-400'

export default function AdminCostsPage() {
  const { locale } = useLocale()
  const tx = (key) => COST_TEXT[key][locale === 'en' ? 'en' : 'vi']
  const [prices, setPrices] = useState(readPrices)
  const [proInput, setProInput] = useState(String(readPrices().pro))
  const [notice, setNotice] = useState('')
  const [accounts, setAccounts] = useState([])
  const [financialReport, setFinancialReport] = useState(null)
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

  useEffect(() => { loadAccounts() }, [])
  useEffect(() => {
  async function loadFinancialReport() {
    try {
      const response = await api.get('/admin/financial-report', {
        params: { month: '2026-11' }
      })

      setFinancialReport(response.data)
    } catch (error) {
      console.error('Không tải được báo cáo tài chính:', error)
    }
  }

  loadFinancialReport()
}, [])

  function savePrices(e) {
    e.preventDefault()
    const value = Number(proInput)
    if (!Number.isSafeInteger(value) || value < 0) {
      setNotice('invalidPrice')
      return
    }
    const next = { free: 0, pro: value }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    setPrices(next)
    setNotice('savedPrice')
  }

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
    return (!q || text.includes(q)) && (filter === 'all' || (filter === 'unknown' ? !plan : plan === filter))
  })

  return (
    <div className="space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-cyan-300">DBCAS Skill Analytics · {tx('admin')}</p>
        <h1 className="mt-2 text-3xl font-bold text-ink">{tx('title')}</h1>
        <p className="mt-2 text-sm text-sub">{tx('intro')}</p>
      </div>
{financialReport && (
  <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
    {[
      ['Doanh thu', financialReport.revenue_vnd],
      ['Chi phí AI', financialReport.ai_cost_vnd],
      ['Chi phí Hosting', financialReport.hosting_cost_vnd],
      ['Số dư còn lại', financialReport.remaining_vnd],
    ].map(([label, value]) => (
      <div className={panel} key={label}>
        <p className="text-sm text-sub">{label}</p>
        <p className="mt-2 text-3xl font-bold text-cyan-300">
          {money(value)}
        </p>
      </div>
    ))}
  </section>
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

      <section className="grid gap-5 lg:grid-cols-2" aria-label={tx('pricing')}>
        <div className={panel}>
          <h2 className="text-lg font-semibold text-ink">{tx('freePackage')}</h2>
          <p className="mt-3 text-3xl font-bold text-ink">{money(prices.free)}</p>
          <p className="mt-3 text-sm text-sub">{tx('freeNote')}</p>
          <span className="mt-4 inline-block rounded-full bg-cyan-400/10 px-3 py-1 text-xs text-cyan-300">{tx('freeBadge')}</span>
        </div>
        <div className={panel}>
          <h2 className="text-lg font-semibold text-ink">{tx('proPackage')}</h2>
          <p className="mt-3 text-3xl font-bold text-cyan-300">{money(prices.pro)}</p>
          <p className="mt-3 text-sm text-sub">{tx('proNote')}</p>
          <form className="mt-5 space-y-3" onSubmit={savePrices}>
            <label htmlFor="pro-price" className="block text-sm font-medium text-ink">{tx('priceLabel')}</label>
            <input id="pro-price" type="number" min="0" step="1" value={proInput} onChange={(e) => { setProInput(e.target.value); setNotice('') }} className={field} />
            <button type="submit" className="rounded-lg bg-cyan-400 px-4 py-2 font-semibold text-slate-950 hover:bg-cyan-300">{tx('savePrice')}</button>
            {notice && <p role="status" className="text-sm text-sub">{tx(notice)}</p>}
          </form>
        </div>
      </section>

      <section className={panel}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-ink">{tx('usersTitle')}</h2>
            <p className="mt-1 text-sm text-sub">{tx('usersHelp')}</p>
          </div>
          <button type="button" onClick={loadAccounts} className="rounded-lg border border-edge2 px-4 py-2 text-sm text-ink hover:bg-surface-hover">{tx('reload')}</button>
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <input aria-label={tx('searchLabel')} placeholder={tx('searchPlaceholder')} value={query} onChange={(e) => setQuery(e.target.value)} className={`${field} max-w-sm`} />
          <select aria-label={tx('filterLabel')} value={filter} onChange={(e) => setFilter(e.target.value)} className={`${field} max-w-xs`}>
            <option value="all">{tx('allPlans')}</option>
            <option value="pro">Pro</option>
            <option value="free">Free</option>
            <option value="unknown">{tx('noData')}</option>
          </select>
        </div>
        {loading ? <p className="mt-4 text-sm text-sub">{tx('loading')}</p> : error ? (
          <p role="alert" className="mt-4 text-sm text-rose-300">{tx('loadError')} {String(error)}</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[650px] text-left text-sm">
              <thead className="border-b border-edge text-sub"><tr>
                <th className="px-3 py-3">{tx('user')}</th><th className="px-3 py-3">Email</th><th className="px-3 py-3">{tx('currentPlan')}</th><th className="px-3 py-3">{tx('subscriptionStatus')}</th>
              </tr></thead>
              <tbody>
                {filteredAccounts.map((account) => (
                  <tr className="border-b border-edge/60" key={account.account_id ?? account.email}>
                    <td className="px-3 py-3 text-ink">{account.full_name || tx('notUpdated')}</td>
                    <td className="px-3 py-3 text-sub">{account.email}</td>
                    <td className="px-3 py-3"><span className="rounded-md border border-edge2 px-2 py-1 text-ink">{knownPlan(account)?.toUpperCase() || tx('noData')}</span></td>
                    <td className="px-3 py-3 text-sub">{knownSubscriptionStatus(account) || tx('noPurchaseData')}</td>
                  </tr>
                ))}
                {!filteredAccounts.length && <tr><td colSpan={4} className="px-3 py-6 text-center text-sub">{tx('noMatches')}</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
