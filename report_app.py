import streamlit as st
import pandas as pd
import os
from PIL import Image
from datetime import datetime
from google import genai

# 1. 페이지 설정
st.set_page_config(page_title="엘케이어학원 학습 리포트", layout="centered")

# 2. AI 클라이언트 설정
if "gemini_api_key" in st.secrets:
    client = genai.Client(api_key=st.secrets["gemini_api_key"])
else:
    st.error("Secrets에 'gemini_api_key'를 등록해 주세요.")

# --- [상세 커리큘럼 데이터 정의 - 절대 요약 금지] ---

# [문법] Azar Basic (Red) 전체 세부 항목 (1-1 ~ 7-10)
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

# [라이팅] Bridge Writing (1~6) & OK Writing (1~7)
WRITING_DATA = {
    "Basic Structure": [f"Unit {i}" for i in range(1, 13)],
    "Bridge Writing 1": ["Vocabulary", "Sentence 1~5", "Part 1~5", "Story 1-1~2-5"],
    "Bridge Writing 2": ["Vocabulary", "Sentence 1~6", "Part 1~6", "Story 1-1~3-4"],
    "Bridge Writing 3": ["Vocabulary", "Sentence 1~6", "Part 1~6", "Story 1-1~3-4"],
    "Bridge Writing 4-1": ["Vocabulary", "Sentence 1~6", "Part 1~6", "Story"],
    "Bridge Writing 4-2": ["Vocabulary", "Sentence 1~6", "Part 1~6", "Story"],
    "Bridge Writing 5": ["Vocabulary", "Sentence 1~6", "Part 1~6", "Story"],
    "Bridge Writing 6": ["Vocabulary", "Sentence 1~6", "Part 1~6", "Story"],
    "OK Writing 1": ["Vocab", "Sentence 1~6", "Part 1. 전치사", "Part 2. 진행형", "Part 3. 부정문", "Part 4. and/because", "Part 5. 명령문", "Story 1-1~3-4"],
    "OK Writing 2": ["Vocab", "Sentence 1~6", "Part 1. 소유격", "Part 2. There is/are", "Part 3. but/because", "Part 4. 대상 2개", "Part 5. 의문문", "Part 6. look+형용사", "Part 7. don't", "Story 1-1~3-4"],
    "OK Writing 3": ["Vocab", "Sentence 1~9", "Part 1. of", "Part 2. to부정사", "Part 3. can", "Part 4. 비인칭", "Part 5. Let's", "Part 6. 3인칭단수", "Part 7. doesn't", "Story 1-1~3-5"],
    "OK Writing 4": ["Vocab", "Sentence 1~7", "Part 1. will", "Part 2. must", "Part 3. to부정사", "Part 4. that절", "Part 5. Do", "Part 6. 의문사", "Story 1-1~2-4"],
    "OK Writing 5": ["Vocab", "Sentence 1~9", "Part 1. 명령문", "Part 2. 빈도부사", "Part 3. Does", "Part 4. to부정사", "Part 5. 원급", "Part 6. 비교급", "Part 7. 최상급", "Story 1-1~2-2"],
    "OK Writing 6": ["Vocab", "Sentence 1~8", "Part 1. 과거", "Part 2. have to", "Part 3. Did", "Part 4. didn't", "Part 5. 동명사주어", "Part 6. 의문사구", "Part 7. 접속사", "Story 1-1~1-6"],
    "OK Writing 7": ["Vocab", "Sentence 1~12", "Part 1. 동명사목적어", "Part 2. 가주어 it", "Part 3. 형용사보어", "Part 4. 재귀대명사", "Part 5. 의문사구", "Part 6. should", "Part 7. 지각동사", "Story 1-1~3-2"],
    "Training for Reading S1": ["Training 1~11"], "Training for Reading S2": ["Training 1~11"],
    "Training for Reading S3": ["Training 1~9", "Story"], "Training for Reading S4": ["Training 1~9", "Story"]
}

