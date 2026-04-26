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
HISTORY_FILE = "student_history.json"  # 과거 정보 저장용 파일명

# 2. AI 클라이언트 설정
if "gemini_api_key" in st.secrets:
    client = genai.Client(api_key=st.secrets["gemini_api_key"])
else:
    st.error("Secrets에 'gemini_api_key'를 등록해 주세요.")

# --- [기능 함수] ---
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
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

# 3. 데이터 정의
GRADE_LIST = ["초등", "중등", "고등"]
CLASS_LIST = ["선택 없음", "Beginner-2시", "Beginner-3시", "Beginner-4시", "Ph1", "Ph2", "Ph3", "Ph4", "Ph5", "Inter 2시", "Inter 3시", "Inter 4시", "G-Advanced 2시", "G-Advanced 3시", "G-Advanced 4시"]
V_BOOKS = ["능률 보카 기본", "능률 보카 필수", "교육청 필수 900", "보카익스프레스", "보카클리어", "기타"]
AZAR_LIST = ["선택 안 함", "Azar Basic (Red)", "Azar Fundamentals (Black)", "기타"]
WRITING_LIST = ["선택 안 함", "OK Writing 1~7", "Bridge Writing Starter~6", "Training for Reading S1~S4"]
WRITING_UNITS = ["Vocab", "Sentence", "Part 1", "Part 2", "Part 3", "Part 4", "Part 5", "Story"]

# --- [화면 구성] ---
if "page" not in st.session_state: st.session_state.page = 'input'
if "ai_res" not in st.session_state: st.session_state.ai_res = ""
history_data = load_history()

if st.session_state.page == 'input':
    st.title("🍎 엘케이어학원 학습 리포트") 
    
    # [히스토리 불러오기 기능 추가]
    with st.expander("🔍 학생 과거 정보 불러오기", expanded=False):
        all_students = sorted(list(history_data.keys()))
        search_name = st.selectbox("기존 학생 선택", ["직접 입력"] + all_students)
        if search_name != "직접 입력":
            st.info(f"'{search_name}' 학생의 최근 기록을 기반으로 작성합니다.")
            last_record = history_data[search_name]

    st.divider()

    # 1. 기본 정보
    st.subheader("📍 1. 기본 정보")
    report_date = st.date_input("학습일 선택", value=datetime.today())
    c1, c2, c3 = st.columns(3)
    # 기록이 있으면 자동으로 해당 값 선택
    grade_val = last_record.get("grade", "초등") if search_name != "직접 입력" else "초등"
    class_val = last_record.get("class", "선택 없음") if search_name != "직접 입력" else "선택 없음"
    
    grade = c1.selectbox("학년", GRADE_LIST, index=GRADE_LIST.index(grade_val))
    class_name = c2.selectbox("반 선택", CLASS_LIST, index=CLASS_LIST.index(class_val))
    name = st.text_input("학생 이름", value=search_name if search_name != "직접 입력" else "", placeholder="이름 입력")

    st.divider()

    # 2. 어휘 섹션
    st.subheader("🅰️ 2. 어휘 (Vocabulary)")
    v_book = st.selectbox("어휘 교재", V_BOOKS)
    cv1, cv2, cv3 = st.columns(3)
    v_unit = cv1.text_input("Unit", value="1")
    v_corr = cv2.number_input("맞은 개수", min_value=0, value=0)
    v_tot = cv3.number_input("전체 개수", min_value=1, value=20)

    st.divider()

    # 3. 주교재 상세 (모든 세부 선택란 포함)
    st.subheader("📚 3. 주교재 수업 상세")
    cc1, cc2 = st.columns(2)
    elt_book = cc1.selectbox("ELT 독해", ["선택 안 함", "30/40 Word", "40/60 Read it"])
    g_book = cc2.selectbox("문법 (Grammar)", AZAR_LIST)
    
    # 문법 세부 단원 (강제 노출)
    g_ls = st.selectbox("└ 문법 챕터 선택", ["선택 안 함"] + [f"Chapter {i:02d}" for i in range(1, 21)])

    cr1, cr2 = st.columns(2)
    r_book = cr1.selectbox("독해 (Reading/News)", ["선택 안 함", "리딩튜터", "수능토픽", "Newspaper"])
    w_book = cr2.selectbox("라이팅 (Writing)", WRITING_LIST)
    
    # 라이팅 세부 단원 (강제 노출)
    w_ls = st.selectbox("└ 라이팅 유닛 선택", ["선택 안 함"] + WRITING_UNITS)

    st.divider()

    # 4. AI 과제 분석
    st.subheader("📸 4. AI 과제 분석")
    uploaded_file = st.file_uploader("과제 사진 업로드", type=['jpg', 'jpeg', 'png'])
    domain = st.selectbox("분석 영역 선택", ["선택 안 함", "문법", "어휘", "독해", "라이팅"])
    
    if st.button("🤖 AI 분석 시작"):
        if uploaded_file and domain != "선택 안 함":
            with st.spinner("분석 중..."):
                try:
                    img = Image.open(uploaded_file)
                    img.thumbnail((800, 800))
                    prompt = f"엘케이어학원 선생님으로서 이 {domain} 과제 사진을 보고 학생의 상태를 2~3문장 한국어로 분석해줘."
                    response = client.models.generate_content(model="gemini-1.5-flash", contents=[prompt, img])
                    st.session_state.ai_res = response.text
                    st.success("분석 완료!")
                except Exception as e:
                    st.error(f"오류: {e}")
    
    ai_feedback = st.text_area("AI 피드백 결과", value=st.session_state.ai_res, height=120)

    st.divider()

    # 5. 총평 및 저장
    st.subheader("✍️ 5. 선생님 총평")
    content = st.text_area("추가 피드백 (태도 등)")
    hw_status = st.selectbox("과제 수행도", ["매우 우수", "우수", "보통", "미흡"])

    if st.button("리포트 생성 및 저장", type="primary"):
        if not name:
            st.warning("학생 이름을 입력해 주세요.")
        else:
            # 반명 로직 처리
            display_class = f"{class_name} " if class_name != "선택 없음" else ""
            target_info = f"{grade} {display_class}{name} 학생"
            
            main_items = []
            if elt_book != "선택 안 함": main_items.append(f"• ELT독해: {elt_book}")
            if g_book != "선택 안 함": main_items.append(f"• 문법: {g_book} [{g_ls}]")
            if r_book != "선택 안 함": main_items.append(f"• 독해: {r_book}")
            if w_book != "선택 안 함": main_items.append(f"• 라이팅: {w_book} [{w_ls}]")
            
            f_sec = f"\n[선생님 피드백]\n{content}\n" if content.strip() else ""
            a_sec = f"\n[AI 과제 분석 - {domain}]\n{ai_feedback}\n" if ai_feedback.strip() else ""

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

            # 히스토리에 학생 정보 저장 (학년, 반 등)
            history_data[name] = {"grade": grade, "class": class_name, "last_date": str(report_date)}
            save_history(history_data)

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
