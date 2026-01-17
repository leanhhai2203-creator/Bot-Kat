from keep_alive import keep_alive
import os
import discord
from discord.ext import commands, tasks
import random
from datetime import datetime
from discord import app_commands
import motor.motor_asyncio
import asyncio

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

# Danh sách khẩu lệnh cực ngầu
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
        "atk": 70, 
        "drop_buff": 0.1, 
        "effect": "Tăng 10% rơi đồ", 
        "color": 0xe74c3c,
        "icon": "🔥"
    },
    "Băng Tinh Hổ": {
        "atk": 60, 
        "break_buff": 5, 
        "effect": "Tăng 5% tỉ lệ đột phá", 
        "color": 0x3498db,
        "icon": "❄️"
    },
    "Thôn Phệ Thú": {
        "atk": 55, 
        "exp_mult": 1.15, 
        "effect": "Tăng 15% EXP", 
        "color": 0x9b59b6,
        "icon": "🐾"
    },
    "Huyền Quy": {
        "atk": 55, 
        "risk_reduce": 0.5, 
        "effect": "Giảm 50% rủi ro Lôi Kiếp", 
        "color": 0x2ecc71,
        "icon": "🐢"
    },
    "Hóa Hình Hồ Ly": {
        "atk": 65,
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
    atk, hp = lv * 5, lv * 50
    for t in EQ_TYPES:
        eq_lv = eq.get(t, 0)
        if t in ("Kiếm", "Nhẫn"): atk += eq_lv * 15
        else: hp += eq_lv * 150
    if pet_name in PET_CONFIG: atk += PET_CONFIG[pet_name].get("atk", 0)
    return int((atk * 10) + hp + random.randint(0, 100))

async def add_exp(uid: str, amount: int):
    uid = str(uid)
    u = await users_col.find_one({"_id": uid})
    if not u or (u["level"] % 10 == 0 and u["exp"] >= exp_needed(u["level"])): return
    await users_col.update_one({"_id": uid}, {"$inc": {"exp": amount}})

async def check_level_up(uid, channel, name):
    uid = str(uid)
    u = await users_col.find_one({"_id": uid})
    if not u: return
    
    lv, exp = u.get("level", 1), u.get("exp", 0)
    new_lv = lv
    leveled = False

    # Vòng lặp kiểm tra tăng cấp
    while exp >= exp_needed(new_lv):
        # CHỐT CHẶN: Nếu cấp hiện tại là 10, 20, 30... thì DỪNG LẠI không cho lên tiếp
        if new_lv % 10 == 0:
            break
            
        exp -= exp_needed(new_lv)
        new_lv += 1
        leveled = True
        
        # Giới hạn cấp độ tối đa nếu cần (ví dụ 100)
        if new_lv >= 100: break

    if leveled:
        await users_col.update_one(
            {"_id": uid}, 
            {"$set": {"level": new_lv, "exp": exp}}
        )
        embed = discord.Embed(
            title="✨ CẢNH GIỚI PHI THĂNG ✨", 
            description=f"Chúc mừng đạo hữu **{name}** đã lên **Cấp {new_lv}**!\n🧘 **{get_realm(new_lv)}**", 
            color=discord.Color.green()
        )
        if channel: await channel.send(embed=embed)
    else:
        # Nếu không tăng cấp (do kẹt mốc 10) thì vẫn phải cập nhật lại lượng EXP dư
        await users_col.update_one({"_id": uid}, {"$set": {"exp": exp}})

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

# ========== EVENTS ==========
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Đã đồng bộ {len(synced)} lệnh Slash. Bot sẵn sàng!")
        if not thien_y_loop.is_running(): thien_y_loop.start()
    except Exception as e: print(f"❌ Lỗi: {e}")
@bot.event
async def on_message(message):
    if message.author.bot: return
    
    uid = str(message.author.id)
    now = datetime.now().timestamp()
    content = message.content.strip().lower()

    # 1. CHỐNG TRÙNG LẶP
    if content == last_msg_content.get(uid):
        return 

    # 2. KIỂM TRA ĐỘ DÀI & COOLDOWN
    if len(content) >= MIN_MSG_LEN and now - last_msg_time.get(uid, 0) >= MSG_COOLDOWN:
        last_msg_time[uid] = now
        last_msg_content[uid] = content
        
        # 3. LẤY DỮ LIỆU TỪ DB
        user_data = await users_col.find_one({"_id": uid})
        if not user_data:
            user_data = {"level": 1, "exp": 0, "linh_thach": 10, "pet": None}
            await users_col.insert_one({"_id": uid, **user_data})

        # 4. TÍNH TOÁN EXP CƠ BẢN
        rate = CHANNEL_EXP_RATES.get(message.channel.id, 0.1)
        base_exp = int(MSG_EXP * rate)
        pet_bonus = 0
        
        # --- LOGIC THẢ ICON THEO PET & CỘNG THÊM EXP ---
        user_pet = user_data.get("pet")
        
        if user_pet in PET_ICONS:
            # A. Luôn thả icon của Pet đó nếu tin nhắn hợp lệ
            try:
                await message.add_reaction(PET_ICONS[user_pet])
            except:
                pass

            # B. Riêng Thôn Phệ Thú có tỷ lệ cộng thêm EXP (Bonus)
            if user_pet == "Thôn Phệ Thú" and random.random() < 0.30:
                pet_bonus = random.randint(5, 15)
                # Nếu muốn Pet giúp sức thì thả thêm 1 icon lấp lánh
                try: await message.add_reaction("✨")
                except: pass
        # ----------------------------------------------

        total_gain = base_exp + pet_bonus
        
        # 5. CẬP NHẬT DATABASE & CHECK LEVEL
        await add_exp(uid, total_gain)
        await check_level_up(uid, message.channel, message.author.display_name)
        
    await bot.process_commands(message)
# ========== LỆNH SLASH (/) ==========

@bot.tree.command(name="check", description="Xem thông tin cá nhân")
async def check(interaction: discord.Interaction):
    await interaction.response.defer()
    uid = str(interaction.user.id)
    u = await users_col.find_one_and_update({"_id": uid}, {"$setOnInsert": {"level": 1, "exp": 0, "linh_thach": 10}}, upsert=True, return_document=True)
    eq = await eq_col.find_one({"_id": uid}) or {}
    power = await calc_power(uid)
    pet_name = u.get("pet")
    pet_text = f"**{pet_name}**" if pet_name in PET_CONFIG else "Chưa thu phục"
    eq_text = "\n".join([f"• {t}: cấp {eq.get(t, '➖')}" for t in EQ_TYPES])
    
    embed = discord.Embed(title=f"📜 TRẠNG THÁI: {interaction.user.display_name}", description=f"**Cảnh giới:** {get_realm(u['level'])}", color=0x3498db)
    embed.add_field(name="🔮 Tu vi", value=f"Cấp {u['level']} (EXP: {u['exp']})")
    embed.add_field(name="⚡ Lực chiến", value=f"**{power:,}**")
    embed.add_field(name="💎 Linh thạch", value=f"{u.get('linh_thach', 0)}")
    embed.add_field(name="🐾 Linh thú", value=pet_text, inline=False)
    embed.add_field(name="🧰 Trang bị", value=eq_text, inline=False)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="diemdanh", description="Điểm danh nhận quà")
