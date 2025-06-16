import discord
from discord.ext import commands
import os
import re
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

CATEGORY_KEYWORDS = {
    "요리": ["요리", "토르타", "타코", "또르띠아", "부리토", "나쵸", "케사디야", "토르티야", "피클", "스튜", "수프", "볶음", "카레", "샌드위치"],
    "광물": ["원석", "블록", "광석", "수정", "다이아몬드", "에메랄드", "금", "은", "철"],
    "물고기": ["도미", "연어", "숭어", "잉어", "정어리", "개복치", "금붕어", "농어", "다랑어", "랍스터", "만타가오리", "메기", "문어", "아귀", "줄돔", "해파리", "흰동가리", "블루탱", "강꼬치고기", "뱀장어"]
}

# 작물 상세 정보를 담는 딕셔너리 (기존과 동일)
CROP_DETAILS = {
    "마늘": {"수확량": "1 ~ 6개", "재배 단계": "4단계", "계절": "가을 겨울", "숙련도": None},
    "홉": {"수확량": "1 ~ 6개", "재배 단계": "4단계", "계절": "봄 가을", "숙련도": None},
    "가지": {"수확량": "1 ~ 6개", "재배 단계": "4단계", "계절": "여름 가을", "숙련도": None},
    "포도": {"수확량": "2 ~ 4개", "재배 단계": "4단계", "계절": "가을 겨울", "숙련도": None},
    "고추": {"수확량": "2 ~ 4개", "재배 단계": "4단계", "계절": "봄 여름", "숙련도": None},
    "옥수수": {"수확량": "2 ~ 4개", "재배 단계": "4단계", "계절": "여름 가을", "숙련도": None},
    "토마토": {"수확량": "2 ~ 4개", "재배 단계": "4단계", "계절": "봄 겨울", "숙련도": None},
    "양배추": {"수확량": "1개", "재배 단계": "4단계", "계절": "봄 여름", "숙련도": None},
    "배추": {"수확량": "1개", "재배 단계": "4단계", "계절": "봄 겨울", "숙련도": None},
    "파인애플": {"수확량": "1개", "재배 단계": "4단계", "계절": "여름 가을", "숙련도": None},
    "블랙베리": {"수확량": "1 ~ 2개", "재배 단계": "5단계", "계절": "봄 겨울", "숙련도": 10},
    "블루베리": {"수확량": "1 ~ 2개", "재배 단계": "5단계", "계절": "봄 가을", "숙련도": 10},
    "라즈베리": {"수확량": "1 ~ 2개", "재배 단계": "5단계", "계절": "봄 겨울", "숙련도": 10},
    "체리": {"수확량": "1 ~ 2개", "재배 단계": "5단계", "계절": "봄 여름", "숙련도": 10},
    "구기자": {"수확량": "1 ~ 2개", "재배 단계": "5단계", "계절": "봄 겨울", "숙련도": 10},
    "리치": {"수확량": "1 ~ 2개", "재배 단계": "5단계", "계절": "봄 여름", "숙련도": 10},
    "아보카도": {"수확량": "1 ~ 2개", "재배 단계": "5단계", "계절": "봄 여름", "숙련도": 10},
    "카람볼라": {"수확량": "1 ~ 2개", "재배 단계": "5단계", "계절": "여름 가을", "숙련도": 20},
    "오이": {"수확량": "1 ~ 2개", "재배 단계": "5단계", "계절": "여름 가을", "숙련도": 20},
    "키위": {"수확량": "1 ~ 2개", "재배 단계": "5단계", "계절": "여름 가을", "숙련도": 20},
    "망고": {"수확량": "1 ~ 2개", "재배 단계": "5단계", "계절": "여름 가을", "숙련도": 20},
    "파파야": {"수확량": "1 ~ 2개", "재배 단계": "5단계", "계절": "여름 가을", "숙련도": 20},
    "구아바": {"수확량": "1 ~ 2개", "재배 단계": "5단계", "계절": "봄 여름", "숙련도": 30},
    "두리안": {"수확량": "1개", "재배 단계": "5단계", "계절": "봄 여름", "숙련도": 30},
    "코코넛": {"수확량": "1개", "재배 단계": "5단계", "계절": "여름 가을", "숙련도": 40},
}

def classify_item(name):
    # '특상품' 또는 '황금' 접두어를 제거하고 기본 작물 이름으로 매칭 시도
    base_name_for_check = name.replace("특상품 ", "").replace("황금 ", "")
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in name for keyword in keywords):
            return category
    
    # CROP_DETAILS에 있는 아이템이면 "작물"로 분류
    if base_name_for_check in CROP_DETAILS:
        return "작물"
    return "기타" # 분류되지 않은 아이템은 "기타"로 분류

