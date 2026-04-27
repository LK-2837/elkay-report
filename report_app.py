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

# [데이터 보강] Phonics 상세 유닛 데이터 (이미지 분석 결과)
PHONICS_DATA = {
    "Phonics 1": [f"<Unit {i:02d}>" for i in range(1, 11)],
    "Phonics 2": [
        "<Unit 01> (hat, cat, bat, rat, man, can, pan, van) / A cat has the hat. / A man has the pan. / A bat has the rat.",
        "<Unit 02> (map, lap, nap, gap, ham, jam, ram, Sam) / Sam has the jam. / The ram has a nap. A map is on the lap.",
        "<Unit 03> (net, jet, vet, wet, bed, red, Ted) / The bed is red. / Ted is wet. / The jet is in the net.",
        "<Unit 04> (leg, Meg, keg, pen, men, hen, ten) / The hen is in the keg. The pen is on Meg. / The men have ten legs.",
        "<Unit 05> (hit, pit, kit, sit, pin, bin, fin, win) / He hits the bin. / He sits on the pin. / The kit is in the pit.",
        "<Unit 06> (zip, dip, lip, rip, pig, big, dig, wig) / The pig is big. / I zip my lips. / I have a big wig.",
        "<Unit 07> (pot, cot, dot, hot, box, fox, ox) / The fox is on the box. / The bug has dots. / The ox is in the pot.",
        "<Unit 08> (top, mop, hop, pop, dog, log, fog, jog) / I have a mop. / I jog with my dog. / I play with a top.",
        "<Unit 09> (hut, cut, nut, sun, gun, fun, run) / She cuts the nut. / They run in the sun. / A gun is in the hut.",
        "<Unit 10> (tub, rub, sub, cub, mug, bug, rug, hug) / The bug is on the sub. / They hug on the rug. / The cub jumps to the tub."
    ],
    "Phonics 3": [
        "<Unit 01> (tape, ape, cape, game, name, same, case, base, vase) / The ape has a cape. / They have the same name. / A vase is on the case.",
        "<Unit 02> (cake, bake, lake, cane, mane, Jane, cave, save, wave) / Jane bakes the cake. / We wave at the lake. / A cane is in the cave.",
        "<Unit 03> (bite, kite, site, hide, ride, side, ice, dice, rice) / I bite the ice. / You ride a bike. / You have one dice.",
        "<Unit 04> (bike, hike, like, pine, line, nine, dive, five, hive) / He likes me. / I see five lines. / A hive is in the pine.",
        "<Unit 05> (rope, hope, nope, dome, home, Rome, hose, rose, nose) / A hose is in the dome. / A rose is on the dome. / I hope to go home.",
        "<Unit 06> (note, vote, rote, bone, cone, zone, hole, pole, mole) / Two bones are in the hole. / Two poles are in the pet zone. / Two notes are on the cone.",
        "<Unit 07> (mute, cute, cube, tube, use, fuse) / This is a cube. / This is a fuse. / This is a cute tube.",
        "<Unit 08> (Duke, puke, dune, June, tune, huge) / Duke pukes on the dune. / I can make a tune. / This is a huge box."
    ],
    "Phonics 4": [
        "<Unit 01> (plate, plum, plane, black, block, blade, flag, flap, flute) / A plum is on the plate. / A flag flaps on the plane. / Here is a black block.",
        "<Unit 02> (press, price, prize, bride, brave, brick, frog, frame, free) / I press the brick. / He is free now. / I win the prize.",
        "<Unit 03> (clap, clip, clam, globe, glass, glove, slide, sled, sleep) / He sleeps in the clam. / She slides into the glass. / A clip is in the glove.",
        "<Unit 04> (crab, crane, creep, grape, grass, green, drive, drum, dress) / A crab creeps on the drum. / I want a grape dress. / A crane drives the green car.",
        "<Unit 05> (spin, space, spice, stop, stick, stove, skate, ski, skin) / Four balls spin on the ski. / Four balls stop on the ski. / Four sticks are in space.",
        "<Unit 06> (smoke, smell, smile, sneeze, snake, sniff, sweep, swan, swim) / Swans swim in the lake. / We smile at the snake. / The dog sniffs at two bones.",
        "<Unit 07> (lamp, jump, stamp, drink, wink, skunk, hang, song, ring) / I jump over the lamp. / I wink and drink. / I sing a song.",
        "<Unit 08> (chess, cheese, bench, lunch, shell, ship, fish, wash) / The chess is on the bench. / I wash the shell. / Cheese and fish are for lunch.",
        "<Unit 09> (whale, white, wheel, wheat, phone, graph, photo, dolphin) / A whale is in the photo. / Wheat is on the phone. / A wheel is on the dolphin.",
        "<Unit 10> (thin, thick, bath, math, this, that, these, those) / This is a thick book. / That is a thin book. / These are math books."
    ],
    "Phonics 5": [
        "<Unit 01> (tail, snail, train, chain, play, tray, clay, spray) / He plays with clay. / All chains are on the tray. / All snails are on the train.",
        "<Unit 02> (bee, seed, tree, tea, meat, leaf, key, honey, money) / The key is old. / The bee paints a money tree. / A leaf is in the honey tea.",
        "<Unit 03> (die, pie, tie, find, kind, blind, sigh, fight, night) / He is very kind. / She sighs at night. / They fight for the pie.",
        "<Unit 04> (boat, coat, soap, road, grow, blow, crow, snow) / A crow blows the soap boat. / A plant grows in the snow. / A coat is on the road.",
        "<Unit 05> (new, chew, stew, blue, clue, glue, room, spoon, moon) / He finds the clue. / The blue glue is on the spoon. / The goat chews my new tie.",
        "<Unit 06> (paw, draw, straw, head, bread, thread, book, foot, look) / Draw the paw now. / Draw the head again. / Look at the open book now.",
        "<Unit 07> (house, mouse, brown, clown, oil, soil, boy, toy) / A mouse lives in the house. / The boy jumps up and down. / The clown has brown soil.",
        "<Unit 08> (baby, study, cloudy, cherry, cry, dry, fly, sky) / They cry with the baby. / They dry the cherry. / They study in the sky.",
        "<Unit 09> (car, arm, star, shark, corn, fork, store, horse) / A horse eats corn. / A star is under the fork. / A shark is in the car store.",
        "<Unit 10> (nurse, purse, burn, bird, girl, skirt, mother, teacher, farmer) / The girl wears a skirt and a purse. / My teacher gives me the bird. / My mother is a nurse."
    ]
}

