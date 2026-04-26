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

# 2. AI 클라이언트 설정 (안정형)
if "gemini_api_key" in st.secrets:
    client = genai.Client(api_key=st.secrets["gemini_api_key"])
else:
    st.error("Secrets에 'gemini_api_key'를 등록해 주세요.")

# --- [기능 함수] ---
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

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

# 3. [복구 데이터] 상세 커리큘럼 정의
# 꺽쇠 형식의 유닛 리스트 (1-16)
UNIT_NUMBERS = [f"<Unit {i:02d}>" for i in range(1, 17)]

# Azar Basic 1권 상세 챕터
AZAR_BASIC_CHAPTERS = [
    "Chapter 01 (Using Be)", "Chapter 02 (Be-Negative/Question)", "Chapter 03 (Present Simple)",
    "Chapter 04 (Present Continuous)", "Chapter 05 (Talking about Present)", "Chapter 06 (Nouns & Pronouns)",
    "Chapter 07 (Count/Noncount Nouns)", "Chapter 08 (Past Time Part 1)", "Chapter 09 (Past Time Part 2)",
    "Chapter 10 (Future Time Part 1)", "Chapter 11 (Future Time Part 2)", "Chapter 12 (Modals Part 1)",
    "Chapter 13 (Modals Part 2)", "Chapter 14 (Nouns & Modifiers)", "Chapter 15 (Comparisons)", "Chapter 16 (Phrasal Verbs)"
]

# 독해 교재 상세 리스트
READING_BOOKS = [
    "리딩튜터 스타터(1)", "리딩튜터 스타터(2)", "리딩튜터 스타터(3)",
    "리딩튜터 주니어(1)", "리딩튜터 주니어(2)", "리딩튜터 주니어(3)", "리딩튜터 주니어(4)",
    "수능토픽(레벨1)", "수능토픽(레벨2)", "수능토픽(레벨3)",
    "English Newspaper (Kids)", "English Newspaper (Junior)", "자체 독해 자료"
]

# --- [메인 화면] ---
if "page" not in st.session_state: st.session_state.page = 'input'
if "ai_res" not in st.session_state: st.session_state.ai_res = ""
history_data = load_history()

