import { useState } from 'react'
import { useLocale } from '../i18n'

const translations = {
  vi: {
    title: 'Nâng cấp tài khoản',
    subtitle: 'Lựa chọn gói học tập phù hợp với nhu cầu của bạn.',
    freeDesc: 'Trải nghiệm các tính năng đánh giá cơ sở dữ liệu.',
    proDesc: 'Mở rộng khả năng đánh giá và phát triển kỹ năng.',
    freeFeatures: [
      '3 phiên đánh giá miễn phí',
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
    ],
    freeButton: 'Chọn gói Free',
    proButton: 'Chọn gói Pro',
    period: '/30 ngày',
    selected: 'Bạn đã chọn gói',
    demo: 'Đây là bản minh họa. Chưa thực hiện thanh toán hoặc kích hoạt gói.',
    recommended: 'Đề xuất',
  },
  en: {
    title: 'Upgrade Your Account',
    subtitle: 'Choose a learning plan that suits your needs.',
    freeDesc: 'Explore essential database assessment features.',
    proDesc: 'Unlock more assessment and learning opportunities.',
    freeFeatures: [
      '3 free assessment sessions',
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
    ],
    freeButton: 'Choose Free',
    proButton: 'Choose Pro',
    period: '/30 days',
    selected: 'You selected',
    demo: 'This is a demonstration. No payment or subscription is activated.',
    recommended: 'Recommended',
  },
}

export default function UpgradePage() {
  const { locale } = useLocale()
  const content = translations[locale] || translations.vi
  const [selectedPlan, setSelectedPlan] = useState(null)

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
