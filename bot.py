from keep_alive import keep_alive
import os
import discord
from discord import app_commands, SelectOption
from discord.ui import Select, View
from discord.ext import commands, tasks
import random
from discord import app_commands
import motor.motor_asyncio
import asyncio
import time
from datetime import datetime, timedelta
# ========== KẾT NỐI MONGODB ==========
MONGO_URI = os.getenv("MONGO_URI") 
cluster = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db_mongo = cluster["game_database"] 
users_col = db_mongo["users"]       
eq_col = db_mongo["equipment"]      

# ========== CONFIG ==========
TOKEN = os.getenv("DISCORD_TOKEN")
INTENTS = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=INTENTS)

ADMIN_ID = 472564016917643264 
MSG_EXP = 10
MIN_MSG_LEN = 7
MSG_COOLDOWN = 20
last_msg_time = {}
last_msg_content = {} 
server_avg_lv = 1.0
last_ban_warn = {} 
# Các kênh nhận thông báo quan trọng
NOTIFY_CHANNELS = [1455081842473697362, 1455837230332641280, 1454793019160006783, 1454793109094268948, 1454506037779369986] 
CHANNEL_EXP_RATES = {
    1455081842473697362: 0.4, 1455837230332641280: 0.4,
    1454793019160006783: 0.4, 1454793109094268948: 0.4,
    1454506037779369986: 1.5, 1461017212365181160: 1.2
}

# --- CẤU HÌNH CẢNH GIỚI & LINH THÚ ---
REALMS = [
    ("Luyện Khí", 10), ("Trúc Cơ", 20), ("Kết Đan", 30),
    ("Nguyên Anh", 40), ("Hóa Thần", 50), ("Luyện Hư", 60),
    ("Hợp Thể", 70), ("Đại Thừa", 80),
    ("Đại Tiên", 90), ("Thiên Tiên", 100)
]
THAN_KHI_CONFIG = {
    "Hiên Viên Kiếm": {"desc": "Là ý chí của thánh đạo ngưng tụ thành hình, nơi ánh sáng và công lý giao thoa giữa cõi hư vô.", "atk": 200, "color": 0xFFD700},
    "Thần Nông Đỉnh": {"desc": "Sự tĩnh lặng của vạn vật trước lúc khai sinh, là hơi thở của sự sống ẩn mình trong vòng xoáy luân hồi.", "atk": 200, "color": 0x2ECC71},
    "Hạo Thiên Tháp": {"desc": "Một điểm tựa giữa dòng thời gian vô tận, nơi trật tự ngự trị và bóng tối buộc phải cúi đầu.", "atk": 200, "color": 0x3498DB},
    "Đông Hoàng Chung": {"desc": "Tiếng vọng từ thuở sơ khai tan vào hư không, là dư chấn của một thực tại vĩnh hằng không thể lay chuyển.", "atk": 200, "color": 0xE67E22},
    "Phục Hy Cầm": {"desc": "Giai điệu của những vì sao lạc lối, sợi dây liên kết giữa tâm thức và nhịp đập của vũ trụ.", "atk": 200, "color": 0x9B59B6},
    "Bàn Cổ Phủ": {"desc": "Ranh giới mỏng manh giữa tồn tại và hư diệt, là vết rách đầu tiên trên bức màn của bóng đêm vĩnh cửu.", "atk": 200, "color": 0x7E5109},
    "Luyện Yêu Hồ": {"desc": "Cõi mộng nằm gọn trong lòng bàn tay, nơi thực và ảo đan xen thành một vòng lặp không có điểm dừng.", "atk": 200, "color": 0x1ABC9C},
    "Côn Lôn Kính": {"desc": "Ánh nhìn phản chiếu từ một chiều không gian khác, soi rọi những sự thật bị chôn vùi dưới lớp bụi ký ức.", "atk": 200, "color": 0xECF0F1},
    "Nữ Oa Thạch": {"desc": "Mảnh vỡ của bầu trời vỡ nát, mang trong mình hơi ấm từ bàn tay cứu rỗi thuở hồng hoang.", "atk": 200, "color": 0xE91E63},
    "Không Đồng Ấn": {"desc": "Dấu ấn của định mệnh khắc lên dòng chảy sinh mệnh, là quyền năng nắm giữ sự bất biến giữa cõi vô thường.", "atk": 200, "color": 0x1F1F1F}
}
THAN_CHU_THIEN_PHAT = [
    "📜 Thiên đạo vô tình, coi vạn vật là chó rơm! THIÊN PHẠT GIÁNG LÂM!!!",
    "⚡ Ta nắm giữ lôi đình trong tay, nhân danh Thiên Đạo: TRỪ KHỬ TU VI!",
    "⛈️ Sóng cuộn mây vần, thiên kiếp đã định, kẻ nghịch thiên tất bại!",
    "🌩️ Một tiếng sấm vang, chấn động cửu tiêu, đại năng cũng phải cúi đầu!",
    "🏮 Vận mệnh đã an bài, lôi phat giáng thế, gột rửa bụi trần!"
]

EQ_TYPES = ["Kiếm", "Nhẫn", "Giáp", "Tay", "Ủng"]
PET_CONFIG = {
    "Tiểu Hỏa Phượng": {
        "atk": 180, 
        "hp": 2000,
        "drop_buff": 0.1, 
        "effect": "Tăng 10% rơi đồ", 
        "color": 0xe74c3c,
        "icon": "🔥"
    },
    "Băng Tinh Hổ": {
        "atk": 170,
        "hp": 2300,
        "break_buff": 5, 
        "effect": "Tăng 5% tỉ lệ đột phá", 
        "color": 0x3498db,
        "icon": "❄️"
    },
    "Thôn Phệ Thú": {
        "atk": 170, 
        "hp": 2200,
        "exp_mult": 1.15, 
        "effect": "Tăng 15% EXP", 
        "color": 0x9b59b6,
        "icon": "🐾"
    },
    "Huyền Quy": {
        "atk": 120, 
        "hp": 3000,
        "risk_reduce": 0.5, 
        "effect": "Giảm 50% rủi ro Lôi Kiếp", 
        "color": 0x2ecc71,
        "icon": "🐢"
    },
    "Hóa Hình Hồ Ly": {
        "atk": 190,
        "hp": 1500,
        "lt_buff": 0.2, # Tăng 20% Linh thạch nhận được
        "effect": "Tăng 20% Linh Thạch",
        "color": 0xff99cc,
        "icon": "🦊"
    }
}

# ========== UTIL FUNCTIONS (THUẦN MONGODB) ==========

def exp_needed(lv: int):
    return 40 + lv * 8 if lv <= 50 else 200 + lv * 25

def get_realm(lv: int):
    for name, maxlv in REALMS:
        if lv <= maxlv:
            tầng = lv % 10 if lv % 10 else 10
            return f"{name} tầng {tầng}"
    return "Thiên Tiên viên mãn"

def get_monster_data(lv: int):
    if lv <= 10: return "Yêu thú", 0.15, (1, 2)
    elif lv <= 30: return "Ma thú", 0.20, (2, 4)
    elif lv <= 60: return "Linh thú", 0.25, (4, 7)
    else: return "Cổ thú", 0.30, (6, 9)
async def calc_power(uid: str) -> int:
    uid = str(uid)
    u = await users_col.find_one({"_id": uid})
    if not u: return 0
    
    eq = await eq_col.find_one({"_id": uid}) or {}
    lv, pet_name = u.get("level", 1), u.get("pet")
    than_khi_name = u.get("than_khi") 
    
    # 1. Chỉ số gốc từ Level (lv * 5)
    atk, hp = lv * 5, lv * 50
    
    # 2. Cộng chỉ số từ Trang bị
    for t in EQ_TYPES:
        eq_lv = eq.get(t, 0)
        
        if t == "Kiếm":
            # CHỈ cộng Atk Kiếm nếu KHÔNG có Thần Khí
            if not than_khi_name:
                atk += eq_lv * 15
        
        elif t == "Nhẫn":
            # LUÔN cộng Atk Nhẫn trong mọi trường hợp
            atk += eq_lv * 15
            
        else: 
            # Các trang bị còn lại (Giáp, v.v.) cộng HP
            hp += eq_lv * 150
            
    # 3. Cộng chỉ số Thần Khí (Nếu có)
    if than_khi_name:
        atk += 200 # Cộng 200 ATK từ Thần Khí
            
    # 4. Chỉ số từ Pet (Giữ nguyên)
    if pet_name in PET_CONFIG:
        pet_stats = PET_CONFIG[pet_name]
        atk += pet_stats.get("atk", 0)
        hp += pet_stats.get("hp", 0) 

    # 5. Tính toán Lực chiến tổng hợp (Power)
    power = (atk * 10) + hp + random.randint(0, 100)
    return int(power)
