import { useEffect, useState } from 'react'
import api from '../api'
import { useLocale } from '../i18n'

const translations = {
  vi: {
    title: 'Nâng cấp tài khoản',
    subtitle: 'Lựa chọn gói học tập phù hợp với nhu cầu của bạn.',
    freeDesc: 'Đầy đủ tính năng, tối đa 3 lượt làm bài mỗi tháng.',
    proDesc: 'Cùng các tính năng, không giới hạn lượt làm bài trong 30 ngày.',
    freeFeatures: [
      '3 lượt Kiểm tra và Luyện tập mỗi tháng, tự làm mới khi sang tháng',
      'Làm bài MCQ, SQL và tự luận',
      'Xem kết quả và lịch sử làm bài',
      'Đánh giá AI và phân tích kỹ năng CSDL',
      'Lộ trình học tập cá nhân hóa',
      'Theo dõi năng lực và nhận gợi ý học tập',
    ],
    proFeatures: [
      'Không giới hạn phiên đánh giá',
      'Đầy đủ bài MCQ, SQL và tự luận',
      'Đánh giá AI và phân tích kỹ năng CSDL',
      'Lộ trình học tập cá nhân hóa',
      'Xem lịch sử và tiến độ học tập',
      'Bài bắt đầu khi đang dùng Pro không trừ lượt Free',
    ],
    freeButton: 'Gói Free',
    proButton: 'Mua Pro',
    renewButton: 'Gia hạn Pro thêm 30 ngày',
    period: '/30 ngày',
    demo: 'Đơn hàng đã hoàn tất. Gói Pro đã được cập nhật.',
    buyError: 'Không xử lý được đơn hàng. Tài khoản chưa thay đổi.',
    cardNumber: 'Số thẻ',
    expiry: 'Hạn của thẻ (MM/YY)',
    cvc: 'CVC',
    confirm: 'Xác nhận mua Pro',
    cancel: 'Hủy',
    invalidCard:
      'Không xử lý được thẻ này. Kiểm tra số thẻ, hạn thẻ và CVC; tài khoản chưa thay đổi.',
    declined: 'Thẻ bị từ chối. Chưa tạo đơn hàng và tài khoản chưa thay đổi.',
    recommended: 'Đề xuất',
    currentPlan: 'Gói hiện tại:',
    remaining: 'Lượt Free còn lại trong tháng:',
    proActive: 'Gói Pro đang hoạt động. Bạn có thể làm bài dù lượt Free còn 0.',
    proExpiry: 'Pro có hiệu lực đến:',
    loading: 'Đang tải thông tin gói...',
    error: 'Chưa lấy được thông tin gói từ máy chủ.',
    unavailable: 'Chưa có dữ liệu lượt Free.',
    sessionUnit: 'lượt',
  },
  en: {
    title: 'Upgrade Your Account',
    subtitle: 'Choose a learning plan that suits your needs.',
    freeDesc: 'All features, up to 3 sessions each month.',
    proDesc: 'The same features with unlimited sessions for 30 days.',
    freeFeatures: [
      '3 assessment and practice sessions per calendar month',
      'MCQ, SQL and essay assessments',
      'View results and assessment history',
      'AI assessment and database skill analysis',
      'Personalized learning paths',
      'Competency tracking and learning recommendations',
    ],
    proFeatures: [
      'Unlimited assessment sessions',
      'Full MCQ, SQL and essay assessments',
      'AI assessment and database skill analysis',
      'Personalized learning paths',
      'Learning history and progress tracking',
      'Assessments started during Pro do not consume Free sessions',
    ],
    freeButton: 'Free plan',
    proButton: 'Buy Pro',
    renewButton: 'Extend Pro by 30 days',
    period: '/30 days',
    demo: 'The order has been completed. The Pro package has been updated.',
    buyError: 'Could not process the order. Your plan was not changed.',
    cardNumber: 'Card number',
    expiry: 'Card expiry (MM/YY)',
    cvc: 'CVC',
    confirm: 'Confirm Pro purchase',
    cancel: 'Cancel',
    invalidCard:
      'This card could not be processed. Check the number, expiry and CVC; your plan was not changed.',
    declined: 'The card was declined. No order was recorded and your plan was not changed.',
    recommended: 'Recommended',
    currentPlan: 'Current plan:',
    remaining: 'Free sessions remaining this month:',
    proActive: 'Pro is active. You can start assessments even with 0 Free sessions.',
    proExpiry: 'Pro active until:',
    loading: 'Loading plan information...',
    error: 'Unable to load plan information from the server.',
    unavailable: 'Free session balance is unavailable.',
    sessionUnit: 'sessions',
  },
}

