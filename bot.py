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
import datetime
from datetime import datetime, timedelta



# ========== KẾT NỐI MONGODB ==========
MONGO_URI = os.getenv("MONGO_URI") 
cluster = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db_mongo = cluster["game_database"] 
users_col = db_mongo["users"]       
eq_col = db_mongo["equipment"]      
active_battles = set() # Dùng để ngăn tu sĩ phân thân đánh nhiều boss cùng lúc
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
    1455081842473697362: 0.5, 1455837230332641280: 0.5,
    1454793019160006783: 0.5, 1454793109094268948: 0.5,
    1454506037779369986: 1, 1461017212365181160: 1.5, 1462672263911313439: 1.25
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
    "Không Đồng Ấn": {"desc": "Dấu ấn của định mệnh khắc lên dòng chảy sinh mệnh, là quyền năng nắm giữ sự bất biến giữa cõi vô thường.", "atk": 200, "color": 0x1F1F1F},
    "Hiện Thân Thần Vật - Côn Lôn Kính":{"desc": "Sức mạnh từ bản thể Côn Lôn Kính - nguồn: Thanh Thanh", "atk": 150, "color": 0xECF0F1}
}
THANH_GIAP_CONFIG = {
    "Long Lân Thánh Giáp": {
        "quote": "『 LONG LÂN HỘ THỂ - BẤT DIỆT KIM THÂN 』",
        "desc": "Đúc từ vảy của Thái Cổ Chân Long, vạn tiễn bất xâm.",
        "hp": 2500,
        "color": 0xFFD700
    },
    "Phượng Hoàng Niết Bàn Y": {
        "quote": "『 PHƯỢNG DIỆM TRÙNG SINH - VĨNH CỬU TRƯỜNG SINH 』",
        "desc": "Hỏa diệm bất diệt, sinh mệnh dồi dào như được tái sinh.",
        "hp": 2500,
        "color": 0xFF4500
    },
    "Huyền Vũ Minh Giáp": {
        "quote": "『 TRẤN THỦ BẮC MINH - PHÒNG NGỰ TUYỆT ĐỐI 』",
        "desc": "Sự kiên cố của phương Bắc, vững chãi như đại địa.",
        "hp": 2500,
        "color": 0x2F4F4F
    },
    "Bạch Hổ Sát Thần Khải": {
        "quote": "『 BẠCH HỔ SÁT QUÂN - CHIẾN Ý THÔNG THIÊN 』",
        "desc": "Sát khí hộ thân, nhiễu loạn tâm trí kẻ thù.",
        "hp": 2500,
        "color": 0xF5F5F5
    },
    "Thiên Hà Tinh Thần Bào": {
        "quote": "『 TINH TÚ GIÁNG TRẦN - NHẤT NIỆM VĨNH HẰNG 』",
        "desc": "Dệt từ ánh sáng vạn vì sao, sinh mệnh hòa cùng thiên địa.",
        "hp": 2500,
        "color": 0x4169E1
    },
    "Hỗn Nguyên Thánh Y": {
        "quote": "『 HỖN NGUYÊN NHẤT KHÍ - ĐẠO PHÁP TỰ NHIÊN 』",
        "desc": "Chứa đựng sức mạnh sơ khai, giúp tinh huyết bất tận.",
        "hp": 2500,
        "color": 0x9370DB
    },
    "Lôi Đình Chiến Giáp": {
        "quote": "『 VẠN LÔI TỀ PHÁT - THẾ NHƯ CỬU THIÊN 』",
        "desc": "Sấm sét thiên kiếp rèn giũa thân thể kim cang.",
        "hp": 2500,
        "color": 0xFFFF00
    },
    "Thanh Liên Pháp Y": {
        "quote": "『 THANH LIÊN BẤT NHIỄM - TỊNH HÓA THÂN TÂM 』",
        "desc": "Đóa sen xanh thanh lọc cơ thể, gia tăng thọ mệnh.",
        "hp": 2500,
        "color": 0x00FF7F
    },
    "Vô Cực Ma Giáp": {
        "quote": "『 VÔ CỰC MA TÂM - HẤP THỤ THIÊN ĐỊA 』",
        "desc": "Hấp thụ u minh lực để gia cố sinh mệnh.",
        "hp": 2500,
        "color": 0x1A1A1A
    },
    "Cửu Thiên Huyền Nữ Bào": {
        "quote": "『 HUYỀN NỮ GIÁNG THẾ - PHỦ TRƯỚNG TIÊN KHÍ 』",
        "desc": "Mềm mại nhưng bền bỉ, mang theo tiên khí bảo mệnh.",
        "hp": 2500,
        "color": 0xFFB6C1
    },
    "Vạn Cổ Quy Nguyên - Thiên Đạo Bất Diệt Khải": {
        "quote": "『 VẠN CỔ QUY NGUYÊN - THIÊN ĐẠO BẤT DIỆT 』",
        "desc": "Trấn Thế Chi Bảo. Thân ngoài ngũ hành, lôi phạt không thể chạm đến.",
        "hp": 5000,
        "color": 0xFFFFFF,
        "effect": "khang_loi_phat"
    }
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
    "U Minh Tước": {
        "atk": 220, 
        "hp": 2000, 
        "effect": "Tăng 5% tỷ lệ thắng mọi trận đấu",
        "icon": "🌀",
        "color": 0x4B0082
    },
    "Băng Tinh Hổ": {
        "atk": 170,
        "hp": 2300,
        "break_buff": 0.05, 
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
        "lt_buff": 0.2, 
        "effect": "Tăng 20% Linh Thạch",
        "color": 0xff99cc,
        "icon": "🦊"
    }
}
BOSS_CONFIG = {
    "Hồng Tụ Tôn Sứ": {
        "multiplier": 20, 
        "base": 10000, 
        "reward": (10, 18), 
        "penalty": 500, 
        "color": 0x3498db,
        "desc": "Yêu nữ am tường ảo thuật, thích hợp cho tu sĩ mới vào nghề."
    },
    "Lôi Âm Tôn Sứ": {
        "multiplier": 35, # Tăng từ 30 -> 35
        "base": 40000,   # Tăng từ 20,000 -> 25,000
        "reward": (18, 25), # Tăng nhẹ thưởng để xứng tầm
        "penalty": 1500, # Tăng phạt (vượt ngưỡng rớt cấp nhanh hơn)
        "color": 0xe67e22,
        "desc": "Hộ pháp đọa lạc, lôi điện quanh thân, thực lực không thể coi thường."
    },
    "Mục Dã Di": {
        "multiplier": 55, # Tăng mạnh từ 40 -> 55
        "base": 70000,   # Tăng mạnh từ 40,000 -> 55,000
        "reward": (25, 35), # Thưởng xứng đáng cho đại nạn
        "penalty": 3000, # Phạt cực nặng (5k EXP thường là rớt thẳng 1-2 cấp)
        "color": 0x992d22,
        "desc": "Thượng cổ Ma Thần, sức mạnh đủ để hủy thiên diệt địa."
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
    # Truy vấn dữ liệu từ Database
    u = await users_col.find_one({"_id": uid})
    if not u: 
        return 0
    
    # Lấy dữ liệu trang bị, nếu không có thì mặc định là dictionary trống
    eq = await eq_col.find_one({"_id": uid}) or {}
    
    # Khai báo các thông tin cơ bản
    lv = u.get("level", 1)
    pet_name = u.get("pet")
    than_khi_name = u.get("than_khi") 
    thanh_giap_name = u.get("thanh_giap")
    
    # 1. Chỉ số gốc từ Level (Lv 1: Atk 5, HP 50)
    atk, hp = lv * 5, lv * 50
    
    # 2. Cộng chỉ số từ Trang bị rèn đúc (EQ_TYPES)
    # Giả định EQ_TYPES gồm: Kiếm, Giáp, Nhẫn, Mũ, Giày...
    for t in EQ_TYPES:
        eq_lv = eq.get(t, 0)
        if eq_lv <= 0: continue # Không có trang bị hoặc cấp 0 thì bỏ qua
        
        if t == "Kiếm":
            # NẾU CÓ Thần Khí: Kiếm thường không còn tác dụng (bị đè)
            if not than_khi_name:
                atk += eq_lv * 15
        
        elif t == "Giáp":
            # NẾU CÓ Thánh Giáp: Giáp thường không còn tác dụng (bị đè)
            if not thanh_giap_name:
                hp += eq_lv * 150
                
        elif t == "Nhẫn":
            # Nhẫn luôn luôn cộng Atk (Không bị Thần Khí đè)
            atk += eq_lv * 15
            
        else: 
            # Các trang bị còn lại (Mũ, Giày, Hộ cổ...) cộng HP bình thường
            hp += eq_lv * 150
            
    # 3. Cộng chỉ số từ Cực phẩm (Sử dụng .get() để tránh lỗi crash nếu config thiếu)
    if than_khi_name and than_khi_name in THAN_KHI_CONFIG:
        # Lấy chỉ số ATK từ config, mặc định 200 nếu không ghi rõ
        atk += THAN_KHI_CONFIG[than_khi_name].get("atk", 200)
            
    if thanh_giap_name and thanh_giap_name in THANH_GIAP_CONFIG:
        # Lấy chỉ số HP từ config, mặc định 2500 nếu không ghi rõ
        hp += THANH_GIAP_CONFIG[thanh_giap_name].get("hp", 2500)

    # 4. Cộng chỉ số từ Linh Thú (Pet)
    if pet_name and pet_name in PET_CONFIG:
        p_stats = PET_CONFIG[pet_name]
        atk += p_stats.get("atk", 0)
        hp += p_stats.get("hp", 0) 

    # 5. Tổng lực chiến (Power)
    # Công thức Thiên Đạo: (Công * 10) + Thủ + Biến số thiên cơ (0-100)
    total_power = (atk * 10) + hp + random.randint(0, 100)
    
    return int(total_power)
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
async def check_level_down(uid):
    user = await users_col.find_one({"_id": uid})
    if not user: return False
    
    lv = user.get("level", 1)
    exp = user.get("exp", 0)
    
    # 1. Nếu EXP vẫn >= 0 hoặc đang ở cấp 1 thì không cần xử lý
    if exp >= 0 or lv <= 1: 
        return False

    # 2. THIẾT LẬP CÁC MỐC KHÓA (Checkpoints)
    # Nếu đang ở các mốc này, dù EXP âm cũng không bị lùi cấp
    checkpoints = [21, 31, 41, 51, 61] 
    if lv in checkpoints:
        # Thay vì rớt cấp, ta chỉ reset EXP về 0 để cảnh cáo
        await users_col.update_one({"_id": uid}, {"$set": {"exp": 0}})
        return False

    # 3. LOGIC GIẢM CẤP
    new_lv = lv - 1
    
    # Lấy EXP cần thiết của cấp mới để tính toán số dư
    # (Ví dụ: đang âm 500, cấp mới cần 1000 -> sẽ còn 500/1000)
    req_exp_new_lv = exp_needed(new_lv) 
    new_exp = req_exp_new_lv + exp 
    
    await users_col.update_one(
        {"_id": uid},
        {"$set": {"level": new_lv, "exp": max(0, new_exp)}}
    )
    return True
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

# Hàm phụ để phát thông báo chấn động đến tất cả kênh trong NOTIFY_CHANNELS
async def broadcast_anomaly(bot, title, message, color, thumbnail_url=None):
    for channel_id in NOTIFY_CHANNELS:
        channel = bot.get_channel(channel_id)
        if channel:
            try:
                embed = discord.Embed(title=title, description=message, color=color)
                if thumbnail_url:
                    embed.set_thumbnail(url=thumbnail_url)
                embed.set_footer(text="Thiên địa dị tượng - Vạn dân bái phục!")
                await channel.send(embed=embed)
            except Exception as e:
                print(f"Không thể gửi thông báo đến kênh {channel_id}: {e}")
# ========== LỆNH SLASH (/) ==========
@bot.tree.command(name="check", description="Xem hồ sơ tu tiên & lực chiến chính xác")
async def info(interaction: discord.Interaction):
    try:
        # 1. Chống treo lệnh
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
        thanh_giap_name = u.get("thanh_giap") # Lấy tên Thánh Giáp từ Database
        pet_name = u.get("pet")

        # 3. GỌI HÀM TÍNH POWER
        total_power = await calc_power(uid)

        # 4. TÍNH TOÁN CẢNH GIỚI
        stages = ["Luyện Khí", "Trúc Cơ", "Kết Đan", "Nguyên Anh", "Hóa Thần", 
                  "Luyện Hư", "Hợp Thể", "Đại Thừa", "Đại Tiên", "Thiên Tiên"]
        idx = (level - 1) // 10
        idx = max(0, min(idx, len(stages) - 1))
        current_stage = stages[idx]
        tang = (level - 1) % 10 + 1
        display_canh_gioi = f"Lv.{level} - {current_stage} tầng {tang}"

        # 5. XỬ LÝ HIỂN THỊ TRANG BỊ & MÀU SẮC
        kiem_lv = eq.get("Kiếm", 0)
        nhan_lv = eq.get("Nhẫn", 0)
        giap_lv = eq.get("Giáp", 0)
        tay_lv = eq.get("Tay", 0)
        ung_lv = eq.get("Ủng", 0)

        # Thiết lập màu sắc Embed (Ưu tiên Thần Khí rồi đến Thánh Giáp)
        embed_color = discord.Color.blue()
        if than_khi_name:
            embed_color = discord.Color.gold()
        elif thanh_giap_name:
            embed_color = discord.Color.from_rgb(255, 215, 0) # Màu vàng kim cho Thánh Giáp

        # Hiển thị Vũ khí (Thần Khí vs Kiếm thường)
        if than_khi_name:
            weapon_display = f"🌟 **{than_khi_name}**"
        else:
            weapon_display = f"⚔️ Kiếm Cấp {kiem_lv}" if kiem_lv > 0 else "⚔️ Vô nhận kiếm"

        # --- LOGIC MỚI: HIỂN THỊ THÁNH GIÁP THAY THẾ GIÁP THƯỜNG ---
        if thanh_giap_name:
            giap_display = f"🛡️ **{thanh_giap_name}**"
        else:
            giap_display = f"🛡️ Giáp Cấp {giap_lv}" if giap_lv > 0 else "🛡️ Bố y"

        # 6. HIỂN THỊ EXP
        if level % 10 == 0:
            exp_display = f"`{int(cur_exp):,} / Đỉnh Phong (Cần Đột Phá)`"
        else:
            needed = exp_needed(level) 
            exp_display = f"`{int(cur_exp):,} / {int(needed):,}`"

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
            f"{giap_display}\n" # Hiển thị logic Thánh Giáp mới ở đây
            f"🧤 Tay: Cấp {tay_lv}\n"
            f"👢 Ủng: Cấp {ung_lv}"
        )
        embed.add_field(name="📦 Trang Bị Khảm Nạm", value=trang_bi_str, inline=True)
        embed.add_field(name="🦄 Linh Thú", value=f"🐾 **{pet_name or 'Chưa có'}**", inline=True)

        # 8. Gửi phản hồi cuối cùng
        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"❌ Lỗi lệnh check: {e}")
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