PHONICS_DATA = {
    "Phonics 1": [f"<Unit {i:02d}>" for i in range(1, 11)],
    "Phonics 2": ["<Unit 01> (hat, cat, bat, rat, man, can, pan, van) / A cat has the hat.", "<Unit 02> (map, lap, nap, gap, ham, jam, ram, Sam) / Sam has the jam.", "<Unit 03> (net, jet, vet, wet, bed, red, Ted) / The bed is red.", "<Unit 04> (leg, Meg, keg, pen, men, hen, ten) / The hen is in the keg.", "<Unit 05> (hit, pit, kit, sit, pin, bin, fin, win) / He hits the bin.", "<Unit 06> (zip, dip, lip, rip, pig, big, dig, wig) / The pig is big.", "<Unit 07> (pot, cot, dot, hot, box, fox, ox) / The fox is on the box.", "<Unit 08> (top, mop, hop, pop, dog, log, fog, jog) / I have a mop.", "<Unit 09> (hut, cut, nut, sun, gun, fun, run) / She cuts the nut.", "<Unit 10> (tub, rub, sub, cub, mug, bug, rug, hug) / The bug is on the sub."],
    "Phonics 3": ["<Unit 01> (tape, ape, cape, game, name, same, case, base, vase) / The ape has a cape.", "<Unit 02> (cake, bake, lake, cane, mane, Jane, cave, save, wave) / Jane bakes the cake.", "<Unit 03> (bite, kite, site, hide, ride, side, ice, dice, rice) / I bite the ice.", "<Unit 04> (bike, hike, like, pine, line, nine, dive, five, hive) / He likes me.", "<Unit 05> (rope, hope, nope, dome, home, Rome, hose, rose, nose) / A hose is in the dome.", "<Unit 06> (note, vote, rote, bone, cone, zone, hole, pole, mole) / Two bones are in the hole.", "<Unit 07> (mute, cute, cube, tube, use, fuse) / This is a cube.", "<Unit 08> (Duke, puke, dune, June, tune, huge) / Duke pukes on the dune."],
    "Phonics 4": ["<Unit 01> (plate, plum, plane, black, block, blade, flag, flap, flute) / A plum is on the plate.", "<Unit 02> (press, price, prize, bride, brave, brick, frog, frame, free) / I press the brick.", "<Unit 03> (clap, clip, clam, globe, glass, glove, slide, sled, sleep) / He sleeps in the clam.", "<Unit 04> (crab, crane, creep, grape, grass, green, drive, drum, dress) / A crab creeps on the drum.", "<Unit 05> (spin, space, spice, stop, stick, stove, skate, ski, skin) / Four balls spin on the ski.", "<Unit 06> (smoke, smell, smile, sneeze, snake, sniff, sweep, swan, swim) / Swans swim in the lake.", "<Unit 07> (lamp, jump, stamp, drink, wink, skunk, hang, song, ring) / I jump over the lamp.", "<Unit 08> (chess, cheese, bench, lunch, shell, ship, fish, wash) / The chess is on the bench.", "<Unit 09> (whale, white, wheel, wheat, phone, graph, photo, dolphin) / A whale is in the photo.", "<Unit 10> (thin, thick, bath, math, this, that, these, those) / This is a thick book."],
    "Phonics 5": ["<Unit 01> (tail, snail, train, chain, play, tray, clay, spray) / He plays with clay.", "<Unit 02> (bee, seed, tree, tea, meat, leaf, key, honey, money) / The key is old.", "<Unit 03> (die, pie, tie, find, kind, blind, Birdie, fight, night) / He is very kind.", "<Unit 04> (boat, coat, soap, road, grow, blow, crow, snow) / A crow blows the soap boat.", "<Unit 05> (new, chew, stew, blue, clue, glue, room, spoon, moon) / He finds the clue.", "<Unit 06> (paw, draw, straw, head, bread, thread, book, foot, look) / Draw the paw now.", "<Unit 07> (house, mouse, brown, clown, oil, soil, boy, toy) / A mouse lives in the house.", "<Unit 08> (baby, study, cloudy, cherry, cry, dry, fly, sky) / They cry with the baby.", "<Unit 09> (car, arm, star, shark, corn, fork, store, horse) / A horse eats corn.", "<Unit 10> (nurse, purse, burn, bird, girl, skirt, mother, teacher, farmer) / The girl wears a skirt and a purse."]
}

V_BOOKS_LIST = ["능률 보카 기본 400", "능률 보카 필수 500", "[개정]교육청 초등어휘 900", "보카클리어 중학기본", "보카클리어 중학실력", "보카클리어 중학완성", "워드마스터 고등기본", "보카익스프레스[중등]", "기타"]
ELT_BOOKS = ["30 Word Reading(1)", "30 Word Reading(2)", "40 Word Reading(1)", "40 Word Reading(2)", "40 Read it(1)", "40 Read it(2)", "40 Read it(3)", "60 Read it(1)", "60 Read it(2)", "60 Read it(3)"]
READING_BOOKS_LIST = ["리딩튜터 스타터(1)", "리딩튜터 스타터(2)", "리딩튜터 스타터(3)", "리딩튜터 주니어(1)", "리딩튜터 주니어(2)", "리딩튜터 주니어(3)", "리딩튜터 주니어(4)", "수능토픽(레벨1)", "수능토픽(레벨2)", "수능토픽(레벨3)", "자체 독해 자료"]

