import streamlit as st
import pandas as pd
import os
from PIL import Image
from datetime import datetime
from google import genai

# 1. 페이지 설정
st.set_page_config(page_title="엘케이어학원 학습 리포트", layout="centered")

# 2. 클라이언트 설정 (과제 정밀 분석용)
if "gemini_api_key" in st.secrets:
    client = genai.Client(api_key=st.secrets["gemini_api_key"])
else:
    st.error("Secrets에 'gemini_api_key'를 등록해 주세요.")

# --- [상세 커리큘럼 데이터 정의] ---

# 어휘 교재 전체 목록 복구
V_BOOKS_LIST = [
    "능률 보카 기본 400", "능률 보카 필수 500", "능률 보카 교육청 900", 
    "보카클리어 중학기본", "보카클리어 중학실력", "보카익스프레스", "기타"
]

# ELT 독해 교재
ELT_BOOKS = [
    "30 Word Reading(1)", "30 Word Reading(2)", "40 Word Reading(1)", "40 Word Reading(2)", 
    "40 Read it(1)", "40 Read it(2)", "40 Read it(3)", "60 Read it(1)", "60 Read it(2)", "60 Read it(3)"
]

# 독해 교재 (영자신문 세분화 유지)
READING_BOOKS = [
    "리딩튜터 스타터(1)", "리딩튜터 스타터(2)", "리딩튜터 스타터(3)",
    "리딩튜터 주니어(1)", "리딩튜터 주니어(2)", "리딩튜터 주니어(3)", "리딩튜터 주니어(4)",
    "수능토픽(레벨1)", "수능토픽(레벨2)", "수능토픽(레벨3)",
    "English Newspaper_Kids", "English Newspaper_Kinder", "자체 독해 자료"
]

# 문법 (Azar 통합 리스트 유지)
AZAR_BASIC_FULL_LIST = [
    "1-1 단수 인칭대명사+Be동사", "1-2 복수 인칭대명사+Be동사", "1-3 단수 명사+Be동사", "1-4 복수 명사+Be동사", 
    "1-5 인칭대명사+Be동사 축약", "1-6 Be동사 부정문", "1-7 Be동사+형용사", "1-8 Be동사+장소", "1-9 Be동사 구조 요약",
    "2-1 This/That", "2-2 These/Those", "2-3 Be동사 Yes/No 의문문", "2-4 의문문 대답", 
    "2-5 Where 의문문", "2-6 Have/Has", "2-7 소유격 인칭대명사", "2-8 What/Who 의문문",
    "3-1 현재시제 형태/의미", "3-2 빈도부사", "3-3 빈도부사 위치", "3-4 3인칭 단수 -es", 
    "3-5 3인칭 단수 -y", "3-6 Has, Does, Goes", "3-7 Like/Want/Need/Would Like", "3-8 현재시제 부정문", 
    "3-9 Yes/No 의문문", "3-10 Where/What 의문문", "3-11 When/What Time 의문문",
    "4-1 현재진행형 Be+-ing", "4-2 동사의 -ing", "4-3 현재진행 부정문", "4-4 현재진행 의문문", 
    "4-5 현재 vs 진행", "4-6 상태동사", "4-7 See/Look/Watch/Hear/Listen", "4-8 Think About vs That", "4-9 명령문",
    "5-1 명사 단수/복수", "5-2 불규칙 복수형", "5-3 형용사의 쓰임", "5-4 명사: 주어/목적어", 
    "5-5 주격/목적격 대명사", "5-6 전치사+목적격 대명사", "5-7 소유형용사/대명사", "5-8 명사 소유격", "5-9 Whose 의문문", "5-10 소유격 불규칙 복수",
    "6-1 셀 수 있는/없는 명사", "6-2 A vs An", "6-3 A/An vs Some", "6-4 물질명사 수량", 
    "6-5 Many/Much/Few/Little", "6-6 정관사 The", "6-7 관사 미사용", "6-8 Some/Any",
    "7-1 비인칭주어 It(시간)", "7-2 시간 전치사", "7-3 비인칭주어 It(날씨)", "7-4 There+Be동사", 
    "7-5 There+Be동사 의문문", "7-6 How Many 의문문", "7-7 장소 전치사", "7-8 위치 전치사", "7-9 Would Like", "7-10 Would Like vs Like"
]

