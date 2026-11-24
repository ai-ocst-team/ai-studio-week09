# FEEDBACK_LOG — 12주차 교차 테스트 피드백 처리 기록

- **프로젝트**: 사진 평가 대시보드 (Streamlit)
- **공식 배포 URL**: https://photo-grader.streamlit.app/
- **작성자(Task 4)**: 류시향
- **작성일**: 2026-11-24
- **받은 피드백**: 총 5건 (반영 4건 / 백로그 1건)

## 0. 요약

| # | 제안자 | 유형 | 피드백 요약 | 처리 결과 | 관련 커밋 |
|---|---|---|---|---|---|
| 1 | 강민규 | 제안 | A컷/B컷 기준 점수 제공 | ✅ 반영 | `ed548ee` |
| 2 | 강민규 | 사용성 | 상위 태그 차트 설명 추가 | ✅ 반영 | `ed548ee` |
| 3 | 신동훈 | 사용성/제안 | 감성 태그 의미 설명 | ✅ 반영 | `ed548ee` |
| 4 | 신동훈 | 버그 제보 | 태그 드롭다운 화살표 미작동 | ✅ 재현 확인 후 UI 개선 반영 | `ed548ee` |
| 5 | 신동훈 | 제안 | 다중 CSV 업로드 병합 | ⏸ 백로그 / 보류 | 해당 없음 |
**ed548ee** (피드백 ①~④ 통합 커밋)
---

## 1. 반영 항목

### 피드백 1. A컷/B컷 기준 점수 (강민규, 제안)

**① 피드백 원문**
> "A컷/B컷 구분을 위해 점수에 따라 몇 점까지가 A컷이고 B컷인지를 판단하는 기준이 있으면 사용자가 사진을 고를 때 더 편할 것 같습니다!"

**② 수정 전 화면/동작**
- 설명: 점수는 표시되지만 A컷/B컷을 가르는 기준과 건수가 없어, 사용자가 직접 점수를 보고 판단해야 했다. 
- 캡처: `docs/screenshots_week12/01_normal_utf8_1.png`, `docs/screenshots_week12/01b_normal_filter.png`

**③ 수정 내용 및 근거**
- 수정 내용:
  - 사이드바에 A컷/B컷 기준 점수 설정 추가 (기본값 8.0 / 6.0)
  - `backend.assign_cut_grades` 도입
  - KPI에 A컷/B컷 수와 기준 설명 추가
  - 기준이 역전되면 경고 후 기본값을 적용
- 근거: 사진 선별(culling)이 이 서비스의 핵심 사용 목적이므로, 판단 기준을 명시하고 사용자가 조정할 수 있게 했다.

**④ 수정 후 캡처**
- `docs/screenshots_week12/after_01_normal_utf8_1.png` (A/B컷 KPI와 기준 설명)
- `docs/screenshots_week12/after_01b_normal_filter.png` (사이드바 A/B컷 기준 슬라이더)
- `docs/screenshots_week12/after_01c_cutoff_warning.png` (기준 역전 경고)

**⑤ 커밋 해시**: `ed548ee`

---

### 피드백 2. 상위 감성 태그 차트 설명 (강민규, 사용성)

**① 피드백 원문**
> "상위 감성 태그 평균 점수 (최대 5개, 2회 이상) -> 이 문구에 대한 설명을 추가해주면 더 직관적으로 차트의 의미를 이해할 수 있을 것 같습니다. 예를 들어 '나의 강점 분석(2회 이상 등장한 태그 대상)' 등의 문구를 따로 작게 삽입하는 방식도 있을 것 같습니다."

**② 수정 전 화면/동작**
- 설명: 차트 제목만 있고 "최대 5개, 2회 이상"이 무엇을 뜻하는지 설명이 없었다.
- 캡처: `docs/screenshots_week12/01_normal_utf8_2.png`

**③ 수정 내용 및 근거**
- 수정 내용: 차트 하단에 `st.caption`으로 설명 문구를 추가했다. ("나의 강점 분석 — 최소 2회 이상 등장한 감성 태그의 평균 점수 TOP 5입니다.")
- 근거: 제안된 방식(작은 보조 문구)이 레이아웃 변경 없이 의미를 전달하는 가장 작은 수정이다.

**④ 수정 후 캡처**: `docs/screenshots_week12/after_01_normal_utf8_2.png`

**⑤ 커밋 해시**: `ed548ee`

---

### 피드백 3. 감성 태그 의미 설명 (신동훈, 사용성/제안)

**① 피드백 원문**
> "감성 태그의 종류가 다양해서 좋은 것 같습니다! 다만 각 감성 태그가 어떤 의미를 나타내는지에 대한 설명도 함께 제공된다면, 사용자가 태그를 더 쉽게 이해하고 선택할 수 있을 것 같습니다."

