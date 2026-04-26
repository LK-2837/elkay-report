import streamlit as st
import os
import json
import io
from PIL import Image
from datetime import datetime
from google import genai  # 2026년 최신형 AI 라이브러리
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# 1. 페이지 설정
st.set_page_config(page_title="엘케이어학원 학습 리포트", layout="centered")

# 설정값
FOLDER_ID = "1bMHs-3Ak27JU_ADF9_UVknkHjCEtumR2"
HISTORY_FILE = "student_history.json"

# 2. 최신형 AI 클라이언트 설정
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

# --- [입력 화면] ---
if "page" not in st.session_state: st.session_state.page = 'input'
if "ai_res" not in st.session_state: st.session_state.ai_res = ""

if st.session_state.page == 'input':
    st.title("🍎 엘케이어학원 학습 리포트") 
    
    st.divider()
    st.subheader("📍 기본 정보")
    report_date = st.date_input("학습일 선택", value=datetime.today())
    c1, c2, c3 = st.columns(3)
    grade = c1.selectbox("학년", ["초등", "중등", "고등"])
    class_name = c2.selectbox("반 선택", ["선택 없음", "Beginner", "Phonics", "Intermediate", "Advanced"])
    name = st.text_input("학생 이름", placeholder="이름을 입력하세요")

    st.divider()
    st.subheader("📸 AI 과제 정밀 분석")
    uploaded_file = st.file_uploader("과제 사진 업로드", type=['jpg', 'jpeg', 'png'])
    domain = st.selectbox("분석 영역", ["선택 안 함", "문법", "어휘", "독해", "라이팅"])
    
    # [AI 분석 버튼] 사진이 있고 영역을 선택했을 때만 마법처럼 나타납니다!
    if uploaded_file and domain != "선택 안 함":
        st.success(f"✅ {domain} 사진 업로드 완료! 아래 버튼을 누르세요.")
        if st.button("🤖 AI 과제 분석 시작 (초고속 모드)"):
            with st.spinner("AI 선생님이 분석 중입니다..."):
                try:
                    img = Image.open(uploaded_file)
                    # 속도를 위해 사진 크기 최적화
                    img.thumbnail((1024, 1024))
                    
                    prompt = f"너는 엘케이어학원 선생님이야. 이 {domain} 과제 사진을 보고 학생의 학습 상태를 정중하게 분석해줘. 한국어로 2~3문장으로 써줘."
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=[prompt, img]
                    )
                    st.session_state.ai_res = response.text
                except Exception as e:
                    st.error(f"분석 중 오류 발생: {e}")

    ai_feedback = st.text_area("AI 분석 결과", value=st.session_state.ai_res, height=150)
    content = st.text_area("선생님 추가 피드백")
    hw_status = st.selectbox("과제 수행도", ["매우 우수", "우수", "보통", "미흡"])

    if st.button("리포트 생성 및 저장", type="primary"):
        # [반명 로직] '선택 없음'이면 아예 공간 삭제
        display_class = f"{class_name} " if class_name != "선택 없음" else ""
        target_info = f"{grade} {display_class}{name} 학생"
        
        report_text = f"""[ 엘케이어학원 학습 리포트 ]

■ 대상: {target_info}
■ 학습일: {report_date}

1. 학습 내용
• 분석 영역: {domain}
• 선생님 피드백: {content}

[ AI 과제 정밀 분석 ]
{ai_feedback}

■ 과제 수행도: {hw_status}"""

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
    st.text_area("텍스트 복사", st.session_state.final_text, height=400)
    if st.button("처음으로 돌아가기"):
        st.session_state.ai_res = ""
        st.session_state.page = 'input'
        st.rerun()
