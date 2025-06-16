import discord
import os
import re
from discord.ext import commands

# --- 환경 변수 설정 ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID") or 0)  # 시세 알림 메시지가 올라오는 채널 ID

if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
if not SOURCE_CHANNEL_ID:
    raise ValueError("SOURCE_CHANNEL_ID 환경 변수가 설정되지 않았습니다.")

# --- 봇 설정 ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- 작물 기본 정보 ---
fixed_crop_details = {
    "마늘": {"mastery": "-", "season": "여름 가을"},
    "홉": {"mastery": "-", "season": "봄 겨울"},
    "가지": {"mastery": "-", "season": "여름 가을"},
    "포도": {"mastery": "-", "season": "가을 겨울"},
    "고추": {"mastery": "-", "season": "봄 여름"},
    "옥수수": {"mastery": "-", "season": "여름 가을"},
    "토마토": {"mastery": "-", "season": "봄 겨울"},
    "양배추": {"mastery": "-", "season": "봄 여름"},
    "배추": {"mastery": "-", "season": "봄 겨울"},
    "파인애플": {"mastery": "-", "season": "여름 가을"},
    # 숙련도 10
    "블랙베리": {"mastery": "10", "season": "봄 겨울"},
    "블루베리": {"mastery": "10", "season": "봄 겨울"},
    "라즈베리": {"mastery": "10", "season": "봄 겨울"},
    "체리": {"mastery": "10", "season": "봄 겨울"},
    "구기자": {"mastery": "10", "season": "봄 겨울"},
    "리치": {"mastery": "10", "season": "봄 여름"},
    "아보카도": {"mastery": "10", "season": "봄 여름"},
    "카람볼라": {"mastery": "10", "season": "봄 여름"},
    # 숙련도 20
    "오이": {"mastery": "20", "season": "여름 가을"},
    "키위": {"mastery": "20", "season": "여름 가을"},
    "망고": {"mastery": "20", "season": "여름 가을"},
    "파파야": {"mastery": "20", "season": "여름 가을"},
    # 숙련도 30
    "구아바": {"mastery": "30", "season": "봄 여름"},
    "두리안": {"mastery": "30", "season": "봄 여름"},
    # 숙련도 40
    "코코넛": {"mastery": "40", "season": "여름 가을"}
}

# --- 수익률 계산 ---
def calculate_profit_rate(cost, price):
    if cost == 0:
        return None
    return (price - cost) / cost * 100

# --- 메시지 파싱 ---
def parse_discord_message_data(content: str):
    parsed = []
    regex = re.compile(r"^\s*(?P<name>.+?)\s*\((?P<stage>\d+)단계\).*?원가\s*:\s*(?P<cost>[\d,]+).*?(?:변동후|현재가)\s*:\s*(?P<price>[\d,]+)")
    for line in content.splitlines():
        text = line.strip().lstrip('- ').replace('`', '').strip()
        m = regex.match(text)
        if not m:
            continue
        name  = m['name']
        base  = name.replace("특상품 ","").replace("황금 ","")
        cost  = int(m['cost'].replace(',', ''))
        price = int(m['price'].replace(',', ''))
        profit = calculate_profit_rate(cost, price)
        prem = name.startswith("특상품")
        gold = name.startswith("황금")
        parsed.append({'name': name, 'base': base, 'stage': f"{m['stage']}단계", 'cost': cost, 'price': price, 'profit': profit, 'prem': prem, 'gold': gold})
    return parsed

# --- 커맨드 처리 ---
@bot.command(name="작물시세")
async def crop(ctx, season: str):
    # 알림 채널에서 최근 알림 메시지 검색
    channel = bot.get_channel(SOURCE_CHANNEL_ID)
    alert = None
    async for msg in channel.history(limit=50):
        # embed 메시지 지원
        if msg.author.bot:
            if msg.embeds:
                desc = msg.embeds[0].description or ''
                if '🏪 무역상점1 가격 변동 알림' in desc:
                    alert = desc
                    break
            elif '🏪 무역상점1 가격 변동 알림' in msg.content:
                alert = msg.content
                break
    if not alert:
        return await ctx.send("❗ 최근 알림 메시지를 찾을 수 없습니다.")

    # 상승 섹션 추출
    try:
        data_text = alert.split('📈 가격 상승된 아이템:')[1]
    except IndexError:
        return await ctx.send("❗ 알림 형식이 올바르지 않습니다.")

    all_data = parse_discord_message_data(data_text)
    # 필터: 특상품/황금 제외 & 계절 매칭
    filtered = [c for c in all_data if not c['prem'] and not c['gold'] and season in fixed_crop_details.get(c['base'], {}).get('season', '')]
    if not filtered:
        return await ctx.send(f"❗ '{season}' 계절 작물이 없습니다.")
    # 판매가 기준 내림차순 TOP10
    top10 = sorted(filtered, key=lambda x: x['price'], reverse=True)[:10]

    lines = [f"**🏪 무역상점1 {season} 계절 TOP10 (판매가 순)**", "---"]
    for i, c in enumerate(top10, 1):
        info = fixed_crop_details.get(c['base'], {'mastery': '-', 'season': '-'})
        lines.append(f"{i}. **{c['name']}** (단계:{c['stage']}, 원가:{c['cost']:,}원, 판매가:{c['price']:,}원) 수익률:{c['profit']:.2f}% (숙련도:{info['mastery']}, 계절:{info['season']})")

    await ctx.send("\n".join(lines))

# --- 봇 실행 ---
bot.run(DISCORD_BOT_TOKEN)
