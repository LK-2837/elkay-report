import streamlit as st
import os
import json
from PIL import Image
from io import BytesIO
from datetime import datetime

# 1. 페이지 설정 및 초기화
st.set_page_config(page_title="엘케이어학원 마스터 리포트", layout="centered")

HISTORY_FILE = "student_history.json"

if 'page' not in st.session_state: st.session_state.page = 'input'
if 'data' not in st.session_state: st.session_state.data = {}

# --- [데이터 저장/불러오기 함수] ---
def save_to_history(new_data):
    # 사진 제외 텍스트 데이터 저장 (날짜는 문자열로 변환)
    history_to_save = {k: str(v) if k == 'date' else v for k, v in new_data.items() if k != "image"}
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            all_history = json.load(f)
    else:
        all_history = {}
    name = history_to_save['name']
    if name not in all_history: all_history[name] = []
    all_history[name].append(history_to_save)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(all_history, f, ensure_ascii=False, indent=4)

def load_last_student_data(name):
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            all_history = json.load(f)
            if name in all_history and len(all_history[name]) > 0:
                return all_history[name][-1]
    return None

# 2. 모든 데이터 정의 (슬림화 없이 전체 유지)
GRADE_LIST = ["초등", "중등", "고등"]
CLASS_LIST = ["선택 없음", "Beginner-2시", "Beginner-3시", "Beginner-4시", "Ph1", "Ph2", "Ph3", "Ph4", "Ph5", "Inter 2시", "Inter 3시", "Inter 4시", "G-Advanced 2시", "G-Advanced 3시", "G-Advanced 4시"]

AZAR_DATA = {
    "Chapter 01": ["1-1 단수 인칭대명사+Be동사", "1-2 복수 인칭대명사+Be동사", "1-3 단수 명사+Be동사", "1-4 복수 명사+Be동사", "1-5 축약", "1-6 부정문", "1-7 형용사", "1-8 장소", "1-9 요약"],
    "Chapter 02": ["2-1 This/That", "2-2 These/Those", "2-3 Yes/No 의문문", "2-4 대답", "2-5 Where", "2-6 Have/Has", "2-7 소유격", "2-8 What/Who"],
    "Chapter 03": ["3-1 현재시제", "3-2 빈도부사", "3-3 위치", "3-4 3인칭단수 -es", "3-5 -y동사", "3-6 불규칙", "3-7 Like To/Want To", "3-8 부정문", "3-9 의문문", "3-10 Where/What", "3-11 When/What Time"],
    "Chapter 04": ["4-1 현재진행형", "4-2 -ing", "4-3 부정문", "4-4 의문문", "4-5 현재 vs 진행", "4-6 상태동사", "4-7 감각동사", "4-8 Think About", "4-9 명령문"],
    "Chapter 05": ["5-1 단수/복수", "5-2 불규칙", "5-3 형용사", "5-4 주어/목적어", "5-5 인칭대명사", "5-6 전치사+목적격", "5-7 소유대명사", "5-8 's소유격", "5-9 Whose", "5-10 불규칙 소유격"]
}

