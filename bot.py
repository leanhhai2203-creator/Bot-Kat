from keep_alive import keep_alive
import discord
from discord.ext import commands, tasks
import aiosqlite
import random
from datetime import datetime
from discord import app_commands

# ========== CONFIG ==========
import os
TOKEN = os.getenv("DISCORD_TOKEN")
INTENTS = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=INTENTS)

DB_PATH = "game.db"
MAX_LEVEL = 100
ADMIN_ID = 472564016917643264 

MSG_EXP = 10
# --- CẤU HÌNH THIÊN Ý ---
THIEN_Y_QUOTES = [
    "🌤️ Thiên địa mở mang, linh khí tràn trề, toàn dân hưởng phúc!",
    "🌈 Thụy tường giáng thế, một luồng tiên khí gột rửa thân tâm!",
    "✨ Chân tiên hiển thánh, ban phát cơ duyên cho chúng sinh!"
]

TA_NIEM_QUOTES = [
    "🌑 Ma khí trỗi dậy, tâm ma xâm chiếm lục địa!",
    "⚡ Thiên nộ giáng lâm, vạn vật bị tước đoạt linh khí!",
    "🌪️ Hư không dao động, tu vi chúng sinh bị cắn trả!"
]

@tasks.loop(hours=4.8)
async def thien_y_loop():
    async with aiosqlite.connect(DB_PATH) as db:
        is_thien_y = random.choice([True, False])
        percent = random.randint(5, 10)
        
        if is_thien_y:
            title, color = "✨ THIÊN Ý GIÁNG LÂM ✨", discord.Color.gold()
            quote = random.choice(THIEN_Y_QUOTES)
            await db.execute("UPDATE users SET exp = exp + (exp * ? / 100)", (percent,))
            msg = f"Tất cả đạo hữu được ban phúc, tăng **{percent}%** EXP tu vi!"
        else:
            title, color = "🌑 TÀ NIỆM PHÁT TÁC 🌑", discord.Color.dark_purple()
            quote = random.choice(TA_NIEM_QUOTES)
            await db.execute("UPDATE users SET exp = MAX(0, exp - (exp * ? / 100))", (percent,))
            msg = f"Cảnh báo! Tâm ma quấy nhiễu, chúng sinh bị tổn hao **{percent}%** EXP!"
        
        await db.commit()

        # PHẦN GỬI EMBED PHẢI NẰM Ở ĐÂY (Thụt lề thẳng hàng với async with)
        embed = discord.Embed(title=title, description=f"*{quote}*\n\n{msg}", color=color)
        for channel_id in NOTIFY_CHANNELS:
            channel = bot.get_channel(channel_id)
            if channel:
                try: await channel.send(embed=embed)
                except: pass
KHAU_NGU = [
    "Thiên địa biến sắc, linh khí hội tụ về một điểm!",
    "Vạn dặm mây tím kéo đến, điềm lành báo hiệu một bậc kỳ tài xuất thế!",
    "Tiếng rồng ngâm hổ gầm vang vọng khắp cửu tiêu!",
    "Đạo vận viên mãn, thân thể thoát thai hoán cốt!",
    "Trải qua vô vàn khổ hạnh, cuối cùng cũng chạm đến chân lý!"
]
NOTIFY_CHANNELS = [1455081842473697362, 1455837230332641280, 1454793019160006783, 1454793109094268948, 1454506037779369986] 
CHANNEL_EXP_RATES = {
    1455081842473697362: 0.2,
    1455837230332641280: 0.2,
    1454793019160006783: 0.2,
    1454793109094268948: 0.2,
    1454506037779369986: 1.5,
}
MIN_MSG_LEN = 7
MSG_COOLDOWN = 20
last_msg_time = {}

# ========== DATA ==========
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

# ========== DATABASE ==========
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Cấu trúc bảng users
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            exp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            last_daily TEXT,
            last_gacha TEXT,
            attack_count INTEGER DEFAULT 0,
            last_attack TEXT,
            linh_thach INTEGER DEFAULT 0,
            dotpha INTEGER DEFAULT 0,
            gacha_count INTEGER DEFAULT 0,
            last_gacha_day TEXT,
            pet TEXT DEFAULT NULL
        )
        """)

        # Cấu trúc bảng equipment
        await db.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            user_id INTEGER,
            type TEXT,
            level INTEGER
        )
        """)
        await db.commit()

# Hàm này phải nằm RIÊNG BIỆT, không thụt lề chung với init_db
async def upgrade_db():
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            # Lệnh này yêu cầu Database tự thêm cột 'pet' vào bảng 'users'
            await db.execute("ALTER TABLE users ADD COLUMN pet TEXT DEFAULT NULL")
            await db.commit()
            print("✅ Đã nâng cấp Database thành công: Thêm cột Linh thú!")
        except:
            # Nếu cột đã có rồi thì nó sẽ báo lỗi, ta dùng 'pass' để bỏ qua
            pass