@bot.tree.command(name="gacha", description="Tầm bảo: Trang bị, Linh thú & Thánh giáp")
@app_commands.describe(lan="Chọn số lần quay (1 hoặc 10)")
async def gacha(interaction: discord.Interaction, lan: int = 1):
    await interaction.response.defer()
    
    if lan not in [1, 10]:
        return await interaction.followup.send("❌ Đạo hữu chỉ có thể quay 1 hoặc 10 lần!")

    uid = str(interaction.user.id)
    today = datetime.now().strftime("%Y-%m-%d")
    user_name = interaction.user.display_name

    # 1. LẤY DỮ LIỆU USER
    u = await users_col.find_one({"_id": uid})
    if not u:
        u = {"_id": uid, "level": 1, "exp": 0, "linh_thach": 10, "gacha_count": 0, "last_gacha_day": ""}
        await users_col.insert_one(u)

    # Tính toán lượt miễn phí
    gacha_count = u.get("gacha_count", 0) if u.get("last_gacha_day") == today else 0
    
    # Tính phí: lượt miễn phí chỉ áp dụng cho Quay 1. Quay 10 mặc định tốn 10 LT.
    # Hoặc nếu đạo hữu muốn ưu đãi: quay 10 tốn 9 LT (Mua 10 tặng 1)
    if lan == 1:
        cost = 0 if gacha_count < 3 else 1
    else:
        cost = 10 # Quay 10 lần tốn 10 linh thạch

    if u.get("linh_thach", 0) < cost:
        return await interaction.followup.send(f"❌ Đạo hữu không đủ **{cost} Linh thạch** để thực hiện {lan} lần quay.")

    # --- KHỞI TẠO BIẾN TỔNG HỢP ---
    tg_msg = ""
    list_pets = []
    total_exp_bonus = 0
    new_eq_msg = ""
    got_tg_this_turn = False
    final_color = discord.Color.blue()
    current_user_tg = u.get("thanh_giap")

    # --- 1. KHỞI TẠO BIẾN (PHẢI NẰM NGOÀI VÒNG LẶP) ---
    # Những biến này chỉ được tạo 1 lần trước khi quay
    got_tg_this_turn = False    # Chốt chặn trúng Thánh Giáp trong cụm x10
    got_pet_this_turn = False   # Chốt chặn trúng Linh Thú trong cụm x10

    # Lấy dữ liệu hiện tại của user để kiểm tra điều kiện sở hữu
    current_user_tg = u.get("thanh_giap")
    current_user_pet = u.get("pet")
    
    list_pets = [] # Khởi tạo danh sách pet trúng

    # --- 2. VÒNG LẶP GACHA (BẮT ĐẦU TỪ ĐÂY) ---
    for _ in range(lan):
        
        # 1. LOGIC THÁNH GIÁP (0.5% - Độc bản toàn server)
        # Điều kiện: User chưa có giáp AND chưa trúng giáp trong lượt quay x10 này
        if not current_user_tg and not got_tg_this_turn and random.random() <= 0.005:
            try:
                # Quét danh sách các Thánh Giáp đã có chủ trên toàn server
                owned_tg = await users_col.distinct("thanh_giap", {"thanh_giap": {"$ne": None}})
                # Lọc ra những bộ còn trống trong CONFIG
                available_tg = [tg for tg in THANH_GIAP_CONFIG.keys() if tg not in owned_tg]
                
                if available_tg:
                    new_tg = random.choice(available_tg)
                    # Cập nhật ngay lập tức vào DB để xác nhận chủ quyền
                    await users_col.update_one({"_id": uid}, {"$set": {"thanh_giap": new_tg}})
                    
                    got_tg_this_turn = True
                    current_user_tg = new_tg # Chặn không cho trúng thêm ở các lượt for sau
                    tg_msg = f"\n\n🛡️ **THÁNH VẬT XUẤT THẾ: [{new_tg}]**"
                    final_color = 0xFFD700
            except Exception as e:
                print(f"Lỗi Gacha Thánh Giáp: {e}")

        # 2. LOGIC LINH THÚ (0.2% - Mỗi người chỉ mang 1 con)
        # Điều kiện: User chưa có Linh thú trên người AND chưa trúng con nào trong lượt x10 này
        if not current_user_pet and not got_pet_this_turn and random.random() <= 0.002:
            try:
                # Chọn linh thú ngẫu nhiên từ cấu hình
                p_name = random.choice(list(PET_CONFIG.keys()))
                p_icon = PET_CONFIG[p_name].get('icon', '🐾')
                
                # Cập nhật linh thú vào DB
                await users_col.update_one({"_id": uid}, {"$set": {"pet": p_name}})
                
                got_pet_this_turn = True
                current_user_pet = p_name # Chặn không cho trúng thêm ở các lượt for sau
                list_pets.append(f"{p_icon} {p_name}")
                
                # Chỉ đổi màu nếu không trúng Thánh Giáp (Thánh giáp ưu tiên màu Vàng)
                if not got_tg_this_turn:
                    final_color = 0x4B0082 if p_name == "U Minh Tước" else 0xFFAC33
            except Exception as e:
                print(f"Lỗi Gacha Linh Thú: {e}")

        # 3. LOGIC TRANG BỊ THƯỜNG (Tiếp tục tại đây...)

    # 3. LOGIC TRANG BỊ THƯỜNG (Chỉ chạy nếu không trúng 2 món trên hoặc tùy hỉ đạo hữu)
    # ... (Giữ nguyên phần rã đồ nhận EXP của đạo hữu)

        # C. LOGIC TRANG BỊ
        eq_type = random.choice(EQ_TYPES)
        lv = random.choices(range(1, 11), weights=[25, 20, 15, 10, 10, 8, 5, 3, 3, 1])[0]
        
        # Kiểm tra rã đồ (Nếu có thánh giáp thì rã Giáp thường)
        if eq_type == "Giáp" and current_user_tg:
            total_exp_bonus += lv * 10
        else:
            # Lấy level đồ cũ để so sánh
            cur_eq = await eq_col.find_one({"_id": uid}) or {}
            if lv > cur_eq.get(eq_type, 0):
                await eq_col.update_one({"_id": uid}, {"$set": {eq_type: lv}}, upsert=True)
                new_eq_msg = f"🎁 Nhận trang bị mới: **{eq_type} cấp {lv}**"
            else:
                total_exp_bonus += lv * 10

    # --- CẬP NHẬT DATABASE ---
    new_count = gacha_count + lan
    await users_col.update_one(
        {"_id": uid},
        {
            "$set": {"gacha_count": new_count, "last_gacha_day": today},
            "$inc": {"linh_thach": -cost}
        }
    )
    
    if total_exp_bonus > 0:
        await add_exp(uid, total_exp_bonus)
        await check_level_up(uid, interaction.channel, user_name)

    # --- HIỂN THỊ ---
    pet_str = f"\n🐾 **Linh thú:** {', '.join(list_pets)}" if list_pets else ""
    exp_str = f"\n♻️ **Rã đồ thừa nhận:** {total_exp_bonus} EXP" if total_exp_bonus > 0 else ""
    status = f"🎰 Lượt: {new_count}/3 (Miễn phí)" if new_count <= 3 and lan == 1 else f"💎 Chi phí: {cost} Linh thạch"

    embed = discord.Embed(
        title=f"🔮 KẾT QUẢ GACHA x{lan} 🔮",
        description=f"{new_eq_msg}{tg_msg}{pet_str}{exp_str}\n\n{status}",
        color=final_color
    )
    
    if got_tg_this_turn:
        embed.set_footer(text=f"Thánh vật: {THANH_GIAP_CONFIG[new_tg].get('effect', 'Vô song')}")
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
    else:
        embed.set_footer(text="Cơ duyên do trời, vận mệnh tại ta.")

    await interaction.followup.send(embed=embed)
