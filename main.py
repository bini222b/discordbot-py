import discord
from discord.ext import commands
import os
import re
from discord import app_commands

print("DEBUG: 봇 스크립트 시작 지점!")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

discord_bot_token = os.getenv("DISCORD_BOT_TOKEN")
if discord_bot_token:
    print("DEBUG: 봇 토큰 환경 변수 감지됨.")
else:
    print("ERROR: 봇 토큰 환경 변수를 찾을 수 없습니다! 'DISCORD_BOT_TOKEN' 확인 필요.")

CATEGORY_KEYWORDS = {
    "요리": ["요리", "토르타", "타코", "또르띠아", "부리토", "나쵸", "케사디야", "토르티야", "피클", "스튜", "수프", "볶음", "카레", "샌드위치"],
    "광물": ["원석", "블록", "광석", "수정", "다이아몬드", "에메랄드", "금", "은", "철"],
    "물고기": ["도미", "연어", "숭어", "잉어", "정어리", "개복치", "금붕어", "농어", "다랑어", "랍스터", "만타가오리", "메기", "문어", "아귀", "줄돔", "해파리", "흰동가리", "블루탱", "강꼬치고기", "뱀장어"]
}

CROP_DETAILS = {
    "마늘": {"수확량": "1 ~ 6개", "재배 단계": "4단계", "계절": "가을 겨울", "숙련도": None},
    "홉": {"수확량": "1 ~ 6개", "재배 단계": "4단계", "계절": "봄 가을", "숙련도": None},
    "가지": {"수확량": "1 ~ 6개", "재배 단계": "4단계", "계절": "여름 가을", "숙련도": None},
    # ... 이외 항목 생략 ...
}

# 접두어 제거 및 작물명 정리 함수
def clean_base_name(name: str) -> str:
    # '특상품', '황금' 등의 접두어 제거
    return re.sub(r'^(특상품|황금)\s*', '', name).strip()

# 카테고리 분류 함수
def classify_item(name: str) -> str:
    base = clean_base_name(name)
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in name for keyword in keywords):
            return category
    if base in CROP_DETAILS:
        return "작물"
    return "기타"

# 아이템 파싱 함수
def parse_items(text: str, exclude_keyword=None, only_category=None, only_grade=None, only_season=None):
    result = []
    print(f"DEBUG: parse_items 호출됨. only_season: {only_season}. 원본 텍스트 첫 100자:\n{text[:100]}...")

    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith(('## ', '### ', '가격 상승된 아이템:', '가격 하락된 아이템:', '가격 유지된 아이템:')):
            continue
        if s.startswith('- '):
            cleaned_lines.append(s[2:].strip())
        else:
            cleaned_lines.append(s)

    print(f"DEBUG: 전처리 후 cleaned_lines ({len(cleaned_lines)}개): {cleaned_lines[:5]}...")

    for line in cleaned_lines:
        parts = re.split(r', *(?=[가-힣\s]+?\s*\(\d+(?:등급|단계)\))', line)
        for block in parts:
            block = block.strip()
            if not block:
                continue
            # 변동 알림 형식
            m = re.search(r"(.+?)\s*\((\d+(?:등급|단계))\):\s*`?원가:\s*`?([\d,]+)`?,\s*`?변동전:\s*`?([\d,]+)`?,\s*`?변동후:\s*`?([\d,]+)`?,", block)
            if m:
                name, grade, cost_str, prev_str, after_str = m.groups()
            else:
                # 일반 시세 형식
                m2 = re.search(r"(.+?)\s*\((\d+(?:등급|단계))\):\s*`?원가:\s*`?([\d,]+)`?,\s*`?현재가:\s*`?([\d,]+)`?", block)
                if not m2:
                    print(f"DEBUG: 파싱 실패 블록: {block[:50]}...")
                    continue
                name, grade, cost_str, after_str = m2.groups()

            full_name = f"{name.strip()} {grade.strip()}"
            base = clean_base_name(name)

            # 필터링
            if exclude_keyword and exclude_keyword in full_name:
                continue
            category = classify_item(full_name)
            if only_category and category != only_category:
                continue
            if only_grade and only_grade not in grade:
                continue

            # 계절 필터링
            if only_season:
                if category == "작물" and base in CROP_DETAILS:
                    seasons = CROP_DETAILS[base]["계절"].split()
                    if only_season not in seasons:
                        print(f"DEBUG: 계절 불일치: {full_name} (요청:{only_season}, 실제:{CROP_DETAILS[base]['계절']})")
                        continue
                else:
                    continue

            try:
                cost = int(cost_str.replace(',', ''))
                after = int(after_str.replace(',', ''))
                profit_rate = (after - cost) / cost * 100
            except ValueError:
                print(f"가격 변환 오류: {cost_str} 또는 {after_str} in {block}")
                continue

            item = {
                'name': full_name,
                'cost': cost,
                'after': after,
                'profit_rate': profit_rate,
                'category': category,
                'grade': grade
            }
            if category == "작물" and base in CROP_DETAILS:
                item.update(CROP_DETAILS[base])

            result.append(item)
            print(f"DEBUG: 아이템 파싱 성공: {full_name}")

    return sorted(result, key=lambda x: x['after'], reverse=True)

