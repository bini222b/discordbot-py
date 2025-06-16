import discord
import os
import re

# --- 환경 변수에서 설정 로드 ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID"))
RESULT_CHANNEL_ID = int(os.getenv("RESULT_CHANNEL_ID"))

# 필수 환경 변수 확인
if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
if not SOURCE_CHANNEL_ID:
    raise ValueError("SOURCE_CHANNEL_ID 환경 변수가 설정되지 않았습니다. 봇이 메시지를 읽을 채널 ID를 설정하세요.")
if not RESULT_CHANNEL_ID:
    raise ValueError("RESULT_CHANNEL_ID 환경 변수가 설정되지 않았습니다. 봇이 결과를 보낼 채널 ID를 설정하세요.")

# --- Discord 봇 설정 ---
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# --- 웹 페이지의 `fixedCropDetails`를 Python 딕셔너리로 변환 ---
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

# --- Discord 메시지 내용을 파싱하는 함수 수정 ---
def parse_discord_message_data(message_content):
    parsed_data = []
    lines = message_content.splitlines()

    # 예전보다 훨씬 단순한 정규식(변동후 또는 마지막 숫자)
    regex = re.compile(
        r"^\s*(?P<name>.+?)\s*\((?P<stage>\d+)단계\)\s*:\s*"
        r"원가\s*:\s*(?P<cost>[\d,]+)"
        r"(?:\s*,\s*(?:변동후|현재가)\s*:\s*(?P<price>[\d,]+))?"
    )

    for raw in lines:
        # 1) 마크다운 불필요 문구 정리: 앞쪽의 '- ' 제거, backtick 제거
        line = raw.strip()
        line = re.sub(r"^[-*]\s*", "", line)   # 맨 앞의 '- ' 또는 '* ' 제거
        line = line.replace("`", "")           # backtick 전부 제거
        if not line:
            continue

        m = regex.match(line)
        if not m:
            print(f"경고: 형식 불일치 - {line}")
            continue

        name   = m.group("name").strip()
        stage  = f"{m.group('stage')}단계"
        cost_s = m.group("cost")
        price_s= m.group("price")

        # 변동후 그룹에 없으면 숫자 목록의 마지막을 fallback
        if not price_s:
            nums = re.findall(r"[\d,]+", line)
            price_s = nums[-1] if len(nums) >= 2 else None
        if not price_s:
            print(f"경고: 판매가 추출 실패 - {line}")
            continue

        cost  = int(cost_s.replace(",", ""))
        price = int(price_s.replace(",", ""))
        profit = calculate_profit_rate(cost, price)

        is_premium = name.startswith("특상품")
        is_gold    = name.startswith("황금")
        base_name  = name.replace("특상품 ", "").replace("황금 ", "").strip()

        parsed_data.append({
            "name":       name,
            "baseName":   base_name,
            "stage":      stage,
            "cost":       cost,
            "price":      price,
            "profitRate": profit,
            "isPremium":  is_premium,
            "isGold":     is_gold
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
        # 특정 명령어로 시작하는 메시지만 처리하려면 주석 해제 (예: !시세 또는 !계산)
        # if not message.content.lower().startswith('!시세'):
        #     return

        print(f"SOURCE_CHANNEL_ID({message.channel.name})에서 메시지 수신: {message.content[:100]}...") # 메시지 일부 출력

        try:
            # 메시지 내용을 파싱하여 작물 데이터 추출
            all_crop_data = parse_discord_message_data(message.content)

            if not all_crop_data:
                await message.channel.send("🚧 메시지에서 유효한 작물 시세 데이터를 찾을 수 없습니다. 형식을 확인해 주세요.",
                                           reference=message.to_reference()) # 원본 메시지에 답장
                return

            processed_results = []
            for item in all_crop_data:
                # `baseName`을 사용하여 `fixed_crop_details`에서 숙련도/계절 정보를 가져옵니다.
                details = fixed_crop_details.get(item["baseName"], {"mastery": "-", "season": "-"})
                
                # profitRate가 메시지에서 직접 파싱되었거나, 아니면 여기서 다시 계산
                profit_rate = item["profitRate"]
                
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
            message_parts = [
                "**📈 작물 시세 분석 결과 📉**", 
                f"*(원본 메시지: {message.jump_url})*", # 원본 메시지 링크 추가
                "---"
            ]

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
            print(f"메시지 처리 중 알 수 없는 오류 발생: {e}")
            await message.channel.send(f"⚠️ **메시지 처리 중 오류가 발생했습니다:** {e}",
                                       reference=message.to_reference()) # 원본 메시지에 답장

# 봇 실행
if __name__ == "__main__":
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except discord.errors.LoginFailure as e:
        print(f"봇 토큰 오류: {e}. DISCORD_BOT_TOKEN 환경 변수를 확인하세요.")
    except Exception as e:
        print(f"봇 실행 중 치명적인 오류 발생: {e}")