async def add_exp(uid: str, amount: int):
    uid = str(uid)
    # 1. Lấy dữ liệu để kiểm tra điều kiện cấp độ
    u = await users_col.find_one({"_id": uid})
    
    # 2. Nếu là người mới hoàn toàn -> Tạo mới
    if not u:
        await users_col.insert_one({
            "_id": uid, 
            "level": 1, 
            "exp": amount, 
            "linh_thach": 1, 
            "pet": None
        })
        return

    # 3. Logic Cảnh giới: Kiểm tra mốc 10, 20, 30...
    current_lv = u.get("level", 1)
    current_exp = u.get("exp", 0)

    if current_lv % 10 == 0:
        needed = exp_needed(current_lv)
        # Nếu đã đầy hoặc vượt quá EXP cần thiết thì không cộng thêm
        if current_exp >= needed:
            return # Đã chạm đỉnh cảnh giới, phải đột phá!
        
        # Nếu chưa đầy, chỉ cho phép cộng thêm vừa đủ đến mốc 'needed'
        # Tránh việc rã đồ nhận quá nhiều EXP làm tràn mốc khi chưa đột phá
        if current_exp + amount > needed:
            amount = needed - current_exp

    # 4. Nếu không vướng cảnh giới hoặc chưa đầy bình, tiến hành cộng EXP
    # Sử dụng $inc để đảm bảo tính toán chính xác trên Database
    await users_col.update_one(
        {"_id": uid}, 
        {"$inc": {"exp": amount}}
    )

async def check_level_up(uid, channel, name):
    uid = str(uid)
    u = await users_col.find_one({"_id": uid})
    if not u: return
    
    lv = u.get("level", 1)
    exp = u.get("exp", 0)
    new_lv = lv
    leveled = False

    # Vòng lặp kiểm tra thăng cấp
    while exp >= exp_needed(new_lv):
        # CHỐT CHẶN: Nếu đang ở đỉnh phong 10, 20, 30... thì không cho lên 11, 21, 31...
        if new_lv % 10 == 0:
            break
            
        exp -= exp_needed(new_lv)
        new_lv += 1
        leveled = True
        
        if new_lv >= 100: 
            break

    # Chỉ cập nhật Database nếu thực sự có sự thay đổi về Cấp độ hoặc EXP dư trong vòng lặp
    if leveled:
        await users_col.update_one(
            {"_id": uid}, 
            {"$set": {"level": new_lv, "exp": exp}}
        )
        
        realm_name = get_realm(new_lv)
        embed = discord.Embed(
            title="✨ CẢNH GIỚI PHI THĂNG ✨", 
            description=f"Chúc mừng đạo hữu **{name}** đã lên **Cấp {new_lv}**!\n🧘 Cảnh giới: **{realm_name}**", 
            color=discord.Color.green()
        )
        if channel: 
            try:
                await channel.send(embed=embed)
            except:
                pass # Tránh treo bot nếu channel bị xóa hoặc thiếu quyền
    # Không cần phần 'else' cập nhật exp nếu đạo hữu đã dùng $inc trong hàm add_exp
# ========== VÒNG LẶP THIÊN Ý (MONGODB) ==========
@tasks.loop(hours=4.8)
async def thien_y_loop():
    is_thien_y = random.choice([True, False])
    percent = random.randint(5, 10)
    if is_thien_y:
        await users_col.update_many({}, {"$mul": {"exp": 1 + (percent / 100)}})
        msg = f"Tất cả đạo hữu được ban phúc, tăng **{percent}%** EXP!"
    else:
        await users_col.update_many({}, {"$mul": {"exp": max(0, 1 - (percent / 100))}})
        msg = f"Cảnh báo! Tâm ma quấy nhiễu, tổn hao **{percent}%** EXP!"
    # (Đoạn này đạo hữu có thể thêm logic gửi tin nhắn vào kênh NOTIFY_CHANNELS nếu muốn)
@tasks.loop(minutes=30)
async def update_server_avg():
    global server_avg_lv
    try:
        # Chỉ lấy Top 10 cao thủ hàng đầu server
        top_players = await users_col.find().sort([("level", -1)]).limit(15).to_list(length=15)
        if top_players:
            total_lv = sum(p.get("level", 1) for p in top_players)
            server_avg_lv = total_lv / len(top_players)
            print(f"✨ [Thiên Đạo] Level trung bình Top 10: {server_avg_lv:.2f}")
    except Exception as e:
        print(f"❌ Lỗi cập nhật Thiên Đạo: {e}")
# ========== EVENTS ==========
@bot.event
async def on_ready():
    try:
        # 1. Đồng bộ lệnh Slash trước để tu sĩ có thể dùng lệnh ngay
        synced = await bot.tree.sync()
        print(f"✅ Đã đồng bộ {len(synced)} lệnh Slash.")

        # 2. Chạy tính toán Level trung bình LẦN ĐẦU TIÊN ngay lập tức
        # Điều này đảm bảo server_avg_lv có giá trị đúng trước khi Bot nhận tin nhắn
        await update_server_avg() 

        # 3. Sau đó mới bắt đầu các vòng lặp định kỳ
        if not update_server_avg.is_running():
            update_server_avg.start()
        if not thien_y_loop.is_running():
            thien_y_loop.start()
            
        # 4. Thông báo trạng thái cuối cùng
        print(f"✅ Đã đăng nhập: {bot.user}")
        print(f"✨ Level trung bình Top 10 (Khởi tạo): {server_avg_lv:.2f}")
        print("🚀 Bot đã sẵn sàng nhận lệnh và ban phúc!")

    except Exception as e:
        print(f"❌ Lỗi nghiêm trọng khi khởi động Bot: {e}")
@bot.event

async def on_message(message):
    if message.author.bot: return
    
    uid = str(message.author.id)
    now_dt = datetime.now()
    now_ts = now_dt.timestamp()
    content = message.content.strip().lower()

    # 1. BỘ LỌC SPAM & TRÙNG LẶP
    if content == last_msg_content.get(uid): return 
    if not (len(content) >= MIN_MSG_LEN and now_ts - last_msg_time.get(uid, 0) >= MSG_COOLDOWN):
        return

    last_msg_time[uid] = now_ts
    last_msg_content[uid] = content
    
    # 2. TRUY VẤN DỮ LIỆU TU SĨ
    user_data = await users_col.find_one({"_id": uid})
    if not user_data:
        user_data = {"level": 1, "exp": 0, "linh_thach": 10, "pet": None}
        await users_col.insert_one({"_id": uid, **user_data})

    # --- KIỂM TRA TRẠNG THÁI CẤM TÚC (ĐÃ SỬA) ---
    ban_until = user_data.get("ban_exp_until")
    if ban_until:
        # Đảm bảo so sánh cùng kiểu datetime
        # Nếu ban_until trong DB bị lưu nhầm là số, ta dùng datetime.fromtimestamp
        if isinstance(ban_until, (int, float)):
            ban_until = datetime.fromtimestamp(ban_until)

        if now_dt < ban_until:
            if uid not in last_ban_warn or (now_ts - last_ban_warn[uid]) > 60:
                time_str = ban_until.strftime('%H:%M %d/%m')
                await message.channel.send(
                    f"⚠️ {message.author.mention}, đạo hữu đang bị cấm túc. Hết hạn: {time_str}",
                    delete_after=10
                )
                last_ban_warn[uid] = now_ts
            
            await bot.process_commands(message)
            return # Dừng tại đây, không xuống phần cộng EXP
    # ------------------------------------------
    # --------------------------------------

    # 3. TÍNH TOÁN HỆ SỐ KÊNH
    rate = CHANNEL_EXP_RATES.get(message.channel.id, 0.1)
    base_exp = int(MSG_EXP * rate)
    
    # --- LOGIC BUFF X2 CHO NGƯỜI LV THẤP ---
    global server_avg_lv
    user_lv = user_data.get("level", 1)
    is_server_buffed = False
    
    if user_lv < server_avg_lv:
        base_exp = base_exp * 2  
        is_server_buffed = True
    # --------------------------------------

    # 4. LOGIC LINH THÚ & ICON
    pet_bonus = 0
    user_pet = user_data.get("pet")
    
    if user_pet in PET_CONFIG:
        pet_info = PET_CONFIG[user_pet]
        try: await message.add_reaction(pet_info["icon"])
        except: pass

        if user_pet == "Thôn Phệ Thú":
            pet_bonus = int(base_exp * (pet_info.get("exp_mult", 1.15) - 1))
            if is_server_buffed:
                try: await message.add_reaction("✨")
                except: pass
    
    elif is_server_buffed:
        try: await message.add_reaction("✨")
        except: pass

    # 5. TỔNG KẾT & GHI DANH
    total_gain = base_exp + pet_bonus
    await add_exp(uid, total_gain)
    await check_level_up(uid, message.channel, message.author.display_name)
    
    await bot.process_commands(message)
