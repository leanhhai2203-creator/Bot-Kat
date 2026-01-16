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

# Các kênh nhận thông báo quan trọng
NOTIFY_CHANNELS = [1455081842473697362, 1455837230332641280, 1454793019160006783, 1454793109094268948, 1454506037779369986] 
CHANNEL_EXP_RATES = {
    1455081842473697362: 0.3, 1455837230332641280: 0.3,
    1454793019160006783: 0.3, 1454793109094268948: 0.3,
    1454506037779369986: 1.5, 1461017212365181160: 1.2
}

# --- CẤU HÌNH CẢNH GIỚI & LINH THÚ ---
REALMS = [
    ("Luyện Khí", 10), ("Trúc Cơ", 20), ("Kết Đan", 30),
    ("Nguyên Anh", 40), ("Hóa Thần", 50), ("Luyện Hư", 60),
    ("Hợp Thể", 70), ("Đại Thừa", 80),
    ("Đại Tiên", 90), ("Thiên Tiên", 100)
]

EQ_TYPES = ["Kiếm", "Nhẫn", "Giáp", "Tay", "Ủng"]
PET_CONFIG = {
    "Tiểu Hỏa Phượng": {"atk": 50, "effect": "Tăng 10% rơi đồ", "color": 0xe74c3c},
    "Băng Tinh Hổ": {"atk": 45, "effect": "Tăng 5% tỉ lệ đột phá", "color": 0x3498db},
    "Thôn Phệ Thú": {"atk": 40, "effect": "Tăng 15% EXP","exp_mult": 1.15, "color": 0x9b59b6},
    "Huyền Quy": {"atk": 30, "effect": "Giảm 50% rủi ro Lôi Kiếp", "color": 0x2ecc71},
    "Hóa Hình Hồ Ly": {"atk": 35, "effect": "X2 tỉ lệ rơi Linh Thạch", "color": 0xff99cc}
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
    uid, now = str(message.author.id), datetime.now().timestamp()
    if len(message.content.strip()) >= MIN_MSG_LEN and now - last_msg_time.get(uid, 0) >= MSG_COOLDOWN:
        last_msg_time[uid] = now
        rate = CHANNEL_EXP_RATES.get(message.channel.id, 0.1)
        await users_col.update_one({"_id": uid}, {"$setOnInsert": {"level": 1, "exp": 0, "linh_thach": 10, "pet": None}}, upsert=True)
        await add_exp(uid, int(MSG_EXP * rate))
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
    if not u: return await interaction.followup.send("❌ Đạo hữu chưa có hồ sơ tu tiên!")

    lv = u.get("level", 1)
    linh_thach = u.get("linh_thach", 0)
    exp = u.get("exp", 0)

    if lv % 10 != 0:
        return await interaction.followup.send(f"❌ Cần đạt mốc **10 cấp** để đột phá. Hiện tại: **Lv {lv}**")

    needed = exp_needed(lv)
    if exp < needed:
        return await interaction.followup.send(f"❌ Chưa đủ EXP! (Cần {exp}/{needed})")

    # Tính linh thạch yêu cầu
    required_lt = 1 if lv < 30 else (3 if lv < 60 else (6 if lv < 90 else 12))

    if linh_thach < required_lt:
        return await interaction.followup.send(f"❌ Cần **{required_lt} Linh thạch**. Bạn có: **{linh_thach}**")

    # Tỉ lệ thành công
    realm_index = lv // 10
    rate = max(10, 100 - realm_index * 8)
    success = random.randint(1, 100) <= rate

    if success:
        await users_col.update_one(
            {"_id": uid},
            {"$set": {"level": lv + 1, "exp": 0}, "$inc": {"linh_thach": -required_lt}}
        )
        quote = random.choice(KHAU_NGU)
        embed = discord.Embed(
            title="🔥 ĐỘT PHÁ THÀNH CÔNG 🔥",
            description=f"*{quote}*\n\n🎉 **{interaction.user.display_name}** đã lên **{get_realm(lv + 1)}**!",
            color=discord.Color.gold()
        )
        # Thông báo kênh chung
        for ch_id in NOTIFY_CHANNELS:
            channel = bot.get_channel(ch_id)
            if channel: await channel.send(embed=embed)
    else:
        # THẤT BẠI + LOGIC LÔI KIẾP
        tut_cap = 1
        loi_kiep_msg = ""
        if lv >= 30 and random.randint(1, 100) <= 25:
            tut_cap = random.randint(2, 3)
            loi_kiep_msg = "⚡ **LÔI KIẾP BẤT NGỜ!** Đạo hữu bị đánh văng tu vi!"

        # Cập nhật tụt cấp (Không để level thấp hơn 1)
        new_lv = max(1, lv - tut_cap)
        await users_col.update_one(
            {"_id": uid},
            {"$set": {"level": new_lv}, "$inc": {"linh_thach": -required_lt}}
        )
        
        embed = discord.Embed(
            title="💥 ĐỘT PHÁ THẤT BẠI 💥",
            description=f"😔 **{interaction.user.display_name}** thất bại!\n{loi_kiep_msg}\n📉 Giảm: **{tut_cap} cấp**\n💸 Mất: **{required_lt} Linh thạch**",
            color=discord.Color.red()
        )

    await interaction.followup.send(embed=embed)
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
    
    # 1. Lấy Top 10 cao thủ từ MongoDB
    top_users = await users_col.find().sort([("level", -1), ("exp", -1)]).limit(10).to_list(length=10)
    
    if not top_users:
        return await interaction.followup.send("⚠️ Chưa có tu sĩ nào ghi danh trên bảng vàng.")

    description = ""
    for i, user in enumerate(top_users):
        uid = int(user.get("_id")) # Chuyển ID sang số nguyên
        lv = user.get("level", 1)
        exp = user.get("exp", 0)
        pet = user.get("pet", "Không")
        
        # --- PHẦN SỬA: LẤY TÊN THAY VÌ ID ---
        member = interaction.guild.get_member(uid)
        if member:
            # Lấy tên hiển thị trong server (Nickname)
            name_display = f"**{member.display_name}**"
        else:
            # Nếu không tìm thấy trong server thì dùng Mention để Discord tự hiện tên
            name_display = f"<@{uid}>"
            
        # Biểu tượng cho Top 3
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"**#{i+1}**"
        
        description += f"{medal} {name_display} - **Cấp {lv}** ({exp} EXP) | 🐾: {pet}\n"

    # 2. Tạo giao diện Embed
    embed = discord.Embed(
        title="🏆 BẢNG XẾP HẠNG TU TIÊN 🏆",
        description=description,
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    
    embed.set_footer(text="Cập nhật theo thời gian thực")
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
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. Lấy và khởi tạo User (thay cho create_user/get_user)
    u = await users_col.find_one_and_update(
        {"_id": uid},
        {"$setOnInsert": {
            "level": 1, "exp": 0, "linh_thach": 10, "pet": None,
            "attack_count": 0, "last_attack": ""
        }},
        upsert=True,
        return_document=True
    )

    # Kiểm tra lượt đánh
    attack_count = u.get("attack_count", 0) if u.get("last_attack") == today else 0
    if attack_count >= 3:
        return await interaction.followup.send("❌ Đạo hữu đã cạn kiệt linh lực. Hãy tịnh dưỡng đến ngày mai!")

    # 2. Dữ liệu Linh thú & Quái vật (Giữ nguyên logic của đạo hữu)
    pet_name = u.get("pet")
    pet_data = PET_CONFIG.get(pet_name, {"atk": 0, "effect": "Không", "exp_mult": 1.0, "lt_chance": 30})
    monster, drop_rate, eq_range = get_monster_data(u["level"])
    
    # 3. Tính toán chỉ số
    total_atk = (u["level"] * 10) + pet_data.get("atk", 0)
    base_exp = exp_needed(u["level"]) // 5
    exp_gain = int(base_exp * pet_data.get("exp_mult", 1.0))
    
    lt_chance = pet_data.get("lt_chance", 30) 
    lt_gain = random.randint(1, 5) if random.randint(1, 100) <= lt_chance else 0

    # 4. Kiểm tra bình cảnh (Chặn EXP tại cấp 10, 20...)
    can_gain_exp = True
    if u["level"] % 10 == 0:
        if u["exp"] >= exp_needed(u["level"]):
            can_gain_exp = False
            exp_gain = 0

    # 5. Logic rơi trang bị (Ghi trực tiếp vào eq_col)
    drop_msg = ""
    final_drop_rate = drop_rate + pet_data.get("drop_buff", 0)
    if random.random() <= final_drop_rate:
        eq_type = random.choice(EQ_TYPES)
        eq_lv = random.randint(*eq_range)
        
        # Logic save_equipment trên MongoDB
        current_eq = await eq_col.find_one({"_id": uid}) or {}
        if eq_lv > current_eq.get(eq_type, 0):
            await eq_col.update_one({"_id": uid}, {"$set": {eq_type: eq_lv}}, upsert=True)
            drop_msg = f"\n🎁 **VẬN MAY!** Nhận được: `{eq_type} Cấp {eq_lv}`"
        else:
            drop_msg = f"\n🗑️ Đánh rơi `{eq_type} Cấp {eq_lv}` nhưng phẩm chất quá thấp."

    # 6. Logic hồi lượt (Thôn Phệ Thú)
    actual_count_inc = 1
    refund_msg = ""
    if pet_name == "Thôn Phệ Thú" and random.randint(1, 100) <= 20:
        actual_count_inc = 0
        refund_msg = "\n🌀 **Thôn Phệ Thú** hấp thụ linh khí, giúp bạn không tốn thể lực!"

    # 7. CẬP NHẬT DATABASE (Sử dụng $inc và $set)
    await users_col.update_one(
        {"_id": uid},
        {
            "$inc": {"exp": exp_gain, "linh_thach": lt_gain, "attack_count": actual_count_inc},
            "$set": {"last_attack": today}
        }
    )

    # 8. Hiển thị (Giữ nguyên giao diện của đạo hữu)
    embed = discord.Embed(
        title="⚔️ TRẬN CHIẾN KẾT THÚC",
        description=f"Đạo hữu vung kiếm tiêu diệt **{monster}**!",
        color=discord.Color.green() if exp_gain > 0 else discord.Color.orange()
    )
    exp_info = f"📈 Kinh nghiệm: **+{exp_gain} EXP**" if can_gain_exp else "⚠️ **BÌNH CẢNH!** Hãy `/dotpha` ngay."
    lt_info = f"\n💎 Linh thạch: **+{lt_gain}**" if lt_gain > 0 else ""
    
    embed.add_field(name="Chiến lợi phẩm", value=f"{exp_info}{lt_info}{drop_msg}{refund_msg}", inline=False)
    embed.set_footer(text=f"Lực chiến: {total_atk} | Lượt đánh còn lại: {3 - (attack_count + actual_count_inc)}")
    
    await interaction.followup.send(embed=embed)
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