# ========== UTIL ==========
async def create_user(uid: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM users WHERE user_id=?",
            (uid,)
        ) as cur:
            if await cur.fetchone() is None:
                await db.execute("""
                    INSERT INTO users (
                        user_id, exp, level, last_daily, last_gacha,
                        attack_count, last_attack,
                        linh_thach, dotpha, gacha_count, last_gacha_day
                    ) VALUES (?,0,1,NULL,NULL,0,NULL,0,0,0,NULL)
                """, (uid,))
                await db.commit()

async def get_user(uid: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id=?",
            (uid,)
        ) as cur:
            row = await cur.fetchone()
            if row is None:
                await create_user(uid)
                return await get_user(uid)
            return dict(row)

def get_monster_data(lv: int):
    if lv <= 10:
        return "Yêu thú", 0.15, (1, 2)   # Chỉ rơi đồ cấp 1-2
    elif lv <= 30:
        return "Ma thú", 0.20, (2, 4)   # Chỉ rơi đồ cấp 2-4
    elif lv <= 60:
        return "Linh thú", 0.25, (4, 7)  # Chỉ rơi đồ cấp 4-7
    else:
        return "Cổ thú", 0.30, (6, 9)   # Max là cấp 9, cấp 10 chỉ có ở Gacha

async def calc_power(uid: int) -> int:
    u = await get_user(uid) # Đảm bảo hàm này lấy đủ cột 'pet'
    eq = await get_equipment(uid)

    lv = u["level"]
    pet_name = u.get("pet") # Lấy tên linh thú từ DB

    # 1. Chỉ số cơ bản theo Level
    atk = lv * 5  
    hp = lv * 50  

    # 2. Cộng chỉ số từ trang bị
    for t, l in eq.items():
        if t in ("Kiếm", "Nhẫn"):
            atk += l * 15  
        elif t in ("Giáp", "Tay", "Ủng"):
            hp += l * 150  

    # 3. CỘNG CHỈ SỐ TỪ LINH THÚ (MỚI)
    # Truy xuất ATK từ bảng cấu hình PET_CONFIG
    pet_atk_bonus = 0
    if pet_name in PET_CONFIG:
        pet_atk_bonus = PET_CONFIG[pet_name]["atk"]
    
    atk += pet_atk_bonus

    # 4. Công thức Power: (ATK * 10) + HP
    total_power = (atk * 10) + hp
    
    # Luck factor (Biến động ngẫu nhiên)
    random_factor = random.randint(0, 100)
    
    return int(total_power + random_factor)
def exp_needed(lv: int):
    return 40 + lv * 8 if lv <= 50 else 200 + lv * 25

def get_realm(lv: int):
    for name, maxlv in REALMS:
        if lv <= maxlv:
            tầng = lv % 10 if lv % 10 else 10
            return f"{name} tầng {tầng}"
    return "Thiên Tiên viên mãn"

async def add_exp(uid: int, amount: int):
    u = await get_user(uid)
    # Nếu đang ở mốc cấp 10, 20, 30... và đã đủ EXP để đột phá
    if u["level"] % 10 == 0 and u["exp"] >= exp_needed(u["level"]):
        return # Ngừng cộng thêm EXP

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET exp = exp + ? WHERE user_id=?",
            (amount, uid)
        )
        await db.commit()

async def check_level_up(uid, channel, name):
    u = await get_user(uid)
    exp = u["exp"]
    lv = u["level"]
    leveled = False

    # Thêm điều kiện lv % 10 != 0 để dừng lại ngay khi chạm mốc đột phá
    while lv < MAX_LEVEL and exp >= exp_needed(lv) and lv % 10 != 0:
        exp -= exp_needed(lv)
        lv += 1
        leveled = True
        await channel.send(f"🎉 **{name} lên Lv {lv}!**\n🧘 {get_realm(lv)}")

    if leveled:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE users SET exp=?, level=? WHERE user_id=?",
                (exp, lv, uid)
            )
            await db.commit()