# ========== LỆNH SLASH (/) ==========
@bot.tree.command(name="check", description="Xem hồ sơ tu tiên & lực chiến chính xác")
async def info(interaction: discord.Interaction):
    try:
        # 1. Chống treo lệnh: Báo cho Discord Bot đang xử lý
        await interaction.response.defer()
        uid = str(interaction.user.id)
        
        # 2. Lấy dữ liệu người dùng
        u = await users_col.find_one({"_id": uid})
        if not u:
            return await interaction.followup.send("⚠️ Đạo hữu chưa có tên trong sổ sinh tử!")
        
        eq = await eq_col.find_one({"_id": uid}) or {}
        level = u.get("level", 1)
        cur_exp = u.get("exp", 0)
        than_khi_name = u.get("than_khi")
        pet_name = u.get("pet")

        # 3. GỌI HÀM TÍNH POWER (Đảm bảo đồng nhất số liệu)
        # Bần đạo gọi hàm calc_power mà đạo hữu đã cung cấp
        total_power = await calc_power(uid)

        # 4. TÍNH TOÁN CẢNH GIỚI (Lv.X - Cảnh giới tầng Y)
        stages = ["Luyện Khí", "Trúc Cơ", "Kết Đan", "Nguyên Anh", "Hóa Thần", 
                  "Luyện Hư", "Hợp Thể", "Đại Thừa", "Đại Tiên", "Thiên Tiên"]
        idx = (level - 1) // 10
        idx = max(0, min(idx, len(stages) - 1))
        current_stage = stages[idx]
        tang = (level - 1) % 10 + 1
        display_canh_gioi = f"Lv.{level} - {current_stage} tầng {tang}"

        # 5. XỬ LÝ HIỂN THỊ VŨ KHÍ & MÀU SẮC
        # Lấy cấp độ các trang bị để hiển thị (đúng tên đạo hữu yêu cầu)
        kiem_lv = eq.get("Kiếm", 0)
        nhan_lv = eq.get("Nhẫn", 0)
        giap_lv = eq.get("Giáp", 0)
        tay_lv = eq.get("Tay", 0)
        ung_lv = eq.get("Ủng", 0)

        embed_color = discord.Color.blue()
        if than_khi_name:
            weapon_display = f"🌟 **{than_khi_name}**"
            # Giả sử đạo hữu có bảng màu trong config, nếu không mặc định màu Vàng Kim
            embed_color = discord.Color.gold()
        else:
            weapon_display = f"⚔️ Kiếm Cấp {kiem_lv}" if kiem_lv > 0 else "⚔️ Vô nhận kiếm"

        # 6. HIỂN THỊ EXP
        # Theo logic check_level_up: Đạt mốc % 10 thì dừng thăng cấp
        if level % 10 == 0:
            exp_display = f"`{cur_exp} / Đỉnh Phong (Cần Đột Phá)`"
        else:
            needed = level * 100
            exp_display = f"`{cur_exp} / {needed}`"

        # 7. KHỞI TẠO EMBED
        embed = discord.Embed(title=f"📜 HỒ SƠ TU TIÊN: {interaction.user.display_name}", color=embed_color)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        embed.add_field(name="📜 Cảnh Giới", value=f"**{display_canh_gioi}**", inline=False)
        embed.add_field(name="⚔️ Lực Chiến", value=f"**{total_power:,}**", inline=True)
        embed.add_field(name="💎 Linh Thạch", value=f"{u.get('linh_thach', 0)} viên", inline=True)
        embed.add_field(name="✨ Linh Lực", value=exp_display, inline=False)

        trang_bi_str = (
            f"Vũ khí: {weapon_display}\n"
            f"💍 Nhẫn: Cấp {nhan_lv}\n"
            f"🛡️ Giáp: Cấp {giap_lv}\n"
            f"🧤 Tay: Cấp {tay_lv}\n"
            f"👢 Ủng: Cấp {ung_lv}"
        )
        embed.add_field(name="📦 Trang Bị Khảm Nạm", value=trang_bi_str, inline=True)
        embed.add_field(name="🦄 Linh Thú", value=f"🐾 **{pet_name or 'Chưa có'}**", inline=True)

        # 8. Gửi phản hồi cuối cùng
        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"❌ Lỗi lệnh check: {e}")
        # Nếu lỗi xảy ra, cố gắng báo cho người dùng thay vì treo
        try:
            await interaction.followup.send("⚠️ Linh lực hỗn loạn, không thể xem hồ sơ lúc này!")
        except:
            pass
@bot.tree.command(name="diemdanh", description="Điểm danh nhận cơ duyên thăng 1 cấp")
async def diemdanh(interaction: discord.Interaction):
    await interaction.response.defer()
    
    uid = str(interaction.user.id)
    # Lấy ngày hiện tại định dạng YYYY-MM-DD
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # 1. Khởi tạo/Lấy dữ liệu (Dùng find_one_and_update để tránh race condition)
        u = await users_col.find_one_and_update(
            {"_id": uid}, 
            {"$setOnInsert": {"level": 1, "exp": 0, "linh_thach": 1, "last_daily": "Never"}}, 
            upsert=True, 
            return_document=True
        )
        
        # Kiểm tra nếu đã điểm danh hôm nay
        if u.get("last_daily") == today: 
            return await interaction.followup.send("❌ Hôm nay đạo hữu đã nhận bổng lộc rồi!")

        current_lv = int(u.get("level", 1))
        
        # 2. KIỂM TRA CHẶN BUG ĐỘT PHÁ
        # logic: lv 9, 19, 29... không được lên 10, 20, 30 qua điểm danh
        is_at_bottleneck = (current_lv + 1) % 10 == 0
        # logic: lv 10, 20, 30... đang kẹt chưa đột phá
        is_stuck_at_gate = (current_lv % 10 == 0)

        if is_at_bottleneck or is_stuck_at_gate:
            # Chỉ cho Linh thạch, không cho cấp
            await users_col.update_one(
                {"_id": uid},
                {"$inc": {"linh_thach": 1}, "$set": {"last_daily": today}}
            )
            
            msg = (f"⚠️ Cảnh giới cấp {current_lv} sát mốc đại hạn! Thiên đạo không thể giúp ngươi nhảy vọt." 
                   if is_at_bottleneck else 
                   f"⚠️ Đạo hữu kẹt tại đỉnh phong {current_lv}! Hãy đột phá trước.")
                
            return await interaction.followup.send(f"{msg}\n\n✅ Điểm danh thành công: Nhận **1 Linh Thạch**.")

        # 3. TRƯỜNG HỢP HỢP LỆ -> THĂNG 1 CẤP
        new_level = current_lv + 1
        
        # Cập nhật DB
        await users_col.update_one(
            {"_id": uid},
            {
                "$set": {"level": new_level, "exp": 0, "last_daily": today},
                "$inc": {"linh_thach": 1}
            }
        )
        
        # Gửi thông báo bằng Embed
        embed = discord.Embed(
            title="🎊 ĐẠI CƠ DUYÊN 🎊",
            description=(f"Đạo hữu {interaction.user.mention} điểm danh, linh khí quán đỉnh!\n"
                         f"✨ Thăng lên: **Cấp {new_level}**\n"
                         f"💎 Nhận được: **1 Linh thạch**"),
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        # Lưu ý: Dùng link ảnh trực tiếp kết thúc bằng .png/.jpg
        embed.set_thumbnail(url="https://i.imgur.com/8S9UvY6.png") 
        
        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"❌ Lỗi điểm danh: {e}")
        await interaction.followup.send("⚠️ Pháp trận điểm danh gặp trục trặc, hãy thử lại sau!")
