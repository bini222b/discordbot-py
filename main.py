
import discord
from discord.ext import commands
import os
import re

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

CATEGORY_KEYWORDS = {
    "요리": ["요리", "토르타", "타코", "또르띠아", "부리토", "나쵸", "케사디야", "토르티야", "피클", "스튜", "수프", "볶음"],
    "광물": ["원석", "블록", "광석", "수정", "다이아몬드", "에메랄드", "금", "은", "철"],
    "물고기": ["도미", "연어", "가물치", "숭어", "잉어", "정어리", "개복치", "금붕어", "농어", "다랑어", "랍스터", "만타가오리", "메기", "문어", "아귀", "줄돔", "해파리", "흰동가리", "블루탱", "강꼬치고기", "뱀장어"]
}

def classify_item(name):
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in name for keyword in keywords):
            return category
    return "작물"

def parse_items(text, exclude_keyword=None, only_category=None):
    pattern = r"(.+?)\s*\((\d+등급|\d+단계)\):\s*원가:\s*([\d,]+).*?(?:변동후|현재가):\s*([\d,]+)"
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

    return sorted(result, key=lambda x: x['profit_rate'], reverse=True)[:5]

@bot.event
async def on_ready():
    print(f"봇 작동 중: {bot.user}")

@bot.command()
async def 황금제외(ctx):
    await analyze(ctx, exclude_keyword="황금")

@bot.command()
async def 요리만(ctx):
    await analyze(ctx, only_category="요리")

@bot.command()
async def 광물만(ctx):
    await analyze(ctx, only_category="광물")

@bot.command()
async def 물고기만(ctx):
    await analyze(ctx, only_category="물고기")

@bot.command()
async def 작물만(ctx):
    await analyze(ctx, only_category="작물")

async def analyze(ctx, exclude_keyword=None, only_category=None):
    messages = await ctx.channel.history(limit=50).flatten()
    for msg in messages:
        if msg.author.bot:
            continue
        if "원가" in msg.content and ("변동후" in msg.content or "현재가" in msg.content):
            items = parse_items(msg.content, exclude_keyword, only_category)
            if items:
                response = f"📊 수익률 TOP 5"
                if only_category:
                    response += f" - {only_category}"
                if exclude_keyword:
                    response += f' ("{exclude_keyword}" 제외)'
                response += "\\n"

                for i, item in enumerate(items, start=1):  # ✅ 여기가 올바른 들여쓰기
                    response += f"{i}. {item['name']} - {item['profit_rate']:.2f}% (원가: {item['cost']} → 현재가: {item['after']})\\n"

                await ctx.send(response)
                return

    await ctx.send("최근 메시지에서 시세 정보를 찾을 수 없어요.")

