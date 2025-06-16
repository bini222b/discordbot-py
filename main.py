import discord
import os
import re

# --- 환경 변수에서 설정 로드 ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID") or 0)
RESULT_CHANNEL_ID = int(os.getenv("RESULT_CHANNEL_ID") or 0)

# 필수 환경 변수 확인
if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
if not SOURCE_CHANNEL_ID:
    raise ValueError("SOURCE_CHANNEL_ID 환경 변수가 설정되지 않았습니다. 메시지를 읽을 채널 ID를 설정하세요.")
if not RESULT_CHANNEL_ID:
    raise ValueError("RESULT_CHANNEL_ID 환경 변수가 설정되지 않았습니다. 결과를 보낼 채널 ID를 설정하세요.")

# --- Discord 봇 설정 ---
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

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

# --- 수익률 계산 함수 ---
def calculate_profit_rate(cost, price):
    if cost is None or cost == 0 or price is None:
        return None
    return ((price - cost) / cost) * 100

# --- Discord 메시지 파싱 함수 ---
def parse_discord_message_data(message_content):
    parsed_data = []
    lines = message_content.splitlines()
    # 변동전(prev), 변동후 또는 현재가(price) 그룹 포함
    regex = re.compile(
        r"^\s*(?P<name>.+?)\s*\((?P<stage>\d+)단계\)\s*:\s*"
        r"원가\s*:\s*(?P<cost>[\d,]+)"
        r"(?:\s*,\s*변동전\s*:\s*(?P<prev>[\d,]+))?"
        r"(?:\s*,\s*(?:변동후|현재가)\s*:\s*(?P<price>[\d,]+))?"
    )

    for raw in lines:
        # 마크다운 기호 제거
        line = raw.strip()
        line = re.sub(r"^[-*]\s*", "", line)
        line = line.replace("`", "")
        if not line:
            continue

        m = regex.match(line)
        if not m:
            print(f"경고: 형식 불일치 - {line}")
            continue

        name    = m.group("name").strip()
        stage   = f"{m.group('stage')}단계"
        cost_s  = m.group("cost")
        price_s = m.group("price")

        # 1) 변동후/현재가  2) 변동전(prev)  3) '변동률' 이전 텍스트에서 마지막 숫자
        if not price_s:
            price_s = m.group("prev")
        if not price_s:
            no_pct   = line.split("변동률")[0]
            nums     = re.findall(r"[\d,]+", no_pct)
            # 원가, 변동전, 변동후 순서이므로 3개 이상일 때 마지막이 변동후
            price_s  = nums[2] if len(nums) >= 3 else None
        if not price_s:
            print(f"경고: 판매가 추출 실패 - {line}")
            continue

        cost   = int(cost_s.replace(",", ""))
        price  = int(price_s.replace(",", ""))
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

# --- 메시지 분할 헬퍼 ---
def _split_message(message_parts, max_len=1900):
    current_message = []
    current_len = 0
    for part in message_parts:
        part_len = len(part) + 2 if current_message else len(part)
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
    print(f"로그인 완료: {bot.user.name} (ID: {bot.user.id})")

@bot.event
async def on_message(message):
    # 봇 자신의 메시지나 다른 채널은 무시
    if message.author == bot.user or message.channel.id != SOURCE_CHANNEL_ID:
        return

    content = message.content.strip()
    if not content:
        # 텍스트가 없으면 무시
        return

    # 파싱
    all_crop_data = parse_discord_message_data(content)
    if not all_crop_data:
        await message.channel.send(
            "🚧 메시지에서 유효한 작물 시세 데이터를 찾을 수 없습니다. 형식을 확인해주세요.",
            reference=message.to_reference()
        )
        return

    # 숙련도/계절 정보 추가 및 정렬
    processed = []
    for item in all_crop_data:
        details = fixed_crop_details.get(item["baseName"], {"mastery": "-", "season": "-"})
        processed.append({
            **item,
            "mastery": details["mastery"],
            "season":  details["season"]
        })
    processed.sort(
        key=lambda x: x["profitRate"] if x["profitRate"] is not None else -float('inf'),
        reverse=True
    )

    # 메시지 생성 및 전송
    message_parts = ["**📈 작물 시세 분석 결과 📉**", "---"]
    for i, crop in enumerate(processed[:10]):
        premium_tag = " ✨(특상품)" if crop["isPremium"] else ""
        gold_tag    = " 🌟(황금)" if crop["isGold"]    else ""
        profit_disp = f"{crop['profitRate']:.2f}%" if crop['profitRate'] is not None else "계산 불가"
        message_parts.append(
            f"{i+1}. **{crop['name']}** (단계: {crop['stage']}, 원가: {crop['cost']:,}원, 판매가: {crop['price']:,}원)"
            f"{premium_tag}{gold_tag} - **수익률: {profit_disp}** (숙련도: {crop['mastery']}, 계절: {crop['season']})"
        )

    result_ch = bot.get_channel(RESULT_CHANNEL_ID)
    if result_ch:
        for chunk in _split_message(message_parts):
            await result_ch.send(chunk)
    else:
        print(f"오류: 결과 채널({RESULT_CHANNEL_ID})을 찾을 수 없습니다.")

# --- 봇 실행 ---
if __name__ == "__main__":
    bot.run(DISCORD_BOT_TOKEN)