@bot.tree.command(name="gacha", description="Gacha trang bị & Linh thú & Thần khí (Tốn 1 Linh thạch sau 3 lượt)")
async def gacha(interaction: discord.Interaction):
    await interaction.response.defer()
    uid = str(interaction.user.id)
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. LẤY DỮ LIỆU USER
    u = await users_col.find_one({"_id": uid})
    if not u:
        u = {"_id": uid, "level": 1, "exp": 0, "linh_thach": 10, "gacha_count": 0, "last_gacha_day": ""}
        await users_col.insert_one(u)

    gacha_count = u.get("gacha_count", 0) if u.get("last_gacha_day") == today else 0
    linh_thach = u.get("linh_thach", 0)
    cost = 0 if gacha_count < 3 else 1

    # Kiểm tra Linh thạch
    if linh_thach < cost:
        return await interaction.followup.send(f"❌ Đạo hữu không đủ **{cost} Linh thạch** để tiếp tục.")

    # 2. LOGIC GACHA THẦN KHÍ (Tỉ lệ 0.1% - Độc bản)
    tk_msg = ""
    user_than_khi = u.get("than_khi")
    
    # Chỉ gacha thần khí nếu chưa có món nào
    if not user_than_khi and random.random() <= 0.005: 
        owned_tk = await users_col.distinct("than_khi", {"than_khi": {"$ne": None}})
        available_tk = [tk for tk in THAN_KHI_CONFIG.keys() if tk not in owned_tk]
        
        if available_tk:
            user_than_khi = random.choice(available_tk)
            await users_col.update_one({"_id": uid}, {"$set": {"than_khi": user_than_khi}})
            tk_msg = f"\n🔥 **DỊ TƯỢNG!** Đạo hữu đã cảm ứng và thu phục được Thần Khí: **[{user_than_khi}]**!"

    # 3. LOGIC GACHA LINH THÚ (Tỉ lệ 0.5% - Độc bản)
    pet_msg = ""
    if not u.get("pet") and random.random() <= 0.002: 
        owned_pets = await users_col.distinct("pet", {"pet": {"$ne": None}})
        available_pets = [p for p in PET_CONFIG.keys() if p not in owned_pets]
        if available_pets:
            pet_got = random.choice(available_pets)
            await users_col.update_one({"_id": uid}, {"$set": {"pet": pet_got}})
            pet_msg = f"\n🎊 **THIÊN CƠ!** Đạo hữu thu phục được Linh thú: **{pet_got}**!"

    # 4. LOGIC GACHA TRANG BỊ & PHÂN RÃ
    eq_type = random.choice(EQ_TYPES) # "Kiếm", "Giáp", v.v...
    lv = random.choices(range(1, 11), weights=[25, 20, 15, 10, 10, 8, 5, 3, 3, 1])[0]
    
    current_eq = await eq_col.find_one({"_id": uid}) or {}
    old_lv = current_eq.get(eq_type, 0)
    
    exp_bonus = 0
    msg = ""

    # KIỂM TRA SLOT KIẾM & THẦN KHÍ
    if eq_type == "Kiếm" and user_than_khi:
        # Nếu đã có Thần Khí, mọi loại Kiếm thường đều bị rã
        exp_bonus = lv * 100
        msg = f"⚔️ Uy áp từ **[{user_than_khi}]** khiến **Kiếm cấp {lv}** vừa xuất hiện đã vụn nát, nhận **{exp_bonus} EXP**."
    elif lv > old_lv:
        # Nhận đồ mạnh hơn
        await eq_col.update_one({"_id": uid}, {"$set": {eq_type: lv}}, upsert=True)
        msg = f"🎁 Nhận được **{eq_type} cấp {lv}**"
    else:
        # Phân rã đồ yếu hơn hoặc bằng
        exp_bonus = lv * 100
        msg = f"🗑️ **{eq_type} cấp {lv}** quá yếu, rã nhận **{exp_bonus} EXP**"

    # 5. CẬP NHẬT DATABASE TỔNG HỢP
    new_gacha_count = gacha_count + 1
    await users_col.update_one(
        {"_id": uid},
        {
            "$set": {"gacha_count": new_gacha_count, "last_gacha_day": today},
            "$inc": {"linh_thach": -cost}
        }
    )

    # Xử lý EXP và Check Level Up (Dùng hàm add_exp cũ có chặn lv 10)
    if exp_bonus > 0:
        await add_exp(uid, exp_bonus)
        await check_level_up(uid, interaction.channel, interaction.user.display_name)

    # 6. HIỂN THỊ KẾT QUẢ
    status = f"🎰 Lượt: **{new_gacha_count}/3** (Miễn phí)" if new_gacha_count <= 3 else f"💎 Phí: **1 Linh thạch**"
    
    # Chọn màu Embed (Ưu tiên màu Thần khí nếu vừa quay trúng)
    color = discord.Color.blue()
    if user_than_khi and tk_msg != "": 
        color = THAN_KHI_CONFIG[user_than_khi]["color"]
    elif pet_msg != "":
        color = discord.Color.gold()

    embed = discord.Embed(
        title="🔮 KẾT QUẢ GACHA 🔮",
        description=f"{msg}{tk_msg}{pet_msg}\n\n{status}",
        color=color
    )
    if user_than_khi and tk_msg != "":
        embed.set_footer(text=THAN_KHI_CONFIG[user_than_khi]["desc"])

    await interaction.followup.send(embed=embed)
@bot.tree.command(name="solo", description="Thách đấu người chơi khác (Ẩn lực chiến, cược linh thạch)")
async def solo(interaction: discord.Interaction, target: discord.Member, linh_thach: int | None = None):
    await interaction.response.defer()
    uid = str(interaction.user.id)
    tid = str(target.id)

    if uid == tid:
        return await interaction.followup.send("❌ Không thể tự solo với chính mình!")
    if target.bot:
        return await interaction.followup.send("❌ Không thể thách đấu với linh thể (Bot)!")

    bet = linh_thach or 0
    if bet < 0:
        return await interaction.followup.send("❌ Số linh thạch không hợp lệ!")

    # Lấy dữ liệu 2 bên từ MongoDB
    u1 = await users_col.find_one({"_id": uid})
    u2 = await users_col.find_one({"_id": tid})

    if not u1 or not u2:
        return await interaction.followup.send("❌ Một trong hai đạo hữu chưa có hồ sơ tu tiên!")

    if bet > 0:
        if u1.get("linh_thach", 0) < bet or u2.get("linh_thach", 0) < bet:
            return await interaction.followup.send(f"❌ Một trong hai không đủ **{bet} linh thạch** để cược!")

    p1_power = await calc_power(uid)
    p2_power = await calc_power(tid)

    class SoloView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)

        async def interaction_check(self, i: discord.Interaction):
            if i.user.id != target.id:
                await i.response.send_message("❌ Bạn không phải người bị thách đấu!", ephemeral=True)
                return False
            return True

        @discord.ui.button(label="✅ Tiếp Chiến", style=discord.ButtonStyle.success)
        async def accept(self, i: discord.Interaction, button: discord.ui.Button):
            # Kiểm tra lại linh thạch trên Cloud trước khi đánh
            curr_u1 = await users_col.find_one({"_id": uid})
            curr_u2 = await users_col.find_one({"_id": tid})
            
            if bet > 0 and (curr_u1["linh_thach"] < bet or curr_u2["linh_thach"] < bet):
                return await i.response.edit_message(content="❌ Trận đấu hủy bỏ! Một bên đã không còn đủ linh thạch.", view=None)

            total_power = p1_power + p2_power
            if total_power == 0: total_power = 1
            
            win_chance = p1_power / total_power
            roll = random.random()
            
            if roll <= win_chance:
                winner_id, winner_name, winner_pet = uid, interaction.user.display_name, curr_u1.get("pet")
                loser_id, loser_name = tid, target.display_name
            else:
                winner_id, winner_name, winner_pet = tid, target.display_name, curr_u2.get("pet")
                loser_id, loser_name = uid, interaction.user.display_name

            # XỬ LÝ CƯỢC TRÊN MONGODB
            if bet > 0:
                # Trừ tiền cả 2
                await users_col.update_many({"_id": {"$in": [uid, tid]}}, {"$inc": {"linh_thach": -bet}})
                # Cộng hũ cho người thắng
                await users_col.update_one({"_id": winner_id}, {"$inc": {"linh_thach": bet * 2}})

            p1_percent = round((p1_power / total_power) * 100, 1)
            p2_percent = round(100 - p1_percent, 1)
            pet_msg = f"\n🐾 Trợ lực từ linh thú **{winner_pet}** thật dũng mãnh!" if winner_pet else ""

            result_embed = discord.Embed(
                title="⚔️ TRẬN THƯ HÙNG KẾT THÚC ⚔️",
                description=(
                    f"🔵 **{interaction.user.display_name}**: {p1_power:,} LC ({p1_percent}%)\n"
                    f"🔴 **{target.display_name}**: {p2_power:,} LC ({p2_percent}%)\n"
                    f"🏆 Người thắng: **{winner_name}**\n💀 Kẻ bại: {loser_name}\n"
                    f"💰 Kết quả: " + (f"Thắng cược **{bet} Linh thạch**" if bet > 0 else "Vang danh thiên hạ") + pet_msg
                ),
                color=discord.Color.gold()
            )
            await i.response.edit_message(content=None, embed=result_embed, view=None)
            self.stop()

        @discord.ui.button(label="❌ Thủ Thế", style=discord.ButtonStyle.danger)
        async def decline(self, i: discord.Interaction, button: discord.ui.Button):
            await i.response.edit_message(content=f"❌ **{target.display_name}** đã chọn cách thủ thế.", embed=None, view=None)
            self.stop()

    invite_msg = f"⚔️ **{interaction.user.display_name}** thách đấu **{target.mention}**!\n" + \
                 (f"💎 Cược: **{bet} Linh thạch**" if bet > 0 else "🎲 Giao hữu")
    await interaction.followup.send(content=invite_msg, view=SoloView())