# ========== EQUIPMENT ==========
async def get_equipment(uid: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT type, MAX(level)
            FROM equipment
            WHERE user_id=?
            GROUP BY type
        """, (uid,)) as cur:
            rows = await cur.fetchall()
            # VD: {"Kiếm": 5, "Giáp": 3}
            return {r[0]: r[1] for r in rows}


async def save_equipment(uid: int, eq_type: str, lv: int) -> bool:
    # 🔒 KHÓA CẤP TRANG BỊ
    lv = min(lv, 10)

    eq = await get_equipment(uid)

    # Nếu đồ mới yếu hơn hoặc bằng → bỏ
    if lv <= eq.get(eq_type, 0):
        return False

    async with aiosqlite.connect(DB_PATH) as db:
        # Xóa đồ cũ cùng loại
        await db.execute(
            "DELETE FROM equipment WHERE user_id=? AND type=?",
            (uid, eq_type)
        )

        # Lưu đồ mới (auto trang bị)
        await db.execute(
            "INSERT INTO equipment (user_id, type, level) VALUES (?,?,?)",
            (uid, eq_type, lv)
        )
        await db.commit()

    return True
def calc_power_from_data(lv, eq):
    atk = lv * 2.2
    hp = lv * 22
    for t, l in eq.items():
        if t in ["Kiếm", "Nhẫn"]:
            atk += l * 6
        else:
            hp += l * 25
    return atk * 1.6 + hp * 0.55 + random.randint(0, 80)

# ========== EVENTS ==========
@bot.event
async def on_ready():
    # Bước 1: Tạo file và bảng dữ liệu ngay lập tức
    await init_db()
    
    # Bước 2: Nâng cấp cột nếu cần (như cột pet)
    await upgrade_db()

    # Bước 3: Đồng bộ lệnh Slash (/)
    try:
        synced = await bot.tree.sync()
        print(f"✅ Đã đồng bộ {len(synced)} lệnh Slash.")
    except Exception as e:
        print(f"❌ Lỗi đồng bộ lệnh: {e}")

    # Bước 4: Khởi động vòng lặp Thiên Ý sau khi DB đã sẵn sàng
    if not thien_y_loop.is_running():
        thien_y_loop.start()

    print(f"🚀 Bot {bot.user} đã sẵn sàng trên Render!")
@bot.event
async def on_message(message):
    # 1. Bỏ qua nếu tin nhắn từ bot khác hoặc chính nó
    if message.author.bot:
        return

    uid = message.author.id
    await create_user(uid)

    # 2. Xử lý logic cộng EXP
    now = datetime.now().timestamp()
    
    # Kiểm tra độ dài tin nhắn tối thiểu (MIN_MSG_LEN = 7)
    if len(message.content.strip()) >= MIN_MSG_LEN:
        # Kiểm tra thời gian chờ giữa 2 lần nhận EXP (MSG_COOLDOWN = 10s)
        if now - last_msg_time.get(uid, 0) >= MSG_COOLDOWN:
            last_msg_time[uid] = now
            
            # Lấy hệ số nhân của kênh từ danh sách CHANNEL_EXP_RATES
            # Nếu không có trong danh sách, mặc định là 1.0
            rate = CHANNEL_EXP_RATES.get(message.channel.id, 1.0)
            final_exp = int(MSG_EXP * rate)
            
            # Thực hiện cộng EXP và kiểm tra lên cấp
            await add_exp(uid, final_exp)
            await check_level_up(uid, message.channel, message.author.display_name)
    await bot.process_commands(message)

# ========== SLASH COMMANDS ==========
@bot.tree.command(name="check", description="Xem thông tin tu vi, trang bị và linh thú")
async def check(interaction: discord.Interaction):
    await interaction.response.defer()

    uid = interaction.user.id
    await create_user(uid)

    u = await get_user(uid)
    eq = await get_equipment(uid)
    
    # ✅ TÍNH TOÁN LỰC CHIẾN (Đã bao gồm Pet ở bước trước)
    power = await calc_power(uid)

    # 🐾 XỬ LÝ HIỂN THỊ LINH THÚ
    pet_name = u.get("pet")
    if pet_name in PET_CONFIG:
        pet_data = PET_CONFIG[pet_name]
        pet_text = f"**{pet_name}**\n└ ⚔️ ATK: +{pet_data['atk']}\n└ ✨ {pet_data['effect']}"
        embed_color = pet_data.get("color", 0x3498db) # Lấy màu theo pet hoặc mặc định xanh dương
    else:
        pet_text = "Chưa thu phục"
        embed_color = 0x7f8c8d # Màu xám khi không có pet

    # 🧰 XỬ LÝ TRANG BỊ
    eq_text = ""
    for t in EQ_TYPES:
        if t in eq:
            eq_text += f"• {t}: cấp {eq[t]}\n"
        else:
            eq_text += f"• {t}: ➖\n"

    # 📜 TẠO EMBED CHUYÊN NGHIỆP
    embed = discord.Embed(
        title=f"📜 BẢNG TRẠNG THÁI: {interaction.user.display_name}",
        description=f"**Cảnh giới:** {get_realm(u['level'])}",
        color=embed_color
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    # Các thông số chính
    embed.add_field(name="🔮 Tu vi", value=f"Cấp {u['level']} (EXP: {u['exp']})", inline=True)
    embed.add_field(name="⚡ Lực chiến", value=f"**{power}**", inline=True)
    embed.add_field(name="💎 Linh thạch", value=f"{u['linh_thach']}", inline=True)

    # Phần Linh thú và Trang bị
    embed.add_field(name="🐾 Linh thú trợ chiến", value=pet_text, inline=False)
    embed.add_field(name="🧰 Trang bị đang mang", value=eq_text, inline=False)

    # Footer hiển thị lượt đánh hôm nay
    today = datetime.now().strftime("%Y-%m-%d")
    atk_count = u.get("attack_count", 0) if u.get("last_attack") == today else 0
    embed.set_footer(text=f"Lượt đánh hôm nay: {atk_count}/3")

    await interaction.followup.send(embed=embed)
@bot.tree.command(name="gacha", description="Gacha trang bị & Linh thú độc bản (Tốn 1 Linh thạch sau 3 lượt)")
async def gacha(interaction: discord.Interaction):
    await interaction.response.defer()

    uid = interaction.user.id
    await create_user(uid)

    today = datetime.now().strftime("%Y-%m-%d")
    u = await get_user(uid)

    gacha_count = u["gacha_count"] if u["last_gacha_day"] == today else 0
    linh_thach = u["linh_thach"]
    cost = 0 if gacha_count < 3 else 1

    # 1. KIỂM TRA ĐIỀU KIỆN
    if cost > 0 and linh_thach < cost:
        return await interaction.followup.send(f"❌ Đạo hữu không đủ **{cost} Linh thạch** để tiếp tục.")

    # 2. LOGIC GACHA LINH THÚ (ĐỘC BẢN)
    pet_msg = ""
    # Chỉ cho quay Linh thú nếu người dùng CHƯA có linh thú
    if not u.get("pet"): 
        if random.random() <= 0.005: 
            async with aiosqlite.connect(DB_PATH) as db:
                # Tìm tất cả Linh thú đã có chủ
                async with db.execute("SELECT DISTINCT pet FROM users WHERE pet IS NOT NULL") as cursor:
                    owned_pets = [row[0] for row in await cursor.fetchall()]
                
                # Lọc danh sách Linh thú chưa ai sở hữu
                available_pets = [p for p in PET_CONFIG.keys() if p not in owned_pets]
                
                if available_pets:
                    pet_got = random.choice(available_pets)
                    await db.execute("UPDATE users SET pet = ? WHERE user_id = ?", (pet_got, uid))
                    await db.commit()
                    pet_msg = f"\n🎊 **THIÊN CƠ!** Đạo hữu là người duy nhất thu phục được: **{pet_got}**!"
                else:
                    pet_msg = "\n⚠️ *Thiên hạ Linh thú đã có chủ hết, không còn con nào vô chủ để thu phục.*"

    # 3. LOGIC GACHA TRANG BỊ (Giữ nguyên)
    eq_type = random.choice(EQ_TYPES)
    lv = random.choices(range(1, 11), weights=[25, 20, 15, 10, 10, 8, 5, 3, 3, 1])[0]
    saved = await save_equipment(uid, eq_type, lv)
    msg = f"🎁 Nhận được **{eq_type} cấp {lv}**" if saved else f"🗑️ **{eq_type} cấp {lv}** quá yếu, đã phân rã"

    # 4. CẬP NHẬT DATABASE
    gacha_count += 1
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users SET gacha_count=?, last_gacha_day=?, linh_thach = linh_thach - ? WHERE user_id=?
        """, (gacha_count, today, cost, uid))
        await db.commit()

    # 5. HIỂN THỊ
    status = f"🎰 Lượt: **{gacha_count}/3** (Free)" if gacha_count <= 3 else f"💎 Phí: **{cost} Linh thạch**"
    embed = discord.Embed(
        title="🔮 KẾT QUẢ GACHA 🔮",
        description=f"{msg}{pet_msg}\n\n{status}",
        color=discord.Color.gold() if "🎊" in pet_msg else discord.Color.blue()
    )
    await interaction.followup.send(embed=embed)