# 라이팅 및 트레이닝북 전체 상세 목차 유지
WRITING_DATA = {
    "OK Writing 1": ["Vocab", "Sentence 1~6", "Part 1. 전치사", "Part 2. 진행형", "Part 3. 부정문", "Part 4. and/because", "Part 5. 명령문", "Story 1-1~3-4"],
    "OK Writing 2": ["Vocab", "Sentence 1~6", "Part 1. 소유격", "Part 2. There is/are", "Part 3. but/because", "Part 4. 대상 2개", "Part 5. 의문문", "Part 6. look+형용사", "Part 7. don't", "Story 1-1~3-4"],
    "OK Writing 3": ["Vocab", "Sentence 1~9", "Part 1. of", "Part 2. to부정사", "Part 3. can", "Part 4. 비인칭", "Part 5. Let's", "Part 6. 3인칭단수", "Part 7. doesn't", "Story 1-1~3-5"],
    "OK Writing 4": ["Vocab", "Sentence 1~7", "Part 1. will", "Part 2. must", "Part 3. to부정사", "Part 4. that절", "Part 5. Do", "Part 6. 의문사", "Story 1-1~2-4"],
    "OK Writing 5": ["Vocab", "Sentence 1~9", "Part 1. 명령문", "Part 2. 빈도부사", "Part 3. Does", "Part 4. to부정사", "Part 5. 원급", "Part 6. 비교급", "Part 7. 최상급", "Story 1-1~2-2"],
    "OK Writing 6": ["Vocab", "Sentence 1~8", "Part 1. 과거", "Part 2. have to", "Part 3. Did", "Part 4. didn't", "Part 5. 동명사주어", "Part 6. 의문사구", "Part 7. 접속사", "Story 1-1~1-6"],
    "OK Writing 7": ["Vocab", "Sentence 1~12", "Part 1. 동명사목적어", "Part 2. 가주어 it", "Part 3. 형용사보어", "Part 4. 재귀대명사", "Part 5. 의문사구", "Part 6. should", "Part 7. 지각동사", "Story 1-1~3-2"],
    "Bridge Writing 시리즈": ["Vocab", "Sentence 1~6", "Part 1~6", "Story"],
    "Training for Reading S1": ["Vocabulary", "Training 1. a/an/the+명사", "Training 2. 복수명사", "Training 3. 형용사+명사", "Training 4. 전치사+명사 (1)", "Training 5. 전치사+명사 (2)", "Training 6. 전치사+명사 (3)", "Training 7. 주인공+동작 (1)", "Training 8. 주인공+동작 (2)", "Training 9. 주인공+동작 (3)", "Training 10. 주인공+동작+대상 (1)", "Training 11. 주인공+동작+대상 (2)"],
    "Training for Reading S2": ["Vocabulary", "Training 1. 주인공+be+명사 (1)", "Training 2. 주인공+be+명사 (2)", "Training 3. 주인공+be+형용사", "Training 4. 주인공+be+명사/형용사 (1)", "Training 5. 주인공+be+명사/형용사 (2)", "Training 6. 주인공+be+명사/형용사 (3)", "Training 7. 주인공+be+전치사+명사 (1)", "Training 8. 주인공+be+전치사+명사 (2)", "Training 9. 주인공+be+전치사+명사 (3)", "Training 10. 주인공+be+명사/형용사/전치사 (Review)", "Training 11. 명령문"],
    "Training for Reading S3": ["Vocabulary", "Training 1. This/That+is+단수명사", "Training 2. This/That+is+소유격+명사 (1)", "Training 3. This/That+is+소유격+명사 (2)", "Training 4. 주인공과 대상이 ‘소유격+명사’", "Training 5. 주인공+동작+전치사+명사", "Training 6. 주인공+동작+대상+전치사+명사", "Training 7. 명령문: 동작+(대상)+전치사+명사", "Training 8. 주인공+be+~ing+(대상)", "Training 9. 주인공+be+~ing+(대상)+전치사+명사", "Story 1-1", "Story 1-2", "Story 1-3", "Story 2", "Story 3"],
    "Training for Reading S4": ["Vocabulary", "Training 1. 주인공+동작+대상(대명사)", "Training 2. 명사 and 명사", "Training 3. 형용사 and 형용사", "Training 4. 문장 and 문장", "Training 5. Because 주인공+동작", "Training 6. 주인공+동작+(대상)+부사", "Training 7. 부사+형용사", "Training 8. 부사+부사", "Training 9. 부사의 다양한 위치", "Story 1-1", "Story 1-2", "Story 1-3", "Story 2-1", "Story 2-2"]
}