@bot.tree.command(name="dotpha", description="Đột phá cảnh giới (Lôi kiếp từ cấp 30)")
async def dotpha(interaction: discord.Interaction):
    await interaction.response.defer()
    uid = str(interaction.user.id)
    
    u = await users_col.find_one({"_id": uid})
    if not u: 
        return await interaction.followup.send("❌ Đạo hữu chưa có hồ sơ tu tiên!")

    lv = u.get("level", 1)
    linh_thach = u.get("linh_thach", 0)
    exp = u.get("exp", 0)
    pet_name = u.get("pet", "Không")

    # 1. LẤY CHỈ SỐ PET (Nếu có) - KHÔNG LÀM THAY ĐỔI CÔNG THỨC GỐC
    pet_data = PET_CONFIG.get(pet_name, {})
    break_buff = pet_data.get("break_buff", 0)    # Mặc định = 0 nếu pet không có buff này
    risk_reduce = pet_data.get("risk_reduce", 0)  # Mặc định = 0 nếu pet không có buff này

    # 2. KIỂM TRA ĐIỀU KIỆN (Giữ nguyên code cũ)
    if lv % 10 != 0:
        return await interaction.followup.send(f"❌ Cần đạt đỉnh phong (cấp 10, 20...) để đột phá. Hiện tại: **Cấp {lv}**")

    needed = exp_needed(lv)
    if exp < needed:
        return await interaction.followup.send(f"❌ Tu vi chưa đủ! (Cần {int(exp)}/{needed} EXP)")

    # 3. TÍNH LINH THẠCH YÊU CẦU (Giữ nguyên các mốc 1, 3, 6, 12)
    required_lt = 1 if lv < 30 else (3 if lv < 60 else (6 if lv < 80 else 12))
    if linh_thach < required_lt:
        return await interaction.followup.send(f"❌ Cần **{required_lt} Linh thạch**. Đạo hữu chỉ có: **{linh_thach}**")

    # 4. TỈ LỆ THÀNH CÔNG (Giữ nguyên công thức: 100 - realm*8)
    realm_index = lv // 10
    base_rate = max(5, 90 - (realm_index * 10))
    final_rate = base_rate + break_buff # Chỉ cộng thêm, không làm giảm tỉ lệ gốc
    
    success = random.randint(1, 100) <= final_rate

    if success:
        # THÀNH CÔNG (Giữ nguyên: Reset EXP về 0)
        await users_col.update_one(
            {"_id": uid},
            {
                "$set": {"level": lv + 1, "exp": 0}, 
                "$inc": {"linh_thach": -required_lt}
            }
        )
        
        pet_msg = f"\n✨ Nhờ có **{pet_name}** trợ lực (+{break_buff}%), đạo hữu đã thuận lợi thăng cấp!" if break_buff > 0 else ""
        quote = random.choice(KHAU_NGU) if 'KHAU_NGU' in globals() else "Thiên địa chứng giám, ta đã đột phá!"
        
        embed = discord.Embed(
            title="🔥 ĐỘT PHÁ THÀNH CÔNG 🔥",
            description=f"*{quote}*\n{pet_msg}\n🎉 **{interaction.user.display_name}** đã phi thăng lên **{get_realm(lv + 1)}**!",
            color=discord.Color.gold()
        )
        await interaction.followup.send(embed=embed)
            
    else:
        # THẤT BẠI (Giữ nguyên logic tụt cấp và Lôi Kiếp cấp 30)
        base_tut_cap = 1
        loi_kiep_msg = ""
        
        # Giữ nguyên tỉ lệ 30% xuất hiện Lôi Kiếp cấp cao
        if lv >= 30 and random.randint(1, 100) <= 30:
            base_tut_cap = random.randint(2, 5)
            loi_kiep_msg = "\n⚡ **LÔI KIẾP BẤT NGỜ!** Đạo hữu bị đánh văng tu vi!"

        # ÁP DỤNG GIẢM RỦI RO (Chỉ kích hoạt nếu có Pet như Huyền Quy)
        if risk_reduce > 0 and base_tut_cap > 1:
            tut_cap = max(1, int(base_tut_cap * (1 - risk_reduce)))
            pet_risk_msg = f"\n🐢 **{pet_name}** đã bảo vệ đạo hữu khỏi lôi kiếp cường đại!"
        else:
            tut_cap = base_tut_cap
            pet_risk_msg = ""

        new_lv = max(1, lv - tut_cap)
        await users_col.update_one(
            {"_id": uid},
            {
                "$set": {"level": new_lv}, 
                "$inc": {"linh_thach": -required_lt}
            }
        )
        
        fail_embed = discord.Embed(
            title="💥 ĐỘT PHÁ THẤT BẠI 💥",
            description=f"😔 **{interaction.user.display_name}** đã gục ngã trước thiên kiếp!{loi_kiep_msg}{pet_risk_msg}\n\n📉 Khấu trừ: **{tut_cap} cấp**\n💸 Tổn hao: **{required_lt} Linh thạch**",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=fail_embed)
@bot.tree.command(name="huongdan", description="Cẩm nang tu tiên toàn tập")
async def huongdan(interaction: discord.Interaction):
    # Tạo Embed chính
    embed = discord.Embed(
        title="📜 CẨM NANG TU TIÊN TOÀN TẬP",
        description="Chào mừng đạo hữu bước vào con đường tu chân. Dưới đây là những quy tắc cơ bản để đắc đạo thành tiên.",
        color=discord.Color.blue()
    )

    # 1. Cơ chế Tu vi & Đột phá
    embed.add_field(
        name="🔮 Tu Vi & Đột Phá",
        value=(
            "• **Kiếm EXP:** Nhắn tin tại các kênh linh địa hoặc dùng `/attack` đánh quái.\n"
            "• **Bình cảnh:** Khi đạt cấp **10, 20, 30...** đạo hữu sẽ bị chặn EXP.\n"
            "• **Đột phá:** Dùng lệnh `/dotpha`. Tỉ lệ thành công là 50%. Thất bại sẽ bị phản phệ (mất lượt)!"
        ),
        inline=False
    )

    # 2. Hệ thống Linh Thú
    embed.add_field(
        name="🐾 Linh Thú Hộ Thân",
        value=(
            "• **Sở hữu:** Có tỉ lệ 1% nhận được khi dùng lệnh `/gacha`.\n"
            "• **Lợi ích:** Mỗi linh thú tăng mạnh **Lực chiến** và có buff riêng (Ví dụ: Thôn Phệ Thú tăng 15% EXP).\n"
            "• **Lưu ý:** Mỗi tu sĩ chỉ có thể sở hữu **duy nhất một** linh thú."
        ),
        inline=False
    )

    # 3. Gacha & Trang bị
    embed.add_field(
        name="🎁 Gacha & Linh Thạch",
        value=(
            "• **Lượt miễn phí:** Có 3 lượt `/gacha` miễn phí mỗi ngày.\n"
            "• **Linh thạch:** Sau khi hết lượt free, tốn **2 Linh thạch** cho mỗi lần quay tiếp theo.\n"
            "• **Trang bị:** Giúp tăng chỉ số ATK/HP để tính Lực chiến tổng."
        ),
        inline=False
    )

    # 4. Các lệnh quan trọng
    embed.add_field(
        name="📜 Danh sách khẩu quyết (Lệnh)",
        value=(
            "`/check`: Xem trạng thái, tu vi và Linh thú của bản thân.\n"
            "`/attack`: Đi săn quái vật kiếm EXP và Linh thạch.\n"
            "`/diemdanh`: Nhận linh thạch và EXP mỗi ngày.\n"
            "`/bxh`: Xem bảng xếp hạng cường giả trong server."
        ),
        inline=False
    )

    # Hình ảnh minh họa và Footer
    embed.set_footer(text="Chúc đạo hữu sớm ngày phi thăng!")
    # Đạo hữu có thể thêm ảnh minh họa tiên cảnh ở đây
    embed.set_thumbnail(url="https://i.imgur.com/8pY8Xf8.png") 

    await interaction.response.send_message(embed=embed)
