import discord
from discord.ext import commands, tasks
import os
import re

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

CATEGORY_KEYWORDS = {
    "요리": ["요리", "토르타", "타코", "또르띠아", "부리토", "나쵸", "케사디야", "토르티야", "피클", "스튜", "수프", "볶음", "카레", "샌드위치"],
    "광물": ["원석", "블록", "광석", "수정", "다이아몬드", "에메랄드", "금", "은", "철"],
    "물고기": ["도미", "연어", "숭어", "잉어", "정어리", "개복치", "금붕어", "농어", "다랑어", "랍스터", "만타가오리", "메기", "문어", "아귀", "줄돔", "해파리", "흰동가리", "블루탱", "강꼬치고기", "뱀장어"]
}

def classify_item(name):
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in name for keyword in keywords):
            return category
    return "작물"

def parse_items(text, exclude_keyword=None, only_category=None):
    pattern = r"(.+?)\s*\((\d+등급|\d+단계)\):.*?원가:\s*`?([\d,]+)`?.*?(?:변동후|현재가):\s*`?([\d,]+)`?"
    matches = re.findall(pattern, text)
    result = []

    for name, grade, cost_str, after_str in matches:
        full_name = f"{name.strip()} {grade.strip()}"
        if exclude_keyword and exclude_keyword in full_name:
            continue
        category = classify_item(full_name)
        if only_category and category != only_category:
            continue
        try:
            cost = int(cost_str.replace(",", ""))
            after = int(after_str.replace(",", ""))
            profit_rate = ((after - cost) / cost) * 100
            result.append({
                'name': full_name,
                'cost': cost,
                'after': after,
                'profit_rate': profit_rate,
                'category': category
            })
        except:
            continue

    return sorted(result, key=lambda x: x['profit_rate'], reverse=True)

@bot.event
async def on_ready():
    print(f"✅ 봇 작동 중: {bot.user}")
    auto_scan.start()

async def send_top_items(channel, exclude_keyword=None, only_category=None, limit=5):
    messages = [m async for m in channel.history(limit=50)]
    for msg in messages:
        if msg.author.bot:
            continue

        content = msg.content
        if not content and msg.embeds:
            content = msg.embeds[0].description or ""

        if "원가" in content and ("변동후" in content or "현재가" in content):
            items = parse_items(content, exclude_keyword, only_category)
            if items:
                response = f"📊 수익률 TOP {limit}"
                if only_category:
                    response += f" - {only_category}"
                if exclude_keyword:
                    response += f' ("{exclude_keyword}" 제외)'
                response += "\n"

                for i, item in enumerate(items[:limit], start=1):
                    response += f"{i}. {item['name']} - {item['profit_rate']:.2f}% (원가: {item['cost']} → 현재가: {item['after']})\n"

                await channel.send(response)
                return
    await channel.send("최근 메시지에서 시세 정보를 찾을 수 없어요.")

@bot.command()
async def 작물(ctx):
    if ctx.channel.name != "작물-시세":
        await ctx.send("❗ 이 명령어는 #작물-시세 채널에서만 사용할 수 있어요.")
        return
    await send_top_items(ctx.channel, only_category="작물")

@bot.command()
async def 요리(ctx):
    if ctx.channel.name != "요리-시세":
        await ctx.send("❗ 이 명령어는 #요리-시세 채널에서만 사용할 수 있어요.")
        return
    await send_top_items(ctx.channel, only_category="요리")

@bot.command()
async def 광물(ctx):
    if ctx.channel.name != "광물-시세":
        await ctx.send("❗ 이 명령어는 #광물-시세 채널에서만 사용할 수 있어요.")
        return
    await send_top_items(ctx.channel, only_category="광물")

@bot.command()
async def 물고기(ctx):
    if ctx.channel.name != "물고기-시세":
        await ctx.send("❗ 이 명령어는 #물고기-시세 채널에서만 사용할 수 있어요.")
        return
    await send_top_items(ctx.channel, only_category="물고기")

@bot.command()
async def 황금제외(ctx):
    await send_top_items(ctx.channel, exclude_keyword="황금")

@bot.command()
async def top10(ctx):
    await send_top_items(ctx.channel, limit=10)

@tasks.loop(minutes=2)
async def auto_scan():
    channel_ids = os.getenv("DISCORD_CHANNEL_IDS", "").split(",")
    for cid in channel_ids:
        try:
            channel = bot.get_channel(int(cid.strip()))
            if channel:
                await send_top_items(channel, limit=5)
        except Exception as e:
            print(f"❌ 채널 오류: {cid}, 에러: {e}")

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