async def diemdanh(interaction: discord.Interaction):
    await interaction.response.defer()
    uid, today = str(interaction.user.id), datetime.now().strftime("%Y-%m-%d")
    u = await users_col.find_one_and_update({"_id": uid}, {"$setOnInsert": {"level": 1, "exp": 0, "linh_thach": 10}}, upsert=True, return_document=True)
    
    if u.get("last_daily") == today: return await interaction.followup.send("❌ Hôm nay đã điểm danh rồi!")
    
    reward = exp_needed(u["level"])
    await users_col.update_one({"_id": uid}, {"$set": {"last_daily": today}, "$inc": {"exp": reward, "linh_thach": 1}})
    await check_level_up(uid, interaction.channel, interaction.user.display_name)
    await interaction.followup.send(f"✅ Điểm danh thành công! +{reward} EXP, +1 Linh thạch.")

@bot.tree.command(name="gacha", description="Gacha trang bị & Linh thú độc bản (Tốn 1 Linh thạch sau 3 lượt)")
async def gacha(interaction: discord.Interaction):
    await interaction.response.defer()
    uid = str(interaction.user.id)
    today = datetime.now().strftime("%Y-%m-%d")

    # Lấy data user
    u = await users_col.find_one({"_id": uid})
    if not u:
        # Khởi tạo nếu chưa có hồ sơ
        u = {"_id": uid, "linh_thach": 10, "gacha_count": 0, "last_gacha_day": ""}
        await users_col.insert_one(u)

    gacha_count = u.get("gacha_count", 0) if u.get("last_gacha_day") == today else 0
    linh_thach = u.get("linh_thach", 0)
    cost = 0 if gacha_count < 3 else 1

    # 1. KIỂM TRA ĐIỀU KIỆN
    if linh_thach < cost:
        return await interaction.followup.send(f"❌ Đạo hữu không đủ **{cost} Linh thạch** để tiếp tục.")

    # 2. LOGIC GACHA LINH THÚ (ĐỘC BẢN - CHUYỂN SANG MONGODB)
    pet_msg = ""
    if not u.get("pet"): 
        if random.random() <= 0.005: 
            # Tìm danh sách pet ĐÃ CÓ CHỦ bằng lệnh distinct
            owned_pets = await users_col.distinct("pet", {"pet": {"$ne": None}})
            available_pets = [p for p in PET_CONFIG.keys() if p not in owned_pets]
            
            if available_pets:
                pet_got = random.choice(available_pets)
                # Cập nhật ngay lập tức vào MongoDB
                await users_col.update_one({"_id": uid}, {"$set": {"pet": pet_got}})
                pet_msg = f"\n🎊 **THIÊN CƠ!** Đạo hữu là người duy nhất thu phục được: **{pet_got}**!"
            else:
                pet_msg = "\n⚠️ *Thiên hạ Linh thú đã có chủ hết, không còn con nào vô chủ để thu phục.*"

    # 3. LOGIC GACHA TRANG BỊ
    eq_type = random.choice(EQ_TYPES)
    lv = random.choices(range(1, 11), weights=[25, 20, 15, 10, 10, 8, 5, 3, 3, 1])[0]
    
    # Thay thế hàm save_equipment bằng logic trực tiếp
    current_eq = await eq_col.find_one({"_id": uid}) or {}
    old_lv = current_eq.get(eq_type, 0)
    
    if lv > old_lv:
        await eq_col.update_one({"_id": uid}, {"$set": {eq_type: lv}}, upsert=True)
        msg = f"🎁 Nhận được **{eq_type} cấp {lv}**"
    else:
        msg = f"🗑️ **{eq_type} cấp {lv}** quá yếu, đã phân rã"

    # 4. CẬP NHẬT DATABASE (Gộp chung các thay đổi để tối ưu)
    new_gacha_count = gacha_count + 1
    await users_col.update_one(
        {"_id": uid},
        {
            "$set": {"gacha_count": new_gacha_count, "last_gacha_day": today},
            "$inc": {"linh_thach": -cost}
        }
    )

    # 5. HIỂN THỊ
    status = f"🎰 Lượt: **{new_gacha_count}/3** (Free)" if new_gacha_count <= 3 else f"💎 Phí: **{cost} Linh thạch**"
    embed = discord.Embed(
        title="🔮 KẾT QUẢ GACHA 🔮",
        description=f"{msg}{pet_msg}\n\n{status}",
        color=discord.Color.gold() if "🎊" in pet_msg else discord.Color.blue()
    )
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
    required_lt = 1 if lv < 30 else (3 if lv < 60 else (6 if lv < 90 else 12))
    if linh_thach < required_lt:
        return await interaction.followup.send(f"❌ Cần **{required_lt} Linh thạch**. Đạo hữu chỉ có: **{linh_thach}**")

    # 4. TỈ LỆ THÀNH CÔNG (Giữ nguyên công thức: 100 - realm*8)
    realm_index = lv // 10
    base_rate = max(10, 100 - (realm_index * 8))
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
            base_tut_cap = random.randint(2, 3)
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
    embed.set_thumbnail(url="https://i.imgur.com/vHInX9T.png") 

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




















