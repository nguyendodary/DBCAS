import { useEffect, useState } from 'react'
import api from '../api'
import { useLocale } from '../i18n'

const translations = {
  vi: {
    title: 'Nâng cấp tài khoản',
    subtitle: 'Lựa chọn gói học tập phù hợp với nhu cầu của bạn.',
    freeDesc: 'Trải nghiệm các tính năng đánh giá cơ sở dữ liệu.',
    proDesc: 'Mở rộng khả năng đánh giá và phát triển kỹ năng.',
    freeFeatures: [
      '3 lượt làm bài miễn phí mỗi tháng , tự làm mới khi sang tháng',
      'Làm bài MCQ, SQL và tự luận',
      'Xem kết quả và lịch sử làm bài',
      'Theo dõi năng lực cơ bản',
      'Nhận gợi ý học tập cơ bản',
    ],
    proFeatures: [
      'Không giới hạn phiên đánh giá',
      'Đầy đủ bài MCQ, SQL và tự luận',
      'Đánh giá AI nâng cao',
      'Phân tích chi tiết 10 kỹ năng CSDL',
      'Lộ trình học tập cá nhân hóa',
      'Xem lịch sử và tiến độ học tập',
      'Bài bắt đầu khi đang dùng Pro không trừ lượt Free',
    ],
    freeButton: 'Chọn gói Free',
    proButton: 'Chọn gói Pro',
    period: '/30 ngày',
    selected: 'Bạn đã chọn gói',
    demo: 'Đây là bản minh họa. Chưa thực hiện thanh toán hoặc kích hoạt gói.',
    recommended: 'Đề xuất',
    currentPlan: 'Gói hiện tại:',
    remaining: 'Lượt Free còn lại trong tháng:',
    proActive: 'Gói Pro đang hoạt động. Bạn có thể làm bài dù lượt Free còn 0.',
    loading: 'Đang tải thông tin gói...',
    error: 'Chưa lấy được thông tin gói từ máy chủ.',
    unavailable: 'Chưa có dữ liệu lượt Free.',
    sessionUnit: 'lượt',
  },
  en: {
    title: 'Upgrade Your Account',
    subtitle: 'Choose a learning plan that suits your needs.',
    freeDesc: 'Explore essential database assessment features.',
    proDesc: 'Unlock more assessment and learning opportunities.',
    freeFeatures: [
      '3 free assessment sessions per calendar month , reset monthly',
      'MCQ, SQL and essay assessments',
      'View results and assessment history',
      'Basic competency tracking',
      'Basic learning recommendations',
    ],
    proFeatures: [
      'Unlimited assessment sessions',
      'Full MCQ, SQL and essay assessments',
      'Advanced AI assessment',
      'Detailed analysis of 10 database skills',
      'Personalized learning paths',
      'Learning history and progress tracking',
      'Assessments started during Pro do not consume Free sessions',
    ],
    freeButton: 'Choose Free',
    proButton: 'Choose Pro',
    period: '/30 days',
    selected: 'You selected',
    demo: 'This is a demonstration. No payment or subscription is activated.',
    recommended: 'Recommended',
    currentPlan: 'Current plan:',
    remaining: 'Free sessions remaining this month:',
    proActive: 'Pro is active. You can start assessments even with 0 Free sessions.',
    loading: 'Loading plan information...',
    error: 'Unable to load plan information from the server.',
    unavailable: 'Free session balance is unavailable.',
    sessionUnit: 'sessions',
  },
}

export default function UpgradePage() {
  const { locale } = useLocale()
  const content = translations[locale] || translations.vi

  const [selectedPlan, setSelectedPlan] = useState(null)
  const [planInfo, setPlanInfo] = useState(null)
  const [planError, setPlanError] = useState(false)

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

    return () => {
      mounted = false
    }
  }, [])

  const isPro = String(planInfo?.plan || '').toLowerCase() === 'pro'
  const remaining = planInfo?.free_sessions_remaining

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
      price: 99000,
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
                {new Intl.NumberFormat(locale === 'en' ? 'en-US' : 'vi-VN').format(plan.price)} VND
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

            <button
              type="button"
              onClick={() => setSelectedPlan(plan.id)}
              className={`w-full rounded-xl px-4 py-3 font-semibold text-white ${
                plan.id === 'pro'
                  ? 'bg-cyan-600 hover:bg-cyan-700'
                  : 'bg-slate-600 hover:bg-slate-700'
              }`}
            >
              {plan.id === 'free' ? content.freeButton : content.proButton}
            </button>
          </section>
        ))}
      </div>

      {/* Thông báo chọn gói minh họa */}
      {selectedPlan && (
        <div role="status" className="mt-6 rounded-xl border border-cyan-400 p-4 text-ink">
          <p>
            {content.selected} {selectedPlan === 'free' ? 'Free Trial' : 'Pro'}.
          </p>
          <p className="mt-1 text-sm text-sub">{content.demo}</p>
        </div>
      )}
    </div>
  )
}
