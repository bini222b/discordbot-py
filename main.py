import discord
import os
import re
from discord.ext import commands
from discord import app_commands

# --- 환경 변수에서 설정 로드 ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID") or 0)  # 슬래시 명령어를 동기화할 서버 ID

# 봇 권한 설정
intents = discord.Intents.default()
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
def parse_discord_message_data(message_content: str):
    parsed = []
    regex = re.compile(r"^\s*(?P<name>.+?)\s*\((?P<stage>\d+)단계\).*?원가\s*:\s*(?P<cost>[\d,]+).*?(?:변동후|현재가)\s*:\s*(?P<price>[\d,]+)")
    for line in message_content.splitlines():
        text = line.strip().replace('`','').lstrip('- ').strip()
        m = regex.match(text)
        if not m:
            continue
        name = m['name'].strip()
        stage = f"{m['stage']}단계"
        cost = int(m['cost'].replace(',',''))
        price = int(m['price'].replace(',',''))
        profit = calculate_profit_rate(cost, price)
        is_prem = name.startswith("특상품")
        is_gold = name.startswith("황금")
        base = name.replace("특상품 ","").replace("황금 ","")
        parsed.append({"name":name,"base":base,"stage":stage,"cost":cost,"price":price,"profit":profit,"prem":is_prem,"gold":is_gold})
    return parsed

# --- 슬래시 커맨드 등록 ---
class CropCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="작물시세", description="계절별 작물 시세 TOP10 조회")
    @app_commands.describe(
        season="봄, 여름, 가을, 겨울 중 하나"
    )
    async def crop(self, interaction: discord.Interaction, season: str):
        await interaction.response.defer()
        # 최근 채팅 히스토리에서 Trade alert 메시지 찾기
        channel = interaction.channel
        alert_msg = None
        async for msg in channel.history(limit=20):
            if msg.author.bot and '🏪 무역상점1 가격 변동 알림' in msg.content:
                alert_msg = msg.content
                break
        if not alert_msg:
            return await interaction.followup.send("❗ 최근 알림 메시지를 찾을 수 없습니다.")

        # 알림 본문에서 ‘📈 가격 상승된 아이템:’ 뒤부터 파싱
        parts = alert_msg.split('📈 가격 상승된 아이템:')
        if len(parts) < 2:
            return await interaction.followup.send("❗ 알림 형식이 올바르지 않습니다.")
        data_text = parts[1]
        all_data = parse_discord_message_data(data_text)
        # 필터링: 특상품·황금 제외, 계절 포함
        filtered = [c for c in all_data if not c['prem'] and not c['gold'] and season in fixed_crop_details.get(c['base'],{}).get('season','')]
        if not filtered:
            return await interaction.followup.send(f"❗ '{season}' 계절의 작물을 찾을 수 없습니다.")
        # 판매가 기준 내림차순 TOP10
        top10 = sorted(filtered, key=lambda x: x['price'], reverse=True)[:10]
        lines = [f"**🏪 무역상점1 {season} 계절 TOP10 (판매가 순)**", "---"]
        for i, c in enumerate(top10,1):
            info = fixed_crop_details.get(c['base'],{'mastery':'-','season':'-'})
            lines.append(f"{i}. **{c['name']}** (단계:{c['stage']}, 원가:{c['cost']:,}원, 판매가:{c['price']:,}원) 수익률:{c['profit']:.2f}% (숙련도:{info['mastery']}, 계절:{info['season']})")
        await interaction.followup.send("\n".join(lines))

# Cog 추가 및 동기화
@bot.event
async def on_ready():
    bot.tree.copy_global_to(guild=discord.Object(id=GUILD_ID))
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Logged in as {bot.user} and synced slash commands.")

bot.add_cog(CropCog(bot))

# --- 봇 실행 ---
bot.run(TOKEN)
