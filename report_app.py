import streamlit as st
import os
import json
import io
from PIL import Image
from datetime import datetime
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# 1. 페이지 설정
st.set_page_config(page_title="엘케이어학원 학습 리포트", layout="centered")

# 구글 드라이브 및 파일 설정
FOLDER_ID = "1bMHs-3Ak27JU_ADF9_UVknkHjCEtumR2"
HISTORY_FILE = "student_history.json"

# Gemini AI 설정
if "gemini_api_key" in st.secrets:
    genai.configure(api_key=st.secrets["gemini_api_key"])

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

def save_to_history(new_data):
    history_to_save = {k: str(v) if k == 'date' else v for k, v in new_data.items() if k != "image"}
    all_history = {}
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f: all_history = json.load(f)
    name = history_to_save['name']
    if name not in all_history: all_history[name] = []
    all_history[name].append(history_to_save)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f: json.dump(all_history, f, ensure_ascii=False, indent=4)

def load_last_student_data(name):
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            all_history = json.load(f)
            if name in all_history and len(all_history[name]) > 0: return all_history[name][-1]
    return None

# 2. 데이터 정의 (방대한 교재 리스트 완전 복구)
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

# --- [화면 구성] ---
if "page" not in st.session_state or st.session_state.page == 'input':
    st.title("🍎 엘케이어학원 학습 리포트") 
    
    st.subheader("🔍 히스토리 검색")
    c_search, c_btn = st.columns([3, 1])
    search_name = c_search.text_input("학생 이름을 입력하세요", placeholder="예: 강재윤")
    if c_btn.button("🔄 기록 불러오기"):
        last_data = load_last_student_data(search_name)
        if last_data:
            for k, v in last_data.items():
                if k == 'date': st.session_state[f"{k}_key"] = datetime.strptime(v, '%Y-%m-%d').date()
                else: st.session_state[f"{k}_key"] = v
            st.rerun()

    st.divider()
    st.subheader("📍 기본 정보")
    report_date = st.date_input("학습일 선택", value=datetime.today(), key="date_key")
    c1, c2, c3 = st.columns(3)
    academy = c1.text_input("학원명", value="엘케이어학원", key="academy_key")
    class_name = c2.selectbox("반 선택", CLASS_LIST, key="class_key")
    grade = c3.selectbox("학년", GRADE_LIST, key="grade_key")
    name = st.text_input("학생 이름 확인", value=search_name)

    st.divider()
    st.subheader("🅰️ 어휘 (Vocabulary)")
    v_book = st.selectbox("어휘 교재", ["능률 보카 기본 400", "보카클리어", "기타"], key="v_book_key")
    cv1, cv2, cv3 = st.columns(3)
    v_unit = cv1.text_input("Unit", key="v_unit_key")
    v_corr = cv2.number_input("맞은 개수", min_value=0)
    v_tot = cv3.number_input("전체 개수", min_value=1, value=20)

    st.divider()
    st.subheader("📚 주교재 수업 상세")
    elt_book = st.selectbox("ELT Reading", ["선택 안 함"] + ELT_BOOKS, key="elt_book_key")
    r_book = st.selectbox("Reading (Tutor/News)", ["선택 안 함"] + READING_BOOKS_DATA, key="r_book_key")
    w_book = st.selectbox("Writing (OK/Bridge/Training)", ["선택 안 함"] + list(WR