WRITING_DATA = {
    "Basic Structure": ["1. 명사", "2. 대명사", "3. 형용사", "4. 동작", "5. 기본문장Ⅰ", "6. 전치사", "7. 기본문장+전치사+명사", "8. 기본문장Ⅱ"],
    "OK Writing 1": ["Vocab", "Sentence 1~6", "Part 1. 전치사", "Part 2. 진행형", "Part 3. 부정문", "Part 4. and/because", "Part 5. 명령문", "Story 1-1~3-4"],
    "OK Writing 2": ["Vocab", "Sentence 1~6", "Part 1. 소유격", "Part 2. There is/are", "Part 3. but/because", "Part 4. 대상 2개", "Part 5. 의문문", "Part 6. look+형용사", "Part 7. don't", "Story 1-1~3-4"],
    "OK Writing 3": ["Vocab", "Sentence 1~9", "Part 1. of", "Part 2. to부정사", "Part 3. can", "Part 4. 비인칭", "Part 5. Let's", "Part 6. 3인칭단수", "Part 7. doesn't", "Story 1-1~3-5"],
    "OK Writing 4": ["Vocab", "Sentence 1~7", "Part 1. will", "Part 2. must", "Part 3. to부정사", "Part 4. that절", "Part 5. Do", "Part 6. 의문사", "Story 1-1~2-4"],
    "OK Writing 5": ["Vocab", "Sentence 1~9", "Part 1. 명령문", "Part 2. 빈도부사", "Part 3. Does", "Part 4. to부정사", "Part 5. 원급", "Part 6. 비교급", "Part 7. 최상급", "Story 1-1~2-2"],
    "OK Writing 6": ["Vocab", "Sentence 1~8", "Part 1. 과거", "Part 2. have to", "Part 3. Did", "Part 4. didn't", "Part 5. 동명사주어", "Part 6. 의문사구", "Part 7. 접속사", "Story 1-1~1-6"],
    "OK Writing 7": ["Vocab", "Sentence 1~12", "Part 1. 동명사목적어", "Part 2. 가주어 it", "Part 3. 형용사보어", "Part 4. 재귀대명사", "Part 5. 의문사구", "Part 6. should", "Part 7. 지각동사", "Story 1-1~3-2"],
    "Bridge Writing Starter": ["Vocab", "Sentence 1~3", "Part 1. 복수", "Part 2. 소유격", "Part 3. 진행형", "Part 4. but", "Part 5. 명령문", "Story 1-1~3-3"],
    "Bridge Writing 1": ["Vocab", "Sentence 1~5", "Part 1. 관사", "Part 2. 전치사", "Part 3. but/because", "Part 4. 부정문", "Part 5. 의문문", "Story 1-1~2-5"],
    "Bridge Writing 2": ["Vocab", "Sentence 1~6", "Part 1. 의문사", "Part 2. 3인칭", "Part 3. 형용사보어", "Part 4. will", "Part 5. 's", "Part 6. Please", "Story 1-1~3-4"],
    "Bridge Writing 3": ["Vocab", "Sentence 1~6", "Part 1. There", "Part 2. 소유격", "Part 3. 의문사", "Part 4. Don't", "Part 5. can", "Part 6. to", "Story 1-1~3-4"],
    "Bridge Writing 4-1": ["Vocab", "Sentence 1~6", "Part 1~5", "Story 1-1~2-5"],
    "Bridge Writing 4-2": ["Vocab", "Sentence 1~6", "Part 1~5", "Story 1-1~3-3"],
    "Bridge Writing 5": ["Vocab", "Sentence 1~9", "Part 1~6", "Story 1-1~2-4"],
    "Bridge Writing 6-1": ["Vocab", "Sentence 1~6", "Part 1~6", "Story 1-1~2-4"],
    "Bridge Writing 6-2": ["Vocab", "Sentence 1~6", "Part 1~6", "Story 1-1~3-2"],
    "Training for Reading S1": ["Vocab", "Training 1~11"],
    "Training for Reading S2": ["Vocab", "Training 1~11"],
    "Training for Reading S3": ["Vocab", "Training 1~9", "Story 1~3"],
    "Training for Reading S4": ["Vocab", "Training 1~9", "Story 1~2.2"]
}

READING_BOOKS_DATA = [
    "English Newspaper_Kids", "English Newspaper_Kinder", 
    "리딩튜터 스타터(1)", "리딩튜터 스타터(2)", "리딩튜터 스타터(3)", 
    "리딩튜터 주니어(1)", "리딩튜터 주니어(2)", "리딩튜터 주니어(3)", "리딩튜터 주니어(4)", 
    "수능토픽(레벨1)", "수능토픽(레벨2)", "수능토픽(레벨3)"
]

