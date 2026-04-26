import streamlit as st
import os
import json
import io
from PIL import Image
from datetime import datetime
from google import genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# 1. 페이지 설정
st.set_page_config(page_title="엘케이어학원 학습 리포트", layout="centered")

# 설정값
FOLDER_ID = "1bMHs-3Ak27JU_ADF9_UVknkHjCEtumR2"
HISTORY_FILE = "student_history.json"

# 2. AI 클라이언트 설정 (2026년 가장 안정적인 모델 설정)
if "gemini_api_key" in st.secrets:
    client = genai.Client(api_key=st.secrets["gemini_api_key"])
else:
    st.error("Secrets에 'gemini_api_key'를 등록해 주세요.")

# --- [내부 기능 함수] ---
def upload_to_google_drive(content, file_name, folder_id):
    try:
        info = json.loads(st.secrets["google_drive"]["service_account_json"])
        creds = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        fh = io.BytesIO(content.encode('utf-8'))
        media = MediaIoBaseUpload(fh, mimetype='text/plain', resumable=True)
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return True, "성공"
    except Exception as e:
        return False, str(e)

# 3. 방대한 교재 데이터 정의 (선생님이 쓰시던 상세 목록 100% 복구)
GRADE_LIST = ["초등", "중등", "고등"]
CLASS_LIST = ["선택 없음", "Beginner-2시", "Beginner-3시", "Beginner-4시", "Ph1", "Ph2", "Ph3", "Ph4", "Ph5", "Inter 2시", "Inter 3시", "Inter 4시", "G-Advanced 2시", "G-Advanced 3시", "G-Advanced 4시"]

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
    "Bridge Writing 4-1": ["Vocab", "Sentence 1~6", "Part 1~5", "Story 1~2.5"],
    "Bridge Writing 4-2": ["Vocab", "Sentence 1~6", "Part 1~5", "Story 1~3.3"],
    "Bridge Writing 5": ["Vocab", "Sentence 1~9", "Part 1~6", "Story 1~2.4"],
    "Bridge Writing 6-1": ["Vocab", "Sentence 1~6", "Part 1~6", "Story 1~2.4"],
    "Bridge Writing 6-2": ["Vocab", "Sentence 1~6", "Part 1~6", "Story 1~3.2"],
    "Training for Reading S1": ["Vocab", "Training 1~11"],
    "Training for Reading S2": ["Vocab", "Training 1~11"],
    "Training for Reading S3": ["Vocab", "Training 1~9", "Story 1~3"],
    "Training for Reading S4": ["Vocab", "Training 1~9", "Story 1~2.2"]
}

READING_BOOKS_DATA = ["리딩튜터 스타터(1)", "리딩튜터 스타터(2)", "리딩튜터 스타터(3)", "리딩튜터 주니어(1)", "리딩튜터 주니어(2)", "리딩튜터 주니어(3)", "리딩튜터 주니어(4)", "수능토픽(레벨1)", "수능토픽(레벨2)", "수능토픽(레벨3)", "English Newspaper_Kids", "English Newspaper_Kinder"]
ELT_BOOKS = ["30 Word Reading(1)", "30 Word Reading(2)", "40 Word Reading(1)", "40 Word Reading(2)", "40 Read it(1)", "40 Read it(2)", "40 Read it(3)", "60 Read it(1)", "60 Read it(2)", "60 Read it(3)"]
V_BOOKS = ["능률 보카 기본 400", "능률 보카 필수 500", "[개정]교육청 필수 900", "보카익스프레스", "보카클리어", "기타"]

# --- [화면 구성] ---
if "page" not in st.session_state: st.session_state.page = 'input'
if "ai_res" not in st.session_state: st.session_state.ai_res = ""

