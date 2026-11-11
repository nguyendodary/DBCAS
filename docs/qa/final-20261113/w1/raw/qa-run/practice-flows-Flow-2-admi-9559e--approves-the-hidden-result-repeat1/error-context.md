# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: practice-flows.spec.js >> Flow 2: admin verifies SQL, adjusts with a reason and approves the hidden result
- Location: e2e\practice-flows.spec.js:148:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText(/Thành công · 1 dòng/)
Expected: visible
Timeout: 20000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByText(/Thành công · 1 dòng/) with timeout 20000ms
  - waiting for getByText(/Thành công · 1 dòng/)

```

```yaml
- link "Chuyển đến nội dung":
  - /url: "#main-content"
- complementary:
  - link "DBCAS":
    - /url: /
    - text: DBCAS SKILL ANALYTICS
  - link "Duyệt bài":
    - /url: /admin/grading
  - navigation "Điều hướng chính":
    - link "Tổng quan nhóm":
      - /url: /admin
    - link "Duyệt bài":
      - /url: /admin/grading
    - link "Tài khoản":
      - /url: /admin/accounts
    - link "Ngân hàng & khái niệm/CLO":
      - /url: /admin/questions
    - link "Hệ thống":
      - /url: /admin/system
  - button "Đăng xuất"
- banner:
  - paragraph: DBCAS Quản trị
  - button "Hướng dẫn"
  - button "Ngôn ngữ"
  - button "Chuyển sang giao diện sáng"
  - text: Q
  - paragraph: Quản trị demo
  - paragraph: admin@dbcas.local
- main:
  - heading "Duyệt bài" [level=1]
  - paragraph: Kiểm tra từng câu SQL và tự luận đã nộp, sau đó công bố kết quả chính thức. Đánh giá tự động ban đầu được giữ trong nhật ký.
  - button "Làm mới kết quả"
  - 'button "Nguyễn An · Luyện tập tự chọn · #6 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #7 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #8 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #9 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #10 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #11 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #12 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #13 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #14 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #15 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #16 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #17 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #18 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #19 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #20 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #21 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #22 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #23 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #24 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #25 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #26 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #27 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #28 Chờ giảng viên duyệt"'
  - 'button "Nguyễn An · Luyện tập tự chọn · #29 Chờ giảng viên duyệt"'
  - 'button "Học viên walkthrough 20261111 · Luyện tập tự chọn · #40 Chờ giảng viên duyệt"'
  - 'button "W1 Limits Learner · Luyện tập tự chọn · #62 Chờ giảng viên duyệt"'
  - 'button "W1 Limits Learner · Luyện tập tự chọn · #63 Chờ giảng viên duyệt"'
  - 'button "W1 Limits Learner · Luyện tập tự chọn · #64 Chờ giảng viên duyệt"'
  - 'button "W1 Limits Learner · Luyện tập tự chọn · #69 Chờ giảng viên duyệt"'
  - 'button "W1 Limits Learner · Luyện tập tự chọn · #70 Chờ giảng viên duyệt"'
  - 'button "W1 Limits Learner · Luyện tập tự chọn · #71 Chờ giảng viên duyệt"'
  - 'button "W1 Limits Learner · Luyện tập tự chọn · #76 Chờ giảng viên duyệt"'
  - 'button "W1 Limits Learner · Luyện tập tự chọn · #77 Chờ giảng viên duyệt"'
  - 'button "W1 Limits Learner · Luyện tập tự chọn · #78 Chờ giảng viên duyệt"'
  - 'button "W1 Limits Learner · Luyện tập tự chọn · #83 Chờ giảng viên duyệt"'
  - 'button "W1 Limits Learner · Luyện tập tự chọn · #84 Chờ giảng viên duyệt"'
  - 'button "W1 Limits Learner · Luyện tập tự chọn · #85 Chờ giảng viên duyệt"'
  - 'button "W1 Practice Learner · Luyện tập tự chọn · #50 Chờ giảng viên duyệt"'
  - 'button "W1 Practice Learner · Luyện tập tự chọn · #51 Chờ giảng viên duyệt"'
  - 'button "W1 Expiry Learner · Luyện tập tự chọn · #65 Chờ giảng viên duyệt"'
  - 'button "W1 Expiry Learner · Luyện tập tự chọn · #72 Chờ giảng viên duyệt"'
  - 'button "W1 Expiry Learner · Luyện tập tự chọn · #79 Chờ giảng viên duyệt"'
  - 'button "Học viên kiểm thử · Luyện tập tự chọn · #110 Chờ giảng viên duyệt"'
  - region "Chi tiết duyệt bài làm":
    - 'heading "Học viên kiểm thử · Luyện tập tự chọn · #110" [level=2]'
    - status: Chờ giảng viên duyệt
    - button "Duyệt"
    - heading "Đánh giá AI" [level=3]
    - paragraph: Đã tổng hợp 1 bài. 0/3 câu trong dữ liệu chi tiết đạt điểm tối đa. Đánh giá dự phòng theo quy tắc; chưa xác nhận chất lượng bởi mô hình thực.
    - list:
      - listitem: "Câu 1: Đối chiếu câu trả lời với đáp án và rubric; luyện lại phần chưa đạt."
      - listitem: "Câu 2: Đối chiếu câu trả lời với đáp án và rubric; luyện lại phần chưa đạt."
      - listitem: "Câu 3: Đối chiếu câu trả lời với đáp án và rubric; luyện lại phần chưa đạt. Điểm tự luận theo quy tắc chỉ là đề xuất, cần đối chiếu rubric."
    - text: SQL Bắt buộc duyệt
    - heading [level=3]
    - paragraph: Câu trả lời của người học
    - text: SELECT 1
    - group: Đáp án tham chiếu / tiêu chí cần đạt
    - paragraph: "Điểm hiện tại: 0 / 1"
    - group: Nhận xét tự động và kết quả kiểm tra SQL
    - text: SQL kiểm tra (chỉ SELECT)
    - textbox "SQL kiểm tra (chỉ SELECT)": SELECT 1
    - button "Đang chạy..." [disabled]
    - group:
      - text: Điểm đã duyệt
      - spinbutton "Điểm đã duyệt": "0"
      - text: Lý do điều chỉnh
      - textbox "Lý do điều chỉnh"
      - button "Lưu điểm điều chỉnh"
    - text: Tự luận Bắt buộc duyệt
    - heading [level=3]
    - paragraph: Câu trả lời của người học
    - text: Chuẩn hóa giúp giảm lặp dữ liệu và tránh bất thường cập nhật. Cần xét khóa, phụ thuộc hàm và phép phân rã không mất mát.
    - group: Đáp án tham chiếu / tiêu chí cần đạt
    - group: Thang chấm điểm
    - paragraph: "Điểm hiện tại: 1,17 / 5"
    - group: Nhận xét tự động và kết quả kiểm tra SQL
    - group:
      - text: Điểm đã duyệt
      - spinbutton "Điểm đã duyệt": "1.17"
      - text: Lý do điều chỉnh
      - textbox "Lý do điều chỉnh"
      - button "Lưu điểm điều chỉnh"
    - group: Trắc nghiệm đã chấm tự động (xem khi cần)
    - heading "Lịch sử công bố" [level=3]
    - list:
      - listitem: 15:12 11 thg 11, 2026 · Chờ nộp bài → Đang chấm bài
      - listitem: 15:12 11 thg 11, 2026 · Đang chấm bài → Chờ giảng viên duyệt