ELT_BOOKS = ["30 Word Reading(1)", "30 Word Reading(2)", "40 Word Reading(1)", "40 Word Reading(2)", "40 Read it(1)", "40 Read it(2)", "40 Read it(3)", "60 Read it(1)", "60 Read it(2)", "60 Read it(3)"]
ELT_UNITS = [str(i) for i in range(1, 17)]
V_BOOKS = ["능률 보카 기본 400", "능률 보카 필수 500", "[개정]교육청 필수 900", "보카익스프레스", "보카클리어", "기타"]
READING_UNITS = [f"{i}({j})" for i in range(1, 11) for j in ["1", "2", "3", "4", "Review"]] + ["직접 입력"]

# --- [입력 화면] ---
if st.session_state.page == 'input':
    st.title("📝 마스터 학습 리포트")
    
    st.subheader("🔍 학생 이름으로 히스토리 검색")
    c_search, c_btn = st.columns([3, 1])
    search_name = c_search.text_input("학생 이름을 입력하세요", placeholder="예: 김철수")
    if c_btn.button("🔄 기록 불러오기"):
        last_data = load_last_student_data(search_name)
        if last_data:
            for k, v in last_data.items(): 
                # 날짜 데이터는 datetime 객체로 변환하여 주입
                if k == 'date':
                    st.session_state[f"{k}_key"] = datetime.strptime(v, '%Y-%m-%d').date()
                else:
                    st.session_state[f"{k}_key"] = v
            st.success(f"'{search_name}' 학생의 최신 정보를 불러왔습니다.")
            st.rerun()

    st.divider()
    st.subheader("📍 기본 정보")
    
    # [날짜 선택 위젯 추가]
    report_date = st.date_input("날짜 선택", value=datetime.today(), key="date_key")
    
    c1, c2, c3 = st.columns(3)
    academy = c1.text_input("학원명", value="엘케이어학원", key="academy_key")
    class_name = c2.selectbox("반 선택", CLASS_LIST, key="class_key")
    grade = c3.selectbox("학년", GRADE_LIST, key="grade_key")
    name = st.text_input("학생 이름 확인/수정", value=search_name)

    st.divider()
    st.subheader("🅰️ 어휘 테스트")
    v_book = st.selectbox("어휘 교재", V_BOOKS, key="v_book_key")
    cv1, cv2, cv3 = st.columns(3)
    v_unit = cv1.text_input("Unit/Range", key="v_unit_key")
    v_corr = cv2.number_input("맞은 개수", min_value=0)
    v_tot = cv3.number_input("전체 개수", min_value=1, value=20)

    st.divider()
    st.subheader("📚 주교재 수업 상세")
    
    st.markdown("**[1] ELT Reading 시리즈**")
    elt_book = st.selectbox("ELT 교재", ["선택 안 함"] + ELT_BOOKS, key="elt_book_key")
    elt_unit = st.selectbox("ELT Unit", ELT_UNITS) if elt_book != "선택 안 함" else ""

    st.markdown("**[2] Grammar (Azar)**")
    g_book = st.selectbox("문법 교재", ["선택 안 함", "Azar Basic English Grammar(1)", "Azar Fundamentals", "기타"], key="g_book_key")
    g_info = ""
    if "Azar" in g_book:
        gc1, gc2 = st.columns(2)
        g_ch = gc1.selectbox("대단원", list(AZAR_DATA.keys()))
        g_ls = gc2.selectbox("세부 단원", AZAR_DATA[g_ch]); g_info = f"{g_ch} [{g_ls}]"

    st.markdown("**[3] Reading (Tutor/News)**")
    r_book = st.selectbox("독해 교재", ["선택 안 함"] + READING_BOOKS_DATA, key="r_book_key")
    r_unit = st.text_input("독해 Unit/Page", key="r_unit_key") if r_book != "선택 안 함" else ""

    st.markdown("**[4] Writing (OK/Bridge/Training)**")
    w_book = st.selectbox("라이팅 교재", ["선택 안 함"] + list(WRITING_DATA.keys()), key="w_book_key")
    w_ls = st.selectbox("라이팅 세부 단원", WRITING_DATA[w_book]) if w_book in WRITING_DATA else ""

    st.markdown("---")
    st.subheader("📸 사진 분석 및 정밀 피드백")
    assignment_file = st.file_uploader("사진 업로드", type=['jpg', 'jpeg', 'png'])
    
    domain = "선택 안 함"
    if assignment_file:
        st.image(assignment_file, width=300)
        domain = st.selectbox("❓ 분석할 영역 선택", ["선택 안 함", "문법", "어휘", "독해", "라이팅"])

    ai_feedback = st.text_area("AI 분석 결과", key="ai_key", height=150)
    content = st.text_area("선생님 상세 피드백", key="content_key")
    hw_status = st.selectbox("과제 수행도", ["매우 우수", "우수", "보통", "미흡"], key="hw_key")

    if st.button("리포트 생성 및 저장", type="primary"):
        v_perc = int((v_corr / v_tot) * 100) if v_tot > 0 else 0
        report_data = {
            "date": report_date,
            "academy": academy, "name": name, "grade": grade, "class_name": class_name,
            "v_book": v_book, "v_unit": v_unit, "v_score": v_perc, "v_correct": v_corr, "v_total": v_tot,
            "elt_book": elt_book, "elt_unit": elt_unit, "g_book": g_book, "g_info": g_info,
            "r_book": r_book, "r_unit": r_unit, "w_book": w_book, "w_lesson": w_ls,
            "content": content, "ai_feedback": ai_feedback, "hw_status": hw_status, "domain": domain
        }
        save_to_history(report_data)
        st.session_state.data = report_data
        if assignment_file: st.session_state.data["image"] = Image.open(assignment_file)
        st.session_state.page = 'result'
        st.rerun()

