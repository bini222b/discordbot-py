import discord
from discord.ext import commands
import os
import re
from discord import app_commands # app_commands 모듈 임포트

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

CATEGORY_KEYWORDS = {
    "요리": ["요리", "토르타", "타코", "또르띠아", "부리토", "나쵸", "케사디야", "토르티야", "피클", "스튜", "수프", "볶음", "카레", "샌드위치"],
    "광물": ["원석", "블록", "광석", "수정", "다이아몬드", "에메랄드", "금", "은", "철"],
    "물고기": ["도미", "연어", "숭어", "잉어", "정어리", "개복치", "금붕어", "농어", "다랑어", "랍스터", "만타가오리", "메기", "문어", "아귀", "줄돔", "해파리", "흰동가리", "블루탱", "강꼬치고기", "뱀장어"]
}

# 작물 상세 정보를 담는 딕셔너리 (제공해주신 이미지 기반)
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
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in name for keyword in keywords):
            return category
    # CROP_DETAILS에 있는 아이템이면 "작물"로 분류
    if any(crop_name in name for crop_name in CROP_DETAILS):
        return "작물"
    return "기타" # 분류되지 않은 아이템은 "기타"로 분류

def parse_items(text, exclude_keyword=None, only_category=None, only_grade=None, only_season=None): # only_season 인자 추가
    # 변경된 정규 표현식: 원가, 변동전, 변동후, 변동률을 정확히 파싱 (쉼표 없음)
    pattern = r"-\s*(.+?)\s*\((\d+등급|\d+단계)\):\s*원가:\s*([\d]+),\s*변동전:\s*[\d]+,\s*변동후:\s*([\d]+),\s*변동률:.*?"
    matches = re.findall(pattern, text)
    result = []

    for name, grade, cost_str, after_str in matches:
        full_name = f"{name.strip()} {grade.strip()}"
        # 아이템의 기본 이름만 추출 (예: "구기자 (1단계)"에서 "구기자")
        base_name = name.strip()

        if exclude_keyword and exclude_keyword in full_name:
            continue
        category = classify_item(full_name)
        if only_category and category != only_category:
            continue
        if only_grade and only_grade not in grade:
            continue
        
        # 계절 필터링 추가
        if only_season:
            # 작물 상세 정보에서 계절 정보를 가져와서 현재 요청된 계절이 포함되는지 확인
            if category == "작물" and base_name in CROP_DETAILS:
                item_seasons = CROP_DETAILS[base_name].get("계절", "").split()
                if only_season not in item_seasons:
                    continue # 요청된 계절에 해당하지 않으면 스킵

        try:
            cost = int(cost_str)
            after = int(after_str)
            profit_rate = ((after - cost) / cost) * 100

            item_data = {
                'name': full_name,
                'cost': cost,
                'after': after,
                'profit_rate': profit_rate,
                'category': category,
                'grade': grade
            }

            # 작물인 경우, 추가 상세 정보를 삽입
            if category == "작물" and base_name in CROP_DETAILS:
                item_data.update(CROP_DETAILS[base_name])

            result.append(item_data)
        except ValueError: # int() 변환 오류는 ValueError로 처리하는 것이 좋습니다.
            print(f"가격 파싱 오류: {cost_str} 또는 {after_str}")
            continue

    return sorted(result, key=lambda x: x['after'], reverse=True) # 판매가(after) 높은 순으로 정렬

@bot.event
async def on_ready():
    print(f"✅ 봇 작동 중: {bot.user}")
    try:
        # 기존에 삭제했던 명령어를 다시 동기화합니다.
        # 주의: 이 작업은 봇이 접속된 모든 서버에 적용되며, 반영까지 시간이 걸릴 수 있습니다.
        # 모든 길드의 명령어를 다시 동기화 (전역 명령어 포함)
        await bot.tree.sync() # 변경된 슬래시 명령어 동기화
        print(f"✅ 슬래시 명령어가 성공적으로 동기화되었습니다.")
    except Exception as e:
        print(f"❌ 슬래시 명령어 동기화 실패: {e}")

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.bot:
        return

    content = message.content
    if not content and message.embeds:
        embed = message.embeds[0]
        content = embed.description or ""
        if not content and embed.fields:
            content = "\n".join(f.value for f in embed.fields if f.value)

    if "원가" in content and ("현재가" in content or "변동후" in content):
        items = parse_items(content) # 자동 감지에서는 계절 필터링 없음
        if items:
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
            await message.channel.send(response)

# send_top_items 함수에 only_season 인자 추가 및 정렬 기준 변경 (판매가 기준)
async def send_top_items(channel, exclude_keyword=None, only_category=None, only_grade=None, only_season=None, limit=5): # only_season 인자 추가
    messages = [m async for m in channel.history(limit=50)]
    found_items = False
    all_filtered_items = [] # 모든 메시지에서 필터링된 아이템을 저장할 리스트

    for msg in messages:
        if msg.webhook_id is None and msg.author.bot:
            continue

        content = msg.content
        if not content and msg.embeds:
            embed = msg.embeds[0]
            content = embed.description or ""
            if not content and embed.fields:
                content = "\n".join(f.value for f in embed.fields if f.value)

        if "원가" in content and ("변동후" in content or "현재가" in content):
            # parse_items 호출 시 only_season 인자 전달
            items = parse_items(content, exclude_keyword, only_category, only_grade, only_season)
            if items:
                all_filtered_items.extend(items)
    
    if all_filtered_items:
        # 모든 필터링된 아이템을 판매가(after) 기준으로 다시 정렬
        sorted_items = sorted(all_filtered_items, key=lambda x: x['after'], reverse=True)
        
        response = f"📊 {only_season} 계절 작물 판매가 TOP {limit}" # 응답 제목 변경
        if only_grade:
            response += f" ({only_grade} 기준)"
        if exclude_keyword:
            response += f' ("{exclude_keyword}" 제외)'
        response += "\n"

        # TOP N개만 출력
        for i, item in enumerate(sorted_items[:limit], start=1):
            response += f"{i}. {item['name']} - 판매가: {item['after']} (원가: {item['cost']})" # 판매가 먼저 표시
            # 작물에 대한 추가 정보 표시
            if item['category'] == "작물":
                details = []
                # 숙련도만 옆에 붙도록 수정
                if '숙련도' in item and item['숙련도'] is not None:
                    details.append(f"숙련도: {item['숙련도']}")
                # 그 외 정보는 추가적으로 원하면 넣을 수 있도록 준비
                if '수확량' in item and item['수확량'] and only_category: # /작물시세에서만 상세 정보 추가 (복잡도 감소)
                    details.append(f"수확량: {item['수확량']}")
                if '재배 단계' in item and item['재배 단계'] and only_category:
                    details.append(f"재배 단계: {item['재배 단계']}")
                if details:
                    response += f" ({', '.join(details)})"
            response += "\n"

        await channel.send(response)
    else:
        await channel.send(f"최근 메시지에서 '{only_season}' 계절의 작물 시세 정보를 찾을 수 없어요.")


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