@bot.tree.command(name="solo", description="Thách đấu người chơi khác (Ẩn lực chiến, cược linh thạch)")
async def solo(
    interaction: discord.Interaction,
    target: discord.Member,
    linh_thach: int | None = None
):
    await interaction.response.defer()

    if interaction.user.id == target.id:
        return await interaction.followup.send("❌ Không thể tự solo với chính mình!")

    if target.bot:
        return await interaction.followup.send("❌ Không thể thách đấu với linh thể (Bot)!")

    # Đảm bảo user tồn tại trong hệ thống
    await create_user(interaction.user.id)
    await create_user(target.id)

    bet = linh_thach or 0
    u1 = await get_user(interaction.user.id)
    u2 = await get_user(target.id)

    # 1. KIỂM TRA ĐIỀU KIỆN CƯỢC
    if bet < 0:
        return await interaction.followup.send("❌ Số linh thạch không hợp lệ!")

    if bet > 0:
        if u1["linh_thach"] < bet or u2["linh_thach"] < bet:
            return await interaction.followup.send(f"❌ Một trong hai đạo hữu không đủ **{bet} linh thạch** để cược!")

    # 2. TÍNH TOÁN LỰC CHIẾN TRƯỚC (Để dùng khi bấm nút)
    p1_power = await calc_power(interaction.user.id)
    p2_power = await calc_power(target.id)

    # 3. ĐỊNH NGHĨA VIEW XÁC NHẬN SOLO
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
            # Kiểm tra lại linh thạch một lần nữa đề phòng đối phương đã tiêu hết
            curr_u1 = await get_user(interaction.user.id)
            curr_u2 = await get_user(target.id)
            
            if bet > 0 and (curr_u1["linh_thach"] < bet or curr_u2["linh_thach"] < bet):
                return await i.response.edit_message(content="❌ Trận đấu hủy bỏ! Một bên đã không còn đủ linh thạch.", view=None)

            # --- LOGIC THẮNG BẠI THEO TỈ LỆ ---
            total_power = p1_power + p2_power
            if total_power == 0: total_power = 1 # Tránh lỗi chia cho 0
            
            win_chance = p1_power / total_power
            roll = random.random()
            
            if roll <= win_chance:
                winner_id, winner_name = interaction.user.id, interaction.user.display_name
                winner_pet = curr_u1.get("pet")
                loser_name = target.display_name
            else:
                winner_id, winner_name = target.id, target.display_name
                winner_pet = curr_u2.get("pet")
                loser_name = interaction.user.display_name

            # --- XỬ LÝ CƯỢC LINH THẠCH ---
            if bet > 0:
                async with aiosqlite.connect(DB_PATH) as db:
                    # Trừ cược cả 2 bên
                    await db.execute("UPDATE users SET linh_thach = linh_thach - ? WHERE user_id IN (?, ?)", (bet, interaction.user.id, target.id))
                    # Cộng hũ cược cho người thắng
                    await db.execute("UPDATE users SET linh_thach = linh_thach + ? WHERE user_id = ?", (bet * 2, winner_id))
                    await db.commit()

            # --- HIỂN THỊ KẾT QUẢ ---
            p1_percent = round((p1_power / total_power) * 100, 1)
            p2_percent = round(100 - p1_percent, 1)
            pet_msg = f"\n🐾 Trợ lực từ linh thú **{winner_pet}** thật dũng mãnh!" if winner_pet else ""

            result_embed = discord.Embed(
                title="⚔️ TRẬN THƯ HÙNG KẾT THÚC ⚔️",
                description=(
                    f"🔵 **{interaction.user.display_name}**: {p1_power:,} LC ({p1_percent}% cơ hội)\n"
                    f"🔴 **{target.display_name}**: {p2_power:,} LC ({p2_percent}% cơ hội)\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🏆 Người thắng: **{winner_name}**\n"
                    f"💀 Kẻ bại: {loser_name}\n\n"
                    f"💰 Kết quả: " + (f"Thắng cược **{bet} Linh thạch**" if bet > 0 else "Vang danh thiên hạ") +
                    f"{pet_msg}"
                ),
                color=discord.Color.gold()
            )
            await i.response.edit_message(content=None, embed=result_embed, view=None)
            self.stop()

        @discord.ui.button(label="❌ Thủ Thế", style=discord.ButtonStyle.danger)
        async def decline(self, i: discord.Interaction, button: discord.ui.Button):
            await i.response.edit_message(content=f"❌ **{target.display_name}** đã chọn cách thủ thế, từ chối giao tranh.", embed=None, view=None)
            self.stop()

    # 4. GỬI CHIẾN THƯ (ẨN LỰC CHIẾN)
    invite_msg = (
        f"⚔️ **{interaction.user.display_name}** đã phát ra chiến thư thách đấu **{target.mention}**!\n"
        + (f"💎 Mức cược: **{bet} Linh thạch**" if bet > 0 else "🎲 Trận đấu giao hữu (Không cược)")
        + f"\n\n*Đạo hữu có dám tiếp chiến hay sẽ chọn con đường thoái lui?*"
    )
    await interaction.followup.send(content=invite_msg, view=SoloView())