# --- [엑셀 불러오기 및 인덱싱 로직] ---
def load_excel_data(file_path):
    try:
        df = pd.read_excel(file_path)
        df.columns = [str(c).strip().replace(" ", "") for c in df.columns]
        if '이름' not in df.columns:
            df = pd.read_excel(file_path, index_col=0).T.reset_index()
            df.columns = [str(c).strip().replace(" ", "") for c in df.columns]
        return df
    except: return None

def find_index(options_list, target_value):
    if not target_value or str(target_value).lower() == 'nan': return 0
    target_clean = str(target_value).strip().replace(" ", "")
    for i, opt in enumerate(options_list):
        if str(opt).strip().replace(" ", "") == target_clean: return i
    return 0

# --- [메인 로직] ---
if "page" not in st.session_state: st.session_state.page = 'input'
if "ai_res" not in st.session_state: st.session_state.ai_res = ""

if st.session_state.page == 'input':
    st.title("🍎 엘케이어학원 학습 리포트") 

    student_data, df, AUTO_FILE = None, None, "student_list.xlsx"

    if os.path.exists(AUTO_FILE):
        df = load_excel_data(AUTO_FILE)
        if df is not None: st.success(f"✅ 명단 자동 불러오기 완료")
    
    with st.expander("📂 학생 명단 관리 (엑셀)", expanded=(df is None)):
        uploaded_excel = st.file_uploader("xlsx 파일을 업로드하세요", type=['xlsx'])
        if uploaded_excel:
            df = load_excel_data(uploaded_excel)
            if df is not None: st.success("새 데이터를 읽었습니다!")

    if df is not None:
        sel_student = st.selectbox("학생 선택", ["선택 안 함"] + list(df['이름'].unique()))
        if sel_student != "선택 안 함": student_data = df[df['이름'] == sel_student].iloc[0]

    st.divider()

    def get_safe(field):
        if student_data is not None:
            field_clean = field.replace(" ", "")
            for k in student_data.index:
                if str(k).strip().replace(" ", "") == field_clean: return str(student_data[k])
        return ""

    # 1. 기본 정보
    report_date = st.date_input("학습일 선택", value=datetime.today())
    c1, c2, c3 = st.columns(3)
    grade_opts = ["초등", "중등", "고등"]
    grade = c1.selectbox("학년", grade_opts, index=find_index(grade_opts, get_safe("학년")))
    class_list = ["선택 없음", "Beginner-2시", "Beginner-3시", "Ph1", "Inter 2시", "G-Advanced 2시"]
    class_name = c2.selectbox("반 선택", class_list, index=find_index(class_list, get_safe("반")))
    name = st.text_input("학생 이름", value=get_safe("이름"))

    st.divider()

    # 2. 어휘 섹션
    st.subheader("🅰️ 2. 어휘 (Vocabulary)")
    vc1, vc2 = st.columns([2, 1])
    v_book = vc1.selectbox("어휘 교재", V_BOOKS_LIST, index=find_index(V_BOOKS_LIST, get_safe("어휘교재")))
    v_unit = vc2.text_input("어휘 Unit", placeholder="예: <Unit 01>")
    
    r1, r2, r3 = st.columns(3)
    v1_c = r1.number_input("1회차 점수", min_value=0, key="v1c")
    v1_t = r1.number_input("1회차 전체", min_value=1, value=20, key="v1t")
    v2_c = r2.number_input("2회차 점수", min_value=0, key="v2c")
    v2_t = r2.number_input("2회차 전체", min_value=1, value=20, key="v2t")
    v3_c = r3.number_input("3회차 점수", min_value=0, key="v3c")
    v3_t = r3.number_input("3회차 전체", min_value=1, value=20, key="v3t")

    st.divider()

    # 3. 주교재 상세
    st.subheader("📚 3. 주교재 및 수업 상세")
    
    # [파닉스]
    p_books = ["선택 안 함"] + list(PHONICS_DATA.keys())
    p_book = st.selectbox("파닉스 교재", p_books, index=find_index(p_books, get_safe("파닉스교재")))
    p_unit = st.selectbox("└ 파닉스 Unit", PHONICS_DATA[p_book]) if p_book != "선택 안 함" else "선택 안 함"

    # [ELT]
    elt_books = ["선택 안 함"] + ELT_BOOKS
    elt_book = st.selectbox("ELT 독해", elt_books, index=find_index(elt_books, get_safe("ELT교재")))
    elt_unit = st.text_input("└ ELT Unit", placeholder="예: <Unit 01>")

    # [영자신문 - 자유 입력 추가!]
    ns_options = ["선택 안 함", "<Kinder>", "<Kids>"]
    news_paper = st.selectbox("영자신문 선택", ns_options, index=find_index(ns_options, get_safe("영자신문")))
    news_unit = st.text_input("└ 영자신문 유닛/주제 입력", placeholder="예: <Unit 01> Space Travel")

    # [일반독해]
    rd_books = ["선택 안 함"] + READING_BOOKS_LIST
    r_book = st.selectbox("독해 교재", rd_books, index=find_index(rd_books, get_safe("독해교재")))
    r_unit = st.text_input("└ 독해 Unit", placeholder="예: <Unit 01>")

    # [문법] - Azar 100% 상세 복구
    gr_books = ["선택 안 함", "Azar Basic (Red)", "Azar Fundamentals", "기타"]
    g_book = st.selectbox("문법 교재", gr_books, index=find_index(gr_books, get_safe("문법교재")))
    g_sub = st.selectbox("└ Azar 상세 항목", AZAR_BASIC_FULL_LIST) if g_book == "Azar Basic (Red)" else st.text_input("└ 단원명 직접 입력")

    # [라이팅] - Bridge 1~6 & OK 1~7 전 시리즈 복구
    wr_books = ["선택 안 함"] + list(WRITING_DATA.keys())
    w_book = st.selectbox("라이팅 교재", wr_books, index=find_index(wr_books, get_safe("라이팅교재")))
    w_ls = st.selectbox("└ 라이팅 세부 단원", WRITING_DATA[w_book]) if w_book != "선택 안 함" else "선택 안 함"

    st.divider()

    # 4. 과제 분석 & 5. 총평
    up_file = st.file_uploader("과제 사진 업로드", type=['jpg', 'png'])
    domain = st.selectbox("분석 영역", ["선택 안 함", "문법", "어휘", "독해", "라이팅"])
    if st.button("🤖 과제 분석 시작") and up_file and domain != "선택 안 함":
        with st.spinner("AI 분석 중..."):
            try:
                img = Image.open(up_file); img.thumbnail((800, 800))
                res = client.models.generate_content(model="gemini-1.5-flash", contents=[f"성취도 분석해줘", img])
                st.session_state.ai_res = res.text
            except Exception as e: st.error(f"오류: {e}")
    ai_fb = st.text_area("분석 결과 확인", value=st.session_state.ai_res, height=120)
    content = st.text_area("선생님 피드백")
    hw_status = st.selectbox("과제 수행도", ["매우 우수", "우수", "보통", "미흡"])

    if st.button("리포트 생성", type="primary"):
        if not name: st.warning("이름을 입력하세요.")
        else:
            display_class = f"{class_name} " if class_name != "선택 없음" else ""
            target_info = f"{grade} {display_class}{name} 학생"
            v_results = [f"• 1회차: {v1_c} / {v1_t} ({int((v1_c/v1_t)*100)}%)"]
            if v2_c > 0: v_results.append(f"• 2회차: {v2_c} / {v2_t}")
            if v3_c > 0: v_results.append(f"• 3회차: {v3_c} / {v3_t}")
            items = []
            if p_book != "선택 안 함": items.append(f"• 파닉스: {p_book} [{p_unit}]")
            if elt_book != "선택 안 함": items.append(f"• ELT독해: {elt_book} [{elt_unit}]")
            if news_paper != "선택 안 함": 
                news_info = f"{news_paper} [{news_unit}]" if news_unit else news_paper
                items.append(f"• 영자신문: {news_info}")
            if r_book != "선택 안 함": items.append(f"• 독해: {r_book} [{r_unit}]")
            if g_book != "선택 안 함": items.append(f"• 문법: {g_book} [{g_sub}]")
            if w_book != "선택 안 함": items.append(f"• 라이팅: {w_book} [{w_ls}]")
            report_text = f"[ 엘케이어학원 학습 리포트 ]\n\n■ 대상: {target_info}\n■ 학습일: {report_date}\n\n1. 어휘 테스트 결과\n- 교재명: {v_book} ({v_unit})\n" + "\n".join(v_results) + f"\n\n2. 주교재 학습 내용\n" + "\n".join(items) + f"\n\n[선생님 피드백]\n{content}\n\n[과제 정밀 분석 - {domain}]\n{ai_fb}\n\n3. 과제 수행도: {hw_status}"
            st.session_state.final_text = report_text
            st.session_state.page = 'result'; st.rerun()

elif st.session_state.page == 'result':
    st.title("📄 완성된 리포트")
    st.text_area("텍스트 복사", st.session_state.final_text, height=500)
    if st.button("처음으로 돌아가기"):
        st.session_state.ai_res = ""; st.session_state.page = 'input'; st.rerun()
