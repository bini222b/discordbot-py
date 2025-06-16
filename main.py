import discord
import os
import re # 정규식 파싱을 위해 추가

# --- 환경 변수에서 설정 로드 ---
# Discord 봇 토큰 (필수)
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
# 메시지를 읽어와 계산할 Discord 채널 ID (숫자, 필수)
# 이 채널에 사용자가 특정 형식의 메시지를 보내면 봇이 이를 처리합니다.
SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID"))
# 봇의 계산된 결과를 보낼 Discord 채널 ID (숫자, 필수)
RESULT_CHANNEL_ID = int(os.getenv("RESULT_CHANNEL_ID"))

# 필수 환경 변수 확인
if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
if not SOURCE_CHANNEL_ID:
    raise ValueError("SOURCE_CHANNEL_ID 환경 변수가 설정되지 않았습니다. 봇이 메시지를 읽을 채널 ID를 설정하세요.")
if not RESULT_CHANNEL_ID:
    raise ValueError("RESULT_CHANNEL_ID 환경 변수가 설정되지 않았습니다. 봇이 결과를 보낼 채널 ID를 설정하세요.")

# --- Discord 봇 설정 ---
# 봇 인텐트 설정 (메시지 내용을 읽기 위해 MESSAGE_CONTENT 활성화)
intents = discord.Intents.default()
intents.message_content = True # 메시지 내용을 읽기 위해 활성화
bot = discord.Client(intents=intents)

# --- 웹 페이지의 `fixedCropDetails`를 Python 딕셔너리로 변환 ---
# 이 데이터는 HTML 파일의 JavaScript 부분에서 복사해 온 것입니다.
# 'basePrice'는 메시지에서 '원가'를 파싱하여 동적으로 사용됩니다.
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
    "블랙베리": {"mastery": "10", "season": "봄 겨울"},
    "블루베리": {"mastery": "10", "season": "봄 겨울"},
    "라즈베리": {"mastery": "10", "season": "봄 겨울"},
    "체리": {"mastery": "10", "season": "봄 겨울"},
    "구기자": {"mastery": "10", "season": "봄 겨울"},
    "리치": {"mastery": "10", "season": "봄 여름"},
    "아보카도": {"mastery": "10", "season": "봄 여름"},
    "카람볼라": {"mastery": "10", "season": "봄 여름"},
    "오이": {"mastery": "20", "season": "여름 가을"},
    "키위": {"mastery": "20", "season": "여름 가을"},
    "망고": {"mastery": "20", "season": "여름 가을"},
    "파파야": {"mastery": "20", "season": "여름 가을"},
    "구아바": {"mastery": "30", "season": "봄 여름"},
    "두리안": {"mastery": "30", "season": "봄 여름"},
    "코코넛": {"mastery": "40", "season": "여름 가을"}
}

# --- 웹 페이지의 `calculateProfitRate` 함수를 Python으로 변환 ---
def calculate_profit_rate(cost, price):
    if cost is None or cost == 0 or price is None:
        return None # 계산 불가
    return ((price - cost) / cost) * 100

# --- 웹 페이지의 `parseCropPriceData` 로직을 Python으로 변환 (Discord 메시지 형식에 맞춰) ---
def parse_discord_message_data(message_content):
    parsed_data = []
    lines = message_content.split('\n')
    # 웹 페이지에서 사용된 정규식과 유사하게 Discord 메시지 파싱
    # 예시: "오이 (2단계): 원가: 7,592, 변동전: 8,123, 변동후: 7,999, 변동률: -1.53%"
    # 또는 "특상품 파인애플 (3단계): 원가: 9,845, 현재가: 10,160"
    regex = r"(.*?)\s*\((.*?)\단계\):\s*(?:원가:\s*([\d,]+),\s*)?(?:변동전:\s*[\d,]+,\s*)?(?:변동후:\s*([\d,]+),\s*)?(?:현재가:\s*([\d,]+))?,?\s*(?:변동률:\s*(-?[\d.]+)%)?"
    
    for line in lines:
        match = re.search(regex, line)
        if match:
            name = match.group(1).strip() if match.group(1) else None
            stage = match.group(2).strip() + '단계' if match.group(2) else None
            cost_str = match.group(3) # 원가
            price_after_str = match.group(4) # 변동후
            current_price_str = match.group(5) # 현재가
            profit_rate_str = match.group(6) # 변동률 (웹페이지에서 수익률과 혼용)

            cost = int(cost_str.replace(',', '')) if cost_str else None
            # 판매가는 '변동후' 또는 '현재가' 중 하나를 사용
            price = int(price_after_str.replace(',', '')) if price_after_str else \
                    (int(current_price_str.replace(',', '')) if current_price_str else None)
            
            profit_rate = float(profit_rate_str) if profit_rate_str else None

            # 이름에서 '특상품' 또는 '황금' 접두사 확인
            is_premium = name.startswith('특상품') if name else False
            is_gold = name.startswith('황금') if name else False

            if name and stage and cost is not None and price is not None:
                # 원본 이름에서 '특상품' 또는 '황금' 접두사를 제거하여 고정 데이터와 매칭
                base_name = name.replace('특상품 ', '').replace('황금 ', '').strip()
                
                # 수익률이 메시지에 포함되어 있지 않거나 계산이 필요한 경우 다시 계산
                if profit_rate is None:
                    profit_rate = calculate_profit_rate(cost, price)

                parsed_data.append({
                    "name": name,
                    "baseName": base_name, # 원본 이름에서 특상품/황금 제외한 이름
                    "stage": stage,
                    "cost": cost,
                    "price": price,
                    "profitRate": profit_rate,
                    "isPremium": is_premium,
                    "isGold": is_gold
                })
    return parsed_data