# --- [결과 화면] ---
elif st.session_state.page == 'result':
    d = st.session_state.data
    st.title(f"📄 {d['name']} 학생 리포트")
    
    main_items = []
    if d['elt_book'] != "선택 안 함": main_items.append(f"• ELT독해: {d['elt_book']} (Unit {d['elt_unit']})")
    if d['g_book'] != "선택 안 함": main_items.append(f"• 문법: {d['g_book']} ({d['g_info']})")
    if d['r_book'] != "선택 안 함": main_items.append(f"• 독해: {d['r_book']} [{d['r_unit']}]")
    if d['w_book'] != "선택 안 함": main_items.append(f"• 라이팅: {d['w_book']} [{d['w_lesson']}]")
    main_study = "\n".join(main_items)

    # [조건부 제목 생성 로직]
    f_sec = f"\n[선생님 피드백]\n{d['content']}\n" if d['content'].strip() else ""
    a_sec = f"\n[AI 과제 정밀 분석 - {d['domain']}]\n{d['ai_feedback']}\n" if d['ai_feedback'].strip() else ""

    report_text = f"""
[ {d['academy']} 학습 리포트 ]

■ 대상: {d['grade']} {d['class_name']} {d['name']} 학생
■ 작성일: {d['date']}

1. 어휘 테스트 결과
- 교재명: {d['v_book']} (Unit {d['v_unit']})
- 결과: {d['v_correct']} / {d['v_total']} (정답률 {d['v_score']}%)

2. 주교재 학습 내용
{main_study}
{f_sec}{a_sec}
3. 과제 수행도: {d['hw_status']}
"""
    st.text_area("텍스트 복사", report_text.strip(), height=400)
    if "image" in d and d["image"]: st.image(d["image"], use_container_width=True)
    if st.button("처음으로 돌아가기"):
        st.session_state.page = 'input'
        st.rerun()