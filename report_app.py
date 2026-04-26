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

# 2. AI 클라이언트 설정
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

# 3. [데이터 복구] 상세 커리큘럼 데이터 정의
UNIT_LIST = [f"<Unit {i:02d}>" for i in range(1, 17)] # 꺽쇠 유닛 리스트

# [문법] Azar Basic 1권 세부 목차 (보내주신 자료 기반) [cite: 1, 2, 4, 5, 6, 8]
AZAR_BASIC_DATA = {
    "Chapter 01": ["1-1 단수 인칭대명사+Be동사", "1-2 복수 인칭대명사+Be동사", "1-3 단수 명사+Be동사", "1-4 복수 명사+Be동사", "1-5 인칭대명사+Be동사 축약", "1-6 Be동사 부정문", "1-7 Be동사+형용사", "1-8 Be동사+장소", "1-9 요약:기본 구조"],
    "Chapter 02": ["2-1 This와 That", "2-2 These와 Those", "2-3 Yes/No 의문문", "2-4 의문문 대답", "2-5 Where 의문문", "2-6 Have와 Has", "2-7 소유격 인칭대명사", "2-8 What/Who 의문문"],
    "Chapter 03": ["3-1 현재시제 형태/의미", "3-2 빈도부사", "3-3 빈도부사 위치", "3-4 3인칭 단수 -es", "3-5 -y로 끝나는 동사", "3-6 불규칙: Has, Does, Goes", "3-7 Like/Want/Need/Would Like", "3-8 현재시제: 부정문", "3-9 Yes/No 의문문", "3-10 Where/What 의문문", "3-11 When/What Time 의문문"],
    "Chapter 04": ["4-1 현재진행형: Be+-ing", "4-2 동사의 -ing", "4-3 현재진행형: 부정문", "4-4 현재진행형: 의문문", "4-5 현재시제 vs 현재진행", "4-6 상태동사", "4-7 See/Look/Watch/Hear/Listen", "4-8 Think About vs That", "4-9 명령문"],
    "Chapter 05": ["5-1 명사의 수: 단수/복수", "5-2 불규칙 복수형", "5-3 형용사의 쓰임", "5-4 명사: 주어/목적어", "5-5 주격/목적격 인칭대명사", "5-6 전치사+목적격 대명사", "5-7 소유형용사/소유대명사", "5-8 명사의 소유격", "5-9 Whose 의문문", "5-10 소유격: 불규칙 복수형"],
    "Chapter 06": ["6-1 셀 수 있는/없는 명사", "6-2 부정관사 A vs An", "6-3 A/An vs Some", "6-4 물질명사 수량 표현", "6-5 Many/Much/Few/Little", "6-6 정관사 The", "6-7 관사 미사용", "6-8 Some과 Any"],
    "Chapter 07": ["7-1 비인칭주어 It (시간)", "7-2 시간 전치사", "7-3 비인칭주어 It (날씨)", "7-4 There+Be동사", "7-5 There+Be동사: 의문문", "7-6 How Many 의문문", "7-7 장소 전치사", "7-8 위치 전치사", "7-9 Would Like", "7-10 Would Like vs Like"]
}

# [독해] 상세 리스트
READING_BOOKS = [
    "리딩튜터 스타터(1)", "리딩튜터 스타터(2)", "리딩튜터 스타터(3)",
    "리딩튜터 주니어(1)", "리딩튜터 주니어(2)", "리딩튜터 주니어(3)", "리딩튜터 주니어(4)",
    "수능토픽(1)", "수능토픽(2)", "수능토픽(3)", "English Newspaper (Kids)", "자체 독해 교재"
]

# [라이팅] 상세 데이터
WRITING_DATA = {
    "OK Writing 1~7": ["Vocab", "Sentence", "Part 1", "Part 2", "Part 3", "Part 4", "Part 5", "Story"],
    "Bridge Writing": ["Vocab", "Sentence", "Part 1~6", "Story"],
    "Training for Reading": ["Vocab", "Training 1~11", "Story"]
}

# --- [메인 화면 로직] ---
if "page" not in st.session_state: st.session_state.page = 'input'
if "ai_res" not in st.session_state: st.session_state.ai_res = ""
history = load_history()