# 이하 on_ready, on_message, send_top_items, 슬래시 명령 등은 동일하게 유지

@bot.event
async def on_ready():
    print(f"DEBUG: on_ready 이벤트 실행됨! 봇 유저: {bot.user}")
    try:
        await bot.tree.sync()
        print("✅ 슬래시 명령어가 성공적으로 동기화되었습니다.")
    except Exception as e:
        print(f"❌ 슬래시 명령어 동기화 실패: {e}")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.id == bot.user.id:
        return
    content = message.content or ''
    if message.embeds and not content.strip():
        extracted = []
        for embed in message.embeds:
            if embed.description:
                extracted.append(embed.description)
            if embed.fields:
                for f in embed.fields:
                    if f.value:
                        extracted.append(f.value)
        content = '\n'.join(extracted)
    if not content.strip():
        return
    if "원가" in content and ("현재가" in content or "변동후" in content):
        items = parse_items(content)
        if items:
            response = "📊 수익률 TOP 5 (자동 감지)\n"
            for i, it in enumerate(items[:5], start=1):
                response += f"{i}. {it['name']} - {it['profit_rate']:.2f}% (원가: {it['cost']}→현재가: {it['after']})\n"
            await message.channel.send(response)

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
    await send_top_items(interaction, only_category="작물", only_season=season, limit=5)

async def send_top_items(interaction, exclude_keyword=None, only_category=None, only_grade=None, only_season=None, limit=5):
    messages = [m async for m in interaction.channel.history(limit=50)]
    all_items = []
    for msg in messages:
        if msg.author.id == bot.user.id:
            continue
        content = msg.content or ''
        if msg.embeds and not content.strip():
            extracted = []
            for embed in msg.embeds:
                if embed.description:
                    extracted.append(embed.description)
                if embed.fields:
                    for f in embed.fields:
                        if f.value:
                            extracted.append(f.value)
            content = '\n'.join(extracted)
        if not content.strip():
            continue
        if "원가" in content and ("변동후" in content or "현재가" in content):
            items = parse_items(content, exclude_keyword, only_category, only_grade, only_season)
            if items:
                all_items.extend(items)
    if all_items:
        all_items.sort(key=lambda x: x['after'], reverse=True)
        resp = f"📊 {only_season} 계절 작물 판매가 TOP {limit}\n"
        for i, it in enumerate(all_items[:limit], start=1):
            resp += f"{i}. {it['name']} - 판매가: {it['after']}\n"
        await interaction.followup.send(resp)
    else:
        await interaction.followup.send(f"최근 메시지에서 '{only_season}' 계절의 작물 시세 정보를 찾을 수 없어요.")

if discord_bot_token:
    bot.run(discord_bot_token)
