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

# 접두어 제거
def clean_base_name(name: str) -> str:
    return re.sub(r'^(특상품|황금)\s*', '', name).strip()

# 아이템 분류
def classify_item(name: str) -> str:
    base = clean_base_name(name)
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(k in name for k in keywords):
            return cat
    if base in CROP_DETAILS:
        return "작물"
    return "기타"

# 아이템 파싱 함수
def parse_items(text: str, exclude_keyword=None, only_category=None, only_grade=None, only_season=None):
    items = []
    print(f"DEBUG: parse_items 호출 (only_season={only_season})")

    # 불필요 라인 제거
    lines = [l.strip().lstrip('- ').strip() for l in text.splitlines()
             if l.strip() and not l.strip().startswith(('##','가격'))]

    # 블록 분리 및 정규식 매칭
    pattern = re.compile(
        r"(?P<name>.+?)\s*\((?P<grade>\d+(?:등급|단계))\):`?원가:(?P<cost>[\d,]+)`?,`?(?:변동전:(?P<before>[\d,]+)`?,)?`?(?:변동후|현재가):(?P<after>[\d,]+)`?,?\s*`?변동률:(?P<rate>[+-]?\d+\.?\d*)%?`")
    for line in lines:
        for block in re.split(r', (?=[^,]+\(\d+)', line):
            m = pattern.search(block)
            if not m:
                print(f"DEBUG: 파싱 실패 블록: {block}")
                continue
            d = m.groupdict()
            full_name = f"{d['name'].strip()} {d['grade']}"
            base = clean_base_name(d['name'])
            category = classify_item(full_name)

            # 필터링
            if exclude_keyword and exclude_keyword in full_name: continue
            if only_category and category != only_category: continue
            if only_grade and only_grade not in d['grade']: continue
            if only_season and category == '작물' and base in CROP_DETAILS:
                seasons = CROP_DETAILS[base]['계절'].split()
                if only_season not in seasons: continue

            # 숫자 변환 및 이익률 계산
            cost = int(d['cost'].replace(',',''))
            after = int(d['after'].replace(',',''))
            rate = float(d['rate'])

            item = {
                'name': full_name,
                'cost': cost,
                'after': after,
                'profit_rate': rate,
                'category': category,
                'grade': d['grade']
            }
            if category == '작물':
                item.update(CROP_DETAILS.get(base, {}))
            items.append(item)

    return sorted(items, key=lambda x: x['after'], reverse=True)

# 봇 이벤트 핸들러
@bot.event
async def on_ready():
    print(f"DEBUG: on_ready - {bot.user}")
    await bot.tree.sync()

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.id == bot.user.id:
        return
    content = message.content or ''
    if message.embeds and not content.strip():
        content = '\n'.join(e.description or '' for e in message.embeds)
    if '원가' in content and ('현재가' in content or '변동후' in content):
        parsed = parse_items(content)
        if parsed:
            resp = '📊 수익률 TOP 5\n'
            for i, it in enumerate(parsed[:5], 1):
                resp += f"{i}. {it['name']} - {it['profit_rate']:.2f}% (원가:{it['cost']}→판매가:{it['after']})\n"
            await message.channel.send(resp)

# 슬래시 커맨드: 계절별 작물 시세
@app_commands.command(name='작물시세', description='계절별 TOP 작물 조회')
@app_commands.choices(season=[
    app_commands.Choice(name='봄', value='봄'),
    app_commands.Choice(name='여름', value='여름'),
    app_commands.Choice(name='가을', value='가을'),
    app_commands.Choice(name='겨울', value='겨울')
])
async def crop_price(interaction: discord.Interaction, season: str):
    await interaction.response.defer()
    msgs = [m async for m in interaction.channel.history(limit=50)]
    all_items = []
    for m in msgs:
        if m.author.id == bot.user.id: continue
        text = m.content or ''
        if m.embeds and not text.strip():
            text = '\n'.join(e.description or '' for e in m.embeds)
        if '원가' in text and ('변동후' in text or '현재가' in text):
            all_items.extend(parse_items(text, only_category='작물', only_season=season))
    if all_items:
        all_items.sort(key=lambda x: x['after'], reverse=True)
        msg = f"📊 {season} 계절 작물 판매가 TOP 5\n"
        for i, it in enumerate(all_items[:5], 1):
            msg += f"{i}. {it['name']} - {it['after']}\n"
        await interaction.followup.send(msg)
    else:
        await interaction.followup.send(f"'{season}' 계절 시세 정보를 찾을 수 없습니다.")

# 봇 실행
if discord_bot_token:
    bot.run(discord_bot_token)

