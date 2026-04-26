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

# 3. [데이터 복구] 선생님 맞춤형 상세 커리큘럼
UNIT_LIST = [f"<Unit {i:02d}>" for i in range(1, 17)] # 꺽쇠 유닛

# [독해] 개별 선택 리스트 (단순화 제거)
READING_BOOKS = [
    "리딩튜터 스타터(1)", "리딩튜터 스타터(2)", "리딩튜터 스타터(3)",
    "리딩튜터 주니어(1)", "리딩튜터 주니어(2)", "리딩튜터 주니어(3)", "리딩튜터 주니어(4)",
    "수능토픽(레벨1)", "수능토픽(레벨2)", "수능토픽(레벨3)",
    "English Newspaper (Kids)", "English Newspaper (Junior)", "자체 독해 자료"
]

# [문법] Azar Basic 1권 통합 세부 목차 (1-1 ~ 7-10)
AZAR_BASIC_FULL_LIST = [
    "Ch1. 1-1 단수 인칭대명사+Be동사", "Ch1. 1-2 복수 인칭대명사+Be동사", "Ch1. 1-3 단수 명사+Be동사", 
    "Ch1. 1-4 복수 명사+Be동사", "Ch1. 1-5 인칭대명사+Be동사 축약", "Ch1. 1-6 Be동사 부정문", 
    "Ch1. 1-7 Be동사+형용사", "Ch1. 1-8 Be동사+장소", "Ch1. 1-9 Be동사 구조 요약",
    "Ch2. 2-1 지시대명사 This와 That", "Ch2. 2-2 지시대명사 These와 Those", "Ch2. 2-3 Be동사 Yes/No 의문문", 
    "Ch2. 2-4 Yes/No 의문문 대답", "Ch2. 2-5 Where 의문문", "Ch2. 2-6 Have와 Has", 
    "Ch2. 2-7 소유격 인칭대명사", "Ch2. 2-8 What/Who 의문문",
    "Ch3. 3-1 현재시제 형태/의미", "Ch3. 3-2 빈도부사", "Ch3. 3-3 빈도부사 위치", 
    "Ch3. 3-4 3인칭 단수 -es", "Ch3. 3-5 3인칭 단수 -y", "Ch3. 3-6 Has, Does, Goes", 
    "Ch3. 3-7 Like/Want/Need/Would Like", "Ch3. 3-8 현재시제 부정문", "Ch3. 3-9 Yes/No 의문문", 
    "Ch3. 3-10 Where/What 의문문", "Ch3. 3-11 When/What Time 의문문",
    "Ch4. 4-1 현재진행형 Be+-ing", "Ch4. 4-2 동사의 -ing", "Ch4. 4-3 현재진행 부정문", 
    "Ch4. 4-4 현재진행 의문문", "Ch4. 4-5 현재 vs 진행", "Ch4. 4-6 상태동사", 
    "Ch4. 4-7 See/Look/Watch/Hear/Listen", "Ch4. 4-8 Think About vs That", "Ch4. 4-9 명령문",
    "Ch5. 5-1 명사 단수/복수", "Ch5. 5-2 불규칙 복수형", "Ch5. 5-3 형용사 쓰임", 
    "Ch5. 5-4 주어/목적어", "Ch5. 5-5 주격/목적격 대명사", "Ch5. 5-6 전치사+목적격 대명사", 
    "Ch5. 5-7 소유형용사/대명사", "Ch5. 5-8 명사 소유격", "Ch5. 5-9 Whose 의문문", "Ch5. 5-10 소유격 불규칙 복수",
    "Ch6. 6-1 셀 수 있는/없는 명사", "Ch6. 6-2 A vs An", "Ch6. 6-3 A/An vs Some", 
    "Ch6. 6-4 물질명사 수량", "Ch6. 6-5 Many/Much/Few/Little", "Ch6. 6-6 정관사 The", 
    "Ch6. 6-7 관사 미사용", "Ch6. 6-8 Some/Any",
    "Ch7. 7-1 비인칭주어 It(시간)", "Ch7. 7-2 시간 전치사", "Ch7. 7-3 비인칭주어 It(날씨)", 
    "Ch7. 7-4 There+Be동사", "Ch7. 7-5 There+Be동사 의문문", "Ch7. 7-6 How Many 의문문", 
    "Ch7. 7-7 장소 전치사", "Ch7. 7-8 위치 전치사", "Ch7. 7-9 Would Like", "Ch7. 7-10 Would Like vs Like"
]

