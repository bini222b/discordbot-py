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
    
    # DEBUG: 전처리 후 cleaned_lines를 parse_items 호출 직후에 출력
    # (이미 send_top_items에서 출력되므로 여기서는 생략, 필요시 주석 해제)
    # print(f"DEBUG: parse_items - 전처리 후 cleaned_lines ({len(cleaned_lines)}개): {cleaned_lines[:5]}...")
    
    for line_content in cleaned_lines:
        item_substrings = re.split(r', *(?=[가-힣\s]+?\s*\(\d+등급|\d+단계\))', line_content)
        
        for block in item_substrings:
            block = block.strip()
            if not block:
                continue

            pattern1 = r"(.+?)\s*\((\d+등급|\d+단계)\):\s*`?원가:\s*([\d,]+)`?,\s*`?변동전:\s*([\d,]+)`?,\s*`?변동후:\s*([\d,]+)`?,\s*`?변동률:.*?"
            match = re.search(pattern1, block)
            
            name, grade, cost_str, after_str = None, None, None, None # 초기화
            source_type = "알 수 없음"

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
                    # 파싱 실패 블록을 DEBUG 로그로 출력
                    print(f"DEBUG: 파싱 실패 블록 (parse_items): {block[:100]}...")
                    continue # 두 패턴 모두 매칭되지 않으면 스킵

            full_name = f"{name.strip()} {grade.strip()}"
            base_name_for_lookup = name.strip().replace("특상품 ", "").replace("황금 ", "")

            # DEBUG: 파싱된 아이템 기본 정보 확인
            print(f"DEBUG: 파싱된 아이템: {full_name}, 카테고리: {classify_item(full_name)}")

            if exclude_keyword and exclude_keyword in full_name:
                print(f"DEBUG: 제외 키워드로 스킵: {full_name}")
                continue
            
            category = classify_item(full_name) # 여기서 한번 더 분류 (위에서 한것과 같음)
            if only_category and category != only_category:
                print(f"DEBUG: 카테고리 불일치로 스킵: {full_name} (요청: {only_category}, 실제: {category})")
                continue
            if only_grade and only_grade not in grade:
                print(f"DEBUG: 등급 불일치로 스킵: {full_name} (요청: {only_grade}, 실제: {grade})")
                continue
            
            # 계절 필터링 로직 (상세 DEBUG 로그 추가)
            if only_season:
                print(f"DEBUG: 계절 필터링 적용 중. 요청 계절: {only_season}. 아이템: {full_name}")
                if category == "작물" and base_name_for_lookup in CROP_DETAILS:
                    item_seasons_str = CROP_DETAILS[base_name_for_lookup].get("계절", "")
                    item_seasons = item_seasons_str.split() # "가을 겨울" -> ["가을", "겨울"]
                    print(f"DEBUG: {full_name}의 CROP_DETAILS 계절: '{item_seasons_str}', 분리된 계절: {item_seasons}")
                    if only_season not in item_seasons:
                        print(f"DEBUG: 계절 불일치로 스킵: {full_name} (요청: {only_season}, 실제: {item_seasons_str})")
                        continue # 요청된 계절에 해당하지 않으면 스킵
                    else:
                        print(f"DEBUG: 계절 일치: {full_name} (요청: {only_season}, 실제: {item_seasons_str})")
                else:
                    # 작물인데 CROP_DETAILS에 없거나, 작물이 아닌 경우 계절 필터링에서 제외
                    print(f"DEBUG: 작물 아님/DETAILS 없음 (계절 필터링): {full_name} (카테고리: {category})")
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
                print(f"DEBUG: 아이템 추가됨: {full_name}") # 아이템이 최종 추가될 때 로그
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
        print(f"DEBUG: 임베드 메시지 감지. 임베드 수: {len(message.embeds)}")
        extracted_embed_content = []
        for embed in message.embeds:
            if embed.description:
                extracted_embed_content.append(embed.description)
                print(f"DEBUG: 임베드 description 내용 추출 ({len(embed.description)}자): {embed.description[:100]}...")
            if embed.fields:
                for field in embed.fields:
                    if field.value:
                        extracted_embed_content.append(field.value)
                        print(f"DEBUG: 임베드 field value 내용 추출 ({len(field.value)}자): {field.value[:100]}...")
        content = "\n".join(extracted_embed_content)
        
    if not content.strip():
        print("DEBUG: 최종 추출된 메시지 내용 없음. 스킵.")
        return

    print(f"DEBUG: on_message 최종 content (첫 200자):\n{content[:200]}")
    
    if "원가" in content and ("현재가" in content or "변동후" in content):
        print("DEBUG: 자동 감지 - '원가' 및 '현재가'/'변동후' 키워드 감지됨.")
        items = parse_items(content)
        if items:
            print(f"DEBUG: 자동 감지에서 {len(items)}개 아이템 파싱 성공.")
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
            print("DEBUG: 자동 감지 응답 전송.")
            await message.channel.send(response)
        else:
            print("DEBUG: 자동 감지 - 파싱된 아이템 없음. (정규식/필터링 문제일 수 있음)")
    else:
        print("DEBUG: 자동 감지 - 시세 키워드 불일치.")