const formatVnd = (amount) =>
  new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(amount)

function formatProExpiry(value, locale) {
  const date = new Date(value)
  if (!Number.isFinite(date.getTime())) return ''
  return new Intl.DateTimeFormat(locale === 'en' ? 'en-GB' : 'vi-VN', {
    timeZone: 'Asia/Ho_Chi_Minh',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function testCardResult(number, expiry, cvc) {
  const digits = number.replace(/\s/g, '')
  const match = /^(0[1-9]|1[0-2])\/(\d{2})$/.exec(expiry.trim())
  if (cvc !== '123' || !match) return null
  const year = 2000 + Number(match[2])
  const month = Number(match[1])
  const now = new Date()
  if (year < now.getFullYear() || (year === now.getFullYear() && month < now.getMonth() + 1))
    return null
  if (digits === '4242424242424242') return 'success'
  if (digits === '4000000000000002') return 'declined'
  return null
}

export default function UpgradePage() {
  const { locale } = useLocale()
  const content = translations[locale] || translations.vi

  const [planInfo, setPlanInfo] = useState(null)
  const [planError, setPlanError] = useState(false)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [actionError, setActionError] = useState('')
  const [offer, setOffer] = useState(null)
  const [checkoutOpen, setCheckoutOpen] = useState(false)
  const [cardNumber, setCardNumber] = useState('')
  const [expiry, setExpiry] = useState('')
  const [cvc, setCvc] = useState('')
  const [checkoutRequestId, setCheckoutRequestId] = useState(null)

  useEffect(() => {
    let mounted = true

    api
      .get('/auth/plan')
      .then(({ data }) => {
        if (mounted) {
          setPlanInfo(data)
          setPlanError(false)
        }
      })
      .catch(() => {
        if (mounted) {
          setPlanError(true)
        }
      })

    api
      .get('/auth/pro-demo-offer')
      .then(({ data }) => {
        if (mounted && data?.currency === 'VND') setOffer(data)
      })
      .catch(() => {
        if (mounted) setActionError(content.buyError)
      })

    return () => {
      mounted = false
    }
  }, [])

  const isPro = String(planInfo?.plan || '').toLowerCase() === 'pro'
  const remaining = planInfo?.free_sessions_remaining

  async function activatePro(event) {
    event.preventDefault()
    if (busy) return
    const result = testCardResult(cardNumber, expiry, cvc)
    if (!result) {
      setActionError(content.invalidCard)
      return
    }
    if (result === 'declined') {
      setActionError(content.declined)
      return
    }
    setBusy(true)
    setActionError('')
    setNotice('')
    try {
      const { data } = await api.post('/auth/buy-pro-demo', {
        request_id: checkoutRequestId,
        test_token: 'dbcas-demo-visa-approved',
      })
      setPlanInfo(data)
      setNotice(content.demo)
      setCheckoutOpen(false)
      setCardNumber('')
      setExpiry('')
      setCvc('')
      setCheckoutRequestId(null)
    } catch {
      setActionError(content.buyError)
    } finally {
      setBusy(false)
    }
  }

  const plans = [
    {
      id: 'free',
      name: 'Free Trial',
      price: 0,
      description: content.freeDesc,
      features: content.freeFeatures,
    },
    {
      id: 'pro',
      name: 'Pro',
      price: offer?.price_vnd,
      description: content.proDesc,
      features: content.proFeatures,
    },
  ]

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8">
      <header className="mb-10 text-center">
        <h1 className="text-3xl font-bold text-ink">{content.title}</h1>
        <p className="mt-3 text-sub">{content.subtitle}</p>
      </header>

      {/* Thông tin gói hiện tại từ Backend */}
      <div className="mb-6 rounded-xl border border-edge bg-surface p-4 text-ink">
        {planInfo ? (
          <>
            <p className="font-semibold">
              {content.currentPlan} {isPro ? 'Pro' : 'Free'}
            </p>

            <p className="mt-2 text-sm text-sub">
              {isPro
                ? content.proActive
                : Number.isInteger(remaining)
                  ? `${content.remaining} ${remaining}/3 ${content.sessionUnit}`
                  : content.unavailable}
            </p>
            {isPro && planInfo.pro_expires_at && (
              <p className="mt-2 text-sm text-sub">
                {content.proExpiry} {formatProExpiry(planInfo.pro_expires_at, locale)}
              </p>
            )}
          </>
        ) : (
          <p className="text-sm text-sub">{planError ? content.error : content.loading}</p>
        )}
      </div>

      {/* Danh sách gói Free và Pro */}
      <div className="grid gap-6 md:grid-cols-2">
        {plans.map((plan) => (
          <section
            key={plan.id}
            className={`relative rounded-2xl border bg-surface p-6 shadow-lg ${
              plan.id === 'pro' ? 'border-cyan-400' : 'border-edge'
            }`}
          >
            {plan.id === 'pro' && (
              <span className="absolute right-5 top-5 rounded-full bg-cyan-500 px-3 py-1 text-xs font-bold text-white">
                {content.recommended}
              </span>
            )}

            <h2 className="text-2xl font-bold text-ink">{plan.name}</h2>

            <p className="mt-2 text-sm text-sub">{plan.description}</p>

            <div className="my-6">
              <span className="text-3xl font-bold text-cyan-400">
                {plan.id === 'pro' && !offer ? '…' : formatVnd(plan.price)}
              </span>

              {plan.id === 'pro' && <span className="ml-2 text-sm text-sub">{content.period}</span>}
            </div>

            <ul className="mb-8 space-y-4">
              {plan.features.map((feature) => (
                <li key={feature} className="flex items-start gap-3 text-ink">
                  <span className="font-bold text-emerald-400">✓</span>
                  <span>{feature}</span>
                </li>
              ))}
            </ul>

            {plan.id === 'pro' ? (
              <button
                type="button"
                onClick={() => {
                  setCheckoutRequestId(crypto.randomUUID())
                  setCheckoutOpen(true)
                  setActionError('')
                }}
                disabled={busy || !planInfo || !offer}
                className="w-full rounded-xl bg-cyan-600 px-4 py-3 font-semibold text-white hover:bg-cyan-700 disabled:opacity-50"
              >
                {busy ? '...' : isPro ? content.renewButton : content.proButton}
              </button>
            ) : (
              <div className="w-full rounded-xl bg-slate-600 px-4 py-3 text-center font-semibold text-white">
                {content.freeButton}
              </div>
            )}
          </section>
        ))}
      </div>

      {checkoutOpen && offer && (
        <form
          onSubmit={activatePro}
          className="mt-6 space-y-4 rounded-xl border border-cyan-400 bg-surface p-6 text-ink"
        >
          <h2 className="text-xl font-semibold">
            {locale === 'en' ? 'Payment' : 'Thanh toán'} · {formatVnd(offer.price_vnd)}
          </h2>
          <label className="block">
            {content.cardNumber}
            <input
              value={cardNumber}
              onChange={(e) => setCardNumber(e.target.value)}
              inputMode="numeric"
              autoComplete="off"
              maxLength={23}
              className="mt-1 block w-full rounded-lg border border-edge2 bg-abyss p-3 text-ink"
            />
          </label>
          <div className="flex gap-4">
            <label className="flex-1">
              {content.expiry}
              <input
                value={expiry}
                onChange={(e) => setExpiry(e.target.value)}
                placeholder="MM/YY"
                autoComplete="off"
                maxLength={5}
                className="mt-1 block w-full rounded-lg border border-edge2 bg-abyss p-3 text-ink"
              />
            </label>
            <label className="flex-1">
              {content.cvc}
              <input
                value={cvc}
                onChange={(e) => setCvc(e.target.value)}
                inputMode="numeric"
                autoComplete="off"
                maxLength={3}
                className="mt-1 block w-full rounded-lg border border-edge2 bg-abyss p-3 text-ink"
              />
            </label>
          </div>
          <div className="flex gap-3">
            <button
              disabled={busy}
              className="rounded-lg bg-cyan-600 px-5 py-3 font-semibold text-white disabled:opacity-50"
            >
              {content.confirm}
            </button>
            <button
              type="button"
              onClick={() => {
                setCheckoutOpen(false)
                setCheckoutRequestId(null)
                setCardNumber('')
                setExpiry('')
                setCvc('')
              }}
              className="rounded-lg border border-edge2 px-5 py-3"
            >
              {content.cancel}
            </button>
          </div>
        </form>
      )}

      {actionError && (
        <p role="alert" className="mt-6 text-rose-400">
          {actionError}
        </p>
      )}
      {notice && (
        <div role="status" className="mt-6 rounded-xl border border-cyan-400 p-4 text-ink">
          {notice}
        </div>
      )}
    </div>
  )
}