@bot.tree.command(name="solo", description="Thách đấu người chơi khác (Ẩn lực chiến, cược linh thạch)")
async def solo(interaction: discord.Interaction, target: discord.Member, linh_thach: int | None = None):
    # Tránh lỗi Unknown Interaction
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

    u1, u2 = await asyncio.gather(
        users_col.find_one({"_id": uid}),
        users_col.find_one({"_id": tid})
    )

    if not u1 or not u2:
        return await interaction.followup.send("❌ Một trong hai đạo hữu chưa có hồ sơ tu tiên!")

    if bet > 0:
        if u1.get("linh_thach", 0) < bet or u2.get("linh_thach", 0) < bet:
            return await interaction.followup.send(f"❌ Một trong hai không đủ **{bet} linh thạch** để cược!")

    # Tính toán lực chiến chuẩn bị cho trận đấu
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
            # Kiểm tra linh thạch thực tế lúc bấm nút
            curr_u1, curr_u2 = await asyncio.gather(
                users_col.find_one({"_id": uid}),
                users_col.find_one({"_id": tid})
            )
            
            if bet > 0 and (curr_u1.get("linh_thach", 0) < bet or curr_u2.get("linh_thach", 0) < bet):
                return await i.response.edit_message(content="❌ Trận đấu hủy bỏ! Một bên đã không còn đủ linh thạch.", view=None)

            total_power = p1_power + p2_power if (p1_power + p2_power) > 0 else 1
            win_chance = p1_power / total_power
            
            # --- XÁC ĐỊNH KẾT QUẢ ---
            is_u1_win = random.random() <= win_chance
            winner_data = curr_u1 if is_u1_win else curr_u2
            winner_name = interaction.user.display_name if is_u1_win else target.display_name
            loser_name = target.display_name if is_u1_win else interaction.user.display_name
            winner_id = uid if is_u1_win else tid

            # Xử lý cược
            if bet > 0:
                await users_col.update_many({"_id": {"$in": [uid, tid]}}, {"$inc": {"linh_thach": -bet}})
                await users_col.update_one({"_id": winner_id}, {"$inc": {"linh_thach": bet * 2}})

            # --- KIỂM TRA HÀO QUANG (THẦN KHÍ & LINH THÚ) ---
            winner_tk = winner_data.get("than_khi")
            winner_pet = winner_data.get("pet")
            
            embed_color = discord.Color.gold()
            special_msg = ""
            embed_title = "⚔️ TRẬN THƯ HÙNG KẾT THÚC ⚔️"

           # --- TÍNH TOÁN HIỆU ỨNG CHIẾN THẮNG (SẮP XẾP LẠI ƯU TIÊN) ---
            winner_tg = winner_data.get("thanh_giap")
            winner_tk = winner_data.get("than_khi")
            winner_pet = winner_data.get("pet")

            # 1. COMBO CỰC PHẨM: CÓ CẢ 3 MÓN
            if winner_tk and winner_tg and winner_pet:
                embed_color = discord.Color.from_rgb(255, 255, 255) # Trắng bạc
                embed_title = "🌌 THIÊN ĐẠO CHÍ TÔN - ĐỘC CÔ CẦU BẠI 🌌"
                special_msg = f"🌌 **KHÍ VẬN NGHỊCH THIÊN!** {winner_name} mặc **{winner_tg}**, tay cầm **{winner_tk}**, cưỡi **{winner_pet}** quét sạch bát hoang!"

            # 2. COMBO CÔNG THỦ TOÀN DIỆN: THẦN KHÍ + THÁNH GIÁP
            elif winner_tk and winner_tg:
                embed_color = discord.Color.from_rgb(255, 140, 0) # Cam đậm (Hỏa long)
                embed_title = "⚔️ CÔNG THỦ TOÀN DIỆN - CHIẾN THẮNG ⚔️"
                special_msg = f"🔥 **Vô đối thiên hạ!** Với sức mạnh của **{winner_tk}** và sự kiên cố của **{winner_tg}**, {winner_name} là bất khả chiến bại!"

            # 3. COMBO TUYỆT THẾ: THẦN KHÍ + LINH THÚ
            elif winner_tk and winner_pet:
                embed_color = discord.Color.from_rgb(255, 0, 255) # Tím
                embed_title = "🔥 TUYỆT THẾ VÔ SONG - CHIẾN THẮNG 🔥"
                special_msg = f"🌟 **Hào quang vạn trượng!** {winner_name} cùng linh thú **{winner_pet}** xuất kích, tay cầm **{winner_tk}** trấn áp quần hùng!"

            # 4. CHỈ CÓ THÁNH GIÁP
            elif winner_tg:
                embed_color = discord.Color.from_rgb(0, 255, 255) # Xanh Cyan
                embed_title = "🛡️ THÁNH GIÁP BẤT DIỆT - CHIẾN THẮNG 🛡️"
                special_msg = f"🛡️ **{winner_tg}** tỏa ra hào quang hộ thể, khiến mọi đòn tấn công của đối phương đều trở nên vô dụng!"

            # 5. CHỈ CÓ THẦN KHÍ
            elif winner_tk:
                embed_color = discord.Color.red()
                embed_title = "🔱 THẦN KHÍ GIÁNG THẾ - CHIẾN THẮNG 🔱"
                special_msg = f"🔱 **{winner_tk}** phát ra uy áp khủng khiếp, khiến đối phương không kịp trở tay!"

            # 6. CHỈ CÓ LINH THÚ
            elif winner_pet:
                embed_color = discord.Color.blue()
                embed_title = "🐾 LINH THÚ HỘ THỂ - CHIẾN THẮNG 🐾"
                special_msg = f"🐾 Linh thú **{winner_pet}** gầm vang trời đất, trợ lực cho chủ nhân giành chiến thắng!"

            p1_percent = round((p1_power / total_power) * 100, 1)
            p2_percent = round(100 - p1_percent, 1)

            result_embed = discord.Embed(title=embed_title, color=embed_color)
            
            # Mô tả chi tiết trận đấu
            desc = (
                f"🔵 **{interaction.user.display_name}**: `{p1_power:,}` LC ({p1_percent}%)\n"
                f"🔴 **{target.display_name}**: `{p2_power:,}` LC ({p2_percent}%)\n\n"
                f"🏆 Người thắng: **{winner_name}**\n"
                f"💀 Kẻ bại: {loser_name}\n"
                f"💰 Kết quả: " + (f"Thắng cược **{bet} 💎**" if bet > 0 else "Vang danh thiên hạ")
            )
            
            if special_msg:
                desc += f"\n\n{special_msg}"
                
            result_embed.description = desc
            result_embed.set_footer(text="Hữu thắng hữu bại, chớ nên nản lòng.")

            await i.response.edit_message(content=None, embed=result_embed, view=None)
            self.stop()

        @discord.ui.button(label="❌ Thủ Thế", style=discord.ButtonStyle.danger)
        async def decline(self, i: discord.Interaction, button: discord.ui.Button):
            await i.response.edit_message(content=f"❌ **{target.display_name}** đã chọn cách thủ thế, từ chối tiếp chiến.", view=None)
            self.stop()

    invite_msg = f"⚔️ **{interaction.user.display_name}** thách đấu **{target.mention}**!\n" + \
                 (f"💎 Cược: **{bet} Linh thạch**" if bet > 0 else "🎲 Trận chiến giao hữu")
    await interaction.followup.send(content=invite_msg, view=SoloView())