def parse_items(text, exclude_keyword=None, only_category=None, only_grade=None, only_season=None):
    result = []

    # 메시지 전처리: 제목 부분 및 불필요한 공백/줄바꿈 제거
    # "가격 상승된 아이템:" 또는 "가격 하락된 아이템:" 이후의 내용만 추출
    cleaned_text = text
    if "가격 상승된 아이템:" in text:
        cleaned_text = cleaned_text.split("가격 상승된 아이템:", 1)[1]
    if "가격 하락된 아이템:" in cleaned_text:
        cleaned_text = cleaned_text.split("가격 하락된 아이템:", 1)[0] # 하락된 아이템 섹션은 분리하여 처리
    
    # 각 아이템 블록을 분리하기 위한 정규 표현식 (줄바꿈 또는 ,로 구분)
    # 쉼표 다음에 새로운 아이템 이름과 (등급) 패턴이 시작하는 지점
    # 또는 줄바꿈 다음에 새로운 아이템 이름과 (등급) 패턴이 시작하는 지점
    item_blocks = re.split(r',\s*(?=[가-힣\s]+?\s*\(\d+등급|\d+단계\):)|(?<=\n)[^\n]*?(?=[가-힣\s]+?\s*\(\d+등급|\d+단계\):)', cleaned_text)

    # 쉼표로 분리된 마지막 아이템 블록에 잔여 데이터가 있을 수 있으므로 한번 더 분할
    # 메시지 끝에 불필요한 쉼표가 있을 수 있으므로 trim
    item_blocks = [block.strip() for block in item_blocks if block.strip()]

    # 특수하게 메시지 중간에 "가격 유지된 아이템:" 같은 섹션 헤더가 있으면 제거
    # 이 헤더는 아이템 정보가 아니므로 파싱에서 제외
    item_blocks = [block for block in item_blocks if "가격 유지된 아이템:" not in block and "가격 상승된 아이템:" not in block and "가격 하락된 아이템:" not in block]

    for block in item_blocks:
        block = block.strip() # 다시 한번 공백 제거
        if not block:
            continue
        
        # 1. '변동전', '변동후', '변동률'이 있는 메시지 형식 (변동 알림 메시지)
        # `원가:`, `변동전:`, `변동후:` 뒤에 `[\d,]+`를 사용하여 쉼표 있는 숫자 파싱
        pattern1 = r"(.+?)\s*\((\d+등급|\d+단계)\):\s*`?원가:\s*([\d,]+)`?,\s*`?변동전:\s*[\d,]+`?,\s*`?변동후:\s*([\d,]+)`?,\s*`?변동률:.*?"
        match = re.search(pattern1, block)
        
        if match:
            name, grade, cost_str, after_str = match.groups()
            source_type = "변동알림"
        else:
            # 2. '현재가'만 있는 메시지 형식 (가격 유지/일반 시세 메시지)
            # `원가:`, `현재가:` 뒤에 `[\d,]+`를 사용하여 쉼표 있는 숫자 파싱
            pattern2 = r"(.+?)\s*\((\d+등급|\d+단계)\):\s*`?원가:\s*([\d,]+)`?,\s*`?현재가:\s*([\d,]+)`?"
            match = re.search(pattern2, block)
            if match:
                name, grade, cost_str, after_str = match.groups() # 현재가를 after_str로 사용
                source_type = "일반시세"
            else:
                # print(f"DEBUG: 파싱 실패 블록: {block[:100]}...") # 디버깅용
                continue # 두 패턴 모두 매칭되지 않으면 스킵

        full_name = f"{name.strip()} {grade.strip()}"
        # '특상품' 또는 '황금' 접두사를 제거하여 CROP_DETAILS 키와 매칭
        base_name_for_lookup = name.strip().replace("특상품 ", "").replace("황금 ", "")

        if exclude_keyword and exclude_keyword in full_name:
            continue
        category = classify_item(full_name)
        if only_category and category != only_category:
            continue
        if only_grade and only_grade not in grade:
            continue
        
        # 계절 필터링 로직
        if only_season:
            # 분류된 카테고리가 '작물'이고, CROP_DETAILS에 해당 작물이 있어야 계절 필터링 적용
            if category == "작물" and base_name_for_lookup in CROP_DETAILS:
                item_seasons_str = CROP_DETAILS[base_name_for_lookup].get("계절", "")
                item_seasons = item_seasons_str.split() # "가을 겨울" -> ["가을", "겨울"]
                if only_season not in item_seasons:
                    # print(f"DEBUG: 계절 불일치: {full_name} (필요: {only_season}, 실제: {item_seasons_str})") # 디버깅용
                    continue # 요청된 계절에 해당하지 않으면 스킵
            else:
                # 작물이 아니거나 CROP_DETAILS에 없는 작물은 계절 필터링에서 제외
                # print(f"DEBUG: 작물 아님/DETAILS 없음: {full_name} (카테고리: {category})") # 디버깅용
                continue

        try:
            cost = int(cost_str.replace(",", ""))
            after = int(after_str.replace(",", ""))
            profit_rate = ((after - cost) / cost) * 100

            item_data = {
                'name': full_name,
                'cost': cost,
                'after': after,
                'profit_rate': profit_rate,
                'category': category,
                'grade': grade
            }
            if category == "작물" and base_name_for_lookup in CROP_DETAILS:
                item_data.update(CROP_DETAILS[base_name_for_lookup])
            result.append(item_data)
        except ValueError:
            print(f"가격 파싱 오류 ({source_type}): {cost_str} 또는 {after_str} for {block[:50]}...")
            continue
        except Exception as e:
            print(f"알 수 없는 파싱 오류: {e} for {block[:50]}...")
            continue

    return sorted(result, key=lambda x: x['after'], reverse=True) # 판매가(after) 높은 순으로 정렬


