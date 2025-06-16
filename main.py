import discord
from discord.ext import commands
import os
import re
from discord import app_commands

print("DEBUG: 봇 스크립트 시작 지점!")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# 토큰을 직접 os.getenv에서 가져와 변수에 할당 (이전과 동일하게 유지)
discord_bot_token = os.getenv("DISCORD_BOT_TOKEN") # 변수명을 token 대신 discord_bot_token으로 변경하여 혼동 방지
if discord_bot_token:
    print("DEBUG: 봇 토큰 환경 변수 감지됨.")
else:
    print("ERROR: 봇 토큰 환경 변수를 찾을 수 없습니다! 'DISCORD_BOT_TOKEN' 확인 필요.")
    # 토큰이 없으면 봇 실행을 중단하는 것이 좋지만, 일단은 에러 메시지만 출력

CATEGORY_KEYWORDS = {
    "요리": ["요리", "토르타", "타코", "또르띠아", "부리토", "나쵸", "케사디야", "토르티야", "피클", "스튜", "수프", "볶음", "카레", "샌드위치"],
    "광물": ["원석", "블록", "광석", "수정", "다이아몬드", "에메랄드", "금", "은", "철"],
    "물고기": ["도미", "연어", "숭어", "잉어", "정어리", "개복치", "금붕어", "농어", "다랑어", "랍스터", "만타가오리", "메기", "문어", "아귀", "줄돔", "해파리", "흰동가리", "블루탱", "강꼬치고기", "뱀장어"]
}

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
    base_name_for_check = name.replace("특상품 ", "").replace("황금 ", "")
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in name for keyword in keywords):
            return category
    
    if base_name_for_check in CROP_DETAILS:
        return "작물"
    return "기타"

def parse_items(text, exclude_keyword=None, only_category=None, only_grade=None, only_season=None):
    result = []

    cleaned_text = text
    lines = cleaned_text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue
        if stripped_line.startswith(('## ', '### ', '가격 상승된 아이템:', '가격 하락된 아이템:', '가격 유지된 아이템:')):
            continue
        if stripped_line.startswith('- '):
            cleaned_lines.append(stripped_line[2:].strip())
        else:
            cleaned_lines.append(stripped_line)
    
    for line_content in cleaned_lines:
        item_substrings = re.split(r', *(?=[가-힣\s]+?\s*\(\d+등급|\d+단계\))', line_content)
        
        for block in item_substrings:
            block = block.strip()
            if not block:
                continue

            pattern1 = r"(.+?)\s*\((\d+등급|\d+단계)\):\s*`?원가:\s*([\d,]+)`?,\s*`?변동전:\s*([\d,]+)`?,\s*`?변동후:\s*([\d,]+)`?,\s*`?변동률:.*?"
            match = re.search(pattern1, block)
            
            if match:
                name, grade, cost_str, prev_str, after_str = match.groups()
                source_type = "변동알림"
            else:
                pattern2 = r"(.+?)\s*\((\d+등급|\d+단계)\):\s*`?원가:\s*([\d,]+)`?,\s*`?현재가:\s*([\d,]+)`?"
                match = re.search(pattern2, block)
                if match:
                    name, grade, cost_str, after_str = match.groups()
                    source_type = "일반시세"
                else:
                    continue

            full_name = f"{name.strip()} {grade.strip()}"
            base_name_for_lookup = name.strip().replace("특상품 ", "").replace("황금 ", "")

            if exclude_keyword and exclude_keyword in full_name:
                continue
            category = classify_item(full_name)
            if only_category and category != only_category:
                continue
            if only_grade and only_grade not in grade:
                continue
            
            if only_season:
                if category == "작물" and base_name_for_lookup in CROP_DETAILS:
                    item_seasons_str = CROP_DETAILS[base_name_for_lookup].get("계절", "")
                    item_seasons = item_seasons_str.split()
                    if only_season not in item_seasons:
                        continue
                else:
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

    return sorted(result, key=lambda x: x['after'], reverse=True)