# [라이팅] 상세 목차
WRITING_DATA = {
    "OK Writing 1": ["Vocab", "Sentence 1~6", "Part 1~5", "Story 1-1~3-4"],
    "OK Writing 2": ["Vocab", "Sentence 1~6", "Part 1~7", "Story 1-1~3-4"],
    "OK Writing 3": ["Vocab", "Sentence 1~9", "Part 1~7", "Story 1-1~3-5"],
    "Bridge Writing": ["Vocab", "Sentence 1~5", "Part 1~6", "Story"],
    "Training for Reading": ["Vocab", "Training 1~11", "Story"]
}

# --- [메인 화면] ---
if "page" not in st.session_state: st.session_state.page = 'input'
if "ai_res" not in st.session_state: st.session_state.ai_res = ""
history = load_history()

if st.session_state.page == 'input':
    st.title("🍎 엘케이어학원 학습 리포트") 

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
    v_unit = cv1.selectbox("Unit 선택", UNIT_LIST) # 꺽쇠 유닛
    v_corr = cv2.number_input("맞은 개수", min_value=0)
    v_tot = cv3.number_input("전체 개수", min_value=1, value=20)

    st.divider()

    # 3. 주교재 수업 상세 (선생님 요청 방식 적용)
    st.subheader("📚 3. 주교재 및 수업 상세")
    
    # [독해] 개별 선택
    r_book = st.selectbox("독해 교재", ["선택 안 함"] + READING_BOOKS)
    r_unit = st.selectbox("독해 Unit", ["선택 안 함"] + UNIT_LIST)

    # [문법] 교재 선택 후 바로 세부 항목 선택 (단일 흐름)
    g_book = st.selectbox("문법 교재", ["선택 안 함", "Azar Basic (Red)", "기타"])
    g_sub = "선택 안 함"
    if g_book == "Azar Basic (Red)":
        g_sub = st.selectbox("└ 세부 항목 (1-1 ~ 7-10)", AZAR_BASIC_FULL_LIST)
    elif g_book == "기타":
        g_sub = st.text_input("└ 단원명 직접 입력")

    # [라이팅]
    w_book = st.selectbox("라이팅 교재", ["선택 안 함"] + list(WRITING_DATA.keys()))
    w_ls = "선택 안 함"
    if w_book != "선택 안 함":
        w_ls = st.selectbox("└ 라이팅 세부 유닛", WRITING_DATA[w_book])

    st.divider()

    # 4. AI 과제 분석
    st.subheader("📸 4. AI 과제 분석")
    up_file = st.file_uploader("사진 업로드", type=['jpg', 'png'])
    domain = st.selectbox("분석 영역", ["선택 안 함", "문법", "어휘", "독해", "라이팅"])
    
    if st.button("🤖 AI 분석 시작"):
        if up_file and domain != "선택 안 함":
            with st.spinner("분석 중..."):
                try:
                    img = Image.open(up_file)
                    img.thumbnail((800, 800))
                    prompt = f"엘케이어학원 선생님으로서 이 {domain} 과제 사진을 보고 학생의 상태를 한국어로 2~3문장 분석해줘."
                    res = client.models.generate_content(model="gemini-1.5-flash", contents=[prompt, img])
                    st.session_state.ai_res = res.text
                except Exception as e: st.error(f"오류: {e}")

    ai_fb = st.text_area("AI 분석 결과", value=st.session_state.ai_res, height=120)

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
        if g_book != "선택 안 함": items.append(f"• 문법: {g_book} [{g_sub}]")
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
    st.text_area("텍스트 복사", st.session_state.final_text, height=450)
    if st.button("처음으로 돌아가기"):
        st.session_state.ai_res = ""; st.session_state.page = 'input'; st.rerun()