@bot.event
async def on_ready():
    print(f"✅ 봇 작동 중: {bot.user}")
    try:
        await bot.tree.sync() # 변경된 슬래시 명령어 동기화
        print(f"✅ 슬래시 명령어가 성공적으로 동기화되었습니다.")
    except Exception as e:
        print(f"❌ 슬래시 명령어 동기화 실패: {e}")

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.id == bot.user.id: # 봇 자신의 메시지 (자동 감지 응답 등)는 무시
        return
    
    # 일반 봇 메시지이지만 웹훅이 아닌 경우 스킵 (웹훅 메시지는 bot.author.bot = True)
    # 웹훅 메시지는 webhook_id가 None이 아님 (주로) 또는 is_webhook() 메소드 사용
    # 여기서는 msg.webhook_id is None 대신, msg.author.bot만 보고 웹훅 메시지는 걸러내지 않고 진행
    # (다른 서버 팔로우 메시지는 봇으로 인식되지만 webhook_id가 있을 수 있음)
    # 현재 코드에서는 msg.webhook_id is None and msg.author.bot을 제외 조건으로 썼는데,
    # 웹훅 메시지는 msg.author.bot은 True이지만 msg.webhook_id가 None이 아니므로 걸러지지 않음.
    # 즉, 봇 메시지 중 '본인 봇' 메시지만 제외하는 것이 더 정확.
    # 따라서 이 조건은 삭제하고 아래 on_message의 첫번째 줄만 유지

    content = message.content
    if not content and message.embeds:
        embed = message.embeds[0]
        content = embed.description or ""
        if not content and embed.fields:
            content = "\n".join(f.value for f in embed.fields if f.value)
    
    # 메시지 내용이 비어있으면 처리하지 않음
    if not content.strip():
        # print("DEBUG: 빈 메시지 또는 내용 없는 임베드 스킵.") # 디버깅용
        return

    # on_message 에서는 자동 감지이므로 계절 필터링 없음
    if "원가" in content and ("현재가" in content or "변동후" in content):
        # print("DEBUG: 자동 감지 시작 - '원가' 키워드 감지.") # 디버깅용
        items = parse_items(content)
        if items:
            # print(f"DEBUG: 자동 감지에서 {len(items)}개 아이템 파싱 성공.") # 디버깅용
            response = "📊 수익률 TOP 5 (자동 감지)\n"
            for i, item in enumerate(items[:5], start=1):
                response += f"{i}. {item['name']} - {item['profit_rate']:.2f}% (원가: {item['cost']} → 현재가: {item['after']})"
                # 작물에 대한 추가 정보 표시
                if item['category'] == "작물":
                    details = []
                    if '계절' in item and item['계절']:
                        details.append(f"계절: {item['계절']}")
                    if '숙련도' in item and item['숙련도'] is not None:
                        details.append(f"숙련도: {item['숙련도']}")
                    if '수확량' in item and item['수확량']:
                        details.append(f"수확량: {item['수확량']}")
                    if '재배 단계' in item and item['재배 단계']:
                        details.append(f"재배 단계: {item['재배 단계']}")
                    if details:
                        response += f" ({', '.join(details)})"
                response += "\n"
            # print("DEBUG: 자동 감지 응답 전송.") # 디버깅용
            await message.channel.send(response)
        # else:
            # print("DEBUG: 자동 감지 - 파싱된 아이템 없음.") # 디버깅용