import asyncio
@bot.tree.command(name="bxh", description="Xem bảng xếp hạng các đại năng tu tiên")
async def bxh(interaction: discord.Interaction):
    await interaction.response.defer()
    
    # 1. Lấy Top 10 cao thủ từ MongoDB (Sắp xếp theo cấp độ và EXP giảm dần)
    top_users = await users_col.find().sort([("level", -1), ("exp", -1)]).limit(10).to_list(length=10)
    
    if not top_users:
        return await interaction.followup.send("⚠️ Chưa có tu sĩ nào ghi danh trên bảng vàng.")

    description = ""
    for i, user in enumerate(top_users):
        uid = user.get("_id") # Lấy ID người dùng từ DB
        lv = user.get("level", 1) # Lấy cấp độ hiện tại
        
        # Làm tròn EXP để tránh hiện số thập phân như 131.1672
        exp = int(user.get("exp", 0)) 
        pet = user.get("pet", "Không")
        
        # Gọi hàm get_realm để xác định danh hiệu cảnh giới từ cấp độ
        # Đảm bảo hàm get_realm(lv) đã có sẵn trong code của đạo hữu
        realm_name = get_realm(lv) 
        
        # --- LẤY TÊN HIỂN THỊ TRONG SERVER ---
        # Chuyển uid sang int để Discord nhận diện
        member = interaction.guild.get_member(int(uid)) if uid.isdigit() else None
        if member:
            name_display = f"**{member.display_name}**"
        else:
            name_display = f"<@{uid}>" # Nếu không ở trong server thì hiện Mention
            
        # Biểu tượng huy chương cho Top 3
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"**#{i+1}**"
        
        # Định dạng hiển thị: Cảnh giới nằm ngay dưới tên để tạo vẻ uy nghiêm
        description += f"{medal} {name_display}\n└─ *{realm_name}* • Cấp {lv} ({exp} EXP) | 🐾: {pet}\n\n"

    # 2. Tạo giao diện Embed
    embed = discord.Embed(
        title="🏆 BẢNG XẾP HẠNG CAO THỦ TU TIÊN 🏆",
        description=description,
        color=discord.Color.gold(),
        timestamp=datetime.now() # Cập nhật theo thời gian thực
    )
    
    embed.set_footer(text="Khổ luyện thành tài - Danh toại bảng vàng")
    # Đạo hữu có thể thay đổi link ảnh thumbnail dưới đây nếu muốn
    embed.set_thumbnail(url="https://i.imgur.com/8S9UvY6.png")

    await interaction.followup.send(embed=embed)