async def send_top_items(interaction: discord.Interaction, exclude_keyword=None, only_category=None, only_grade=None, only_season=None, limit=5):
    print(f"DEBUG: send_top_items 호출됨. only_season: {only_season}")
    messages = [m async for m in interaction.channel.history(limit=50)] # 최근 50개 메시지 조회
    all_filtered_items = []

    for msg in messages:
        if msg.author.id == bot.user.id:
            print(f"DEBUG: 본인 봇 메시지 스킵: {msg.content[:50]}...")
            continue 
        
        content = msg.content
        if not content and msg.embeds:
            print(f"DEBUG: (send_top_items) 임베드 메시지 감지. 임베드 수: {len(msg.embeds)}")
            extracted_embed_content = []
            for embed in msg.embeds:
                if embed.description:
                    extracted_embed_content.append(embed.description)
                    print(f"DEBUG: (send_top_items) 임베드 description 내용 추출 ({len(embed.description)}자): {embed.description[:100]}...")
                if embed.fields:
                    for field in embed.fields:
                        if field.value:
                            extracted_embed_content.append(field.value)
                            print(f"DEBUG: (send_top_items) 임베드 field value 내용 추출 ({len(field.value)}자): {field.value[:100]}...")
            content = "\n".join(extracted_embed_content)

        if not content.strip():
            print("DEBUG: (send_top_items) 최종 추출된 메시지 내용 없음. 스킵.")
            continue

        print(f"DEBUG: (send_top_items) 메시지 내용 첫 200자:\n{content[:200]}")

        if "원가" in content and ("변동후" in content or "현재가" in content):
            print(f"DEBUG: (send_top_items) 시세 키워드 감지됨. 메시지 길이: {len(content)}")
            print(f"DEBUG: parse_items 호출됨. only_season: {only_season}. 원본 텍스트 첫 100자:\n{content[:100]}...") # 추가된 로그
            items = parse_items(content, exclude_keyword, only_category, only_grade, only_season)
            if items:
                print(f"DEBUG: (send_top_items) {len(items)}개 아이템 파싱 성공. (season: {only_season})")
                all_filtered_items.extend(items)
            else:
                print(f"DEBUG: (send_top_items) 파싱된 아이템 없음. (season: {only_season})")
        else:
            print("DEBUG: (send_top_items) 시세 키워드 불일치.")
    
    if all_filtered_items:
        print(f"DEBUG: 총 {len(all_filtered_items)}개 필터링된 아이템 발견. 최종 응답 생성.")
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
            await interaction.followup.send("결과가 너무 많아 일부만 표시됩니다.")
            await interaction.followup.send(response[:1900] + "...")
        else:
            await interaction.followup.send(response)
    else:
        print(f"DEBUG: (send_top_items) 필터링된 아이템 없음. '찾을 수 없어요' 메시지 전송.")
        await interaction.followup.send(f"최근 메시지에서 '{only_season}' 계절의 작물 시세 정보를 찾을 수 없어요. (최근 50개 메시지 확인)")


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

try:
    print("DEBUG: bot.run() 호출 시도 중...")
    bot.run(discord_bot_token)
except Exception as e:
    print(f"CRITICAL ERROR: 봇 실행 중 치명적인 오류 발생: {e}")
