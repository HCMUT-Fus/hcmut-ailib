# KẾ HOẠCH DỰ ÁN CHI TIẾT (PROJECT PLAN) — HCMUT-AILIB
> **Học phần:** CO2001 – Kỹ năng nghề nghiệp cho Kỹ sư (Professional Skills for Engineers)  
> **Khoa:** Khoa Khoa học và Kỹ thuật Máy tính (CSE) — Trường Đại học Bách Khoa, ĐHQG-HCM  
> **Dự án:** HCMUT-AILib — A Zero-Resource Semantic Retrieval and Research Assistant for Digital Academic Libraries  
> **Repository:** [github.com/HCMUT-Fus/hcmut-ailib](https://github.com/HCMUT-Fus/hcmut-ailib)  
> **Giấy phép (License):** GNU General Public License v3.0 (GNU GPLv3)  
> **Quy mô:** Nhóm 4 thành viên | **Thời gian thực hiện:** 8 Tuần  

---

## 1. TỔNG QUAN DỰ ÁN & MỤC TIÊU KỸ THUẬT

### 1.1. Bối cảnh & Vấn đề (Step 1: Identify the Problem)
Các hệ thống quản lý thư viện truyền thống (OPAC - Online Public Access Catalog) chủ yếu dựa trên đối sánh chuỗi ký tự (exact string matching) và các toán tử Boolean cơ bản. Cơ chế này gặp phải rào cản lớn về **"Vocabulary Mismatch"** (bất đồng bộ từ vựng), khiến người dùng nghiên cứu không thể tìm thấy các tài liệu học thuật liên quan khi tra cứu bằng ngôn ngữ tự nhiên, thuật ngữ chuyên ngành liên ngành hoặc tìm kiếm theo khái niệm ngữ nghĩa.

**HCMUT-AILib** được thiết kế nhằm giải quyết bài toán trên bằng cách xây dựng một công cụ tìm kiếm ngữ nghĩa (Semantic Vector Search) và trợ lý hỗ trợ khám phá tài liệu khoa học cục bộ (Local-first, Zero-cost), vận hành độc lập trên máy tính cá nhân mà không tốn chi phí điện toán đám mây.

### 1.2. Tiêu chí & Ràng buộc Kỹ thuật (Step 2: Criteria & Constraints)
- **Chi phí vận hành ($0.00 - Zero-cost):** Không sử dụng các API đám mây trả phí (OpenAI, Claude); sử dụng 100% tài nguyên mã nguồn mở và API miễn phí.
- **Ràng buộc phần cứng tiêu chuẩn (Zero Physical Goods):** Hoạt động mượt mà trên máy tính sinh viên thông thường (CPU 4 nhân, 8GB RAM, không yêu cầu GPU rời).
- **Tiêu chí hiệu năng (Latency Criterion):** Thời gian phản hồi truy vấn dưới **1.5 giây** cho tập dữ liệu mẫu 1,000 bài báo khoa học.
- **Tiêu chí độ chính xác (Accuracy Criterion):** Điểm **Mean Reciprocal Rank (MRR) > 0.7** trên tập dữ liệu kiểm thử chuẩn gồm 30 câu hỏi truy vấn khoa học có gán nhãn thực nghiệm (Ground Truth).
- **Pháp lý & Đạo đức (Ethics & Legal):** Tuân thủ nghiêm ngặt **Luật Công nghệ Thông tin** và **Luật Sở hữu Trí tuệ Việt Nam**, bảo đảm các điều khoản khai thác dữ liệu học thuật mở từ arXiv API, phân phối theo giấy phép **GNU GPLv3**.

### 1.3. Lựa chọn Kiến trúc Kỹ thuật (Steps 3–6: Design Selection)
Hệ thống lựa chọn phương án **Local Dense Vector Retrieval** (Option C trong phân tích khả thi):
- **Data Ingestion:** Thu thập metadata mở của 1,000 bài báo từ arXiv API qua script tự động (`src/ingest.py`).
- **Embedding Model:** `all-MiniLM-L6-v2` (Sentence-Transformers) với kích thước nhỏ gọn (~120MB RAM, 384 dimensions), tối ưu hóa suy luận trên CPU.
- **Vector Database:** **ChromaDB** chạy ở chế độ nhúng cục bộ (Embedded Local Storage Mode) tại `data/processed/vector_index/`.
- **User Interface:** **Streamlit** (`src/app.py`) cung cấp giao diện tương tác tức thì, trực quan và không phụ thuộc cấu hình phức tạp.

---

## 2. CƠ CẤU NHÂN SỰ & PHÂN CÔNG TRÁCH NHIỆM

Nhóm gồm 4 thành viên, tuân thủ nguyên tắc cân bằng khối lượng công việc, chịu trách nhiệm chéo và thực hiện quy trình kỹ thuật chuẩn mực trên GitHub.

| Thành viên | Vai trò dự án (Role) | Trách nhiệm cốt lõi | Trách nhiệm trên GitHub & Artifacts |
| :--- | :--- | :--- | :--- |
| **Nguyễn Phước Bảo Phú** *(Lead)* | **Project Lead & System Architect** | Quản lý tiến độ tổng thể, sprint cadence, thiết kế kiến trúc hệ thống, lõi tìm kiếm ngữ nghĩa (`src/search_engine.py`), thiết lập CI/CD. | Repository Maintainer, Project Board (Kanban), Tagging Release `v1.0.0`, Chủ trì Báo cáo W3 & W7. |
| **Từ Công Phú** | **Data & Retrieval Engineer** | Xây dựng pipeline cào dữ liệu (`src/ingest.py`), chuẩn hóa JSON schema, sinh vector nhúng và quản trị ChromaDB (`src/indexer.py`). | Quản lý nhánh `feat/ingestion`, `feat/vector-db`, quản lý thư mục `data/raw/` và `data/processed/`. |
| **Nguyễn Vi Kiên** | **Frontend & Integration Engineer** | Phát triển Web Dashboard tương tác bằng Streamlit (`src/app.py`), trực quan hóa dữ liệu, sơ đồ kiến trúc và sơ đồ tư duy. | Quản lý nhánh `feat/ui-dashboard`, tác giả `docs/architecture.png`, `docs/mindmaps/`, `README.md`. |
| **Trần Kiện Đông** | **QA, Ethics & Compliance Lead** | Xây dựng bộ test (`tests/`), đo lường benchmark hiệu năng/MRR, thẩm định pháp lý/đạo đức AI, thư ký ghi biên bản họp tuần. | Reviewer chính cho Pull Requests, chủ trì `reports/ethics_legal_audit.pdf`, quản lý `docs/meeting_minutes/`. |

---

## 3. KẾ HOẠCH HÀNH ĐỘNG CHI TIẾT THEO 8 TUẦN (WBS)

```
[W1: Setup & Định nghĩa] ──> [W2: Nghiên cứu & Thiết kế] ──> [W3: Báo cáo Đề cương] ──> [W4: Đạo đức & Pháp lý]
           │                                                                                   │
[W8: Bảo vệ Cuối kỳ]   <── [W7: Đánh giá & Báo cáo 80%] <── [W6: UI & Tích hợp]     <── [W5: Lõi Động cơ Tìm kiếm]
```

---

### TUẦN 1: ĐẶC TẢ BÀI TOÁN & THIẾT LẬP DỰ ÁN (DESIGN STEPS 1–2)
*Mục tiêu: Thành lập nhóm, định hình phạm vi bài toán, phân rã yêu cầu môn học CO2001 và thiết lập môi trường kỹ thuật.*

- **Bảo Phú (Lead & Architect):**
  - Khởi tạo cấu trúc repository chuẩn trên GitHub (`github.com/HCMUT-Fus/hcmut-ailib`).
  - Thiết lập quy tắc bảo vệ nhánh (`main`, `develop`), cấu hình GitHub Project Board (Kanban).
  - Soạn thảo quy chuẩn đóng góp, template Pull Request (`.github/pull_request_template.md`) và Issue Templates (`.github/ISSUE_TEMPLATE/`).
- **Công Phú (Data):**
  - Nghiên cứu tài liệu arXiv API (query syntax, category taxonomy: `cs.AI`, `cs.CL`, `cs.CV`, rate-limiting 3s/request).
  - Xác định schema cho tập metadata 1,000 bài báo: `title`, `abstract`, `authors`, `doi`, `categories`, `published_date`, `pdf_url`.
  - Khởi tạo danh sách phụ thuộc bước đầu trong `requirements.txt`.
- **Kiên (Frontend):**
  - Soạn thảo bản mô tả dự án và hướng dẫn thiết lập môi trường trong `README.md`.
  - Khảo sát các mẫu giao diện tìm kiếm tài liệu học thuật (Semantic Scholar, arXiv Explorer) để lên ý tưởng UI.
  - Phác thảo wireframe sơ bộ các màn hình chức năng của ứng dụng Streamlit.
- **Đông (QA & Ethics):**
  - Soạn thảo biểu mẫu ghi nhận biên bản cuộc họp nhóm tại `docs/meeting_minutes/week01_meeting.md`.
  - Thiết lập môi trường kiểm thử ảo bằng `pytest`, cấu hình cấu trúc thư mục `tests/`.
  - Lập checklist các tiêu chuẩn chất lượng đồ án theo đề cương học phần CO2001.
- **Sản phẩm bàn giao Tuần 1:**
  - Kho GitHub chuẩn hóa đầy đủ cấu trúc thư mục, quy trình PR & Issue Template.
  - `requirements.txt` cơ sở, `README.md` cập nhật bối cảnh dự án.
  - Biên bản họp: `docs/meeting_minutes/week01_meeting.md`.

---

### TUẦN 2: THIẾT KẾ Ý TƯỞNG, BRAINSTORMING & KIẾN TRÚC HỆ THỐNG (DESIGN STEPS 3–5)
*Mục tiêu: Ứng dụng quy trình Think-Pair-Share (TPS), xây dựng Concept Mindmaps và hoàn thiện sơ đồ khối kiến trúc kỹ thuật.*

- **Bảo Phú (Lead & Architect):**
  - Thống nhất kiến trúc 4 tầng: *Ingestion Layer -> Storage/Vector Index Layer -> Core Retrieval Engine -> Presentation Layer*.
  - Định nghĩa interface lập trình và kiểu dữ liệu trao đổi giữa các file trong `src/` (typing, dataclasses).
  - Cấu hình workflow tự động kiểm tra cú pháp trên GitHub Actions (`.github/workflows/ci.yml`).
- **Công Phú (Data):**
  - Viết script thử nghiệm kết nối arXiv API bằng Python (`urllib` / `requests` / `feedparser`).
  - Xử lý các trường hợp ngoại lệ: bài báo không có DOI, tên tác giả có ký tự đặc biệt, định dạng ngày tháng ISO 8601.
- **Kiên (Frontend):**
  - Tổng hợp nội dung các phiên thảo luận nhóm, thiết kế sơ đồ tư duy (Concept Maps) và xuất vào `docs/mindmaps/`.
  - Vẽ sơ đồ khối kỹ thuật chi tiết của hệ thống (Engineering Block Diagram) và lưu thành `docs/architecture.png`.
- **Đông (QA & Ethics):**
  - Lập Ma trận Đánh giá Khả thi (Feasibility Decision Matrix) so sánh giữa Cloud LLM vs. Inverted Index vs. Local Vector DB.
  - Xây dựng kế hoạch kiểm thử tự động (CI Smoke Test Plan).
  - Biên bản họp: `docs/meeting_minutes/week02_meeting.md`.
- **Sản phẩm bàn giao Tuần 2:**
  - `docs/architecture.png` (Sơ đồ kiến trúc kỹ thuật hệ thống).
  - `docs/mindmaps/` (Sơ đồ tư duy về tính năng và yêu cầu người dùng).
  - `.github/workflows/ci.yml` (CI pipeline syntax checks).
  - Biên bản họp: `docs/meeting_minutes/week02_meeting.md`.

---

### TUẦN 3: TRIỂN KHAI THU THẬP DỮ LIỆU & BÁO CÁO ĐỀ CƯƠNG (DESIGN STEP 6 — MILESTONE 1: OUTLINE REPORT)
*Mục tiêu: Đóng gói tập dữ liệu chuẩn 1,000 bài báo arXiv, hoàn thành và bảo vệ Báo cáo Đề cương dự án.*

- **Bảo Phú (Lead & Architect):**
  - Chủ trì soạn thảo, biên tập và tổng hợp Báo cáo Đề cương Dự án: `reports/outline_report.pdf`.
  - Chuẩn bị slide thuyết trình bảo vệ đề cương trước giảng viên; điều phối buổi phản biện thử nghiệm nội bộ.
  - Review code của nhánh `feat/ingestion`.
- **Công Phú (Data):**
  - Hoàn thiện mã nguồn `src/ingest.py`: tự động hóa thu thập 1,000 bài báo arXiv theo các danh mục trọng điểm (`cs.AI`, `cs.LG`, `cs.CL`, `cs.IR`).
  - Chuẩn hóa và làm sạch văn bản, lưu trữ kết quả đầu ra tại `data/raw/arxiv_sample_1000.json`.
  - Đảm bảo cơ chế sleep/backoff tuân thủ quy định truy vấn của arXiv API (tối đa 1 request / 3 giây).
- **Kiên (Frontend):**
  - Đóng góp nội dung chương "Phân tích Yêu cầu Người dùng & Giao diện Dự kiến" vào Báo cáo Đề cương.
  - Dựng khung layout Streamlit với các tab điều hướng cơ bản trong `src/app.py`.
- **Đông (QA & Ethics):**
  - Xây dựng bộ kiểm thử tính toàn vẹn và định dạng dữ liệu trong `tests/test_ingest.py` (kiểm tra 1,000 bản ghi, định dạng schema, không trùng lặp `id`).
  - Rà soát format, trích dẫn tài liệu tham khảo theo chuẩn IEEE/ACM và xuất bản bản PDF cuối cùng của báo cáo đề cương.
  - Biên bản họp: `docs/meeting_minutes/week03_meeting.md`.
- **Sản phẩm bàn giao Tuần 3:**
  - **`reports/outline_report.pdf`** *(Nộp Milestone 1 môn học & bảo vệ đề cương)*.
  - `src/ingest.py` (Script thu thập và chuẩn hóa dữ liệu hoàn chỉnh).
  - `data/raw/arxiv_sample_1000.json` (Dataset 1,000 bài báo khoa học).
  - `tests/test_ingest.py` (Unit tests cho pipeline nạp dữ liệu).
  - Biên bản họp: `docs/meeting_minutes/week03_meeting.md`.

---

### TUẦN 4: VECTOR EMBEDDING, CHROMA INDEXING & ĐÁNH GIÁ ĐẠO ĐỨC/PHÁP LÝ (MILESTONE 2: ETHICS & LEGAL AUDIT)
*Mục tiêu: Hoàn tất việc tạo vector nhúng cục bộ vào ChromaDB và nộp Báo cáo phân tích Đạo đức & Pháp lý kỹ thuật.*

- **Bảo Phú (Lead & Architect):**
  - Đánh giá và tích hợp mô hình `all-MiniLM-L6-v2` thông qua thư viện `sentence-transformers`.
  - Cập nhật workflow CI: tự động chạy `pytest tests/test_ingest.py` mỗi khi có Pull Request vào nhánh `develop`.
  - Hỗ trợ Đông rà soát cơ sở pháp lý về quyền tác giả đối với phần mềm nguồn mở theo Luật CNTT Việt Nam.
- **Công Phú (Data):**
  - Triển khai `src/indexer.py`: nạp dữ liệu từ `arxiv_sample_1000.json`, kết hợp trường `title` và `abstract` để sinh vector nhúng (384 dimensions).
  - Khởi tạo và cấu hình cơ sở dữ liệu vector ChromaDB ở chế độ Persistent Local Client, lưu tại `data/processed/vector_index/`.
  - Tối ưu kích thước batching để việc sinh vector hoàn tất trong dưới 3 phút trên CPU thường.
- **Kiên (Frontend):**
  - Thiết kế các widget tương tác trên giao diện: khung nhập câu hỏi tự nhiên, thanh trượt chọn số lượng kết quả (Top-K: 1-20), bộ lọc năm và danh mục arXiv.
  - Định nghĩa component thẻ hiển thị bài báo (Paper Card) với đầy đủ thông tin: Tiêu đề, Tác giả, Abstract thu gọn, Link DOI/PDF.
- **Đông (QA & Ethics):**
  - **Chủ trì nghiên cứu và soạn thảo Báo cáo Đạo đức & Pháp lý (`reports/ethics_legal_audit.pdf`):**
    - Phân tích quyền sở hữu trí tuệ đối với dữ liệu bài báo mở (Open Access, giấy phép arXiv non-exclusive distribution license, Creative Commons CC-BY).
    - Đánh giá sự tuân thủ các quy định của **Luật Công nghệ Thông tin (2006)** và **Luật Sở hữu Trí tuệ Việt Nam**.
    - Rà soát tính minh bạch của giấy phép mã nguồn mở **GNU General Public License v3.0 (`LICENSE`)**.
    - Đánh giá đạo đức trong việc sử dụng AI (Bias trong dữ liệu học thuật, tôn trọng quyền riêng tư và bản quyền trích dẫn tác giả).
  - Biên bản họp: `docs/meeting_minutes/week04_meeting.md`.
- **Sản phẩm bàn giao Tuần 4:**
  - **`reports/ethics_legal_audit.pdf`** *(Nộp Milestone 2: Báo cáo Đạo đức & Pháp lý)*.
  - `src/indexer.py` (Script xây dựng kho vector ChromaDB).
  - `data/processed/vector_index/` (Kho vector nhúng hoàn chỉnh).
  - Biên bản họp: `docs/meeting_minutes/week04_meeting.md`.

---

### TUẦN 5: LÕI TÌM KIẾM NGỮ NGHĨA & BỘ KIỂM THỬ RETRIEVAL BENCHMARK (DESIGN STEP 7A)
*Mục tiêu: Hiện thực hóa giải thuật tính độ tương đồng Cosine, logic xếp hạng và xây dựng bộ 30 truy vấn benchmark chuẩn.*

- **Bảo Phú (Lead & Architect):**
  - Phát triển `src/search_engine.py`: tiếp nhận chuỗi truy vấn ngôn ngữ tự nhiên từ người dùng, nhúng câu truy vấn sang vector không gian 384 chiều.
  - Cài đặt thuật toán đo khoảng cách tương đồng Cosine (Cosine Similarity) kết hợp truy vấn gần nhất (Approximate Nearest Neighbors) trong ChromaDB.
  - Xây dựng bộ lọc kết hợp siêu dữ liệu (Metadata Filtering: lọc theo khoảng thời gian xuất bản, lọc theo category hoặc tác giả).
- **Công Phú (Data):**
  - Hỗ trợ xây dựng hàm tính điểm liên quan chuẩn hóa (Normalized Relevance Score) đưa về thang điểm `[0, 1]` hoặc phần trăm độ khớp.
  - Xây dựng tính năng sinh trích dẫn học thuật tự động cho từng bài báo (định dạng BibTeX, APA, IEEE).
- **Kiên (Frontend):**
  - Kết nối giao diện tìm kiếm trong `src/app.py` với backend `src/search_engine.py`.
  - Bổ sung hiệu ứng tải (Loading spinner), xử lý trường hợp không tìm thấy kết quả hoặc truy vấn rỗng.
- **Đông (QA & Ethics):**
  - **Xây dựng bộ kiểm thử `tests/test_retrieval.py`:**
    - Soạn thảo tập 30 truy vấn mẫu (Benchmark Queries) đại diện cho các chủ đề nghiên cứu (ví dụ: *"transfer learning in medical imaging"*, *"low resource neural machine translation"*).
    - Gán nhãn thủ công danh sách các bài báo thực sự liên quan trong tập 1,000 bài (Ground Truth).
    - Cài đặt công thức tính toán tự động chỉ số **MRR (Mean Reciprocal Rank)** và **Precision@5**.
  - Đảm bảo điểm MRR đạt ngưỡng tiêu chí kỹ thuật: **MRR > 0.7**.
  - Biên bản họp: `docs/meeting_minutes/week05_meeting.md`.
- **Sản phẩm bàn giao Tuần 5:**
  - `src/search_engine.py` (Module tìm kiếm ngữ nghĩa cốt lõi).
  - `tests/test_retrieval.py` (Bộ test và tập 30 benchmark queries).
  - Biên bản họp: `docs/meeting_minutes/week05_meeting.md`.

---

### TUẦN 6: PHÁT TRIỂN GIAO DIỆN STREAMLIT & TRỢ LÝ NGHIÊN CỨU (DESIGN STEP 7B)
*Mục tiêu: Hoàn thiện ứng dụng web tương tác hoàn chỉnh, tích hợp tính năng trợ lý nghiên cứu và kiểm thử trải nghiệm người dùng.*

- **Bảo Phú (Lead & Architect):**
  - Tối ưu hóa hiệu năng ứng dụng Streamlit: cấu hình cơ chế lưu trữ đệm (`st.cache_resource` cho mô hình embedding và ChromaDB connection) giúp giảm độ trễ truy vấn xuống **< 1.0 giây**.
  - Xây dựng tính năng "Find Similar Papers" (tìm các bài báo có nội dung tương đồng với bài đang xem).
- **Công Phú (Data):**
  - Rà soát tính ổn định của dữ liệu, viết hàm trích xuất các từ khóa chủ chốt (Key Takeaways / Extractive Keywords) từ phần tóm tắt để hỗ trợ người đọc.
- **Kiên (Frontend):**
  - Hoàn thiện giao diện người dùng chuyên nghiệp trong `src/app.py`:
    - Thanh tìm kiếm trung tâm trực quan với gợi ý từ khóa.
    - Bộ lọc đa tiêu chí linh hoạt ở sidebar.
    - Hiển thị kết quả dạng lưới/thẻ có điểm tương đồng, badge chuyên ngành arXiv, nút "Xem Abstract đầy đủ", nút "Tải PDF", nút "Sao chép BibTeX".
    - Thiết kế giao diện responsive, trực quan, hỗ trợ Light & Dark theme.
- **Đông (QA & Ethics):**
  - Thực hiện kiểm thử đầu cuối thủ công (Manual E2E Testing) trên nhiều trình duyệt (Chrome, Firefox, Edge).
  - Ghi nhận các vấn đề về hiển thị, lỗi biên (edge cases) và tạo GitHub Issues để nhóm xử lý.
  - Đo lường thời gian phản hồi thực tế của giao diện người dùng.
  - Biên bản họp: `docs/meeting_minutes/week06_meeting.md`.
- **Sản phẩm bàn giao Tuần 6:**
  - `src/app.py` (Ứng dụng web Streamlit hoàn thiện, trực quan và ổn định).
  - Pipeline tích hợp thông suốt giữa UI, Search Engine và Vector DB.
  - Biên bản họp: `docs/meeting_minutes/week06_meeting.md`.

---

### TUẦN 7: TỔNG KẾT ĐÁNH GIÁ HIỆU NĂNG & NỘP BÁO CÁO 80% (DESIGN STEP 8 — MILESTONE 3: FINAL EVALUATION REPORT)
*Mục tiêu: Đo lường toàn diện các chỉ số thực nghiệm, tinh chỉnh hệ thống và nộp Báo cáo Đánh giá Tổng kết 80% trọng số.*

- **Bảo Phú (Lead & Architect):**
  - **Chủ trì biên soạn Báo cáo Đánh giá Tổng kết (`reports/final_evaluation.pdf`)** — Báo cáo trọng số 80% của học phần:
    - Tổng hợp kiến trúc kỹ thuật và mức độ thỏa mãn các mục tiêu ban đầu.
    - Đánh giá khả năng mở rộng (Scalability) và phân tích hạn chế của hệ thống.
  - Tạo Git Tag Release phiên bản `v1.0.0` trên GitHub.
- **Công Phú (Data):**
  - Thực hiện thực nghiệm so sánh đối chứng (A/B Comparison): Tìm kiếm từ khóa truyền thống (Lexical Keyword Matching) vs. Tìm kiếm vector ngữ nghĩa (HCMUT-AILib).
  - Thu thập biểu đồ minh họa không gian vector nhúng (t-SNE hoặc PCA) phục vụ báo cáo.
- **Kiên (Frontend):**
  - Tiến hành khảo sát trải nghiệm người dùng (Usability Testing) với 10-15 sinh viên Bách Khoa.
  - Tổng hợp số liệu khảo sát (độ hài lòng, tính dễ sử dụng theo chuẩn System Usability Scale - SUS) để đưa vào báo cáo.
  - Cập nhật tài liệu hướng dẫn sử dụng vào `README.md`.
- **Đông (QA & Ethics):**
  - Tổng hợp toàn bộ số liệu đo lường kỹ thuật:
    - Bảng đo thời gian phản hồi truy vấn (trung bình 0.35s, tối đa 0.85s, đạt chỉ tiêu < 1.5s).
    - Bảng đo độ chính xác: MRR đạt **> 0.7**, Precision@5 đạt **> 80%**.
    - Mức tiêu thụ tài nguyên: RAM ~140MB, CPU < 15%, hoàn toàn đạt tiêu chí Zero-cost.
  - Biên tập, rà soát tính chặt chẽ học thuật và xuất bản file `reports/final_evaluation.pdf`.
  - Biên bản họp: `docs/meeting_minutes/week07_meeting.md`.
- **Sản phẩm bàn giao Tuần 7:**
  - **`reports/final_evaluation.pdf`** *(Nộp Milestone 3: Báo cáo Đánh giá Đồ án 80%)*.
  - Toàn bộ test case trong `tests/` vượt qua 100% trên GitHub Actions CI.
  - Bản phát hành tag `v1.0.0`.
  - Biên bản họp: `docs/meeting_minutes/week07_meeting.md`.

---

### TUẦN 8: ĐÓNG GÓI SẢN PHẨM, TÀI LIỆU HÓA & BẢO VỆ ĐỒ ÁN (FINAL DEFENSE & RELEASE)
*Mục tiêu: Đóng gói tài liệu bàn giao, ghi hình video demo dự phòng, hoàn thiện slide và bảo vệ xuất sắc trước hội đồng.*

- **Bảo Phú (Lead & Architect):**
  - Khóa chính xác các phiên bản thư viện trong `requirements.txt`.
  - Tổng hợp slide thuyết trình bảo vệ đồ án cuối kỳ trước Hội đồng giảng viên Khoa KH&KT Máy tính.
  - Điều phối phân chia thuyết trình và kịch bản trả lời vấn đáp (Q&A Defense Script).
- **Công Phú (Data):**
  - Thực hiện quy trình kiểm tra tính tái lập (Reproducibility Test): sao chép mã nguồn sang một máy tính mới hoàn toàn và chạy kiểm thử từ bước cào dữ liệu đến khởi chạy ứng dụng.
  - Đóng gói file mô tả cấu trúc dữ liệu metadata.
- **Kiên (Frontend):**
  - Hoàn thiện toàn diện `README.md` theo chuẩn quốc tế: huy hiệu CI, ảnh chụp giao diện, sơ đồ kiến trúc, GIF mô phỏng thao tác, hướng dẫn cài đặt 3 bước bằng lệnh `pip`, danh sách tác giả.
  - Quay video demo chất lượng cao (3-5 phút) thuyết minh các tính năng chính làm kịch bản dự phòng khi bảo vệ.
- **Đông (QA & Ethics):**
  - Hoàn tất và lưu trữ toàn bộ 8 biên bản họp nhóm tuần tại `docs/meeting_minutes/`.
  - Rà soát sự toàn vẹn của giấy phép mã nguồn mở `LICENSE` (GNU GPLv3).
  - Lập Bảng tự đánh giá và Đánh giá chéo đóng góp thành viên (Peer Assessment Matrix).
- **Sản phẩm bàn giao Tuần 8:**
  - Mã nguồn hoàn thiện 100%, Clean Code, tài liệu hóa đầy đủ docstrings.
  - `README.md` chuyên nghiệp và video demo ứng dụng.
  - Slide thuyết trình bảo vệ trước Hội đồng.
  - Hồ sơ dự án và biên bản họp 8 tuần hoàn chỉnh.

---

## 4. MA TRẬN PHÂN CÔNG TRÁCH NHIỆM RACI (RACI MATRIX)

> **Quy ước:**
> - **R (Responsible):** Người trực tiếp thực hiện công việc.
> - **A (Accountable):** Người chịu trách nhiệm phê duyệt và giải trình kết quả cuối cùng (duy nhất 1 người).
> - **C (Consulted):** Người đóng góp ý kiến chuyên môn và phối hợp.
> - **I (Informed):** Người được thông báo tiến độ và kết quả.

| Hạng mục / Artifact trong Repository | Bảo Phú (Lead) | Công Phú (Data) | Kiên (Frontend) | Đông (QA/Legal) |
| :--- | :---: | :---: | :---: | :---: |
| **Quản trị Repo, Kanban Board & CI/CD** (`.github/`) | **A / R** | I | I | C |
| **Đặc tả Schema & Cào dữ liệu** (`src/ingest.py`, `data/raw/`) | C | **A / R** | I | C |
| **Vector Indexing & ChromaDB** (`src/indexer.py`, `data/processed/`) | C | **A / R** | C | I |
| **Lõi tìm kiếm ngữ nghĩa Cosine** (`src/search_engine.py`) | **A / R** | C | C | C |
| **Giao diện Web Streamlit** (`src/app.py`) | C | I | **A / R** | C |
| **Sơ đồ kiến trúc & Concept Maps** (`docs/`) | C | C | **A / R** | I |
| **Bộ kiểm thử & Benchmark MRR** (`tests/`) | C | C | I | **A / R** |
| **Báo cáo Đề cương** (`reports/outline_report.pdf` - W3) | **A / R** | C | C | C |
| **Báo cáo Đạo đức & Pháp lý** (`reports/ethics_legal_audit.pdf` - W4) | C | C | I | **A / R** |
| **Báo cáo Đánh giá 80%** (`reports/final_evaluation.pdf` - W7) | **A / R** | C | C | R |
| **Tài liệu hướng dẫn & Video Demo** (`README.md`, Video) | C | I | **A / R** | C |
| **Biên bản họp nhóm 8 tuần** (`docs/meeting_minutes/`) | I | I | I | **A / R** |

---

## 5. QUY CHUẨN KỸ THUẬT & PHỐI HỢP NHÓM (TEAM GOVERNANCE)

### 5.1. Quy trình Phân nhánh Git (Branching Model)
- `main`: Nhánh sản phẩm chính thức, được bảo vệ nghiêm ngặt (Protected branch). Chỉ cập nhật thông qua Pull Request từ `develop` sau khi vượt qua tất cả kiểm thử.
- `develop`: Nhánh tích hợp thường trực trong suốt quá trình phát triển các sprint.
- `feat/<tên-thành-viên>-<tên-chức-năng>`: Nhánh tính năng cá nhân (ví dụ: `feat/congphu-arxiv-ingestion`, `feat/kien-streamlit-dashboard`).
- `fix/<tên-lỗi>`: Nhánh xử lý sự cố khẩn cấp (ví dụ: `fix/chroma-dimension-error`).

### 5.2. Tiêu chuẩn Commit Message (Conventional Commits)
Mỗi commit message phải tuân thủ nghiêm ngặt định dạng:
`type(scope): short description in imperative mood`
- `feat(ingest): add rate limiting and pagination for arxiv api`
- `fix(indexer): resolve memory leakage during batch embedding`
- `test(retrieval): implement 30 benchmark queries for mrr assertion`
- `docs(reports): finalize week 4 ethics and legal audit report`
- `style(ui): improve responsive layout for paper cards`

### 5.3. Quy trình Kiểm duyệt Mã nguồn (Code Review & Pull Requests)
- Không commit trực tiếp lên `main` và `develop`.
- Mỗi Pull Request phải gắn nhãn (Label), liên kết đến GitHub Issue tương ứng.
- Phải có tối thiểu **1 thành viên khác (Đông đối với kiểm thử/chất lượng hoặc Bảo Phú đối với kiến trúc) phê duyệt (Approve)** và CI pipeline chạy thành công trước khi merge.
- Sử dụng hình thức `Squash and merge` để giữ lịch sử Git trên `develop` và `main` được trong sạch.

### 5.4. Lịch họp & Giao tiếp Nhóm
- **Họp đồng bộ tuần (Weekly Standup & Sync):** Diễn ra vào tối thứ Bảy hàng tuần lúc **20:00 - 21:00** qua Google Meet / Discord.
- **Nội dung cuộc họp:** 
  1. Mỗi thành viên báo cáo 3 câu hỏi: *Đã làm được gì tuần qua? Sẽ làm gì tuần tới? Đang gặp khó khăn/nghẽn ở đâu (Blockers)?*
  2. Rà soát tiến độ so với các mốc nộp báo cáo (W3, W4, W7, W8).
  3. Phân công chi tiết và thống nhất giải pháp kỹ thuật.
- **Biên bản họp:** Thư ký (Đông) có trách nhiệm cập nhật biên bản bằng Markdown vào thư mục `docs/meeting_minutes/weekXX_meeting.md` trong vòng 24 giờ sau cuộc họp.

---

## 6. DANH SÁCH KIỂM TRA MỐC TIẾN ĐỘ (PROGRESS TRACKING CHECKLIST)

- [ ] **Cuối Tuần 1:** Hoàn thiện setup Git, quy chuẩn PR/Issue templates, phân công vai trò rõ ràng.
- [ ] **Cuối Tuần 2:** Hoàn tất `docs/architecture.png`, `docs/mindmaps/`, CI workflow chạy ổn định.
- [ ] **MỐC TUẦN 3:** Thu thập 1,000 bài báo vào `data/raw/` & nộp **`reports/outline_report.pdf`**.
- [ ] **MỐC TUẦN 4:** Hoàn tất vector store ChromaDB & nộp **`reports/ethics_legal_audit.pdf`**.
- [ ] **Cuối Tuần 5:** Hoàn thành `src/search_engine.py` và bộ kiểm thử `tests/test_retrieval.py` (MRR > 0.7).
- [ ] **Cuối Tuần 6:** Hoàn thành ứng dụng web Streamlit tương tác `src/app.py`.
- [ ] **MỐC TUẦN 7:** Đo lường benchmark đầy đủ & nộp **`reports/final_evaluation.pdf`** (Báo cáo 80%).
- [ ] **MỐC TUẦN 8:** Đóng gói release `v1.0.0`, hoàn thiện `README.md`, slide thuyết trình và bảo vệ đồ án trước Hội đồng.