@bot.tree.command(name="resetday", description="ADMIN: Reset ngày")
async def resetday(interaction: discord.Interaction):
    # Kiểm tra quyền ADMIN (Giữ nguyên logic của đạo hữu)
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("❌ Bạn không có quyền.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    # Cập nhật toàn bộ server trên MongoDB
    await users_col.update_many(
        {}, # Filter trống = chọn tất cả
        {
            "$set": {
                "gacha_count": 0,
                "last_gacha_day": None,
                "last_daily": None,
                "attack_count": 0,
                "last_attack": None
            }
        }
    )

    await interaction.followup.send("✅ Reset ngày thành công trên hệ thống Cloud.")

class ConfirmPhongSinh(discord.ui.View):
    def __init__(self, pet_name, uid):
        super().__init__(timeout=30)
        self.pet_name = pet_name
        self.uid = str(uid) # Ép kiểu string cho MongoDB
        self.value = None

    @discord.ui.button(label="Xác nhận Phóng sinh", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.uid:
            return await interaction.response.send_message("❌ Đây không phải lễ phóng sinh của đạo hữu!", ephemeral=True)
        
        # Cập nhật MongoDB: Xóa pet và cộng 1 Linh thạch
        await users_col.update_one(
            {"_id": self.uid},
            {
                "$set": {"pet": None},
                "$inc": {"linh_thach": 1}
            }
        )
        
        self.value = True
        self.stop()
        await interaction.response.edit_message(
            content=f"🕊️ Đạo hữu đã phóng sinh **{self.pet_name}**. Nhận lại **1 Linh thạch**.", 
            view=None,
            embed=None
        )

    @discord.ui.button(label="Hủy bỏ", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        await interaction.response.edit_message(content="✅ Đã hủy lệnh phóng sinh. Linh thú vẫn an toàn!", view=None, embed=None)

@bot.tree.command(name="phongsinh", description="Giải phóng Linh thú (Cần xác nhận)")
async def phongsinh(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    
    # Lấy dữ liệu từ MongoDB
    u = await users_col.find_one({"_id": uid})
    if not u or not u.get("pet"):
        return await interaction.response.send_message("❌ Đạo hữu hiện không có Linh thú nào.", ephemeral=True)

    pet_name = u.get("pet")
    view = ConfirmPhongSinh(pet_name, uid)
    
    embed = discord.Embed(
        title="⚠️ XÁC NHẬN PHÓNG SINH",
        description=f"Đạo hữu chắc chắn muốn trả **{pet_name}** về với thiên nhiên?\n\n*Hành động này không thể hoàn tác, đạo hữu sẽ nhận lại 1 Linh thạch.*",
        color=discord.Color.red()
    )
    
    await interaction.response.send_message(embed=embed, view=view)
@bot.tree.command(name="attack", description="Săn quái vật kiếm EXP, Linh thạch và Trang bị")
async def attack(interaction: discord.Interaction):
    await interaction.response.defer()
    
    uid = str(interaction.user.id)
    # Lấy giờ UTC mặc định của hệ thống Render
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # 1. Lấy và khởi tạo User
    u = await users_col.find_one_and_update(
        {"_id": uid},
        {"$setOnInsert": {
            "level": 1, "exp": 0, "linh_thach": 10, "pet": None,
            "attack_count": 0, "last_attack": ""
        }},
        upsert=True,
        return_document=True
    )

    # 2. Kiểm tra ngày để reset lượt đánh
    last_attack_day = u.get("last_attack", "")
    current_attack_count = u.get("attack_count", 0)

    # Nếu ngày trong DB khác ngày UTC hiện tại -> Reset lượt về 0
    if last_attack_day != today:
        current_attack_count = 0

    if current_attack_count >= 3:
        return await interaction.followup.send(f"❌ Đạo hữu đã hết lượt (Reset lúc 00:00 UTC).")

    # 3. Dữ liệu Linh thú & Quái vật (Giữ nguyên các giá trị của đạo hữu)
    pet_name = u.get("pet")
    pet_data = PET_CONFIG.get(pet_name, {"atk": 0, "effect": "Không", "exp_mult": 1.0, "lt_chance": 30})
    monster, drop_rate, eq_range = get_monster_data(u["level"])
    
    # 4. Tính toán chỉ số
    total_atk = (u["level"] * 10) + pet_data.get("atk", 0)
    base_exp = exp_needed(u["level"]) // 5
    exp_gain = int(base_exp * pet_data.get("exp_mult", 1.0))
    
    lt_chance = pet_data.get("lt_chance", 30) 
    lt_gain = random.randint(1, 5) if random.randint(1, 100) <= lt_chance else 0

    # 5. Kiểm tra bình cảnh (Chặn EXP)
    can_gain_exp = True
    if u["level"] % 10 == 0 and u["exp"] >= exp_needed(u["level"]):
        can_gain_exp = False
        exp_gain = 0

    # 6. Logic rơi trang bị
    drop_msg = ""
    final_drop_rate = drop_rate + pet_data.get("drop_buff", 0)
    if random.random() <= final_drop_rate:
        eq_type = random.choice(EQ_TYPES)
        eq_lv = random.randint(*eq_range)
        current_eq = await eq_col.find_one({"_id": uid}) or {}
        if eq_lv > current_eq.get(eq_type, 0):
            await eq_col.update_one({"_id": uid}, {"$set": {eq_type: eq_lv}}, upsert=True)
            drop_msg = f"\n🎁 **VẬN MAY!** Nhận được: `{eq_type} Cấp {eq_lv}`"

   # 7. TÍNH TOÁN SỐ LƯỢT MỚI (Xử lý hồi lượt từ Thôn Phệ Thú)
    actual_count_inc = 1
    refund_msg = ""
    if pet_name == "Thôn Phệ Thú" and random.randint(1, 100) <= 20:
        actual_count_inc = 0
        refund_msg = "\n🌀 **Thôn Phệ Thú** hấp thụ linh khí, giúp bạn không tốn thể lực!"

    # CHỐT CHẶN CUỐI CÙNG: Tính con số chính xác để ghi đè vào Database
    final_count_to_save = current_attack_count + actual_count_inc

    # 8. CẬP NHẬT DATABASE
    await users_col.update_one(
        {"_id": uid},
        {
            "$inc": {
                "exp": exp_gain, 
                "linh_thach": lt_gain
            },
            "$set": {
                "last_attack": today, 
                "attack_count": final_count_to_save 
            }
        }
    )

    # 9. Hiển thị (Đã sửa biến new_count thành final_count_to_save)
    embed = discord.Embed(title="⚔️ CHIẾN BÁO", color=discord.Color.green())
    exp_info = f"📈 +{exp_gain} EXP" if can_gain_exp else "⚠️ **BÌNH CẢNH!**"
    
    embed.add_field(name="Kết quả", value=f"{exp_info} | 💎 +{lt_gain} LT{drop_msg}{refund_msg}")
    
    # Sửa biến tại đây để không bị treo lệnh
    embed.set_footer(text=f"Lượt còn lại: {3 - final_count_to_save}/3 | Giờ UTC: {today}")
    
    await interaction.followup.send(embed=embed)
    
    # Gọi hàm check level để cập nhật tu vi ngay lập tức
    await check_level_up(uid, interaction.channel, interaction.user.display_name)
# --- LỆNH CHUYỂN LINH THẠCH CÓ XÁC NHẬN ---

class ConfirmTransfer(discord.ui.View):
    def __init__(self, sender, receiver, amount):
        super().__init__(timeout=30)  # Nút bấm tồn tại trong 30 giây
        self.sender = sender
        self.receiver = receiver
        self.amount = amount

    @discord.ui.button(label="Xác Nhận", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Chỉ người gửi mới có quyền nhấn xác nhận
        if interaction.user.id != self.sender.id:
            return await interaction.response.send_message("❌ Đây không phải giao dịch của bạn!", ephemeral=True)
        
        # Kiểm tra và trừ tiền người gửi (đảm bảo linh_thach >= số tiền chuyển)
        res1 = await users_col.update_one(
            {"_id": str(self.sender.id), "linh_thach": {"$gte": self.amount}},
            {"$inc": {"linh_thach": -self.amount}}
        )
        
        if res1.modified_count > 0:
            # Cộng tiền cho người nhận
            await users_col.update_one(
                {"_id": str(self.receiver.id)},
                {"$inc": {"linh_thach": self.amount}},
                upsert=True
            )
            
            # Cập nhật thông báo thành công và xóa nút bấm
            await interaction.response.edit_message(
                content=f"✅ **Giao dịch thành công!**\nĐạo hữu **{self.sender.display_name}** đã chuyển `{self.amount}` Linh thạch cho **{self.receiver.display_name}**.",
                view=None
            )
        else:
            await interaction.edit_original_response(content="❌ **Thất bại!** Bạn không đủ linh thạch để thực hiện giao dịch này.", view=None)
        self.stop()

    @discord.ui.button(label="Hủy Bỏ", style=discord.ButtonStyle.red, emoji="✖️")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.sender.id:
            return await interaction.response.send_message("❌ Bạn không có quyền hủy!", ephemeral=True)
            
        await interaction.response.edit_message(content="🚫 **Giao dịch đã bị hủy bỏ.**", view=None)
        self.stop()
#shop
class ShopView(discord.ui.View):
    def __init__(self, uid, users_col, config, available_tk):
        super().__init__(timeout=60)
        self.uid = uid
        self.users_col = users_col
        self.config = config
        
        # Tạo Select Menu và thêm Options trực tiếp tại đây để tránh lỗi treo
        select = discord.ui.Select(
            placeholder="Chọn Thần Khí muốn mua...",
            options=[
                discord.SelectOption(
                    label=name, 
                    description=f"Giá: 80 Linh thạch - {config[name]['desc'][:50]}..."
                ) for name in available_tk[:25]
            ]
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        # Lấy giá trị từ select menu
        selected_tk = interaction.data['values'][0]
        
        # 1. Kiểm tra độc bản (Tránh mua trùng)
        is_taken = await self.users_col.find_one({"than_khi": selected_tk})
        if is_taken:
            return await interaction.response.send_message(f"⌛ Chậm mất rồi! **{selected_tk}** vừa có chủ nhân.", ephemeral=True)
        
        # 2. Kiểm tra linh thạch (Giá 80)
        u = await self.users_col.find_one({"_id": self.uid})
        if not u or u.get("linh_thach", 0) < 80:
            return await interaction.response.send_message("❌ Đạo hữu không đủ 80 Linh thạch!", ephemeral=True)

        # 3. Thực hiện giao dịch
        await self.users_col.update_one(
            {"_id": self.uid},
            {
                "$set": {"than_khi": selected_tk},
                "$inc": {"linh_thach": -80} # Trừ đúng 80
            }
        )
        
        # 4. Phản hồi thành công
        tk_data = self.config[selected_tk]
        embed = discord.Embed(
            title="🔥 GIAO DỊCH THÀNH CÔNG 🔥",
            description=f"Thần khí chọn chủ! Chúc mừng đạo hữu nhận được **{selected_tk}**!\n\n*\"{tk_data['desc']}\"*",
            color=tk_data['color']
        )
        await interaction.response.send_message(embed=embed)
        self.stop()

@bot.tree.command(name="shop", description="Cửa hàng Thần Khí Thượng Cổ (80 Linh thạch/món)")
async def shop(interaction: discord.Interaction):
    await interaction.response.defer()
    uid = str(interaction.user.id)
    
    # 1. Lấy danh sách chưa có chủ
    owned_tk = await users_col.distinct("than_khi", {"than_khi": {"$ne": None}})
    available_tk = [name for name in THAN_KHI_CONFIG.keys() if name not in owned_tk]
    
    if not available_tk:
        return await interaction.followup.send("🏮 Cửa hàng hiện đã trống rỗng!")

    # 2. Kiểm tra sở hữu
    user_data = await users_col.find_one({"_id": uid})
    if user_data and user_data.get("than_khi"):
        return await interaction.followup.send("⚠️ Đạo hữu đã sở hữu Thần Khí, không thể mua thêm!")

    # 3. Khởi tạo View với danh sách có sẵn (Tránh dùng add_option bên ngoài gây treo)
    view = ShopView(uid, users_col, THAN_KHI_CONFIG, available_tk)
    
    await interaction.followup.send("🏛️ **LINH BẢO CÁC** 🏛️\nNơi trao đổi những món thần vật thượng cổ (Giá: 80 Linh thạch).", view=view)
@bot.tree.command(name="captcha", description="Lệnh chấp pháp của riêng Admin để kiểm tra tu sĩ")
async def captcha(interaction: discord.Interaction, target: discord.Member):
    # 1. Kiểm tra ID người dùng
    if interaction.user.id != ADMIN_ID:
        return await interaction.response.send_message(
            "⛔ Đạo hạnh của ngươi chưa đủ để thi triển lệnh Chấp Pháp này!", 
            ephemeral=True # Chỉ người gõ lệnh mới thấy dòng này
        )

    await interaction.response.defer()

    # 2. Chuẩn bị danh sách biểu tượng xác minh
    emojis = ["🔥", "❄️", "⚡", "🍃", "🌑", "☀️", "💎", "🔮"]
    correct_emoji = random.choice(emojis)
    
    # Định nghĩa View cho các nút bấm
    class CaptchaView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30) # 30 giây để xác minh
            self.value = None

        async def check_choice(self, btn_interaction: discord.Interaction, chosen_emoji: str):
            # Chỉ người bị tag (target) mới có thể bấm nút
            if btn_interaction.user.id != target.id:
                return await btn_interaction.response.send_message(
                    "Đây không phải thử thách dành cho ngươi!", 
                    ephemeral=True
                )
            
            if chosen_emoji == correct_emoji:
                self.value = True
                self.stop()
                await btn_interaction.response.edit_message(
                    content=f"✅ **{target.display_name}** đã vượt qua thử thách đạo tâm! Trạng thái: Bình thường.", 
                    view=None
                )
            else:
                self.value = False
                self.stop()
                # Hình phạt khi chọn sai
                await btn_interaction.response.edit_message(
                    content=f"❌ **{target.display_name}** đã chọn sai! Nghi vấn tà thuật (Auto/Spam).", 
                    view=None
                )

    # 3. Tạo các nút bấm tương ứng với danh sách emoji
    view = CaptchaView()
    for e in emojis:
        button = discord.ui.Button(label=e, custom_id=e, style=discord.ButtonStyle.gray)
        
        # Hàm callback khi bấm nút
        async def button_callback(bi, e_val=e):
            await view.check_choice(bi, e_val)
            
        button.callback = button_callback
        view.add_item(button)

    # 4. Gửi pháp trận xác minh vào kênh
    await interaction.followup.send(
        f"🛡️ **PHÁP TRẬN CHẤP PHÁP** 🛡️\n"
        f"Tu sĩ {target.mention} đang bị nghi ngờ tẩu hỏa nhập ma (Spam).\n"
        f"Hãy chứng minh đạo tâm bằng cách nhấn vào biểu tượng: **{correct_emoji}**",
        view=view
    )

    # 5. Xử lý khi hết thời gian mà không bấm (Timeout)
    await view.wait()
    if view.value is None:
        await interaction.edit_original_response(
            content=f"⏰ **{target.display_name}** không có phản ứng sau 30 giây! Kết luận: Treo máy hoặc sử dụng Auto.", 
            view=None
                )
@bot.tree.command(name="loiphat", description="[ADMIN] Thiên phạt: Top 1 (500-1000 EXP) & 2 vị trong Top 2-5 (100-500 EXP)")
async def loiphat(interaction: discord.Interaction):
    # 1. Kiểm tra quyền Admin
    if interaction.user.id != ADMIN_ID:
        return await interaction.response.send_message(
            "❌ **THIÊN PHẠT!** Bạn không có quyền năng này.", 
            ephemeral=True
        )

    await interaction.response.defer()
    
    # 2. Lấy danh sách Top 5 cao thủ
    top_5 = await users_col.find().sort([("level", -1), ("exp", -1)]).limit(5).to_list(length=5)
    
    if len(top_5) < 3:
        return await interaction.followup.send("⚠️ Linh khí server chưa đủ mạnh (cần ít nhất 3 người trong BXH)!")

    # --- LOGIC MỚI: CHỌN MỤC TIÊU ---
    # Top 1 chắc chắn bị đánh
    top_1 = top_5[0]
    # Chọn ngẫu nhiên 2 người từ danh sách còn lại (Top 2 đến Top 5)
    others = top_5[1:] 
    victims_others = random.sample(others, k=min(2, len(others)))
    
    than_chu = random.choice(THAN_CHU_THIEN_PHAT)
    report_msg = f"✨ **KHẨU LỆNH:** *\"{than_chu}\"*\n"
    report_msg += "─" * 15 + "\n\n"

    # 3. XỬ LÝ TOP 1 (Sét đánh cực nặng: 500-1000 EXP)
    t1_uid = top_1.get("_id")
    t1_exp = top_1.get("exp", 0)
    t1_lost = random.randint(500, 1000)
    t1_new_exp = max(0, t1_exp - t1_lost)
    
    await users_col.update_one({"_id": t1_uid}, {"$set": {"exp": t1_new_exp}})
    report_msg += f"🔥 **ĐẠI NẠN TOP 1 - <@{t1_uid}>** bị thiên lôi truy sát!\n   └─ 📉 Hao tổn cực nặng: **-{t1_lost} EXP**\n\n"

    # 4. XỬ LÝ 2 NGƯỜI CÒN LẠI (Sét đánh thường: 100-500 EXP)
    for user in victims_others:
        uid = user.get("_id")
        current_exp = user.get("exp", 0)
        lost_exp = random.randint(100, 500)
        new_exp = max(0, current_exp - lost_exp)
        
        await users_col.update_one({"_id": uid}, {"$set": {"exp": new_exp}})
        report_msg += f"⚡ **<@{uid}>** bị lôi đình đánh trúng!\n   └─ 📉 Hao tổn: **-{lost_exp} EXP**\n\n"

    # 5. Gửi Embed kết quả
    embed = discord.Embed(
        title="⛈️ THIÊN PHẠT BẢNG VÀNG ⛈️",
        description=report_msg,
        color=discord.Color.from_rgb(255, 0, 0) # Màu đỏ cảnh báo
    )
    embed.set_image(url="https://i.imgur.com/K6Y0X9E.gif") 
    embed.set_footer(text=f"Thiên đạo công minh - Người thi triển: {interaction.user.display_name}")
    
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="ban_exp", description="Cấm túc tu sĩ: Không cho nhận EXP trong 6 tiếng")
async def ban_exp(interaction: discord.Interaction, target: discord.Member):
    # 1. Kiểm tra quyền Admin tối thượng
    if interaction.user.id != ADMIN_ID:
        return await interaction.response.send_message("⛔ Ngươi không đủ quyền hạn để thi triển pháp thuật này!", ephemeral=True)

    await interaction.response.defer()

    try:
        # 2. Tính toán thời gian hết hạn (dạng timestamp số)
        # 6 tiếng = 6 * 3600 giây
        ban_duration = 6 * 3600 
        expire_timestamp = time.time() + ban_duration
        
        # 3. Cập nhật vào Database
        await users_col.update_one(
            {"_id": str(target.id)},
            {"$set": {"ban_exp_until": expire_timestamp}},
            upsert=True
        )

        # 4. Hiển thị thời gian hết hạn cho tu sĩ dễ nhìn
        expire_dt = datetime.fromtimestamp(expire_timestamp).strftime('%H:%M:%S %d/%m/%Y')
        
        await interaction.followup.send(
            f"🚫 **THIẾT LUẬT CHẤP PHÁP** 🚫\n"
            f"Tu sĩ {target.mention} đã bị phong tỏa linh mạch (Cấm EXP) trong **6 tiếng**.\n"
            f"Thời hạn giải ấn: `{expire_dt}`"
        )
    except Exception as e:
        print(f"❌ Lỗi lệnh ban_exp: {e}")
        await interaction.followup.send("⚠️ Pháp trận gặp lỗi khi thực thi lệnh cấm.")
@bot.tree.command(name="unban_exp", description="Đại xá thiên hạ: Gỡ bỏ lệnh cấm EXP cho tu sĩ")
async def unban_exp(interaction: discord.Interaction, target: discord.Member):
    # 1. Kiểm tra quyền Admin tối thượng (Cách 2)
    if interaction.user.id != ADMIN_ID:
        return await interaction.response.send_message(
            "⛔ Cảnh giới của ngươi không đủ để ban lệnh Đại Xá!", 
            ephemeral=True
        )

    # 2. Xóa bỏ mốc thời gian cấm trong Database
    # Sử dụng $unset để loại bỏ hoàn toàn trường dữ liệu này
    result = await users_col.update_one(
        {"_id": str(target.id)},
        {"$unset": {"ban_exp_until": ""}} 
    )

    # 3. Thông báo kết quả
    if result.modified_count > 0:
        await interaction.response.send_message(
            f"✨ **ĐẠI XÁ THIÊN HẠ** ✨\n"
            f"Đạo hữu {target.mention} đã được gỡ bỏ cấm túc. "
            f"Từ nay đã có thể tiếp tục hấp thụ linh khí (EXP) bình thường!"
        )
    else:
        await interaction.response.send_message(
            f"❓ Tu sĩ {target.mention} hiện đang không trong trạng thái bị cấm túc.",
            ephemeral=True
        )
@bot.tree.command(name="pay", description="Chuyển linh thạch cho đạo hữu khác")
@app_commands.describe(member="Người nhận linh thạch", amount="Số lượng linh thạch muốn chuyển")
async def pay(interaction: discord.Interaction, member: discord.Member, amount: int):
    # Tránh các lỗi cơ bản
    if amount <= 0:
        return await interaction.response.send_message("❌ Số lượng chuyển phải lớn hơn 0!", ephemeral=True)
    if member.id == interaction.user.id:
        return await interaction.response.send_message("❌ Đạo hữu không thể tự chuyển cho chính mình!", ephemeral=True)
    if member.bot:
        return await interaction.response.send_message("❌ Không thể chuyển linh thạch cho thực thể nhân tạo (Bot)!", ephemeral=True)

    uid = str(interaction.user.id)
    u = await users_col.find_one({"_id": uid})
    
    # Kiểm tra số dư trước khi hiện nút
    current_lt = u.get("linh_thach", 0) if u else 0
    if current_lt < amount:
        return await interaction.response.send_message(f"❌ Bạn không đủ linh thạch (Hiện có: `{current_lt}`)", ephemeral=True)

    # Khởi tạo giao diện xác nhận
    view = ConfirmTransfer(interaction.user, member, amount)
    await interaction.response.send_message(
        f"📜 **XÁC NHẬN GIAO DỊCH**\nĐạo hữu có chắc muốn chuyển **{amount} Linh thạch** cho **{member.mention}** không?\n*(Nút bấm sẽ hết hạn sau 30 giây)*",
        view=view
    )


@bot.tree.command(name="add", description="[ADMIN] Ban thưởng Linh thạch cho tu sĩ")
@app_commands.describe(target="Tu sĩ được ban thưởng", so_luong="Số lượng linh thạch")
async def add(interaction: discord.Interaction, target: discord.Member, so_luong: int):
    # 1. Kiểm tra quyền Admin (Sử dụng ADMIN_ID đã khai báo của đạo hữu)
    if interaction.user.id != ADMIN_ID:
        return await interaction.response.send_message("❌ **THIÊN PHẠT!** Bạn không có quyền năng này.", ephemeral=True)

    if so_luong <= 0:
        return await interaction.response.send_message("❌ Số lượng phải lớn hơn 0!", ephemeral=True)

    await interaction.response.defer()
    tid = str(target.id)

    # 2. Cập nhật trực tiếp (Nếu chưa có user thì tự tạo hồ sơ mới)
    await users_col.update_one(
        {"_id": tid},
        {"$inc": {"linh_thach": so_luong}},
        upsert=True
    )

    # 3. Hiển thị thông báo (Giữ nguyên rực rỡ)
    embed = discord.Embed(
        title="✨ THIÊN BAN LINH VẬT ✨",
        description=(
            f"Bậc đại năng **{interaction.user.display_name}** đã giáng lâm!\n"
            f"Ban thưởng cho **{target.mention}** **{so_luong:,} Linh thạch**."
        ),
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url="https://i.imgur.com/39A72Pj.png")
    
    await interaction.followup.send(embed=embed)

keep_alive()
token = os.getenv("DISCORD_TOKEN")
bot.run(token)



















































