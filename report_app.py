import streamlit as st
import os
import json
import io
from PIL import Image
from datetime import datetime
from google import genai  # 2026 최신형 AI 라이브러리
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# 1. 페이지 설정
st.set_page_config(page_title="엘케이어학원 학습 리포트", layout="centered")

# 설정값
FOLDER_ID = "1bMHs-3Ak27JU_ADF9_UVknkHjCEtumR2"

# 2. AI 클라이언트 설정 (2026년 표준 gemini-2.0-flash 적용)
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

# 3. 데이터 정의 (모든 교재 목록 복구)
GRADE_LIST = ["초등", "중등", "고등"]
CLASS_LIST = ["선택 없음", "Beginner-2시", "Beginner-3시", "Beginner-4시", "Ph1", "Ph2", "Ph3", "Ph4", "Ph5", "Inter 2시", "Inter 3시", "Inter 4시", "G-Advanced 2시", "G-Advanced 3시", "G-Advanced 4시"]

WRITING_DATA = {
    "Basic Structure": ["1. 명사", "2. 대명사", "3. 형용사", "4. 동작", "5. 기본문장Ⅰ", "6. 전치사", "7. 기본문장+전치사+명사", "8. 기본문장Ⅱ"],
    "OK Writing 1~7": ["Vocab", "Sentence", "Part 1~7", "Story"],
    "Bridge Writing 시리즈": ["Vocab", "Sentence", "Part 1~6", "Story"],
    "Training for Reading": ["Vocab", "Training 1~11", "Story"]
}
READING_BOOKS_DATA = ["리딩튜터 시리즈", "수능토픽 시리즈", "English Newspaper"]
ELT_BOOKS = ["30 Word Reading", "40 Word Reading", "40 Read it", "60 Read it"]
V_BOOKS = ["능률 보카 시리즈", "교육청 필수 900", "보카클리어", "기타"]

# --- [화면 구성] ---
if "page" not in st.session_state: st.session_state.page = 'input'
if "ai_res" not in st.session_state: st.session_state.ai_res = ""

if st.session_state.page == 'input':
    st.title("🍎 엘케이어학원 학습 리포트") 
    
    # [섹션 1] 기본 정보
    st.header("1. 기본 정보")
    report_date = st.date_input("학습일 선택", value=datetime.today())
    c1, c2, c3 = st.columns(3)
    grade = c1.selectbox("학년", GRADE_LIST)
    class_name = c2.selectbox("반 선택", CLASS_LIST)
    name = st.text_input("학생 이름 확인", placeholder="이름을 적어주세요")

    st.divider()

    # [섹션 2] 어휘 테스트 (사라졌던 칸 복구)
    st.header("2. 어휘 (Vocabulary)")
    v_book = st.selectbox("어휘 교재 선택", V_BOOKS)
    cv1, cv2, cv3 = st.columns(3)
    v_unit = cv1.text_input("Unit", value="1")
    v_corr = cv2.number_input("맞은 개수", min_value=0, value=0)
    v_tot = cv3.number_input("전체 개수", min_value=1, value=20)

    st.divider()

    # [섹션 3] 주교재 수업 상세 (사라졌던 칸 복구)
    st.header("3. 주교재 수업 상세")
    elt_book = st.selectbox("ELT 독해", ["선택 안 함"] + ELT_BOOKS)
    g_book = st.selectbox("문법 (Grammar)", ["선택 안 함", "Azar 시리즈", "자체 교재", "기타"])
    r_book = st.selectbox("독해 (Reading/News)", ["선택 안 함"] + READING_BOOKS_DATA)
    w_book = st.selectbox("라이팅 (Writing)", ["선택 안 함"] + list(WRITING_DATA.keys()))
    
    w_ls = ""
    if w_book != "선택 안 함":
        w_ls = st.selectbox("세부 단원 선택", WRITING_DATA[w_book])

    st.divider()

    # [섹션 4] AI 과제 분석
    st.header("4. AI 과제 정밀 분석")
    uploaded_file = st.file_uploader("과제 사진을 업로드하세요", type=['jpg', 'jpeg', 'png'])
    domain = st.selectbox("분석 영역", ["선택 안 함", "문법", "어휘", "독해", "라이팅"])
    
    if uploaded_file and domain != "선택 안 함":
        if st.button("🤖 AI 과제 분석 시작"):
            with st.spinner("AI 선생님이 분석 중입니다..."):
                try:
                    img = Image.open(uploaded_file)
                    img.thumbnail((1024, 1024))
                    prompt = f"너는 엘케이어학원 선생님이야. 이 {domain} 과제 사진을 보고 학생의 학습 상태를 정중하게 분석해줘. 한국어로 2~3문장으로 써줘."
                    # 모델명을 gemini-2.0-flash로 변경하여 404 에러 해결
                    response = client.models.generate_content(model="gemini-2.0-flash", contents=[prompt, img])
                    st.session_state.ai_res = response.text
                except Exception as e:
                    st.error(f"AI 오류 발생: {e}")

    ai_feedback = st.text_area("AI 분석 결과", value=st.session_state.ai_res, height=150)

    st.divider()

    # [섹션 5] 선생님 총평 및 수행도
    st.header("5. 선생님 총평")
    content = st.text_area("상세 피드백", placeholder="오늘의 수업 내용과 태도를 적어주세요.")
    hw_status = st.selectbox("과제 수행도", ["매우 우수", "우수", "보통", "미흡"])

    # [저장 버튼]
    if st.button("리포트 생성 및 저장", type="primary"):
        # '선택 없음'일 경우 반 정보 제외 로직
        display_class = f"{class_name} " if class_name != "선택 없음" else ""
        target_info = f"{grade} {display_class}{name} 학생"
        
        main_items = []
        if elt_book != "선택 안 함": main_items.append(f"• ELT독해: {elt_book}")
        if g_book != "선택 안 함": main_items.append(f"• 문법: {g_book}")
        if r_book != "선택 안 함": main_items.append(f"• 독해: {r_book}")
        if w_book != "선택 안 함": main_items.append(f"• 라이팅: {w_book} [{w_ls}]")
        
        f_sec = f"\n[선생님 피드백]\n{content}\n" if content.strip() else ""
        a_sec = f"\n[AI 과제 정밀 분석 - {domain}]\n{ai_feedback}\n" if ai_feedback.strip() else ""

        report_text = f"""[ 엘케이어학원 학습 리포트 ]

■ 대상: {target_info}
■ 학습일: {report_date}

1. 어휘 테스트 결과
- 교재명: {v_book} (Unit {v_unit})
- 결과: {v_corr} / {v_tot} (정답률 {int((v_corr/v_tot)*100)}%)

2. 주교재 학습 내용
{"\n".join(main_items)}
{f_sec}{a_sec}
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
    st.text_area("텍스트 복사", st.session_state.final_text, height=450)
    if st.button("처음으로 돌아가기"):
        st.session_state.ai_res = ""
        st.session_state.page = 'input'
        st.rerun()