if st.session_state.page == 'input':
    st.title("🍎 엘케이어학원 학습 리포트") 
    
    # 1. 기본 정보
    st.subheader("📍 1. 기본 정보")
    report_date = st.date_input("학습일 선택", value=datetime.today())
    c1, c2, c3 = st.columns(3)
    grade = c1.selectbox("학년", GRADE_LIST)
    class_name = c2.selectbox("반 선택", CLASS_LIST)
    name = st.text_input("학생 이름 확인", placeholder="이름을 입력하세요 (예: 강재윤)")

    st.divider()

    # 2. 어휘 정보 (복구됨)
    st.subheader("🅰️ 2. 어휘 (Vocabulary)")
    v_book = st.selectbox("어휘 교재", V_BOOKS)
    cv1, cv2, cv3 = st.columns(3)
    v_unit = cv1.text_input("Unit", value="1")
    v_corr = cv2.number_input("맞은 개수", min_value=0, value=0)
    v_tot = cv3.number_input("전체 개수", min_value=1, value=20)

    st.divider()

    # 3. 주교재 및 수업 상세 (문법/독해/라이팅 복구됨)
    st.subheader("📚 3. 주교재 수업 상세")
    ce1, ce2 = st.columns(2)
    elt_book = ce1.selectbox("ELT Reading", ["선택 안 함"] + ELT_BOOKS)
    g_book = ce2.selectbox("문법 (Grammar)", ["선택 안 함", "Azar Basic", "Azar Fundamentals", "자체 교재", "기타"])
    
    cr1, cr2 = st.columns(2)
    r_book = cr1.selectbox("독해 (Reading/News)", ["선택 안 함"] + READING_BOOKS_DATA)
    w_book = cr2.selectbox("라이팅 (Writing)", ["선택 안 함"] + list(WRITING_DATA.keys()))
    
    w_ls = ""
    if w_book != "선택 안 함":
        w_ls = st.selectbox("라이팅 세부 단원", WRITING_DATA[w_book])

    st.divider()

    # 4. AI 과제 분석 (안정화됨)
    st.subheader("📸 4. AI 과제 정밀 분석")
    uploaded_file = st.file_uploader("과제 사진을 업로드하세요", type=['jpg', 'jpeg', 'png'])
    domain = st.selectbox("분석 영역 선택", ["선택 안 함", "문법", "어휘", "독해", "라이팅"])
    
    if uploaded_file and domain != "선택 안 함":
        if st.button("🤖 AI 과제 분석 시작"):
            with st.spinner("AI 선생님이 꼼꼼하게 읽고 있습니다..."):
                try:
                    img = Image.open(uploaded_file)
                    img.thumbnail((800, 800)) # 용량 최적화
                    prompt = f"너는 엘케이어학원 선생님이야. 이 {domain} 과제 사진을 보고 학생의 학습 상태를 정중하고 따뜻하게 분석해줘. 한국어로 2~3문장으로 짧게 써줘."
                    # gemini-1.5-flash로 안정적인 연결 확보
                    response = client.models.generate_content(
                        model="gemini-1.5-flash", 
                        contents=[prompt, img]
                    )
                    st.session_state.ai_res = response.text
                except Exception as e:
                    st.error(f"AI 오류: {e}")

    ai_feedback = st.text_area("AI 분석 결과 피드백", value=st.session_state.ai_res, height=150)

    st.divider()

    # 5. 선생님 총평 및 수행도 (복구됨)
    st.subheader("✍️ 5. 선생님 총평")
    content = st.text_area("선생님 상세 피드백", placeholder="오늘의 수업 태도와 성취도를 입력하세요.")
    hw_status = st.selectbox("과제 수행도", ["매우 우수", "우수", "보통", "미흡"])

    # 저장 및 생성
    if st.button("리포트 생성 및 저장", type="primary"):
        # [반명 로직] '선택 없음'일 경우 제거
        display_class = f"{class_name} " if class_name != "선택 없음" else ""
        target_info = f"{grade} {display_class}{name} 학생"
        
        main_items = []
        if elt_book != "선택 안 함": main_items.append(f"• ELT독해: {elt_book}")
        if g_book != "선택 안 함": main_items.append(f"• 문법: {g_book}")
        if r_book != "선택 안 함": main_items.append(f"• 독해: {r_book}")
        if w_book != "선택 안 함": main_items.append(f"• 라이팅: {w_book} [{w_ls}]")
        
        f_sec = f"\n[선생님 피드백]\n{content}\n" if content.strip() else ""
        ai_sec = f"\n[AI 과제 정밀 분석 - {domain}]\n{ai_feedback}\n" if ai_feedback.strip() else ""

        # [리포트 서식 적용] ■ 기호 및 학습일 표기
        report_text = f"""[ 엘케이어학원 학습 리포트 ]

■ 대상: {target_info}
■ 학습일: {report_date}

1. 어휘 테스트 결과
- 교재명: {v_book} (Unit {v_unit})
- 결과: {v_corr} / {v_tot} (정답률 {int((v_corr/v_tot)*100)}%)

2. 주교재 학습 내용
{"\n".join(main_items)}
{f_sec}{ai_sec}
3. 과제 수행도: {hw_status}"""

        file_name = f"{report_date.strftime('%Y%m%d')}_{name}.txt"
        success, msg = upload_to_google_drive(report_text, file_name, FOLDER_ID)
        
        if success:
            st.session_state.final_text = report_text
            st.session_state.page = 'result'
            st.rerun()
        else:
            st.error(f"저장 실패: {msg}")

elif st.session_state.page == 'result':
    st.title("📄 완성된 리포트")
    st.text_area("텍스트 복사 (카톡용)", st.session_state.final_text, height=450)
    if st.button("처음으로 돌아가기"):
        st.session_state.ai_res = ""
        st.session_state.page = 'input'
        st.rerun()