# Discord 메시지 길이 제한(2000자)을 고려하여 메시지를 분할하는 헬퍼 함수
def _split_message(message_parts, max_len=1900):
    current_message = []
    current_len = 0
    for part in message_parts:
        # Markdown 줄바꿈 (두 칸 띄어쓰기)을 고려하여 길이 계산
        part_len = len(part) + 2 if current_message else len(part) # 첫 줄은 줄바꿈 없음
        if current_len + part_len > max_len:
            yield "\n".join(current_message)
            current_message = [part]
            current_len = len(part)
        else:
            current_message.append(part)
            current_len += part_len
    if current_message:
        yield "\n".join(current_message)

# --- 봇 이벤트 핸들러 ---
@bot.event
async def on_ready():
    print(f'로그인 완료: {bot.user.name} (ID: {bot.user.id})')
    print('------')
    print(f"메시지를 읽을 채널 ID: {SOURCE_CHANNEL_ID}")
    print(f"결과를 보낼 채널 ID: {RESULT_CHANNEL_ID}")

@bot.event
async def on_message(message):
    # 봇 자신이 보낸 메시지는 무시
    if message.author == bot.user:
        return 

    # 봇이 메시지를 읽어와 계산할 특정 채널에서 온 메시지만 처리
    if message.channel.id == SOURCE_CHANNEL_ID:
        # '!계산' 또는 '!calc'와 같은 명령어로 시작하는 메시지만 처리하도록 할 수 있습니다.
        # if not message.content.lower().startswith('!계산'):
        #    return

        print(f"SOURCE_CHANNEL_ID({message.channel.name})에서 메시지 수신: {message.content[:50]}...") # 메시지 일부 출력

        try:
            # 메시지 내용을 파싱하여 작물 데이터 추출
            all_crop_data = parse_discord_message_data(message.content)

            if not all_crop_data:
                await message.channel.send("🚧 메시지에서 유효한 작물 시세 데이터를 찾을 수 없습니다. 형식을 확인해 주세요.")
                return

            processed_results = []
            for item in all_crop_data:
                # `baseName`을 사용하여 `fixed_crop_details`에서 숙련도/계절 정보를 가져옵니다.
                details = fixed_crop_details.get(item["baseName"], {"mastery": "-", "season": "-"})
                
                # profitRate가 메시지에서 직접 파싱되었거나, 아니면 여기서 다시 계산
                profit_rate = item["profitRate"]
                if profit_rate is None:
                    profit_rate = calculate_profit_rate(item["cost"], item["price"])
                
                processed_results.append({
                    "name": item["name"],
                    "stage": item["stage"],
                    "cost": item["cost"],
                    "price": item["price"],
                    "profitRate": profit_rate,
                    "mastery": details["mastery"],
                    "season": details["season"],
                    "isPremium": item["isPremium"],
                    "isGold": item["isGold"]
                })
            
            # 수익률 기준으로 내림차순 정렬 (웹 페이지와 동일)
            # None 값은 가장 아래로 정렬되도록 처리합니다.
            processed_results.sort(key=lambda x: x["profitRate"] if x["profitRate"] is not None else -float('inf'), reverse=True)
            
            # Discord 메시지 생성 (상위 N개만 표시)
            message_parts = ["**📈 작물 시세 분석 결과 📉**", "---"]

            if processed_results:
                # 상위 10개 작물만 전송 (개수는 조정 가능)
                for i, crop in enumerate(processed_results[:10]): 
                    premium_tag = " ✨(특상품)" if crop["isPremium"] else ""
                    gold_tag = " 🌟(황금)" if crop["isGold"] else ""
                    
                    profit_display = f"{crop['profitRate']:.2f}%" if crop['profitRate'] is not None else "계산 불가"
                    
                    message_parts.append(
                        f"{i+1}. **{crop['name']}** (단계: {crop['stage']}, 원가: {crop['cost']:,}원, 판매가: {crop['price']:,}원)"
                        f"{premium_tag}{gold_tag} - **수익률: {profit_display}** "
                        f"(숙련도: {crop['mastery']}, 계절: {crop['season']})"
                    )
            else:
                message_parts.append("계산할 수 있는 유효한 작물 데이터가 없습니다.")

            # 결과를 보낼 채널 찾기
            result_channel = bot.get_channel(RESULT_CHANNEL_ID)
            if result_channel:
                for chunk in _split_message(message_parts):
                    await result_channel.send(chunk)
                print("계산된 데이터를 Discord 채널로 전송했습니다.")
            else:
                print(f"오류: 결과 채널 ID({RESULT_CHANNEL_ID})를 찾을 수 없습니다. 메시지를 보낼 수 없습니다.")

        except Exception as e:
            print(f"메시지 처리 중 오류 발생: {e}")
            await message.channel.send(f"⚠️ **메시지 처리 중 오류가 발생했습니다:** {e}")

# 봇 실행
if __name__ == "__main__":
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except discord.errors.LoginFailure as e:
        print(f"봇 토큰 오류: {e}. DISCORD_BOT_TOKEN 환경 변수를 확인하세요.")
    except Exception as e:
        print(f"봇 실행 중 치명적인 오류 발생: {e}")