@bot.tree.command(name="dotpha", description="Đột phá cảnh giới (Tăng 5% tỉ lệ sau mỗi lần thất bại)")
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
    # Lấy tỉ lệ tích lũy từ những lần thất bại trước (mặc định là 0)
    luck_bonus = u.get("luck_bonus", 0) 

    # 1. LẤY CHỈ SỐ PET
    pet_data = PET_CONFIG.get(pet_name, {})
    break_buff = pet_data.get("break_buff", 0)
    risk_reduce = pet_data.get("risk_reduce", 0)

    # 2. KIỂM TRA ĐIỀU KIỆN
    if lv % 10 != 0:
        return await interaction.followup.send(f"❌ Cần đạt đỉnh phong để đột phá. Hiện tại: **Cấp {lv}**")

    needed = exp_needed(lv)
    if exp < needed:
        return await interaction.followup.send(f"❌ Tu vi chưa đủ! (Cần {int(exp)}/{needed} EXP)")

    required_lt = 2 if lv < 30 else (5 if lv < 60 else (10 if lv < 80 else 20))
    if linh_thach < required_lt:
        return await interaction.followup.send(f"❌ Cần **{required_lt} Linh thạch**.")

    # 3. TÍNH TỈ LỆ (Gốc + Pet + Bảo hiểm thất bại)
    realm_index = lv // 10
    base_rate = max(5, 90 - (realm_index * 10))
    # Tổng tỉ lệ cuối cùng
    final_rate = base_rate + break_buff + luck_bonus
    
    success = random.randint(1, 100) <= final_rate

    if success:
        # THÀNH CÔNG: Tăng cấp và RESET luck_bonus về 0
        await users_col.update_one(
            {"_id": uid},
            {
                "$set": {"level": lv + 1, "exp": 0, "luck_bonus": 0}, 
                "$inc": {"linh_thach": -required_lt}
            }
        )
        
        luck_msg = f"\n🍀 *Vận may tích lũy (+{luck_bonus}%) đã giúp đạo hữu vượt qua thiên kiếp!*" if luck_bonus > 0 else ""
        pet_msg = f"\n✨ Nhờ có **{pet_name}** trợ lực (+{break_buff}%)!" if break_buff > 0 else ""
        
        embed = discord.Embed(
            title="🔥 ĐỘT PHÁ THÀNH CÔNG 🔥",
            description=f"🎉 **{interaction.user.display_name}** đã phi thăng lên **{get_realm(lv + 1)}**!{luck_msg}{pet_msg}",
            color=discord.Color.gold()
        )
        await interaction.followup.send(embed=embed)
            
    else:
        # THẤT BẠI: Tính toán tụt cấp và CỘNG DỒN 5% BẢO HIỂM
        base_tut_cap = 1
        loi_kiep_msg = ""
        
        if lv >= 30 and random.randint(1, 100) <= 30:
            base_tut_cap = random.randint(2, 5)
            loi_kiep_msg = "\n⚡ **LÔI KIẾP BẤT NGỜ!**"

        if risk_reduce > 0 and base_tut_cap > 1:
            tut_cap = max(1, int(base_tut_cap * (1 - risk_reduce)))
            pet_risk_msg = f"\n🐢 **{pet_name}** đã bảo vệ đạo hữu!"
        else:
            tut_cap = base_tut_cap
            pet_risk_msg = ""

        new_lv = max(1, lv - tut_cap)
        # Cộng thêm 5 vào luck_bonus cho lần sau
        new_luck = luck_bonus + 5
        
        await users_col.update_one(
            {"_id": uid},
            {
                "$set": {"level": new_lv, "luck_bonus": new_luck}, 
                "$inc": {"linh_thach": -required_lt}
            }
        )
        
        fail_embed = discord.Embed(
            title="💥 ĐỘT PHÁ THẤT BẠI 💥",
            description=(
                f"😔 **{interaction.user.display_name}** đã gục ngã!{loi_kiep_msg}{pet_risk_msg}\n"
                f"📉 Khấu trừ: **{tut_cap} cấp**\n"
                f"🛡️ **BẢO HIỂM:** Tỉ lệ đột phá lần tới tăng: **+{new_luck}%**"
            ),
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
    embed.set_thumbnail(url="https://i.postimg.cc/sx0d4pWy/Bxh.jpg") 

    await interaction.response.send_message(embed=embed)
import asyncio
@bot.tree.command(name="bxhlc", description="Vinh danh Top 10 cao thủ có Lực chiến cao nhất server")
async def bxhlc(interaction: discord.Interaction):
    await interaction.response.defer()

    # 1. Lấy danh sách tu sĩ (Quét 100 người để tính toán LC)
    all_users = await users_col.find().to_list(length=100)
    
    if not all_users:
        return await interaction.followup.send("⚠️ Chưa có tu sĩ nào ghi danh trên bảng vàng.")

    leaderboard_data = []

    # 2. Duyệt qua từng tu sĩ và tính lực chiến
    for u in all_users:
        uid = str(u.get("_id"))
        
        # --- LẤY TÊN HIỂN THỊ TRƯƠNG TỰ /BXH ---
        member = interaction.guild.get_member(int(uid)) if uid.isdigit() else None
        if member:
            name_display = member.display_name
        else:
            # Nếu không tìm thấy trong cache, lấy 4 số cuối ID để tránh lỗi hiển thị
            name_display = f"Tu sĩ ({uid[-4:]})"
        
        # GỌI HÀM CALC_POWER (Đảm bảo đồng bộ tuyệt đối với /check)
        power_value = await calc_power(uid)
        
        leaderboard_data.append({
            "name": name_display,
            "power": power_value,
            "level": u.get("level", 1),
            "than_khi": u.get("than_khi")
        })

    # 3. Sắp xếp theo Lực chiến giảm dần và lấy Top 10
    leaderboard_data.sort(key=lambda x: x["power"], reverse=True)
    top_10 = leaderboard_data[:10]

    # 4. Xây dựng nội dung hiển thị
    description = ""
    for i, user in enumerate(top_10):
        # Biểu tượng huy chương cho Top 3
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"**#{i+1}**"
        
        # Thêm thông tin Thần khí nếu có
        tk_tag = f" | ⚔️ `{user['than_khi']}`" if user['than_khi'] else ""
        
        # Định dạng giống /bxh để thống nhất phong cách
        description += f"{medal} **{user['name']}**\n└─ Lực chiến: `{user['power']:,}` • Cấp {user['level']}{tk_tag}\n\n"

    # 5. Tạo Embed
    embed = discord.Embed(
        title="🏆 THIÊN BẢNG LỰC CHIẾN 🏆",
        description=description,
        color=0xF1C40F, # Màu Vàng Kim
        timestamp=datetime.now()
    )
    
    embed.set_footer(text=f"Yêu cầu bởi: {interaction.user.display_name}")

    await interaction.followup.send(embed=embed)
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
    
    # Mặc định buff rơi đồ là 0
    additional_buff = 0
    
    # Kiểm tra nếu có Linh thú và Linh thú đó là Tiểu Hỏa Phượng
    user_pet = u.get("pet")
    if user_pet == "Tiểu Hỏa Phượng":
        additional_buff = 0.25 # Tăng thêm 25% tỷ lệ rơi
        # Chèn thêm một câu thông báo nhỏ cho ngầu
        pet_aura = "✨ *Hỏa Phượng minh khiết, thiên vận gia thân!*"
    else:
        pet_aura = ""

    # Tính toán tỷ lệ rơi cuối cùng
    final_drop_rate = drop_rate + additional_buff
    
    # Thực hiện quay số vận may
    if random.random() <= final_drop_rate:
        eq_type = random.choice(EQ_TYPES)
        eq_lv = random.randint(*eq_range)
        
        # Lấy trang bị hiện tại để so sánh
        current_eq = await eq_col.find_one({"_id": uid}) or {}
        old_lv = current_eq.get(eq_type, 0)
        user_than_khi = u.get("than_khi")

        # TRƯỜNG HỢP 1: Nếu là Kiếm và đã có Thần Khí -> Tự rã
        if eq_type == "Kiếm" and user_than_khi:
            exp_gain = eq_lv * 10
            await add_exp(uid, exp_gain)
            drop_msg = f"{pet_aura}\n⚔️ Uy áp từ **[{user_than_khi}]** khiến **{eq_type} cấp {eq_lv}** vụn nát, nhận **{exp_gain} EXP**."
        
        # TRƯỜNG HỢP 2: Nếu cấp độ mới cao hơn -> Thay đồ mới
        elif eq_lv > old_lv:
            await eq_col.update_one({"_id": uid}, {"$set": {eq_type: eq_lv}}, upsert=True)
            drop_msg = f"{pet_aura}\n🎁 **VẬN MAY!** Nhận được: `{eq_type} Cấp {eq_lv}`"
            
        # TRƯỜNG HỢP 3: Đồ yếu hơn hoặc bằng -> Tự rã
        else:
            exp_gain = eq_lv * 10
            await add_exp(uid, exp_gain)
            drop_msg = f"{pet_aura}\n🗑️ Rơi ra `{eq_type} Cấp {eq_lv}`, tự rã nhận **{exp_gain} EXP**."
   # 7. TÍNH TOÁN SỐ LƯỢT MỚI (Xử lý hồi lượt từ Thôn Phệ Thú)
    actual_count_inc = 1
    refund_msg = ""
    if pet_name == "Tiểu Hỏa Phượng" and random.randint(1, 100) <= 20:
        actual_count_inc = 0
        refund_msg = "\n🌀 **Tiểu Hỏa Phượng** hấp thụ linh khí,Tái Sinh, giúp bạn không tốn thể lực!"

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
                    description=f"Giá: 120 Linh thạch - {config[name]['desc'][:50]}..."
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
        if not u or u.get("linh_thach", 0) < 120:
            return await interaction.response.send_message("❌ Đạo hữu không đủ 80 Linh thạch!", ephemeral=True)

        # 3. Thực hiện giao dịch
        await self.users_col.update_one(
            {"_id": self.uid},
            {
                "$set": {"than_khi": selected_tk},
                "$inc": {"linh_thach": -120} # Trừ đúng 80
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
@bot.tree.command(name="loiphat", description="[ADMIN] Thiên phạt: Giảm EXP và có thể rớt cấp (Bảo hộ mốc 21, 31, 41)")
async def loiphat(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_ID:
        return await interaction.response.send_message("❌ **THIÊN PHẠT!** Bạn không có quyền năng này.", ephemeral=True)

    await interaction.response.defer()
    
    top_5 = await users_col.find().sort([("level", -1), ("exp", -1)]).limit(5).to_list(length=5)
    if len(top_5) < 3:
        return await interaction.followup.send("⚠️ Linh khí server chưa đủ mạnh (cần ít nhất 3 người trong BXH)!")

    top_1 = top_5[0]
    others = top_5[1:] 
    victims_others = random.sample(others, k=min(2, len(others)))
    
    than_chu = random.choice(THAN_CHU_THIEN_PHAT)
    report_msg = f"✨ **KHẨU LỆNH:** *\"{than_chu}\"*\n"
    report_msg += "─" * 15 + "\n\n"

    # --- HÀM XỬ LÝ KHẤU TRỪ TU VI ĐÃ ĐỒNG BỘ ---
    async def apply_penalty(user_data, lost_amount):
        uid = user_data.get("_id")
        lv = user_data.get("level", 1)
        current_exp = user_data.get("exp", 0)
        
        # Mốc bảo hộ đạo hữu yêu cầu (Không rớt khi vừa đột phá)
        PROTECTED_LEVELS = [21, 31, 41, 51, 61, 71, 81, 91]
        
        if current_exp >= lost_amount:
            # Trường hợp 1: Đủ EXP để trừ, giữ nguyên cấp
            new_exp = current_exp - lost_amount
            await users_col.update_one({"_id": uid}, {"$set": {"exp": new_exp}})
            return f"Hao tổn **-{lost_amount} EXP**"
        else:
            # Trường hợp 2: Không đủ EXP để trừ
            if lv in PROTECTED_LEVELS or lv <= 1:
                # Gặp mốc bảo hộ: Chỉ đưa về 0 EXP của cấp hiện tại
                await users_col.update_one({"_id": uid}, {"$set": {"exp": 0}})
                return f"Hao tổn **-{current_exp} EXP** (Đã chạm mốc bảo hộ cấp {lv})"
            else:
                # Thực hiện rớt cấp: Tính số EXP còn thiếu
                remainder = lost_amount - current_exp
                new_lv = lv - 1
                
                # SỬ DỤNG CHÍNH HÀM exp_needed CỦA ĐẠO HỮU
                # EXP tối đa của cấp độ mới (sau khi rớt)
                max_exp_of_new_lv = exp_needed(new_lv)
                
                # EXP còn lại ở cấp thấp hơn
                final_exp = max(0, max_exp_of_new_lv - remainder)
                
                await users_col.update_one(
                    {"_id": uid}, 
                    {"$set": {"level": new_lv, "exp": final_exp}}
                )
                return f"📉 **Rớt xuống Cấp {new_lv}** (Thất thoát {lost_amount} Tu vi)"

    # Xử lý Top 1 và các vị còn lại (Giữ nguyên các chỉ số ngẫu nhiên)
    t1_lost = random.randint(500, 1000)
    res_t1 = await apply_penalty(top_1, t1_lost)
    report_msg += f"🔥 **ĐẠI NẠN TOP 1 - <@{top_1['_id']}>**\n   └─ {res_t1}\n\n"

    for user in victims_others:
        lost_val = random.randint(100, 500)
        res_other = await apply_penalty(user, lost_val)
        report_msg += f"⚡ **<@{user['_id']}>** bị lôi đình đánh trúng!\n   └─ {res_other}\n\n"

    # PHÁT THÔNG BÁO TOÀN SERVER
    await broadcast_anomaly(bot, "⛈️ THIÊN PHẠT GIÁNG LÂM ⛈️", report_msg, 0xFF0000, "https://i.imgur.com/K6Y0X9E.gif")

    await interaction.followup.send("✅ Thiên đạo đã thực thi hình phạt.", ephemeral=True)
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

# --- 1. QUẢN LÝ TRẠNG THÁI ---
active_battles = globals().get('active_battles', set())

# --- 2. GIAO DIỆN CHIẾN ĐẤU (VIEW) ---
class BossInviteView(discord.ui.View):
    def __init__(self, target_id, initiator_id, ten_boss, win_rate, config):
        super().__init__(timeout=60)
        self.ids = [str(initiator_id), str(target_id)]
        self.target_id = target_id
        self.ten_boss = ten_boss
        self.win_rate = win_rate
        self.config = config
        self.message = None

    async def on_timeout(self):
        active_battles.difference_update(self.ids)
        try:
            if self.message: await self.message.edit(content=f"⌛ Lời mời đấu **{self.ten_boss}** đã hết hạn!", view=None)
        except: pass

    @discord.ui.button(label="✅ Tiếp Chiến", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_id:
            return await interaction.response.send_message("❌ Không phải lời mời của bạn!", ephemeral=True)
        
        await interaction.response.edit_message(content="⚔️ **ĐANG GIAO TRANH...**", view=None)
        
        try:
            is_win = random.random() < self.win_rate
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Cập nhật lượt đánh và phần thưởng/hình phạt trong 1 lần truy vấn
            update_data = {"$set": {"last_boss": today}}
            if is_win:
                gift = random.randint(*self.config['reward'])
                update_data["$inc"] = {"linh_thach": gift}
                msg = f"🎉 **THẮNG!** Nhận `{gift}` 💎"
                color = discord.Color.green()
            else:
                penalty = self.config['penalty']
                update_data["$inc"] = {"exp": -penalty}
                msg = f"💀 **BẠI!** Phản phệ `-{penalty:,}` EXP"
                color = discord.Color.red()

            await users_col.update_many({"_id": {"$in": self.ids}}, update_data)
            if not is_win: 
                for uid in self.ids: await check_level_down(uid)

            emb = discord.Embed(title=f"⚔️ CHIẾN BÁO: {self.ten_boss}", description=msg, color=color)
            emb.add_field(name="📈 Tỷ lệ thắng", value=f"`{self.win_rate*100:.1f}%`")
            await interaction.followup.send(content=f"<@{self.ids[0]}> <@{self.ids[1]}>", embed=emb)
        finally:
            active_battles.difference_update(self.ids)
            self.stop()

    @discord.ui.button(label="❌ Từ Chối", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_id:
            return await interaction.response.send_message("❌ Lệnh này không phải của bạn!", ephemeral=True)
        await interaction.response.edit_message(content="❌ Lời mời bị khước từ.", view=None)
        active_battles.difference_update(self.ids)
        self.stop()

# --- 3. LỆNH BOSS ---
@bot.tree.command(name="boss", description="Thảo phạt Ma Thần (Tổ đội 2 người)")
@app_commands.describe(member="Đồng đội", ten_boss="Chọn Ma Thần")
@app_commands.choices(ten_boss=[app_commands.Choice(name=k, value=k) for k in BOSS_CONFIG.keys()])
async def boss_hunt(interaction: discord.Interaction, member: discord.Member, ten_boss: str):
    await interaction.response.defer()
    
    uid1, uid2 = str(interaction.user.id), str(member.id)
    if uid1 == uid2 or uid1 in active_battles or uid2 in active_battles:
        return await interaction.followup.send("❌ Không thể thực hiện (Tự mời hoặc đang bận).")

    u1, u2 = await asyncio.gather(users_col.find_one({"_id": uid1}), users_col.find_one({"_id": uid2}))
    today = datetime.now().strftime("%Y-%m-%d")

    if not u1 or not u2: return await interaction.followup.send("⚠️ Tu sĩ chưa có hồ sơ!")
    if u1.get("last_boss") == today or u2.get("last_boss") == today:
        return await interaction.followup.send("❌ Đã hết lượt thảo phạt hôm nay.")

    active_battles.update([uid1, uid2])
    cfg = BOSS_CONFIG[ten_boss]
    
    # Tính LC Boss & Tỷ lệ thắng (Gom gọn công thức)
    p_total = await calc_power(uid1) + await calc_power(uid2)
    boss_p = int((800 * cfg['multiplier']) + cfg['base'])
    win_rate = max(0.01, min(0.95, p_total / (p_total + boss_p)))

    view = BossInviteView(member.id, interaction.user.id, ten_boss, win_rate, cfg)
    view.message = await interaction.followup.send(
        f"⚔️ **{interaction.user.display_name}** mời **{member.mention}** đấu **{ten_boss}**!\n"
        f"👿 LC Boss: `{boss_p:,}` | 📈 Thắng: `{win_rate*100:.1f}%`", view=view
    )


    
@bot.tree.command(name="thanthu", description="Thần thú thị uy chân ngôn (Chỉ dành cho người có linh thú)")
async def pet_show(interaction: discord.Interaction):
    # 1. Khởi động pháp trận (Defer) để tránh treo lệnh
    await interaction.response.defer()
    uid = str(interaction.user.id)
    
    # 2. Truy vấn dữ liệu tu sĩ
    u = await users_col.find_one({"_id": uid})
    
    # 3. CHỐT CHẶN: Kiểm tra nếu không có Thần Thú
    # Kiểm tra cả trường hợp user không tồn tại hoặc trường pet là None/rỗng/"Chưa có"
    pet_name = u.get("pet") if u else None
    
    if not pet_name or pet_name in [None, "", "Chưa có", "Không có"]:
        embed_none = discord.Embed(
            title="⚠️ LINH THÚ CÁC THÔNG BÁO",
            description=(
                "Đạo hữu hiện tại đơn thương độc mã, bên mình không có linh thú hộ vệ.\n\n"
                "*Hãy nỗ lực tu luyện hoặc tìm kiếm cơ duyên để thu phục Thần Thú!*"
            ),
            color=discord.Color.light_gray()
        )
        return await interaction.followup.send(embed=embed_none)

    # 4. CẤU HÌNH CHÂN NGÔN (Dành cho người đã có Pet)
    pet_actions = {
        "Tiểu Hỏa Phượng": {
            "quotes": [
                "🔥 Thân mang Chân Hỏa, nhất vũ kinh thiên, thiêu rụi tà ma!",
                "🔥 Phượng hoàng niết bàn, hỏa diệm ngập trời, vạn vật thành tro!",
                "🔥 Dưới đôi cánh lửa, tài bảo xuất thế, cơ duyên khó cưỡng!"
            ],
            "color": 0xe74c3c, "icon": "🔥"
        },
        "Băng Tinh Hổ": {
            "quotes": [
                "❄️ Mãnh hổ xuất sơn, hàn khí thấu xương, trấn áp thiên địa!",
                "❄️ Tiếng gầm xé toạc không gian, phá tan xiềng xích, nghịch thiên đột phá!",
                "❄️ Băng tinh vĩnh cửu, đóng băng thời gian, vạn pháp quy nhất!"
            ],
            "color": 0x3498db, "icon": "❄️"
        },
        "Thôn Phệ Thú": {
            "quotes": [
                "🐾 Thôn thiên nạp địa, hấp thụ tinh hoa, tu vi đại tiến!",
                "🐾 Linh thú thượng cổ hiện thân, há miệng nuốt chửng linh lực phương viên vạn dặm!",
                "🐾 Một ngụm sạch bóng, vạn linh quy phục, đạo quả viên mãn!"
            ],
            "color": 0x9b59b6, "icon": "🐾"
        },
        "Huyền Quy": {
            "quotes": [
                "🐢 Bất động như sơn, vạn kiếp bất xâm, bảo hộ chân thân!",
                "🐢 Quy giáp hiện linh văn, ngăn chặn thiên lôi, hóa giải lôi kiếp!",
                "🐢 Trấn giữ phương Bắc, thọ cùng trời đất, vĩnh hằng bất diệt!"
            ],
            "color": 0x2ecc71, "icon": "🐢"
        },
        "Hóa Hình Hồ Ly": {
            "quotes": [
                "🦊 Thiên hồ hóa hình, mị hoặc chúng sinh, ảo cảnh vô biên!",
                "🦊 Cửu vĩ lay động, nghịch chuyển càn khôn, biến ảo khôn lường!",
                "🦊 Linh căn huyền diệu, tâm trí thông tuệ, thấu hiểu thiên cơ!"
            ],
            "color": 0xff69b4, "icon": "🦊"
        }
    }

    # 5. XỬ LÝ THỊ UY
    data = pet_actions.get(pet_name)
    
    # Nếu tên pet không nằm trong danh sách cấu hình (Pet lạ)
    if not data:
        embed_unknown = discord.Embed(
            description=f"🐾 **{pet_name}** đang trầm mặc, uy lực tỏa ra khiến vạn vật xung quanh run sợ!",
            color=0x95a5a6
        )
        return await interaction.followup.send(embed=embed_unknown)

    # Chọn ngẫu nhiên chân ngôn
    selected_quote = random.choice(data["quotes"])

    # 6. HIỂN THỊ KẾT QUẢ
    embed_res = discord.Embed(
        title=f"{data['icon']} {pet_name.upper()} THỊ UY",
        description=f"\n## {selected_quote}\n",
        color=data["color"]
    )
    embed_res.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
    embed_res.set_footer(text="Khí thế chấn động bát hoang!")

    await interaction.followup.send(content=f"📡 **Thông cáo thiên hạ:**", embed=embed_res)
@bot.tree.command(name="thankhi", description="Thị uy Thần Khí, Thánh Giáp và kiểm tra báu vật thất lạc")
async def show_thankhi(interaction: discord.Interaction):
    await interaction.response.defer()
    uid = str(interaction.user.id)

    # 1. DỮ LIỆU THẦN KHÍ (Giữ nguyên Khẩu ngữ của đạo hữu)
    THAN_KHI_DATA = {
        "Hiên Viên Kiếm": {"quote": "『 THÁNH ĐẠO PHỤC HƯNG - VẠN KIẾM QUY TÔNG 』", "desc": "Ý chí của thánh đạo ngưng tụ thành hình.", "color": 0xFFD700, "icon": "⚔️"},
        "Thần Nông Đỉnh": {"quote": "『 SINH LINH VẠN ĐẠI - NHẤT ĐỈNH TRƯỜNG SINH 』", "desc": "Hơi thở của sự sống ẩn mình.", "color": 0x2ECC71, "icon": "🧪"},
        "Hạo Thiên Tháp": {"quote": "『 THÁP TRẤN BÁT HOANG - YÊU MA PHỤC DIỆT 』", "desc": "Một điểm tựa giữa dòng thời gian vô tận.", "color": 0x3498DB, "icon": "🗼"},
        "Đông Hoàng Chung": {"quote": "『 CHUÔNG VANG CỬU GIỚI - CHẤN NHIẾP THIÊN THẦN 』", "desc": "Tiếng vọng từ thuở sơ khai tan vào hư không.", "color": 0xE67E22, "icon": "🔔"},
        "Phục Hy Cầm": {"quote": "『 CẦM TẤU HUYỀN CƠ - LOẠN THẾ BÌNH AN 』", "desc": "Giai điệu của những vì sao lạc lối.", "color": 0x9B59B6, "icon": "🪕"},
        "Bàn Cổ Phủ": {"quote": "『 KHAI THIÊN LẬP ĐỊA - PHÁ VỠ HỒNG MÔNG 』", "desc": "Ranh giới mỏng manh giữa tồn tại và hư diệt.", "color": 0x7E5109, "icon": "🪓"},
        "Luyện Yêu Hồ": {"quote": "『 THU NẠP CÀN KHÔN - LUYỆN HÓA VẠN QUỶ 』", "desc": "Cõi mộng nằm gọn trong lòng bàn tay.", "color": 0x1ABC9C, "icon": "🏺"},
        "Côn Lôn Kính": {"quote": "『 KÍNH CHIẾU LUÂN HỒI - THẤU TẬN CHÂN TÂM 』", "desc": "Ánh nhìn phản chiếu từ chiều không gian khác.", "color": 0xECF0F1, "icon": "🪞"},
        "Nữ Oa Thạch": {"quote": "『 NGŨ SẮC VÁ TRỜI - TÁI TẠO NHÂN GIAN 』", "desc": "Mảnh vỡ của bầu trời vỡ nát.", "color": 0xE91E63, "icon": "💎"},
        "Không Đồng Ấn": {"quote": "『 ĐẾ VƯƠNG VĨNH HẰNG - KHÍ VẬN VÔ CƯƠNG 』", "desc": "Khối đá vĩnh cửu mang sức mạnh trường tồn.", "color": 0xBDC3C7, "icon": "📜"}
    }

    try:
        # 2. TRUY VẤN DỮ LIỆU TỪ DATABASE
        u = await users_col.find_one({"_id": uid})
        my_tk = u.get("than_khi")
        my_tg = u.get("thanh_giap")

        # Quét chủ nhân hiện tại của cực phẩm trên toàn server
        owned_tk = await users_col.distinct("than_khi", {"than_khi": {"$ne": None}})
        owned_tg = await users_col.distinct("thanh_giap", {"thanh_giap": {"$ne": None}})

        # Lọc danh sách vô chủ (Chỉ lấy tên)
        avail_tk = [name for name in THAN_KHI_DATA.keys() if name not in owned_tk]
        avail_tg = [name for name in THANH_GIAP_CONFIG.keys() if name not in owned_tg]

        # 3. KHỞI TẠO EMBED
        embed = discord.Embed(title="🏛️ LINH BẢO MINH BẢNG", color=0x2F3136)
        embed.set_author(name=f"Tu sĩ: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        # --- HIỂN THỊ THẦN KHÍ ---
        if my_tk in THAN_KHI_DATA:
            tk = THAN_KHI_DATA[my_tk]
            embed.add_field(name=f"{tk['icon']} Thần Khí: {my_tk}", value=f"**{tk['quote']}**\n*{tk['desc']}*", inline=False)
            embed.color = tk['color']
        else:
            embed.add_field(name="⚔️ Thần Khí", value="🥀 *Cơ duyên chưa tới, báu vật chưa tìm.*", inline=True)

        # --- HIỂN THỊ THÁNH GIÁP (Chỉ lấy khẩu ngữ desc) ---
        # Hiển thị Thánh Giáp cá nhân
        if my_tg in THANH_GIAP_CONFIG:
            tg = THANH_GIAP_CONFIG[my_tg]
            # Hiển thị Quote (Khẩu ngữ) và Desc (Mô tả)
            embed.add_field(
                name=f"🛡️ Thánh Giáp: {my_tg}", 
                value=f"## {tg.get('quote', '『 HÀO QUANG VẠN TRƯỢNG 』')}\n\n*{tg['desc']}*", 
                inline=False
            )
            if not my_tk: embed.color = tg['color']
        else:
            embed.add_field(name="🛡️ Thánh Giáp", value="🥀 *Thân đơn bóng chiếc, chưa mặc giáp trụ.*", inline=True)
        # --- DANH SÁCH VẬT PHẨM CHƯA CÓ CHỦ ---
        if avail_tk:
            embed.add_field(name="🏛️ Thần Khí Vô Chủ", value=", ".join([f"**{t}**" for t in avail_tk]), inline=False)
        
        if avail_tg:
            # Liệt kê tên các bộ giáp đang thất lạc
            tg_text = ", ".join([f"**{t}**" for t in avail_tg])
            embed.add_field(name="🛡️ Thánh Giáp Thất Lạc", value=tg_text, inline=False)

        embed.set_footer(text="Hào quang vạn trượng, chỉ dành cho kẻ có chân mệnh thiên tử.")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Lỗi lệnh thankhi: {e}")
        await interaction.followup.send("⚠️ Thiên địa nhiễu loạn, minh bảng tạm thời bị che khuất.")
@bot.tree.command(name="addthankhi", description="[ADMIN] Ban tặng Thần Khí thượng cổ cho tu sĩ")
@app_commands.describe(target="Tu sĩ được ban tặng", ten_than_khi="Chọn Thần Khí từ danh sách")
# Tự động tạo danh sách lựa chọn từ các Key trong THAN_KHI_CONFIG
@app_commands.choices(ten_than_khi=[
    app_commands.Choice(name=name, value=name) for name in THAN_KHI_CONFIG.keys()
])
async def add_than_khi(interaction: discord.Interaction, target: discord.Member, ten_than_khi: str):
    # 1. Kiểm tra quyền Admin (Sử dụng ADMIN_ID của đạo hữu)
    if interaction.user.id != ADMIN_ID:
        return await interaction.response.send_message("❌ **THIÊN PHẠT!** Đạo hữu không có quyền năng của Thiên Đạo.", ephemeral=True)

    await interaction.response.defer()
    uid = str(target.id)

    # 2. Kiểm tra hồ sơ tu sĩ trong Database
    user = await users_col.find_one({"_id": uid})
    if not user:
        return await interaction.followup.send(f"❌ Tu sĩ {target.mention} chưa có tên trong sổ sinh tử (chưa có hồ sơ).")

    try:
        # 3. Lấy thông tin thần khí từ Config để hiển thị
        config = THAN_KHI_CONFIG[ten_than_khi]
        
        # 4. Cập nhật vào Database
        await users_col.update_one(
            {"_id": uid},
            {"$set": {"than_khi": ten_than_khi}}
        )

        # 5. Tạo Embed thông báo trang trọng
        embed = discord.Embed(
            title="🔱 THIÊN ĐẠO BAN VẬT 🔱",
            description=f"Chúc mừng tu sĩ **{target.display_name}** đã được ban tặng **{ten_than_khi}**!",
            color=config['color'] # Lấy màu sắc tương ứng từ Config
        )
        embed.add_field(name="📜 Truyền thuyết:", value=f"*{config['desc']}*", inline=False)
        embed.add_field(name="⚔️ Sức mạnh:", value=f"Tăng thêm **{config['atk']}** lực chiến.", inline=True)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="Khí vận đại tăng, chấn động bát hoang!")

        await interaction.followup.send(content=target.mention, embed=embed)

    except Exception as e:
        print(f"Lỗi add thần khí: {e}")
        await interaction.followup.send("❌ Đã xảy ra lỗi khi cập nhật thần khí vào pháp trận.")
@bot.tree.command(name="phongthanbang", description="Bảng phong thần: Vinh danh những tu sĩ sở hữu nhiều báu vật nhất")
async def phong_than_bang(interaction: discord.Interaction):
    await interaction.response.defer()
    
    try:
        # 1. LẤY TẤT CẢ TU SĨ CÓ BÁU VẬT
        # Tìm những người có (than_khi hoặc thanh_giap hoặc pet) không phải None/Empty
        cursor = users_col.find({
            "$or": [
                {"than_khi": {"$ne": None, "$exists": True}},
                {"thanh_giap": {"$ne": None, "$exists": True}},
                {"pet": {"$ne": None, "$exists": True}}
            ]
        })
        
        users_list = await cursor.to_list(length=100)
        
        if not users_list:
            return await interaction.followup.send("🥀 Hiện tại chưa có tu sĩ nào sở hữu báu vật độc bản.")

        # 2. TÍNH TOÁN VÀ PHÂN LOẠI
        leaderboard = []
        for u in users_list:
            tk = u.get("than_khi")
            tg = u.get("thanh_giap")
            pet = u.get("pet")
            
            # Tính tổng số lượng
            count = 0
            details = []
            if tk: 
                count += 1
                details.append(f"⚔️ `{tk}`")
            if tg: 
                count += 1
                details.append(f"🛡️ `{tg}`")
            if pet: 
                count += 1
                details.append(f"🐾 `{pet}`")
            
            if count > 0:
                leaderboard.append({
                    "id": u["_id"],
                    "count": count,
                    "details": " | ".join(details)
                })

        # 3. SẮP XẾP: NHIỀU ĐẾN ÍT
        leaderboard.sort(key=lambda x: x["count"], reverse=True)

        # 4. TẠO EMBED HIỂN THỊ
        embed = discord.Embed(
            title="✨ PHONG THẦN BẢNG - LỤC ĐẠO CHÍ TÔN ✨",
            description="*Danh sách những tu sĩ nắm giữ thiên cơ, sở hữu báu vật hiếm nhất thế gian.*",
            color=0xFFD700
        )
        
        top_str = ""
        for i, entry in enumerate(leaderboard[:15]): # Lấy top 15 người
            # Lấy tên member từ cache hoặc fetch
            member = interaction.guild.get_member(int(entry["id"]))
            name = member.display_name if member else f"Ẩn sĩ ({entry['id']})"
            
            # Huy hiệu cho top 3
            medal = ""
            if i == 0: medal = "🥇 "
            elif i == 1: medal = "🥈 "
            elif i == 2: medal = "🥉 "
            else: medal = f"**#{i+1}** "
            
            top_str += f"{medal} **{name}** — 💎 **{entry['count']}** báu vật\n╰┈➤ {entry['details']}\n\n"

        embed.add_field(name="🏆 Thứ Hạng Tu Sĩ", value=top_str, inline=False)
        embed.set_footer(text="Hào quang vạn trượng - Khí vận hanh thông")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Lỗi Phong Thần Bảng: {e}")
        await interaction.followup.send("⚠️ Pháp trận bị nhiễu loạn, không thể xem bảng phong thần.")
keep_alive()
token = os.getenv("DISCORD_TOKEN")
bot.run(token)













































































































