@bot.event
async def on_ready():
    print(f"DEBUG: on_ready 이벤트 실행됨! 봇 유저: {bot.user}")
    try:
        await bot.tree.sync()
        print(f"✅ 슬래시 명령어가 성공적으로 동기화되었습니다.")
    except Exception as e:
        print(f"❌ 슬래시 명령어 동기화 실패: {e}")

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.id == bot.user.id:
        return
    
    content = message.content
    if not content and message.embeds:
        embed = message.embeds[0]
        content = embed.description or ""
        if not content and embed.fields:
            content = "\n".join(f.value for f in embed.fields if f.value)
    
    if not content.strip():
        return

    if "원가" in content and ("현재가" in content or "변동후" in content):
        items = parse_items(content)
        if items:
            response = "📊 수익률 TOP 5 (자동 감지)\n"
            for i, item in enumerate(items[:5], start=1):
                response += f"{i}. {item['name']} - {item['profit_rate']:.2f}% (원가: {item['cost']} → 현재가: {item['after']})"
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

async def send_top_items(interaction_channel, exclude_keyword=None, only_category=None, only_grade=None, only_season=None, limit=5):
    messages = [m async for m in interaction_channel.history(limit=50)]
    all_filtered_items = []

    for msg in messages:
        if msg.author.id == bot.user.id:
            continue 

        content = msg.content
        if not content and msg.embeds:
            embed = msg.embeds[0]
            content = embed.description or ""
            if not content and embed.fields:
                content = "\n".join(f.value for f in embed.fields if f.value)
        
        if not content.strip():
            continue

        if "원가" in content and ("변동후" in content or "현재가" in content):
            items = parse_items(content, exclude_keyword, only_category, only_grade, only_season)
            if items:
                all_filtered_items.extend(items)
    
    if all_filtered_items:
        sorted_items = sorted(all_filtered_items, key=lambda x: x['after'], reverse=True)
        
        response = f"📊 {only_season} 계절 작물 판매가 TOP {limit}" if only_season else f"📊 작물 판매가 TOP {limit}"
        if only_grade:
            response += f" ({only_grade} 기준)"
        if exclude_keyword:
            response += f' ("{exclude_keyword}" 제외)'
        response += "\n"

        for i, item in enumerate(sorted_items[:limit], start=1):
            response += f"{i}. {item['name']} - 판매가: {item['after']}"
            if item['category'] == "작물":
                details = []
                if '숙련도' in item and item['숙련도'] is not None:
                    details.append(f"숙련도: {item['숙련도']}")
                if '수확량' in item and item['수확량'] and only_category == "작물":
                    details.append(f"수확량: {item['수확량']}")
                if '재배 단계' in item and item['재배 단계'] and only_category == "작물":
                    details.append(f"재배 단계: {item['재배 단계']}")
                if details:
                    response += f" ({', '.join(details)})"
            response += "\n"

        if len(response) > 2000:
            await interaction_channel.send("결과가 너무 많아 일부만 표시됩니다.")
            await interaction_channel.send(response[:1900] + "...")
        else:
            await interaction_channel.send(response)
    else:
        await interaction_channel.send(f"최근 메시지에서 '{only_season}' 계절의 작물 시세 정보를 찾을 수 없어요. (최근 50개 메시지 확인)")


@bot.tree.command(name="작물시세", description="특정 계절의 판매가 높은 작물 TOP 5를 조회합니다.")
@app_commands.describe(season="조회할 계절을 선택하세요.")
@app_commands.choices(season=[
    app_commands.Choice(name="봄", value="봄"),
    app_commands.Choice(name="여름", value="여름"),
    app_commands.Choice(name="가을", value="가을"),
    app_commands.Choice(name="겨울", value="겨울"),
])
async def crop_price_command(interaction: discord.Interaction, season: str):
    await interaction.response.defer()
    await send_top_items(interaction.channel, only_category="작물", only_season=season, limit=5)

# 봇 실행 부분 (가장 마지막)
try:
    print("DEBUG: bot.run() 호출 시도 중...")
    # 토큰 변수명을 discord_bot_token으로 변경했으므로, 이 변수를 사용
    bot.run(discord_bot_token) 
except Exception as e:
    print(f"CRITICAL ERROR: 봇 실행 중 치명적인 오류 발생: {e}")