@bot.tree.command(name="dotpha", description="Đột phá cảnh giới (Lôi kiếp từ cấp 30)")
async def dotpha(interaction: discord.Interaction):
    await interaction.response.defer()

    uid = interaction.user.id
    await create_user(uid)
    u = await get_user(uid)

    lv = u["level"]
    linh_thach = u["linh_thach"]
    exp = u["exp"]

    # 1. Kiểm tra mốc level (10, 20, 30...)
    if lv % 10 != 0:
        await interaction.followup.send(f"❌ Cần đạt mốc **10 cấp** để đột phá. Hiện tại: **Lv {lv}**")
        return

    # 2. Kiểm tra EXP
    needed = exp_needed(lv)
    if exp < needed:
        await interaction.followup.send(f"❌ Chưa đủ EXP! (Cần {exp}/{needed})")
        return

    # 3. Linh thạch yêu cầu (Cập nhật theo mốc mới)
    if lv < 30:
        required_lt = 1
    elif lv < 60:
        required_lt = 3
    elif lv < 90:
        required_lt = 6
    else:
        required_lt = 12

    if linh_thach < required_lt:
        await interaction.followup.send(f"❌ Cần **{required_lt} Linh thạch**. Hiện có: **{linh_thach}**")
        return

    # 4. Tỉ lệ thành công
    realm_index = lv // 10
    rate = max(10, 100 - realm_index * 8)
    success = random.randint(1, 100) <= rate

    async with aiosqlite.connect(DB_PATH) as db:
        if success:
            # Thành công
            await db.execute("UPDATE users SET level = level + 1, exp = 0, linh_thach = linh_thach - ? WHERE user_id = ?", (required_lt, uid))
            quote = random.choice(KHAU_NGU)
            embed = discord.Embed(
                title="🔥 ĐỘT PHÁ THÀNH CÔNG 🔥",
                description=f"*{quote}*\n\n🎉 Chúc mừng **{interaction.user.display_name}**!\n🧘 Cảnh giới: **{get_realm(lv + 1)}**\n💎 Tiêu hao: **{required_lt} Linh thạch**",
                color=discord.Color.gold()
            )
            for ch_id in NOTIFY_CHANNELS:
                channel = bot.get_channel(ch_id)
                if channel: 
                    try: await channel.send(embed=embed)
                    except: pass
        else:
            # THẤT BẠI + LOGIC LÔI KIẾP MỚI (TỪ CẤP 30)
            is_loi_kiep = False
            tut_cap = 1
            loi_kiep_msg = ""
            
            # Nếu cấp >= 30, có 25% xác suất gặp Lôi Kiếp khi thất bại
            if lv >= 30:
                if random.randint(1, 100) <= 25:
                    is_loi_kiep = True
                    tut_cap = random.randint(2, 3) # Tụt 2-3 cấp
                    loi_kiep_msg = "⚡ **LÔI KIẾP BẤT NGỜ!** Thiên địa chấn động, đạo hữu bị đánh văng tu vi!"

            await db.execute("UPDATE users SET level = MAX(1, level - ?), linh_thach = linh_thach - ? WHERE user_id = ?", (tut_cap, required_lt, uid))
            
            embed = discord.Embed(
                title="💥 ĐỘT PHÁ THẤT BẠI 💥",
                description=f"😔 **{interaction.user.display_name}** thất bại!\n{loi_kiep_msg}\n\n📉 Tu vi giảm: **{tut_cap} cấp**\n💸 Mất: **{required_lt} Linh thạch**",
                color=discord.Color.red()
            )
        await db.commit()

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