if st.session_state.page == 'input':
    st.title("🍎 엘케이어학원 학습 리포트") 

    # [과거 기록 불러오기]
    with st.expander("🔍 학생 과거 정보 불러오기", expanded=False):
        all_st = sorted(list(history.keys()))
        search = st.selectbox("학생 선택", ["직접 입력"] + all_st)
        last_rec = history.get(search, {}) if search != "직접 입력" else {}

    st.divider()

    # 1. 기본 정보
    st.subheader("📍 1. 기본 정보")
    report_date = st.date_input("학습일 선택", value=datetime.today())
    c1, c2, c3 = st.columns(3)
    grade = c1.selectbox("학년", ["초등", "중등", "고등"], index=["초등", "중등", "고등"].index(last_rec.get("grade", "초등")))
    class_list = ["선택 없음", "Beginner-2시", "Beginner-3시", "Ph1", "Inter 2시", "G-Advanced 2시"]
    class_name = c2.selectbox("반 선택", class_list, index=class_list.index(last_rec.get("class", "선택 없음")) if last_rec.get("class") in class_list else 0)
    name = st.text_input("학생 이름", value=search if search != "직접 입력" else "")

    st.divider()

    # 2. 어휘 섹션
    st.subheader("🅰️ 2. 어휘 (Vocabulary)")
    v_book = st.selectbox("어휘 교재", ["능률 보카 기본", "능률 보카 필수", "교육청 900", "기타"])
    cv1, cv2, cv3 = st.columns(3)
    v_unit = cv1.selectbox("Unit 선택", UNIT_LIST)
    v_corr = cv2.number_input("맞은 개수", min_value=0)
    v_tot = cv3.number_input("전체 개수", min_value=1, value=20)

    st.divider()

    # 3. 주교재 상세 (아자르 세부 목차 및 꺽쇠 유닛 적용)
    st.subheader("📚 3. 주교재 수업 상세")
    
    # [독해]
    r_book = st.selectbox("독해 교재", ["선택 안 함"] + READING_BOOKS)
    r_unit = "선택 안 함"
    if r_book != "선택 안 함":
        r_unit = st.selectbox("독해 Unit", UNIT_LIST)

    # [문법 - Azar 세부 로직]
    g_book = st.selectbox("문법 교재", ["선택 안 함", "Azar Basic (Red)", "Azar Fundamentals", "기타"])
    g_chap = "선택 안 함"
    g_sub = ""
    if g_book == "Azar Basic (Red)":
        g_chap = st.selectbox("└ 챕터 선택", list(AZAR_BASIC_DATA.keys()))
        g_sub = st.selectbox("└ 세부 항목 선택", AZAR_BASIC_DATA[g_chap])
    elif g_book != "선택 안 함":
        g_sub = st.text_input("└ 단원명 입력")

    # [라이팅]
    w_book = st.selectbox("라이팅 교재", ["선택 안 함"] + list(WRITING_DATA.keys()))
    w_ls = "선택 안 함"
    if w_book != "선택 안 함":
        w_ls = st.selectbox("└ 세부 유닛", WRITING_DATA[w_book])

    st.divider()

    # 4. AI 과제 분석 (gemini-1.5-flash)
    st.subheader("📸 4. AI 과제 분석")
    up_file = st.file_uploader("과제 사진 업로드", type=['jpg', 'png'])
    domain = st.selectbox("분석 영역", ["선택 안 함", "문법", "어휘", "독해", "라이팅"])
    
    if st.button("🤖 AI 분석 시작"):
        if up_file and domain != "선택 안 함":
            with st.spinner("분석 중..."):
                try:
                    img = Image.open(up_file)
                    img.thumbnail((800, 800))
                    prompt = f"엘케이어학원 선생님으로서 이 {domain} 과제의 학습 상태를 한국어로 2~3문장 분석해줘."
                    res = client.models.generate_content(model="gemini-1.5-flash", contents=[prompt, img])
                    st.session_state.ai_res = res.text
                except Exception as e: st.error(f"오류: {e}")

    ai_fb = st.text_area("AI 분석 결과", value=st.session_state.ai_res, height=150)

    st.divider()

    # 5. 선생님 총평
    st.subheader("✍️ 5. 선생님 총평")
    content = st.text_area("상세 피드백 (태도 등)")
    hw_status = st.selectbox("과제 수행도", ["매우 우수", "우수", "보통", "미흡"])

    if st.button("리포트 생성 및 저장", type="primary"):
        if not name: st.warning("이름을 입력하세요."); st.stop()
        
        display_class = f"{class_name} " if class_name != "선택 없음" else ""
        target_info = f"{grade} {display_class}{name} 학생"
        
        items = []
        if r_book != "선택 안 함": items.append(f"• 독해: {r_book} [{r_unit}]")
        if g_book != "선택 안 함": 
            g_info = f"• 문법: {g_book} [{g_chap} - {g_sub}]" if g_book == "Azar Basic (Red)" else f"• 문법: {g_book} [{g_sub}]"
            items.append(g_info)
        if w_book != "선택 안 함": items.append(f"• 라이팅: {w_book} [{w_ls}]")
        
        f_sec = f"\n[선생님 피드백]\n{content}\n" if content.strip() else ""
        a_sec = f"\n[AI 과제 분석 - {domain}]\n{ai_fb}\n" if ai_fb.strip() else ""

        report = f"""[ 엘케이어학원 학습 리포트 ]

■ 대상: {target_info}
■ 학습일: {report_date}

1. 어휘 테스트 결과
- 교재명: {v_book} ({v_unit})
- 결과: {v_corr} / {v_tot} (정답률 {int((v_corr/v_tot)*100)}%)

2. 주교재 학습 내용
{"\n".join(items)}
{f_sec}{a_sec}
3. 과제 수행도: {hw_status}"""

        history[name] = {"grade": grade, "class": class_name}
        save_history(history)

        f_name = f"{report_date.strftime('%Y%m%d')}_{name}.txt"
        success, msg = upload_to_google_drive(report, f_name, FOLDER_ID)
        if success:
            st.session_state.final_text = report
            st.session_state.page = 'result'; st.rerun()
        else: st.error(f"저장 실패: {msg}")

elif st.session_state.page == 'result':
    st.title("📄 완성된 리포트")
    st.text_area("카톡 복사용 텍스트", st.session_state.final_text, height=450)
    if st.button("처음으로 돌아가기"):
        st.session_state.ai_res = ""; st.session_state.page = 'input'; st.rerun()