# --- [메인 화면 로직] ---
if "page" not in st.session_state: st.session_state.page = 'input'
if "ai_res" not in st.session_state: st.session_state.ai_res = ""

if st.session_state.page == 'input':
    st.title("🍎 엘케이어학원 학습 리포트") 

    # [엑셀 불러오기 섹션 - 세로형 대응 유지]
    with st.expander("📂 학생 교재 목록(엑셀) 불러오기", expanded=False):
        uploaded_excel = st.file_uploader("항목명이 세로(A열)로 된 엑셀 파일을 업로드하세요", type=['xlsx'])
        student_data = None
        if uploaded_excel:
            df_raw = pd.read_excel(uploaded_excel, index_col=0) 
            df = df_raw.T.reset_index() 
            st.success("세로형 엑셀 파일을 성공적으로 읽어 뒤집었습니다!")
            sel_student = st.selectbox("학생 선택", ["선택 안 함"] + list(df['이름'].unique()))
            if sel_student != "선택 안 함":
                student_data = df[df['이름'] == sel_student].iloc[0]

    st.divider()

    # 1. 기본 정보
    st.subheader("📍 1. 기본 정보")
    report_date = st.date_input("학습일 선택", value=datetime.today())
    c1, c2, c3 = st.columns(3)
    
    grade_list = ["초등", "중등", "고등"]
    grade_def = grade_list.index(student_data['학년']) if student_data is not None and student_data['학년'] in grade_list else 0
    grade = c1.selectbox("학년", grade_list, index=grade_def)
    
    class_list = ["선택 없음", "Beginner-2시", "Beginner-3시", "Ph1", "Inter 2시", "G-Advanced 2시"]
    class_def = class_list.index(student_data['반']) if student_data is not None and student_data['반'] in class_list else 0
    class_name = c2.selectbox("반 선택", class_list, index=class_def)
    
    name = st.text_input("학생 이름", value=student_data['이름'] if student_data is not None else "", placeholder="이름 입력")

    st.divider()

    # 2. 어휘 섹션 (전체 목록 복구 및 회차별 입력)
    st.subheader("🅰️ 2. 어휘 (Vocabulary)")
    vc1, vc2 = st.columns([2, 1])
    
    v_def = V_BOOKS_LIST.index(student_data['어휘교재']) if student_data is not None and student_data['어휘교재'] in V_BOOKS_LIST else 0
    v_book = vc1.selectbox("어휘 교재", V_BOOKS_LIST, index=v_def)
    v_unit = vc2.text_input("Unit 입력", placeholder="예: <Unit 01>")
    
    st.markdown("**[회차별 테스트 결과]**")
    r1, r2, r3 = st.columns(3)
    with r1:
        v1_c = st.number_input("1회차 맞은 개수", min_value=0, key="v1c")
        v1_t = st.number_input("1회차 전체 개수", min_value=1, value=20, key="v1t")
    with r2:
        v2_c = st.number_input("2회차 맞은 개수", min_value=0, key="v2c")
        v2_t = st.number_input("2회차 전체 개수", min_value=1, value=20, key="v2t")
    with r3:
        v3_c = st.number_input("3회차 맞은 개수", min_value=0, key="v3c")
        v3_t = st.number_input("3회차 전체 개수", min_value=1, value=20, key="v3t")

    st.divider()

    # 3. 주교재 수업 상세 (Unit 입력창 분리 유지)
    st.subheader("📚 3. 주교재 및 수업 상세")
    
    elt_books = ["선택 안 함"] + ELT_BOOKS
    elt_def = elt_books.index(student_data['ELT교재']) if student_data is not None and str(student_data['ELT교재']) in elt_books else 0
    elt_book = st.selectbox("ELT 독해 교재", elt_books, index=elt_def)
    elt_unit = st.text_input("└ ELT Unit 입력", placeholder="예: <Unit 01>")

    r_books = ["선택 안 함"] + READING_BOOKS
    r_def = r_books.index(student_data['독해교재']) if student_data is not None and str(student_data['독해교재']) in r_books else 0
    r_book = st.selectbox("독해 교재", r_books, index=r_def)
    r_unit = st.text_input("└ 독해 Unit 입력", placeholder="예: <Unit 01>")

    g_books = ["선택 안 함", "Azar Basic (Red)", "Azar Fundamentals", "기타"]
    g_def = g_books.index(student_data['문법교재']) if student_data is not None and str(student_data['문법교재']) in g_books else 0
    g_book = st.selectbox("문법 교재", g_books, index=g_def)
    g_sub = "선택 안 함"
    if g_book == "Azar Basic (Red)":
        g_sub = st.selectbox("└ Azar 세부 항목", AZAR_BASIC_FULL_LIST)
    elif g_book != "선택 안 함":
        g_sub = st.text_input("└ 단원명 직접 입력")

    w_books = ["선택 안 함"] + list(WRITING_DATA.keys())
    w_def = w_books.index(student_data['라이팅교재']) if student_data is not None and str(student_data['라이팅교재']) in w_books else 0
    w_book = st.selectbox("라이팅 교재", w_books, index=w_def)
    w_ls = "선택 안 함"
    if w_book != "선택 안 함":
        w_ls = st.selectbox("└ 라이팅 세부 단원", WRITING_DATA[w_book])

    st.divider()

    # 4. 과제 정밀 분석
    st.subheader("📸 4. 과제 정밀 분석")
    up_file = st.file_uploader("과제 사진 업로드", type=['jpg', 'png'])
    domain = st.selectbox("분석 영역", ["선택 안 함", "문법", "어휘", "독해", "라이팅"])
    
    if st.button("🤖 과제 분석 시작"):
        if up_file and domain != "선택 안 함":
            with st.spinner("분석 중..."):
                try:
                    img = Image.open(up_file)
                    img.thumbnail((800, 800))
                    prompt = f"엘케이어학원 선생님으로서 이 {domain} 과제 사진을 보고 학생의 성취도를 한국어로 2~3문장 분석해줘."
                    res = client.models.generate_content(model="gemini-1.5-flash", contents=[prompt, img])
                    st.session_state.ai_res = res.text
                except Exception as e: st.error(f"오류: {e}")

    ai_fb = st.text_area("분석 결과 확인", value=st.session_state.ai_res, height=120)

    st.divider()

    # 5. 선생님 총평
    st.subheader("✍️ 5. 선생님 총평")
    content = st.text_area("상세 피드백 (태도 등)")
    hw_status = st.selectbox("과제 수행도", ["매우 우수", "우수", "보통", "미흡"])

    if st.button("리포트 생성", type="primary"):
        if not name: st.warning("이름을 입력하세요.")
        else:
            display_class = f"{class_name} " if class_name != "선택 없음" else ""
            target_info = f"{grade} {display_class}{name} 학생"
            
            v_results = [f"• 1회차: {v1_c} / {v1_t} ({int((v1_c/v1_t)*100)}%)"]
            if v2_c > 0: v_results.append(f"• 2회차: {v2_c} / {v2_t} ({int((v2_c/v2_t)*100)}%)")
            if v3_c > 0: v_results.append(f"• 3회차: {v3_c} / {v3_t} ({int((v3_c/v3_t)*100)}%)")
            
            items = []
            if elt_book != "선택 안 함": items.append(f"• ELT독해: {elt_book} [{elt_unit}]")
            if r_book != "선택 안 함": items.append(f"• 독해: {r_book} [{r_unit}]")
            if g_book != "선택 안 함": items.append(f"• 문법: {g_book} [{g_sub}]")
            if w_book != "선택 안 함": items.append(f"• 라이팅: {w_book} [{w_ls}]")
            
            f_sec = f"\n[선생님 피드백]\n{content}\n" if content.strip() else ""
            a_sec = f"\n[과제 정밀 분석 - {domain}]\n{ai_fb}\n" if ai_fb.strip() else ""

            report_text = f"""[ 엘케이어학원 학습 리포트 ]

■ 대상: {target_info}
■ 학습일: {report_date}

1. 어휘 테스트 결과
- 교재명: {v_book} ({v_unit})
{"\n".join(v_results)}

2. 주교재 학습 내용
{"\n".join(items)}
{f_sec}{a_sec}
3. 과제 수행도: {hw_status}"""

            st.session_state.final_text = report_text
            st.session_state.page = 'result'; st.rerun()

elif st.session_state.page == 'result':
    st.title("📄 완성된 리포트")
    st.text_area("텍스트 복사", st.session_state.final_text, height=500)
    if st.button("처음으로 돌아가기"):
        st.session_state.ai_res = ""; st.session_state.page = 'input'; st.rerun()
