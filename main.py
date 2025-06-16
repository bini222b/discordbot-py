import discord
from discord.ext import commands
import os
import re
from discord import app_commands

# 로깅 설정
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

# 디버그 로그: 봇 시작 지점
logging.debug("봇 스크립트 시작")

# 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# 토큰 로드
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not DISCORD_BOT_TOKEN:
    logging.error('DISCORD_BOT_TOKEN 환경 변수가 설정되지 않았습니다!')

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

# 이름 정리
def clean_base_name(name: str) -> str:
    return re.sub(r'^(특상품|황금)\s*', '', name).strip()

# 분류
def classify_item(name: str) -> str:
    base = clean_base_name(name)
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(k in name for k in kws):
            return cat
    if base in CROP_DETAILS:
        return '작물'
    return '기타'

# 파싱
def parse_items(text: str, exclude_keyword=None, only_category=None, only_grade=None, only_season=None):
    items = []
    logging.debug(f'parse_items 호출 (only_season={only_season})')

    lines = [l.strip().lstrip('- ') for l in text.splitlines() if l.strip() and not l.startswith(('##','가격'))]
    pattern = re.compile(
        r"(?P<name>.+?)\s*\((?P<grade>\d+(?:등급|단계))\):`?원가:(?P<cost>[\d,]+)`?,?`?(?:변동전:(?P<before>[\d,]+)`?,)?`?(?:변동후|현재가):(?P<after>[\d,]+)`?,?\s*`?변동률:(?P<rate>[+-]?\d+\.?\d*)%?`")

    for line in lines:
        for block in re.split(r', (?=[^,]+\(\d+\))', line):
            m = pattern.search(block)
            if not m:
                logging.debug(f'파싱 실패 블록: {block}')
                continue
            d = m.groupdict()
            full = f"{d['name'].strip()} {d['grade']}"
            base = clean_base_name(d['name'])
            cat = classify_item(full)

            # 필터링
            if exclude_keyword and exclude_keyword in full: continue
            if only_category and cat != only_category: continue
            if only_grade and only_grade not in d['grade']: continue
            if only_season and cat == '작물' and base in CROP_DETAILS:
                if only_season not in CROP_DETAILS[base]['계절'].split(): continue

            cost = int(d['cost'].replace(',',''))
            after = int(d['after'].replace(',',''))
            rate = float(d['rate'])

            item = {
                'name': full,
                'cost': cost,
                'after': after,
                'profit_rate': rate,
                'category': cat,
                'grade': d['grade']
            }
            if cat == '작물':
                item.update(CROP_DETAILS.get(base, {}))
            items.append(item)

    return sorted(items, key=lambda x: x['after'], reverse=True)

# Discord 이벤트
@bot.event
async def on_ready():
    logging.debug(f'on_ready - {bot.user}')
    await bot.tree.sync()

# 메시지 이벤트 (판매 시세 자동 응답)
@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.id == bot.user.id:
        return

    content = message.content or ''
    if message.embeds and not content:
        content = '\n'.join(e.description or '' for e in message.embeds)

    if '원가' in content and ('현재가' in content or '변동후' in content):
        parsed = parse_items(content)
        if parsed:
            resp = '📊 수익률 TOP 5\n'
            for i, it in enumerate(parsed[:5], 1):
                resp += f"{i}. {it['name']} - {it['profit_rate']:.2f}% (원가:{it['cost']}→판매가:{it['after']})\n"
            await message.channel.send(resp)

# 슬래시 커맨드: 계절별 작물 시세 (공개 응답)
@bot.tree.command(name='작물시세', description='계절별 TOP 작물 조회')
@app_commands.choices(season=[
    app_commands.Choice(name='봄', value='봄'),
    app_commands.Choice(name='여름', value='여름'),
    app_commands.Choice(name='가을', value='가을'),
    app_commands.Choice(name='겨울', value='겨울')
])
async def crop_price(interaction: discord.Interaction, season: str):
    logging.debug(f'/작물시세 사용: season={season}')
    # 채널 최근 메시지 가져오기
    msgs = [m async for m in interaction.channel.history(limit=100)]
    all_items = []
    for m in msgs:
        if m.author.id == bot.user.id:
            continue
        text = m.content or ''
        if m.embeds and not text:
            text = '\n'.join(e.description or '' for e in m.embeds)
        if '원가' in text and ('변동후' in text or '현재가' in text):
            all_items.extend(parse_items(text, only_category='작물', only_season=season))

    if not all_items:
        await interaction.response.send_message(f"'{season}' 계절 시세 정보를 찾을 수 없습니다.", ephemeral=False)
        return

    all_items.sort(key=lambda x: x['after'], reverse=True)
    msg = f"📊 {season} 계절 작물 판매가 TOP 5\n"
    for i, it in enumerate(all_items[:5], 1):
        msg += f"{i}. {it['name']} - {it['after']}\n"
    await interaction.response.send_message(msg, ephemeral=False)

# 봇 실행
if DISCORD_BOT_TOKEN:
    bot.run(DISCORD_BOT_TOKEN)