# 기존 데이터들 유지
V_BOOKS_LIST = ["능률 보카 기본 400", "능률 보카 필수 500", "능률 보카 교육청 900", "보카클리어 중학기본", "보카클리어 중학실력", "보카익스프레스", "기타"]
ELT_BOOKS = ["30 Word Reading(1)", "30 Word Reading(2)", "40 Word Reading(1)", "40 Word Reading(2)", "40 Read it(1)", "40 Read it(2)", "40 Read it(3)", "60 Read it(1)", "60 Read it(2)", "60 Read it(3)"]
READING_BOOKS = ["리딩튜터 스타터(1)", "리딩튜터 스타터(2)", "리딩튜터 스타터(3)", "리딩튜터 주니어(1)", "리딩튜터 주니어(2)", "리딩튜터 주니어(3)", "리딩튜터 주니어(4)", "수능토픽(레벨1)", "수능토픽(레벨2)", "수능토픽(레벨3)", "English Newspaper_Kids", "English Newspaper_Kinder", "자체 독해 자료"]
AZAR_BASIC_FULL_LIST = ["1-1 단수 인칭대명사+Be동사", "1-2 복수 인칭대명사+Be동사", "1-3 단수 명사+Be동사", "1-4 복수 명사+Be동사", "1-5 인칭대명사+Be동사 축약", "1-6 Be동사 부정문", "1-7 Be동사+형용사", "1-8 Be동사+장소", "1-9 Be동사 구조 요약", "2-1 This/That", "2-2 These/Those", "2-3 Be동사 Yes/No 의문문", "2-4 의문문 대답", "2-5 Where 의문문", "2-6 Have/Has", "2-7 소유격 인칭대명사", "2-8 What/Who 의문문", "3-1 현재시제 형태/의미", "3-2 빈도부사", "3-3 빈도부사 위치", "3-4 3인칭 단수 -es", "3-5 3인칭 단수 -y", "3-6 Has, Does, Goes", "3-7 Like/Want/Need/Would Like", "3-8 현재시제 부정문", "3-9 Yes/No 의문문", "3-10 Where/What 의문문", "3-11 When/What Time 의문문", "4-1 현재진행형 Be+-ing", "4-2 동사의 -ing", "4-3 현재진행 부정문", "4-4 현재진행 의문문", "4-5 현재 vs 진행", "4-6 상태동사", "4-7 See/Look/Watch/Hear/Listen", "4-8 Think About vs That", "4-9 명령문", "5-1 명사 단수/복수", "5-2 불규칙 복수형", "5-3 형용사의 쓰임", "5-4 명사: 주어/목적어", "5-5 주격/목적격 대명사", "5-6 전치사+목적격 대명사", "5-7 소유형용사/대명사", "5-8 명사 소유격", "5-9 Whose 의문문", "5-10 소유격 불규칙 복수", "6-1 셀 수 있는/없는 명사", "6-2 A vs An", "6-3 A/An vs Some", "6-4 물질명사 수량", "6-5 Many/Much/Few/Little", "6-6 정관사 The", "6-7 관사 미사용", "6-8 Some/Any", "7-1 비인칭주어 It(시간)", "7-2 시간 전치사", "7-3 비인칭주어 It(날씨)", "7-4 There+Be동사", "7-5 There+Be동사 의문문", "7-6 How Many 의문문", "7-7 장소 전치사", "7-8 위치 전치사", "7-9 Would Like", "7-10 Would Like vs Like"]
WRITING_DATA = {
    "OK Writing 1": ["Vocab", "Sentence 1~6", "Part 1. 전치사", "Part 2. 진행형", "Part 3. 부정문", "Part 4. and/because", "Part 5. 명령문", "Story 1-1~3-4"],
    "OK Writing 2": ["Vocab", "Sentence 1~6", "Part 1. 소유격", "Part 2. There is/are", "Part 3. but/because", "Part 4. 대상 2개", "Part 5. 의문문", "Part 6. look+형용사", "Part 7. don't", "Story 1-1~3-4"],
    "OK Writing 3": ["Vocab", "Sentence 1~9", "Part 1. of", "Part 2. to부정사", "Part 3. can", "Part 4. 비인칭", "Part 5. Let's", "Part 6. 3인칭단수", "Part 7. doesn't", "Story 1-1~3-5"],
    "OK Writing 4": ["Vocab", "Sentence 1~7", "Part 1. will", "Part 2. must", "Part 3. to부정사", "Part 4. that절", "Part 5. Do", "Part 6. 의문사", "Story 1-1~2-4"],
    "OK Writing 5": ["Vocab", "Sentence 1~9", "Part 1. 명령문", "Part 2. 빈도부사", "Part 3. Does", "Part 4. to부정사", "Part 5. 원급", "Part 6. 비교급", "Part 7. 최상급", "Story 1-1~2-2"],
    "OK Writing 6": ["Vocab", "Sentence 1~8", "Part 1. 과거", "Part 2. have to", "Part 3. Did", "Part 4. didn't", "Part 5. 동명사주어", "Part 6. 의문사구", "Part 7. 접속사", "Story 1-1~1-6"],
    "OK Writing 7": ["Vocab", "Sentence 1~12", "Part 1. 동명사목적어", "Part 2. 가주어 it", "Part 3. 형용사보어", "Part 4. 재귀대명사", "Part 5. 의문사구", "Part 6. should", "Part 7. 지각동사", "Story 1-1~3-2"],
    "Bridge Writing Starter": ["Vocabulary", "Sentence 1~3", "Part 1. 복수", "Part 2. 소유격", "Part 3. 진행형", "Part 4. but", "Part 5. 명령문", "Story 1-1~3-3"],
    "Bridge Writing 1": ["Vocabulary", "Sentence 1~5", "Part 1. 관사", "Part 2. 전치사", "Part 3. but/because", "Part 4. 부정문", "Part 5. 의문문", "Story 1-1~2-5"],
    "Bridge Writing 2": ["Vocabulary", "Sentence 1~6", "Part 1. 의문사", "Part 2. 3인칭", "Part 3. 형용사보어", "Part 4. will", "Part 5. 's", "Part 6. Please", "Story 1-1~3-4"],
    "Bridge Writing 3": ["Vocabulary", "Sentence 1~6", "Part 1. There", "Part 2. 소유격", "Part 3. 의문사", "Part 4. Don't", "Part 5. can", "Part 6. to", "Story 1-1~3-4"],
    "Training for Reading S1": ["Vocabulary", "Training 1. a/an/the+명사", "Training 2. 복수명사", "Training 3. 형용사+명사", "Training 4. 전치사+명사 (1)", "Training 5. 전치사+명사 (2)", "Training 6. 전치사+명사 (3)", "Training 7. 주인공+동작 (1)", "Training 8. 주인공+동작 (2)", "Training 9. 주인공+동작 (3)", "Training 10. 주인공+동작+대상 (1)", "Training 11. 주인공+동작+대상 (2)"],
    "Training for Reading S2": ["Vocabulary", "Training 1. 주인공+be+명사 (1)", "Training 2. 주인공+be+명사 (2)", "Training 3. 주인공+be+형용사", "Training 4. 주인공+be+명사/형용사 (1)", "Training 5. 주인공+be+명사/형용사 (2)", "Training 6. 주인공+be+명사/형용사 (3)", "Training 7. 주인공+be+전치사+명사 (1)", "Training 8. 주인공+be+전치사+명사 (2)", "Training 9. 주인공+be+전치사+명사 (3)", "Training 10. 주인공+be+명사/형용사/전치사 (Review)", "Training 11. 명령문"],
    "Training for Reading S3": ["Vocabulary", "Training 1. This/That+is+단수명사", "Training 2. This/That+is+소유격+명사 (1)", "Training 3. This/That+is+소유격+명사 (2)", "Training 4. 주인공과 대상이 ‘소유격+명사’", "Training 5. 주인공+동작+전치사+명사", "Training 6. 주인공+동작+대상+전치사+명사", "Training 7. 명령문: 동작+(대상)+전치사+명사", "Training 8. 주인공+be+~ing+(대상)", "Training 9. 주인공+be+~ing+(대상)+전치사+명사", "Story 1-1", "Story 1-2", "Story 1-3", "Story 2", "Story 3"],
    "Training for Reading S4": ["Vocabulary", "Training 1. 주인공+동작+대상(대명사)", "Training 2. 명사 and 명사", "Training 3. 형용사 and 형용사", "Training 4. 문장 and 문장", "Training 5. Because 주인공+동작", "Training 6. 주인공+동작+(대상)+부사", "Training 7. 부사+형용사", "Training 8. 부사+부사", "Training 9. 부사의 다양한 위치", "Story 1-1", "Story 1-2", "Story 1-3", "Story 2-1", "Story 2-2"]
}