- contentinfo:
  - paragraph:
    - strong: DBCAS
    - text: Nền tảng đánh giá năng lực CSDL
  - paragraph: © 2026 DBCAS
```

# Test source

```ts
  77  |       contentType: 'application/json',
  78  |     })
  79  |     expect(errors).toEqual([])
  80  |   } finally {
  81  |     await learnerContext.close()
  82  |     await adminContext.close()
  83  |   }
  84  | })
  85  | 
  86  | test('AI-generated source stays inside chosen concepts and hard difficulty', async ({
  87  |   page,
  88  | }, info) => {
  89  |   await register(page, 'generated')
  90  |   await page.goto('/assessments')
  91  |   const options = await api(page, '/practice/options')
  92  |   const chosen = options.concepts[0]
  93  |   await page.getByRole('button', { name: chosen.concept_name, exact: true }).click()
  94  |   await page.getByRole('button', { name: /Dễ/ }).click()
  95  |   await page.getByRole('button', { name: /Vừa/ }).click()
  96  |   await page.getByRole('radio', { name: 'AI tạo câu hỏi', exact: true }).check()
  97  |   await page.getByLabel('Số câu (1–20)').fill('3')
  98  |   const started = page.waitForResponse(
  99  |     (r) =>
  100 |       new URL(r.url()).pathname === '/api/v1/practice/start' && r.request().method() === 'POST',
  101 |   )
  102 |   await page.getByRole('button', { name: 'Bắt đầu', exact: true }).click()
  103 |   const response = await started
  104 |   expect(response.ok()).toBe(true)
  105 |   const state = await response.json()
  106 |   expect(state.selected_concept_ids).toEqual([chosen.concept_id])
  107 |   expect(state.question_source).toBe('ai')
  108 |   if (process.env.DBCAS_QA_PROVIDER_URL) {
  109 |     expect(state.generation_fallback).toBe(true)
  110 |     expect(state.bank_mixed).toBe(true)
  111 |     expect(state.template_fallback).toBe(false)
  112 |     expect(state.ai_generated_count).toBe(2)
  113 |   }
  114 |   await expect(page).toHaveURL(/\/exam\/\d+$/)
  115 |   expect(state.current_question.difficulty_level).toBeGreaterThanOrEqual(4)
  116 |   await expect(page.getByText(state.current_question.prompt, { exact: true })).toBeVisible()
  117 |   await page.screenshot({ path: info.outputPath('generated-source.png'), fullPage: true })
  118 |   const { sid } = await take(page, state)
  119 |   const adminContext = await page
  120 |     .context()
  121 |     .browser()
  122 |     .newContext({ baseURL: info.project.use.baseURL })
  123 |   try {
  124 |     const admin = await adminContext.newPage()
  125 |     await login(admin, 'admin@dbcas.local')
  126 |     await approve(admin, sid)
  127 |   } finally {
  128 |     await adminContext.close()
  129 |   }
  130 |   await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
  131 |     timeout: 45000,
  132 |   })
  133 |   const evidence = await api(page, `/sessions/${sid}/evidence`)
  134 |   expect(evidence.items).toHaveLength(3)
  135 |   expect(new Set(evidence.items.map((item) => item.question_type))).toEqual(
  136 |     new Set(['mcq', 'sql', 'essay']),
  137 |   )
  138 |   for (const item of evidence.items) {
  139 |     expect(item.difficulty_level).toBeGreaterThanOrEqual(4)
  140 |     expect(item.concepts.map((c) => c.concept_id)).toEqual([chosen.concept_id])
  141 |     if (item.question_type === 'mcq')
  142 |       expect(item.options.filter((o) => o.is_correct)).toHaveLength(1)
  143 |     else if (item.question_type === 'essay') expect(item.rubrics).toHaveLength(4)
  144 |     else expect(item.sql_answer).toBeTruthy()
  145 |   }
  146 | })
  147 | 
  148 | test('Flow 2: admin verifies SQL, adjusts with a reason and approves the hidden result', async ({
  149 |   browser,
  150 | }, info) => {
  151 |   const adminContext = await browser.newContext({ baseURL: info.project.use.baseURL })
  152 |   const learnerContext = await browser.newContext({ baseURL: info.project.use.baseURL })
  153 |   const admin = await adminContext.newPage(),
  154 |     learner = await learnerContext.newPage()
  155 |   try {
  156 |     await login(admin, 'admin@dbcas.local')
  157 |     await setFlow(admin, 'HUMAN_VERIFIED')
  158 |     const cohortBefore = await api(admin, '/admin/analytics/cohort')
  159 |     await register(learner, 'review')
  160 |     const state = await start(learner)
  161 |     const { sid } = await take(learner, state, { approveAfter: false })
  162 |     await expect(
  163 |       learner.getByRole('heading', { name: 'Đang chờ giảng viên duyệt', exact: true }),
  164 |     ).toBeVisible()
  165 |     await expect(learner.getByRole('heading', { name: 'Nhận xét từng câu' })).toHaveCount(0)
  166 |     expect((await api(learner, '/sessions/statistics')).published_formal_sessions).toBe(0)
  167 |     const cohortPending = await api(admin, '/admin/analytics/cohort')
  168 |     expect(cohortPending).toEqual(cohortBefore)
  169 |     await learner.screenshot({ path: info.outputPath('waiting-approval.png'), fullPage: true })
  170 |     // Instructor review may outlast the AI polling budget; approval still arrives automatically.
  171 |     await learner.waitForTimeout(46000)
  172 |     await admin.goto(`/admin/grading/${sid}`)
  173 |     await expect(admin.getByRole('button', { name: 'Duyệt', exact: true })).toBeEnabled({
  174 |       timeout: 45000,
  175 |     })
  176 |     await admin.getByRole('button', { name: 'Chạy SQL kiểm tra', exact: true }).click()
> 177 |     await expect(admin.getByText(/Thành công · 1 dòng/)).toBeVisible()
      |                                                          ^ Error: expect(locator).toBeVisible() failed
  178 |     const sql = admin.getByLabel('SQL kiểm tra (chỉ SELECT)')
  179 |     await sql.fill('DELETE FROM students')
  180 |     await admin.getByRole('button', { name: 'Chạy SQL kiểm tra', exact: true }).click()
  181 |     await expect(admin.getByText(/Không chạy được truy vấn/)).toBeVisible()
  182 |     const form = admin.locator('form').first()
  183 |     await form.getByRole('spinbutton').fill('0.25')
  184 |     await expect(form.getByLabel('Lý do điều chỉnh')).toHaveAttribute('required', '')
  185 |     await form.getByLabel('Lý do điều chỉnh').fill('Điều chỉnh theo rubric sau khi kiểm tra SQL.')
  186 |     await form.getByRole('button', { name: 'Lưu điểm điều chỉnh' }).click()
  187 |     await expect(admin.getByRole('heading', { name: 'Lịch sử điều chỉnh điểm' })).toBeVisible()
  188 |     await expect(admin.getByRole('button', { name: 'Duyệt', exact: true })).toBeEnabled({
  189 |       timeout: 45000,
  190 |     })
  191 |     await expect(admin.getByRole('button', { name: new RegExp(`#${sid}\\b`) })).toContainText(
  192 |       vi.supervisor.pending_review,
  193 |     )
  194 |     await expect(admin.getByText(/^Điểm hiện tại:/).first()).toContainText('0,25')
  195 |     await admin.screenshot({ path: info.outputPath('admin-review.png'), fullPage: true })
  196 |     await admin.getByRole('button', { name: 'Duyệt', exact: true }).click()
  197 |     await learner.getByRole('button', { name: 'Kiểm tra cập nhật', exact: true }).click()
  198 |     await expect(learner.getByText(/Đã được giảng viên duyệt/)).toBeVisible({ timeout: 45000 })
  199 |     await expect(learner.getByText('Điểm đã được điều chỉnh', { exact: true })).toBeVisible()
  200 |     const review = await api(admin, `/admin/grading-reviews/${sid}`)
  201 |     expect(review.score_edits).toHaveLength(1)
  202 |     expect(review.score_edits[0].reason).toContain('rubric')
  203 |     expect(review.events.at(-1).reviewer_id).toBeTruthy()
  204 |     expect((await api(admin, '/admin/analytics/cohort')).finalized_sessions).toBe(
  205 |       cohortBefore.finalized_sessions + 1,
  206 |     )
  207 |     await checkArithmetic(learner, sid)
  208 |     await learner.screenshot({ path: info.outputPath('approved-result.png'), fullPage: true })
  209 |   } finally {
  210 |     await setFlow(admin, 'IMMEDIATE')
  211 |     await learnerContext.close()
  212 |     await adminContext.close()
  213 |   }
  214 | })
  215 | 
  216 | test('Admin navigation has five focused screens and no exam creation surface', async ({
  217 |   page,
  218 | }, info) => {
  219 |   await login(page, 'admin@dbcas.local')
  220 |   const menu = page.locator('.app-sidebar nav')
  221 |   expect(await menu.getByRole('link').count()).toBe(5)
  222 |   expect(
  223 |     await menu
  224 |       .getByRole('link')
  225 |       .evaluateAll((nodes) => nodes.map((node) => node.getAttribute('href'))),
  226 |   ).toEqual(['/admin', '/admin/grading', '/admin/accounts', '/admin/questions', '/admin/system'])
  227 |   for (const route of ['/admin/grading', '/admin/accounts', '/admin/questions', '/admin/system']) {
  228 |     await page.goto(route)
  229 |     await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  230 |     await checkViewport(page)
  231 |   }
  232 |   const token = await page.evaluate(() => localStorage.getItem('dbcas_token'))
  233 |   expect(
  234 |     (
  235 |       await page.request.post('/api/v1/admin/assessments', {
  236 |         data: {},
  237 |         headers: { Authorization: `Bearer ${token}` },
  238 |       })
  239 |     ).status(),
  240 |   ).toBe(404)
  241 |   await page.screenshot({ path: info.outputPath('admin-system.png'), fullPage: true })
  242 | })
  243 | 
  244 | test('390px mobile learner setup, attempt and evaluation fit the viewport', async ({
  245 |   page,
  246 | }, info) => {
  247 |   await page.setViewportSize({ width: 390, height: 844 })
  248 |   await register(page, 'mobile')
  249 |   const state = await start(page, 'ai', 3)
  250 |   await checkViewport(page)
  251 |   await page.screenshot({ path: info.outputPath('mobile-attempt.png'), fullPage: true })
  252 |   const { sid } = await take(page, state)
  253 |   const adminContext = await page
  254 |     .context()
  255 |     .browser()
  256 |     .newContext({ baseURL: info.project.use.baseURL })
  257 |   try {
  258 |     const admin = await adminContext.newPage()
  259 |     await login(admin, 'admin@dbcas.local')
  260 |     await approve(admin, sid)
  261 |   } finally {
  262 |     await adminContext.close()
  263 |   }
  264 |   await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
  265 |     timeout: 45000,
  266 |   })
  267 |   await checkViewport(page)
  268 |   await page.screenshot({ path: info.outputPath('mobile-evaluation.png'), fullPage: true })
  269 |   await page.goto('/assessments')
  270 |   await expect(page.getByRole('button', { name: 'Bắt đầu', exact: true })).toBeVisible()
  271 |   await checkViewport(page)
  272 |   await page.screenshot({ path: info.outputPath('mobile-setup.png'), fullPage: true })
  273 | })
  274 | 
  275 | test('provider outage uses a bounded fallback and caches the unchanged evaluation', async ({
  276 |   page,
  277 | }, info) => {
```