@bot.tree.command(name="bxh", description="Xem Bảng Xếp Hạng Top 10 Cường Giả")
async def bxh(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # Lấy Top 10 dựa trên Level và EXP
            async with db.execute("""
                SELECT user_id, level, exp, pet 
                FROM users 
                ORDER BY level DESC, exp DESC 
                LIMIT 10
            """) as cursor:
                rows = await cursor.fetchall()

        if not rows:
            return await interaction.followup.send("📜 Hiện tại thiên hạ chưa có ai ghi danh.")

        # ✅ Tối ưu: Tính lực chiến song song cho cả 10 người bằng hàm calc_power chuẩn
        # Điều này giúp số liệu khớp hoàn toàn với lệnh /check
        tasks = [calc_power(row[0]) for row in rows]
        powers = await asyncio.gather(*tasks)

        embed = discord.Embed(
            title="🏆 BẢNG VÀNG CƯỜNG GIẢ 🏆",
            description="Danh sách cường giả có tu vi thâm hậu nhất",
            color=discord.Color.gold()
        )

        titles = {1: "🥇 **Thánh Nhân**", 2: "🥈 **Chí Tôn**", 3: "🥉 **Đại Đế**"}
        leaderboard_text = ""

        for i, row in enumerate(rows):
            uid, lv, exp, pet = row
            power = powers[i] # Lấy lực chiến đã tính từ calc_power
            
            member = interaction.guild.get_member(uid)
            name = member.display_name if member else f"Ẩn sĩ ({uid})"
            
            prefix = titles.get(i + 1, f"**#{i + 1}**")
            realm = get_realm(lv)

            leaderboard_text += (
                f"{prefix} — **{name}**\n"
                f"└ `{realm}` (Lv.{lv}) - ⚡ Lực chiến: `{power:,}`\n"
            )

        embed.add_field(name="Thứ hạng / Đạo hiệu / Tu vi", value=leaderboard_text, inline=False)
        embed.set_footer(text=f"Cập nhật: {datetime.now().strftime('%H:%M:%S')}")
        
        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Lỗi BXH: {e}")
        await interaction.followup.send("❌ Có lỗi xảy ra khi tính toán thiên cơ, vui lòng thử lại sau.")
@bot.tree.command(name="resetday", description="ADMIN: Reset ngày")
async def resetday(interaction: discord.Interaction):

    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message(
            "❌ Bạn không có quyền.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users
            SET
                gacha_count = 0,
                last_gacha_day = NULL,
                last_daily = NULL,
                attack_count = 0,
                last_attack = NULL
        """)
        await db.commit()

    await interaction.followup.send("✅ Reset ngày thành công")

class ConfirmPhongSinh(discord.ui.View):
    def __init__(self, pet_name, uid):
        super().__init__(timeout=30) # Nút tồn tại trong 30 giây
        self.pet_name = pet_name
        self.uid = uid
        self.value = None

    @discord.ui.button(label="Xác nhận Phóng sinh", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.uid:
            return await interaction.response.send_message("❌ Đây không phải lễ phóng sinh của đạo hữu!", ephemeral=True)
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET pet = NULL, linh_thach = linh_thach + 1 WHERE user_id = ?", (self.uid,))
            await db.commit()
        
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
    uid = interaction.user.id
    u = await get_user(uid)
    pet_name = u.get("pet")

    if not pet_name:
        return await interaction.response.send_message("❌ Đạo hữu hiện không có Linh thú nào.", ephemeral=True)

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
    
    uid = interaction.user.id
    await create_user(uid)
    u = await get_user(uid)

    # 1. KIỂM TRA LƯỢT ĐÁNH (Reset mỗi ngày)
    today = datetime.now().strftime("%Y-%m-%d")
    attack_count = u["attack_count"] if u["last_attack"] == today else 0
    
    if attack_count >= 3:
        return await interaction.followup.send("❌ Đạo hữu đã cạn kiệt linh lực. Hãy tịnh dưỡng đến ngày mai hoặc chờ cơ duyên hồi phục!")

    # 2. LẤY DỮ LIỆU LINH THÚ & QUÁI VẬT
    pet_name = u.get("pet")
    pet_data = PET_CONFIG.get(pet_name, {"atk": 0, "effect": "Không", "exp_mult": 1.0, "lt_chance": 30})
    
    # Lấy dữ liệu quái phù hợp với Level người chơi
    # Giả sử hàm get_monster_data(lv) trả về: (Tên quái, tỉ lệ rơi đồ, [min_lv_đồ, max_lv_đồ])
    monster, drop_rate, eq_range = get_monster_data(u["level"])
    
    # 3. TÍNH TOÁN CHỈ SỐ CHIẾN ĐẤU
    total_atk = (u["level"] * 10) + pet_data.get("atk", 0)
    
    # Logic cộng EXP: Buff 15% nếu là Thôn Phệ Thú
    base_exp = exp_needed(u["level"]) // 5  # Mặc định nhận 20% exp cấp hiện tại
    exp_gain = int(base_exp * pet_data.get("exp_mult", 1.0))
    
    # Logic rơi Linh thạch: Buff tỉ lệ nếu có pet đặc thù
    lt_chance = pet_data.get("lt_chance", 30) 
    lt_gain = random.randint(1, 5) if random.randint(1, 100) <= lt_chance else 0

    # 4. KIỂM TRA CHẶN EXP (Bình cảnh đột phá)
    can_gain_exp = True
    if u["level"] % 10 == 0:
        if u["exp"] >= exp_needed(u["level"]):
            can_gain_exp = False
            exp_gain = 0

    # 5. LOGIC RƠI TRANG BỊ
    drop_msg = ""
    final_drop_rate = drop_rate + pet_data.get("drop_buff", 0)
    if random.random() <= final_drop_rate:
        eq_type = random.choice(EQ_TYPES)
        eq_lv = random.randint(*eq_range)
        saved = await save_equipment(uid, eq_type, eq_lv)
        if saved:
            drop_msg = f"\n🎁 **VẬN MAY!** Nhận được: `{eq_type} Cấp {eq_lv}`"
        else:
            drop_msg = f"\n🗑️ Đánh rơi `{eq_type} Cấp {eq_lv}` nhưng phẩm chất quá thấp, đã phân rã."

    # 6. LOGIC HỒI LƯỢT (Đặc kỹ Linh thú)
    actual_count = attack_count + 1
    refund_msg = ""
    if pet_name == "Thôn Phệ Thú" and random.randint(1, 100) <= 20: # 20% hồi lượt
        actual_count = attack_count
        refund_msg = "\n🌀 **Thôn Phệ Thú** hấp thụ linh khí quái vật, giúp bạn không tốn thể lực (+1 lượt)!"

    # 7. CẬP NHẬT CƠ SỞ DỮ LIỆU
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users 
            SET exp = exp + ?, 
                attack_count = ?, 
                last_attack = ?, 
                linh_thach = linh_thach + ?
            WHERE user_id = ?
        """, (exp_gain, actual_count, today, lt_gain, uid))
        await db.commit()

    # 8. HIỂN THỊ KẾT QUẢ
    embed = discord.Embed(
        title="⚔️ TRẬN CHIẾN KẾT THÚC",
        description=f"Đạo hữu vung kiếm tiêu diệt **{monster}**!",
        color=discord.Color.green() if exp_gain > 0 else discord.Color.orange()
    )
    
    exp_info = f"📈 Kinh nghiệm: **+{exp_gain} EXP**" if can_gain_exp else "⚠️ **BÌNH CẢNH!** Hãy dùng `/dotpha` để tiếp tục nhận EXP."
    lt_info = f"\n💎 Linh thạch: **+{lt_gain}**" if lt_gain > 0 else ""
    pet_info = f"\n🐾 **Linh thú:** {pet_name} trợ chiến ({pet_data['effect']})" if pet_name else ""
    
    embed.add_field(name="Chiến lợi phẩm", value=f"{exp_info}{lt_info}{drop_msg}{refund_msg}", inline=False)
    if pet_info:
        embed.add_field(name="Sức mạnh linh thú", value=pet_info, inline=False)
        
    embed.set_footer(text=f"Lực chiến: {total_atk} | Lượt đánh còn lại: {3 - actual_count}")
    
    await interaction.followup.send(embed=embed)
@bot.tree.command(name="add", description="[ADMIN] Ban thưởng Linh thạch cho tu sĩ")
@app_commands.describe(target="Tu sĩ được ban thưởng", so_luong="Số lượng linh thạch")
async def add(
    interaction: discord.Interaction, 
    target: discord.Member, 
    so_luong: int
):
    # 1. Kiểm tra quyền Admin
    if interaction.user.id != ADMIN_ID:
        return await interaction.response.send_message(
            "❌ **THIÊN PHẠT!** Đạo hữu không có quyền năng điều khiển linh thạch của trời đất.", 
            ephemeral=True
        )

    # 2. Kiểm tra số lượng hợp lệ
    if so_luong <= 0:
        return await interaction.response.send_message("❌ Số lượng linh thạch phải lớn hơn 0!", ephemeral=True)

    await interaction.response.defer()
    
    # 3. Đảm bảo người nhận có trong DB
    await create_user(target.id)

    # 4. Cập nhật Linh thạch
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET linh_thach = linh_thach + ? WHERE user_id = ?", 
            (so_luong, target.id)
        )
        await db.commit()

    # 5. Hiển thị thông báo rực rỡ
    embed = discord.Embed(
        title="✨ THIÊN BAN LINH VẬT ✨",
        description=(
            f"Bậc đại năng **{interaction.user.display_name}** đã giáng lâm!\n"
            f"Ban thưởng cho **{target.mention}** **{so_luong:,} Linh thạch**.\n\n"
            f"*Chúc đạo hữu sớm ngày đắc đạo!*"
        ),
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url="https://i.imgur.com/39A72Pj.png") # Ảnh linh thạch lấp lánh
    
    await interaction.followup.send(embed=embed)
@bot.tree.command(name="diemdanh")
async def diemdanh(interaction: discord.Interaction):
    await interaction.response.defer()
    uid = interaction.user.id
    await create_user(uid)

    today = datetime.now().strftime("%Y-%m-%d")
    u = await get_user(uid)

    if u["last_daily"] == today:
        await interaction.followup.send("❌ Hôm nay đã điểm danh.")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users
            SET last_daily=?,
                exp = exp + ?,
                linh_thach = linh_thach + 1
            WHERE user_id=?
        """, (today, exp_needed(u["level"]), uid))
        await db.commit()

    await check_level_up(uid, interaction.channel, interaction.user.display_name)
    await interaction.followup.send("✅ Điểm danh thành công (+EXP, +1 Linh Thạch)")


keep_alive()
token = os.getenv("DISCORD_TOKEN")
bot.run(token)