# --- [메인 로직] ---
if "page" not in st.session_state: st.session_state.page = 'input'
if "ai_res" not in st.session_state: st.session_state.ai_res = ""

if st.session_state.page == 'input':
    st.title("🍎 엘케이어학원 학습 리포트") 

    with st.expander("📂 학생 교재 목록(엑셀) 불러오기", expanded=False):
        uploaded_excel = st.file_uploader("항목명이 세로(A열)로 된 엑셀 파일을 업로드하세요", type=['xlsx'])
        student_data = None
        if uploaded_excel:
            df_raw = pd.read_excel(uploaded_excel, index_col=0) 
            df = df_raw.T.reset_index() 
            st.success("세로형 엑셀 파일을 성공적으로 불러왔습니다!")
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

    # 2. 어휘 섹션
    st.subheader("🅰️ 2. 어휘 (Vocabulary)")
    vc1, vc2 = st.columns([2, 1])
    v_def = V_BOOKS_LIST.index(student_data['어휘교재']) if student_data is not None and student_data['어휘교재'] in V_BOOKS_LIST else 0
    v_book = vc1.selectbox("어휘 교재", V_BOOKS_LIST, index=v_def)
    v_unit = vc2.text_input("어휘 Unit 입력", placeholder="예: <Unit 01>")
    
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

    # 3. 주교재 및 수업 상세 (Phonics 섹션 상세 보강)
    st.subheader("📚 3. 주교재 및 수업 상세")
    
    # [Phonics 상세 복구]
    p_books_options = ["선택 안 함"] + list(PHONICS_DATA.keys())
    p_def = p_books_options.index(student_data['파닉스교재']) if student_data is not None and str(student_data['파닉스교재']) in p_books_options else 0
    p_book = st.selectbox("파닉스 교재", p_books_options, index=p_def)
    p_unit = "선택 안 함"
    if p_book != "선택 안 함":
        p_unit = st.selectbox("└ 파닉스 상세 Unit 선택", PHONICS_DATA[p_book])

    # ELT 독해
    elt_books = ["선택 안 함"] + ELT_BOOKS
    elt_def = elt_books.index(student_data['ELT교재']) if student_data is not None and str(student_data['ELT교재']) in elt_books else 0
    elt_book = st.selectbox("ELT 독해 교재", elt_books, index=elt_def)
    elt_unit = st.text_input("└ ELT Unit 입력", placeholder="예: <Unit 01>")

    # 일반 독해
    r_books = ["선택 안 함"] + READING_BOOKS
    r_def = r_books.index(student_data['독해교재']) if student_data is not None and str(student_data['독해교재']) in r_books else 0
    r_book = st.selectbox("독해 교재", r_books, index=r_def)
    r_unit = st.text_input("└ 독해 Unit 입력", placeholder="예: <Unit 01>")

    # 문법
    g_books = ["선택 안 함", "Azar Basic (Red)", "Azar Fundamentals", "기타"]
    g_def = g_books.index(student_data['문법교재']) if student_data is not None and str(student_data['문법교재']) in g_books else 0
    g_book = st.selectbox("문법 교재", g_books, index=g_def)
    g_sub = "선택 안 함"
    if g_book == "Azar Basic (Red)":
        g_sub = st.selectbox("└ Azar 세부 항목", AZAR_BASIC_FULL_LIST)
    elif g_book != "선택 안 함":
        g_sub = st.text_input("└ 단원명 직접 입력")

    # 라이팅
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
            with st.spinner("성취도 분석 중..."):
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
            if p_book != "선택 안 함": items.append(f"• 파닉스: {p_book} [{p_unit}]")
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
