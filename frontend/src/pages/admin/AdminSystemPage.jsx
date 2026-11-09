import { useEffect, useState } from 'react'
import api, { apiMessage } from '../../api'
import { Card } from '../../components/ui'
import { Loading, ErrorState } from '../../components/States'
import { AdminPageHeader } from '../../components/admin'

export default function AdminSystemPage() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    let canceled = false
    setError(null)
    api
      .get('/admin/system')
      .then((r) => {
        if (!canceled) setData(r.data)
      })
      .catch((e) => {
        if (!canceled) setError(apiMessage(e))
      })
    return () => {
      canceled = true
    }
  }, [retry])
  return (
    <div className="space-y-5">
      <AdminPageHeader title="Hệ thống" subtitle="Cấu hình dùng chung trên máy local." />
      {error && <ErrorState message={error} onRetry={() => setRetry((value) => value + 1)} />}
      {!data ? (
        !error && <Loading />
      ) : (
        <>
          <Card className="space-y-3 p-5">
            <h2 className="text-lg font-semibold">Quy trình công bố kết quả</h2>
            <p className="text-sub">
              Mọi bài nộp đều đi qua hai bước. Không có lựa chọn luồng và Admin không cần chọn giữa
              kết quả AI với kết quả đã duyệt.
            </p>
            <ol className="list-decimal space-y-2 pl-5 text-sub">
              <li>
                <strong>AI chấm và đánh giá sơ bộ</strong> ngay sau khi người học nộp bài.
              </li>
              <li>
                <strong>Admin kiểm tra bài nộp:</strong> đối chiếu đáp án, chạy SQL kiểm tra, xem
                nhận xét AI và điều chỉnh điểm nếu cần.
              </li>
              <li>
                <strong>Admin duyệt:</strong> kết quả chính thức được công bố và bài làm chuyển sang
                trạng thái <em>admin-reviewed</em>.
              </li>
            </ol>
            <p className="text-sm text-sub">
              Kết quả AI chỉ là bản tạm tính. Chỉ bài đã được Admin duyệt mới được tính vào đánh giá
              tổng thể và thống kê.
            </p>
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