if st.session_state.page == 'input':
    st.title("🍎 엘케이어학원 학습 리포트") 
    
    # [기능] 과거 기록 불러오기
    with st.expander("🔍 학생 과거 정보 불러오기", expanded=False):
        all_students = sorted(list(history_data.keys()))
        search_name = st.selectbox("기본 정보 자동 채우기", ["직접 입력"] + all_students)
        last_record = history_data.get(search_name, {}) if search_name != "직접 입력" else {}

    st.divider()

    # 1. 기본 정보
    st.subheader("📍 1. 기본 정보")
    report_date = st.date_input("학습일 선택", value=datetime.today())
    c1, c2, c3 = st.columns(3)
    
    grade_idx = ["초등", "중등", "고등"].index(last_record.get("grade", "초등"))
    grade = c1.selectbox("학년", ["초등", "중등", "고등"], index=grade_idx)
    
    class_list = ["선택 없음", "Beginner-2시", "Beginner-3시", "Ph1", "Inter 2시", "G-Advanced 2시"]
    class_idx = class_list.index(last_record.get("class", "선택 없음")) if last_record.get("class") in class_list else 0
    class_name = c2.selectbox("반 선택", class_list, index=class_idx)
    
    name = st.text_input("학생 이름", value=search_name if search_name != "직접 입력" else "", placeholder="이름 입력")

    st.divider()

    # 2. 어휘 섹션
    st.subheader("🅰️ 2. 어휘 (Vocabulary)")
    vc1, vc2 = st.columns([2, 1])
    v_book = vc1.selectbox("어휘 교재", ["능률 보카 기본", "능률 보카 필수", "교육청 900", "보카클리어", "기타"])
    v_unit_num = vc2.selectbox("Unit 선택", UNIT_NUMBERS)
    
    cv1, cv2 = st.columns(2)
    v_corr = cv1.number_input("맞은 개수", min_value=0, value=0)
    v_tot = cv2.number_input("전체 개수", min_value=1, value=20)

    st.divider()

    # 3. 주교재 수업 상세 (독해 및 아자르 문법 복구)
    st.subheader("📚 3. 주교재 및 수업 내용")
    
    col1, col2 = st.columns(2)
    with col1:
        # 독해 교재 리스트 복구
        r_book = st.selectbox("독해 교재 선택", ["선택 안 함"] + READING_BOOKS)
        r_unit = st.selectbox("독해 Unit", ["선택 안 함"] + UNIT_NUMBERS)
        
    with col2:
        # Azar Basic 1권 챕터 복구
        g_book = st.selectbox("문법 교재 선택", ["선택 안 함", "Azar Basic 1 (Red)", "Azar Fundamentals", "기타"])
        g_chapter = "선택 안 함"
        if g_book == "Azar Basic 1 (Red)":
            g_chapter = st.selectbox("└ Azar 상세 챕터", AZAR_BASIC_CHAPTERS)
        else:
            g_chapter = st.text_input("└ 기타 문법 단원", placeholder="단원명 직접 입력")

    st.divider()

    # 4. AI 과제 분석
    st.subheader("📸 4. AI 과제 정밀 분석")
    uploaded_file = st.file_uploader("사진을 올려주세요", type=['jpg', 'jpeg', 'png'])
    domain = st.selectbox("영역 선택", ["선택 안 함", "문법", "어휘", "독해", "라이팅"])
    
    if st.button("🤖 AI 과제 분석 시작"):
        if uploaded_file and domain != "선택 안 함":
            with st.spinner("선생님, 잠시만요! 분석 중입니다..."):
                try:
                    img = Image.open(uploaded_file)
                    img.thumbnail((800, 800))
                    prompt = f"엘케이어학원 선생님으로서 이 {domain} 과제 사진을 분석해서 학생의 성취도를 한국어로 2~3문장 써줘."
                    response = client.models.generate_content(model="gemini-1.5-flash", contents=[prompt, img])
                    st.session_state.ai_res = response.text
                except Exception as e:
                    st.error(f"오류: {e}")
    
    ai_feedback = st.text_area("AI 분석 결과", value=st.session_state.ai_res, height=120)

    st.divider()

    # 5. 선생님 총평
    st.subheader("✍️ 5. 선생님 총평")
    content = st.text_area("추가 피드백 (수업 태도 등)")
    hw_status = st.selectbox("과제 수행도", ["매우 우수", "우수", "보통", "미흡"])

    # 생성 및 저장
    if st.button("리포트 저장 및 생성", type="primary"):
        if not name: st.warning("이름을 입력하세요."); st.stop()
        
        display_class = f"{class_name} " if class_name != "선택 없음" else ""
        target_info = f"{grade} {display_class}{name} 학생"
        
        main_items = []
        if r_book != "선택 안 함": main_items.append(f"• 독해: {r_book} [{r_unit}]")
        if g_book != "선택 안 함": main_items.append(f"• 문법: {g_book} [{g_chapter}]")
        
        f_sec = f"\n[선생님 피드백]\n{content}\n" if content.strip() else ""
        a_sec = f"\n[AI 과제 분석 - {domain}]\n{ai_feedback}\n" if ai_feedback.strip() else ""

        report_text = f"""[ 엘케이어학원 학습 리포트 ]

■ 대상: {target_info}
■ 학습일: {report_date}

1. 어휘 테스트 결과
- 교재명: {v_book} ({v_unit_num})
- 결과: {v_corr} / {v_tot} (정답률 {int((v_corr/v_tot)*100)}%)

2. 주교재 학습 내용
{"\n".join(main_items)}
{f_sec}{a_sec}
3. 과제 수행도: {hw_status}"""

        # 히스토리 업데이트
        history_data[name] = {"grade": grade, "class": class_name}
        save_history(history_data)

        # 저장
        f_name = f"{report_date.strftime('%Y%m%d')}_{name}.txt"
        success, msg = upload_to_google_drive(report_text, f_name, FOLDER_ID)
        if success:
            st.session_state.final_text = report_text
            st.session_state.page = 'result'; st.rerun()
        else: st.error(f"저장 실패: {msg}")

elif st.session_state.page == 'result':
    st.title("📄 완성된 리포트")
    st.text_area("텍스트 복사", st.session_state.final_text, height=450)
    if st.button("처음으로 돌아가기"):
        st.session_state.ai_res = ""; st.session_state.page = 'input'; st.rerun()