# send_top_items 함수: 모든 메시지를 대상으로 필터링된 아이템을 모아서 정렬
async def send_top_items(interaction_channel, exclude_keyword=None, only_category=None, only_grade=None, only_season=None, limit=5):
    # print(f"DEBUG: send_top_items 호출됨. only_season: {only_season}") # 디버깅용
    messages = [m async for m in interaction_channel.history(limit=50)] # 최근 50개 메시지 조회
    all_filtered_items = [] # 모든 메시지에서 필터링된 아이템을 저장할 리스트

    for msg in messages:
        # 본인 봇 메시지(자동감지 응답 등)는 제외
        if msg.author.id == bot.user.id:
            # print(f"DEBUG: 본인 봇 메시지 스킵: {msg.content[:50]}...") # 디버깅용
            continue 

        content = msg.content
        if not content and msg.embeds:
            embed = msg.embeds[0]
            content = embed.description or ""
            if not content and embed.fields:
                content = "\n".join(f.value for f in embed.fields if f.value)
        
        # 메시지 내용이 비어있으면 스킵
        if not content.strip():
            # print("DEBUG: 빈 메시지 스킵.") # 디버깅용
            continue

        if "원가" in content and ("변동후" in content or "현재가" in content):
            # print(f"DEBUG: send_top_items - 시세 키워드 감지됨. 메시지 길이: {len(content)}") # 디버깅용
            # print(f"DEBUG: 메시지 내용 첫 200자:\n{content[:200]}") # 디버깅용
            # parse_items 호출 시 모든 필터링 인자 전달
            items = parse_items(content, exclude_keyword, only_category, only_grade, only_season)
            if items:
                # print(f"DEBUG: send_top_items - {len(items)}개 아이템 파싱 성공. (season: {only_season})") # 디버깅용
                all_filtered_items.extend(items)
            # else:
                # print(f"DEBUG: send_top_items - 파싱된 아이템 없음. (season: {only_season})") # 디버깅용
        # else:
            # print("DEBUG: send_top_items - 시세 키워드 불일치.") # 디버깅용
    
    if all_filtered_items:
        # print(f"DEBUG: 총 {len(all_filtered_items)}개 필터링된 아이템 발견.") # 디버깅용
        # 모든 필터링된 아이템을 판매가(after) 기준으로 다시 정렬
        sorted_items = sorted(all_filtered_items, key=lambda x: x['after'], reverse=True)
        
        response = f"📊 {only_season} 계절 작물 판매가 TOP {limit}" if only_season else f"📊 작물 판매가 TOP {limit}" # 응답 제목 변경
        if only_grade:
            response += f" ({only_grade} 기준)"
        if exclude_keyword:
            response += f' ("{exclude_keyword}" 제외)'
        response += "\n"

        # TOP N개만 출력
        for i, item in enumerate(sorted_items[:limit], start=1):
            response += f"{i}. {item['name']} - 판매가: {item['after']}" # 판매가 먼저 표시
            # 작물에 대한 추가 정보 표시
            if item['category'] == "작물":
                details = []
                # 숙련도만 옆에 붙도록 수정
                if '숙련도' in item and item['숙련도'] is not None:
                    details.append(f"숙련도: {item['숙련도']}")
                # 그 외 정보는 /작물시세에서만 추가적으로 보여주도록 조건 추가
                if '수확량' in item and item['수확량'] and only_category == "작물": 
                    details.append(f"수확량: {item['수확량']}")
                if '재배 단계' in item and item['재배 단계'] and only_category == "작물":
                    details.append(f"재배 단계: {item['재배 단계']}")
                if details:
                    response += f" ({', '.join(details)})"
            response += "\n"

        if len(response) > 2000: # 디스코드 메시지 길이 제한
            await interaction_channel.send("결과가 너무 많아 일부만 표시됩니다.")
            await interaction_channel.send(response[:1900] + "...") # 너무 길면 잘라서 보내기
        else:
            await interaction_channel.send(response)
    else:
        await interaction_channel.send(f"최근 메시지에서 '{only_season}' 계절의 작물 시세 정보를 찾을 수 없어요. (최근 50개 메시지 확인)")


# /작물시세 슬래시 명령어 정의
@bot.tree.command(name="작물시세", description="특정 계절의 판매가 높은 작물 TOP 5를 조회합니다.")
@app_commands.describe(season="조회할 계절을 선택하세요.")
@app_commands.choices(season=[
    app_commands.Choice(name="봄", value="봄"),
    app_commands.Choice(name="여름", value="여름"),
    app_commands.Choice(name="가을", value="가을"),
    app_commands.Choice(name="겨울", value="겨울"),
])
async def crop_price_command(interaction: discord.Interaction, season: str):
    await interaction.response.defer() # 봇이 명령어를 처리 중임을 알림
    # send_top_items 함수를 호출하여 계절별 작물 시세 조회
    await send_top_items(interaction.channel, only_category="작물", only_season=season, limit=5)

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
