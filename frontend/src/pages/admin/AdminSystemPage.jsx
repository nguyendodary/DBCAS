import { useEffect, useState } from 'react'
import api, { apiMessage } from '../../api'
import { Card, btnPrimary } from '../../components/ui'
import { Loading, ErrorState } from '../../components/States'
import { AdminPageHeader } from '../../components/admin'

export default function AdminSystemPage() {
  const [data, setData] = useState(null)
  const [flow, setFlow] = useState('IMMEDIATE')
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(false)
  const [busy, setBusy] = useState(false)
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    let canceled = false
    setError(null)
    api
      .get('/admin/system')
      .then((r) => {
        if (!canceled) {
          setData(r.data)
          setFlow(r.data.result_flow)
        }
      })
      .catch((e) => {
        if (!canceled) setError(apiMessage(e))
      })
    return () => {
      canceled = true
    }
  }, [retry])
  async function save(event) {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError(null)
    setSaved(false)
    try {
      const r = await api.put('/admin/system', { result_flow: flow })
      setData(r.data)
      setSaved(true)
    } catch (e) {
      setError(apiMessage(e))
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="space-y-5">
      <AdminPageHeader title="Hệ thống" subtitle="Cấu hình dùng chung trên máy local." />
      {error && <ErrorState message={error} onRetry={() => setRetry((value) => value + 1)} />}
      {!data ? (
        !error && <Loading />
      ) : (
        <>
          <Card className="p-5">
            <form className="space-y-5" onSubmit={save}>
              <fieldset disabled={busy} className="space-y-3">
                <legend className="mb-3 text-lg font-semibold">Luồng công bố kết quả</legend>
                {[
                  ['IMMEDIATE', 'Tự động', 'Công bố ngay khi chấm điểm và đánh giá hoàn tất.'],
                  [
                    'HUMAN_VERIFIED',
                    'Admin duyệt',
                    'Người học chờ giảng viên kiểm tra và duyệt bài.',
                  ],
                ].map(([value, title, help]) => (
                  <label
                    key={value}
                    className="flex cursor-pointer gap-3 rounded-xl border border-edge p-4"
                  >
                    <input
                      type="radio"
                      name="result-flow"
                      value={value}
                      checked={flow === value}
                      onChange={() => {
                        setFlow(value)
                        setSaved(false)
                      }}
                    />
                    <span>
                      <strong>{title}</strong>
                      <span className="mt-1 block text-sm text-sub">{help}</span>
                    </span>
                  </label>
                ))}
              </fieldset>
              <p className="text-sm text-sub">
                Áp dụng cho bài bắt đầu sau khi lưu. Bài đã bắt đầu giữ luồng lúc tạo.
              </p>
              <button className={btnPrimary} disabled={busy || flow === data.result_flow}>
                {busy ? 'Đang lưu...' : 'Lưu cấu hình'}
              </button>
              {saved && <p role="status">Đã lưu cấu hình.</p>}
            </form>
          </Card>
          <Card className="space-y-3 p-5">
            <h2 className="text-lg font-semibold">Trạng thái AI</h2>
            <p>
              Prompt Builder:{' '}
              {data.prompt_builder_configured
                ? 'Đã đặt đường dẫn model local · kiểm tra prompt trước khi dùng'
                : 'Template dự phòng sẵn sàng'}
            </p>
            <p>
              Evaluator:{' '}
              {data.evaluator_configured
                ? 'Đã cấu hình API · có fallback khi lỗi'
                : 'Đánh giá dự phòng theo quy tắc'}
            </p>
            <p className="text-sm text-sub">
              API key chỉ đặt trong biến môi trường LLM_API_KEY. Không hiển thị khóa trên giao diện.
            </p>
          </Card>
          <Card className="space-y-2 p-5">
            <h2 className="text-lg font-semibold">Thông tin cơ bản</h2>
            <p>Chạy local · {data.database}</p>
            <p>{data.pipeline}</p>
          </Card>
        </>
      )}
    </div>
  )
}