**② 수정 전 화면/동작**
- 설명: 태그 이름만 나열되어 있고 의미 설명이 없었다. 
- 캡처: `docs/screenshots_week12/01b_normal_filter.png`

**③ 수정 내용 및 근거**
- 수정 내용:
  - `backend.TAG_GLOSSARY` 구축
  - `st.expander("감성 태그 의미 가이드")`로 전체 설명 제공
  - 선택된 태그의 설명을 바로 표시
- 근거: 태그 의미는 데이터(backend)에, 표시는 UI(app)에 두어 UI와 백엔드를 분리했다. expander를 써서 화면 공간을 아꼈다.

**④ 수정 후 캡처**
- `docs/screenshots_week12/after_01d_tag_guide_expander.png`
- `docs/screenshots_week12/after_01e_selected_tag_caption.png`

**⑤ 커밋 해시**: `ed548ee`

---

### 피드백 4. 태그 드롭다운 화살표 미작동 (신동훈, 버그 제보)

**① 피드백 원문**
> "사이드바의 감성 태그 선택 드롭다운에서 오른쪽의 아래쪽 화살표를 클릭해도 메뉴가 펼쳐지지 않는 문제가 있습니다."

**② 수정 전 화면/동작 (재현 시도 결과)**
- 로컬 `streamlit 1.67.0` 크롬 환경에서 재현을 시도했다. 우측 화살표 클릭 시 메뉴가 **정상적으로 열렸고, 버그는 재현되지 않았다.**
- 다만 브라우저, 해상도, 사이드바 폭에 따라 좁은 화살표 영역에서 클릭이 실패했을 가능성은 배제할 수 없다. 
- 캡처: `docs/screenshots_week12/01b_normal_filter.png`

**③ 수정 내용 및 근거**
- 수정 내용: `st.sidebar.selectbox`를 `st.sidebar.pills("감성 태그 선택", selection_mode="single", key="tag_filter")`로 교체했다. 선택 해제로 `None`이 될 수 있어 `selected_tag = selected_tag or "전체"`로 방어했다.
- 근거: 화살표를 눌러 메뉴를 여는 단계를 없애 1클릭으로 선택하게 하고, 같은 문제가 다시 생기지 않게 했다. 원인이 확정된 버그 수정이 아니라 **재현 불가 상태에서의 사용성 개선**이다.

**④ 수정 후 캡처**: `docs/screenshots_week12/after_01b_normal_filter.png`

**⑤ 커밋 해시**: `ed548ee`

---

## 2. 미반영 항목 (백로그 / 보류)

### 피드백 5. 다중 CSV 업로드 병합 (신동훈, 제안)

**① 피드백 원문**
> "지금은 csv 파일을 여러 개 업로드 해도 1개만 인식되는데 사진 분석 csv 파일을 여러 개 올리면 합쳐서 평가해주는 방향도 좋을 것 같습니다."

| 항목 | 내용 |
|---|---|
| 분류 | `[백로그 / 보류]` |
| 보류 사유 (한 줄) | 12주차 스코프(상태 관리 안정화·조기 배포)에 비해 변경 부담이 커서 14주차 스코프 락에서 재검토한다. |
| 세부 사유 1 | 파일별 인코딩이 섞여 있을 때(UTF-8/CP949)의 예외 처리 필요 |
| 세부 사유 2 | 파일 간 중복 `id`를 합칠 때의 병합 규칙 필요 |
| 세부 사유 3 | `session_state` 캐시 구조 변경 필요 (`uploaded_file_sig` 등) |
| 재검토 시점 | 14주차 스코프 락 |
| 임시 대응 | [현재 동작 기입: 예) 여러 개 올려도 1개만 인식됨을 안내] |

---

## 3. 방어적 UX 추가 (참고)

| 상황 | 표시 | 캡처 |
|---|---|---|
| CP949 인코딩 감지 | `st.warning` | `docs/screenshots_week12/after_02_cp949_fallback_1.png` |
| 점수 누락·형식 오류 행 제외 | `st.warning` | `docs/screenshots_week12/after_02b_dropped_rows_warning.png` |
| 필수 컬럼 누락 | `st.error` + `st.stop()` | `docs/screenshots_week12/after_03_broken_columns_guard.png` |

수정 전 비교: `docs/screenshots_week12/02_cp949_fallback_1.png`, `02_cp949_fallback_2.png`, `03_broken_columns_guard.png`

## 4. 추가 확인: 챗봇 탭 (신규 기능)

- 캡처: `docs/screenshots_week12/after_04_chatbot_history.png`
- 커밋 해시: `ed548ee`

## 5. 테스트 및 배포 확인

- pytest 로그: `tests/pytest_week12_log.txt`
- 결과: [N passed 기입]
- 배포 URL 확인 일시: [기입]
- 배포 정상 렌더링 여부: [확인 결과 기입]

