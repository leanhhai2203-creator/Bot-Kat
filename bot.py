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
    1454506037779369986: 1, 1461017212365181160: 1.5, 1462672263911313439: 1.5
}

# --- CẤU HÌNH CẢNH GIỚI & LINH THÚ ---
REALMS = [
    ("Luyện Khí", 10), ("Trúc Cơ", 20), ("Kết Đan", 30),
    ("Nguyên Anh", 40), ("Hóa Thần", 50), ("Luyện Hư", 60),
    ("Hợp Thể", 70), ("Đại Thừa", 80),
    ("Chân Tiên", 90), ("Kim Tiên", 100)
]
DANH_NGON = [
    "Trời đất không có nhân từ, coi vạn vật như chó rơm.",
    "Ta là đỉnh phong, vạn cổ độc tôn!",
    "Tu tiên là nghịch thiên mà đi, sơ sẩy một bước là vạn kiếp bất phục.",
    "Dưới chân ta là chúng sinh, trên đầu ta là hư vô.",
    "Nhất niệm thành thần, nhất niệm thành ma.",
    "Vạn đạo quy nguyên, thiên địa bất hủ.",
    "Nghịch thiên nhi hành, tu vi chứng đạo.",
    "Trước mặt ta là luân hồi, sau lưng ta là hư không."
]
AN_DE_DATA = {
    "Thương Long Ấn": {"atk": 300, "hp": 2000, "weight": 22, "desc": "Đông Phương - Mộc"},
    "Bạch Hổ Ấn": {"atk": 300, "hp": 2000, "weight": 22, "desc": "Tây Phương - Kim"},
    "Chu Tước Ấn": {"atk": 300, "hp": 2000, "weight": 22, "desc": "Nam Phương - Hỏa"},
    "Huyền Vũ Ấn": {"atk": 300, "hp": 2000, "weight": 22, "desc": "Bắc Phương - Thủy"},
    "Kỳ Lân Đế Ấn": {"atk": 400, "hp": 4000, "weight": 12, "desc": "Trung Tâm - Thổ (Chí Tôn)"}
}
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
        "risk_reduce": 1,
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
# --- 1. CẤU HÌNH BÍ CẢNH ---
BI_CANH_CONFIG = {
    "tcn": {
        "name": "Tiên Cư Nguyên",
        "boss_power": 35000,
        "boss_chance": 0.4, "trap_chance": 0.1, "treasure_chance": 0.2,
        "exp": 500, "lt": 10, "trap_penalty": 500,
        "gear_rate": [6, 7]
    },
    "nmq": {
        "name": "Nhạn Môn Quan",
        "boss_power": 50000,
        "boss_chance": 0.4, "trap_chance": 0.15, "treasure_chance": 0.25,
        "exp": 750, "lt": 15, "trap_penalty": 750,
        "gear_rate": [7, 8]
    },
    "bctl": {
        "name": "Biên Cảnh Tống Liêu",
        "boss_power": 70000,
        "boss_chance": 0.5, "trap_chance": 0.20, "treasure_chance": 0.2,
        "exp": 1000, "lt": 20, "trap_penalty": 1500,
        "tien_thach_chance": 0.1,
        "tien_thach_amount": 1,
        "gear_rate": [8, 9]
    }
}
PET_CONFIG = {
    "Tiểu Hỏa Phượng": {
        "atk": 180, "hp": 2000, 
        "drop_buff": 0.1, "break_buff": 0, "risk_reduce": 0,
        "effect": "Tăng 10% rơi đồ", "color": 0xe74c3c, "icon": "🔥",
        "quotes": [
            "🔥 Thân mang Chân Hỏa, nhất vũ kinh thiên, thiêu rụi tà ma!",
            "🔥 Phượng hoàng niết bàn, hỏa diệm ngập trời, vạn vật thành tro!",
            "🔥 Dưới đôi cánh lửa, tài bảo xuất thế, cơ duyên khó cưỡng!"
        ]
    },
    "U Minh Tước": {
        "atk": 220, "hp": 2000, 
        "break_buff": 0, "risk_reduce": 0,
        "effect": "Tăng 5% tỷ lệ thắng mọi trận đấu", "icon": "🌀", "color": 0x4B0082,
        "quotes": [
            "🌀 U minh dẫn lối, tước ảnh vô hình, đoạt hồn trong chớp mắt!",
            "🌀 Từ cõi vĩnh hằng trở về, bóng tối của ta bao trùm vạn dặm!",
            "🌀 Đôi cánh vỗ nhẹ, không gian tan vỡ, nghịch chuyển bại thành thắng!"
        ]
    },
    "Băng Tinh Hổ": {
        "atk": 170, "hp": 2300, 
        "break_buff": 5, "risk_reduce": 0,
        "effect": "Tăng 5% tỉ lệ đột phá", "color": 0x3498db, "icon": "❄️",
        "quotes": [
            "❄️ Mãnh hổ xuất sơn, hàn khí thấu xương, trấn áp thiên địa!",
            "❄️ Tiếng gầm xé toạc không gian, phá tan xiềng xích, nghịch thiên đột phá!",
            "❄️ Băng tinh vĩnh cửu, đóng băng thời gian, vạn pháp quy nhất!"
        ]
    },
    "Thôn Phệ Thú": {
        "atk": 170, "hp": 2200, 
        "exp_mult": 1.15, "break_buff": 0, "risk_reduce": 0,
        "effect": "Tăng 15% EXP", "color": 0x9b59b6, "icon": "🐾",
        "quotes": [
            "🐾 Thôn thiên nạp địa, hấp thụ tinh hoa, tu vi đại tiến!",
            "🐾 Linh thú thượng cổ hiện thân, há miệng nuốt chửng linh lực phương viên vạn dặm!",
            "🐾 Một ngụm sạch bóng, vạn linh quy phục, đạo quả viên mãn!"
        ]
    },
    "Huyền Quy": {
        "atk": 120, "hp": 3000, 
        "break_buff": 0, "risk_reduce": 0.5,
        "effect": "Giảm 50% rủi ro Lôi Kiếp", "color": 0x2ecc71, "icon": "🐢",
        "quotes": [
            "🐢 Bất động như sơn, vạn kiếp bất xâm, bảo hộ chân thân!",
            "🐢 Quy giáp hiện linh văn, ngăn chặn thiên lôi, hóa giải lôi kiếp!",
            "🐢 Trấn giữ phương Bắc, thọ cùng trời đất, vĩnh hằng bất diệt!"
        ]
    },
    "Hóa Hình Hồ Ly": {
        "atk": 190, "hp": 2500, 
        "lt_buff": 0.2, "break_buff": 0, "risk_reduce": 0,
        "effect": "Tăng 20% Linh Thạch", "color": 0xff99cc, "icon": "🌸",
        "quotes": [
            "🦊 Cửu vĩ che trời, nhất niệm thành tro. Dưới gót chân ta, vạn cổ thiên ma đều là cát bụi!",
            "🦊 Huyết mạch Thiên Hồ vĩnh hằng bất diệt. Kẻ nghịch ta là ác mộng, kẻ theo ta chính là chân mệnh!",
            "🦊 Chúng sinh điên đảo vì sắc, tu sĩ gục ngã vì tình. Chỉ có chủ nhân mới xứng đáng khiến ta khuynh đảo thiên hạ!",
            "🦊 Mắt tím nhìn thấu luân hồi, linh căn cảm ứng thiên địa. Chút linh thạch này... là lễ vật ta dâng ngài!"
        ]
    }
}
THANH_NHAN_CONFIG = {}
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
    return "Tiên Nhân"

def get_monster_data(lv: int):
    if lv <= 10: return "Yêu thú", 0.15, (1, 2)
    elif lv <= 30: return "Ma thú", 0.20, (2, 4)
    elif lv <= 60: return "Linh thú", 0.25, (4, 7)
    else: return "Cổ thú", 0.30, (6, 9)
async def calc_power(uid: str) -> int:
    uid = str(uid)
    
    # 1. Truy vấn dữ liệu song song (Tối ưu tốc độ)
    # Thay vì await lần lượt, ta lấy dữ liệu user và trang bị cùng lúc nếu cần thiết, 
    # nhưng ở đây giữ nguyên luồng logic đơn giản để dễ debug.
    u = await users_col.find_one({"_id": uid})
    if not u: 
        return 0
    
    # Lấy dữ liệu trang bị, mặc định là dict rỗng nếu chưa có
    eq = await eq_col.find_one({"_id": uid}) or {}
    
    # 2. Khởi tạo biến dữ liệu
    lv = u.get("level", 1)
    pet_name = u.get("pet")
    than_khi_name = u.get("than_khi") 
    thanh_giap_name = u.get("thanh_giap")
    
    # --- BƯỚC 1: TÍNH CHỈ SỐ GỐC TỪ LEVEL ---
    # Lv 1: Atk 5, HP 50
    atk = lv * 5
    hp = lv * 50
    
    # --- BƯỚC 2: CỘNG DỒN CHỈ SỐ TRANG BỊ (Equipment) ---
    # Logic mới: Cộng thẳng vào, không quan tâm có Thần Khí hay không
    for t in EQ_TYPES:
        eq_lv = eq.get(t, 0)
        if eq_lv <= 0: continue 
        
        # Phân loại trang bị để cộng chỉ số tương ứng
        if t in ["Kiếm", "Nhẫn"]:
            # Kiếm và Nhẫn tăng Tấn Công (ATK)
            atk += eq_lv * 15
        else:
            # Giáp, Tay, Ủng (và các loại khác) tăng Máu (HP)
            hp += eq_lv * 150
            
    # --- BƯỚC 3: CỘNG DỒN CHỈ SỐ CỰC PHẨM (Thần Khí & Thánh Giáp) ---
    # Logic mới: Luôn luôn cộng thêm nếu sở hữu
    if than_khi_name and than_khi_name in THAN_KHI_CONFIG:
        # Lấy atk từ config, an toàn với .get()
        atk += THAN_KHI_CONFIG[than_khi_name].get("atk", 200)
            
    if thanh_giap_name and thanh_giap_name in THANH_GIAP_CONFIG:
        # Lấy hp từ config
        hp += THANH_GIAP_CONFIG[thanh_giap_name].get("hp", 2500)

    # --- BƯỚC 4: CỘNG DỒN CHỈ SỐ LINH THÚ (Pet) ---
    if pet_name and pet_name in PET_CONFIG:
        p_stats = PET_CONFIG[pet_name]
        atk += p_stats.get("atk", 0)
        hp += p_stats.get("hp", 0) 

    # --- BƯỚC 5: TỔNG HỢP LỰC CHIẾN ---
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
    
    # 1. Nếu EXP vẫn >= 0 hoặc đang ở tân thủ (lv 1) thì không xử lý
    if exp >= 0 or lv <= 1: 
        return False

    # 2. KIỂM TRA MỐC KHÓA (Checkpoints)
    # Ví dụ: 11 (Trúc Cơ), 21 (Kết Đan)... 
    # Nếu lv là mốc đầu của một cảnh giới mới, không cho rớt xuống cảnh giới cũ
    checkpoints = [11, 21, 31, 41, 51, 61, 71, 81, 91] 
    if lv in checkpoints:
        # Giữ nguyên cấp, nhưng reset EXP về 0 để phạt
        await users_col.update_one({"_id": uid}, {"$set": {"exp": 0}})
        return "reset"

    # 3. LOGIC GIẢM CẤP (PHẢN PHỆ)
    new_lv = lv - 1
    
    # Lấy EXP cần có của cấp mới (cấp vừa lùi xuống)
    # Giả sử hàm exp_needed là hàm đồng bộ (sync), nếu là async hãy thêm await
    try:
        req_exp_new_lv = exp_needed(new_lv) 
    except Exception as e:
        print(f"❌ Lỗi hàm exp_needed: {e}")
        return False

    # Tính toán EXP còn lại sau khi lùi cấp
    # Ví dụ: Cấp 10 cần 1000 EXP. Đang cấp 11 bị âm 200.
    # New_exp = 1000 + (-200) = 800. Người chơi sẽ ở Lv 10 (800/1000)
    new_exp = req_exp_new_lv + exp 
    
    # Đảm bảo EXP không bị âm sau khi tính toán
    final_exp = max(0, new_exp)
    
    await users_col.update_one(
        {"_id": uid},
        {"$set": {"level": new_lv, "exp": final_exp}}
    )
    
    print(f"💀 Đạo hữu {uid} bị phản phệ, rớt xuống cấp {new_lv}")
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
        # 1. ƯU TIÊN: Đồng bộ lệnh Slash trước để người dùng thấy lệnh ngay
        print("🔄 Đang đồng bộ lệnh Slash...")
        synced = await bot.tree.sync()
        print(f"✅ Đã đồng bộ {len(synced)} lệnh Slash.")
        
        print(f"✅ Đã đăng nhập: {bot.user}")

        # 2. XỬ LÝ DATABASE (Chạy ngầm hoặc chạy sau)
        print("⏳ Đang tối ưu hóa Database (Tạo Index)...")
        # Sử dụng background task hoặc làm tuần tự nhưng sau khi đã Sync
        await users_col.create_index([("level", -1)])
        await users_col.create_index([("exp", -1)])
        await users_col.create_index([("than_khi", 1)])
        await users_col.create_index([("thanh_giap", 1)])
        await users_col.create_index([("pet", 1)])
        print("✅ Tối ưu hóa Database hoàn tất!")

        # 3. KHỞI CHẠY CÁC VÒNG LẶP (LOOPS)
        await update_server_avg() 
        if not update_server_avg.is_running(): 
            update_server_avg.start()
            print("📈 Đã chạy vòng lặp Cập nhật Server.")
            
        if not thien_y_loop.is_running(): 
            thien_y_loop.start()
            print("🌌 Đã chạy vòng lặp Thiên Ý.")
            
        print("🚀 Bot đã sẵn sàng và chạy mượt hơn!")

    except Exception as e:
        # Lỗi ở Index hay Loop sẽ không làm bot bị sập hoàn toàn nếu ta bắt lỗi tốt
        print(f"❌ Lỗi khởi động: {e}")
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
        await interaction.response.defer()
        uid = str(interaction.user.id)
        
        # 1. Lấy dữ liệu từ các Collection
        u = await users_col.find_one({"_id": uid})
        if not u:
            return await interaction.followup.send("⚠️ Đạo hữu chưa có tên trong sổ sinh tử!")
        
        eq = await eq_col.find_one({"_id": uid}) or {}
        
        # 2. Thu thập thông tin cơ bản
        level = u.get("level", 1)
        cur_exp = u.get("exp", 0)
        linh_thach = u.get("linh_thach", 0)
        tien_thach = u.get("tien_thach", 0)
        pet_name = u.get("pet")
        
        # Trang bị đặc biệt
        than_khi_name = u.get("than_khi")
        thanh_giap_name = u.get("thanh_giap")
        thanh_nhan_name = u.get("thanh_nhan")
        
        # Ấn Đế (Đế Cách)
        an_de_name = u.get("an_de")
        duc_an_progress = u.get("duc_an_progress", 0)

        # 3. Xử lý hiển thị từng món trang bị
        # Vũ khí
        if than_khi_name:
            weapon_display = f"🌟 **{than_khi_name}**"
        else:
            kiem_lv = eq.get("Kiếm", 0)
            weapon_display = f"⚔️ Kiếm Cấp {kiem_lv}" if kiem_lv > 0 else "⚔️ Vô nhận kiếm"

        # Nhẫn (Thánh Nhẫn)
        if thanh_nhan_name:
            nhan_display = f"💍 **{thanh_nhan_name}**"
        else:
            nhan_lv = eq.get("Nhẫn", 0)
            nhan_display = f"💍 Nhẫn Cấp {nhan_lv}" if nhan_lv > 0 else "💍 Nhẫn Cỏ"

        # Giáp (Thánh Giáp)
        icon_giap = "<:emoji_31:1464123093579731005>"
        if thanh_giap_name:
            giap_display = f"{icon_giap} **{thanh_giap_name}**"
        else:
            giap_lv = eq.get("Giáp", 0)
            giap_display = f"{icon_giap} Giáp Cấp {giap_lv}" if giap_lv > 0 else f"{icon_giap} Bố y"

        # Ấn Đế (Đế Cách)
        if an_de_name and an_de_name in AN_DE_DATA:
            an_icon = AN_DE_DATA[an_de_name].get("icon", "🔱")
            an_display = f"{an_icon} **{an_de_name}**"
        elif duc_an_progress > 0:
            an_display = f"🔨 *Đang đúc ({duc_an_progress}/10)*"
        else:
            an_display = "❌ *Chưa có*"

        # 4. Tính toán Lực chiến & Cảnh giới & Màu sắc
        total_power = await calc_power(uid)
        display_canh_gioi = get_realm(level)

        embed_color = discord.Color.blue()
        if level >= 81:
            embed_color = discord.Color.from_rgb(255, 0, 0) # Đỏ rực cho Địa Tiên
        elif than_khi_name or thanh_giap_name or thanh_nhan_name or an_de_name:
            embed_color = discord.Color.gold() # Vàng kim nếu có đồ cực phẩm

        # 5. Khởi tạo Embed chính
        embed = discord.Embed(title=f"📜 HỒ SƠ TU TIÊN: {interaction.user.display_name}", color=embed_color)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        embed.add_field(name="📜 Cảnh Giới", value=f"**{display_canh_gioi}**", inline=False)
        embed.add_field(name="⚔️ Lực Chiến", value=f"**{total_power:,}**", inline=True)
        
        tai_san_str = f"🔹 Linh Thạch: `{linh_thach:,}`\n🔮 Tiên Thạch: `{tien_thach:,}`"
        embed.add_field(name="💎 Tài Sản", value=tai_san_str, inline=True)

        # Kinh nghiệm (Linh lực)
        if level % 10 == 0:
            exp_display = f"`{int(cur_exp):,} / Đỉnh Phong (Cần Đột Phá)`"
        else:
            needed = exp_needed(level)
            exp_display = f"`{int(cur_exp):,} / {int(needed):,}`"
        embed.add_field(name="✨ Linh Lực", value=exp_display, inline=False)

        # Tổng hợp trang bị (Sắp xếp lại cho scannable)
        trang_bi_str = (
            f"{weapon_display}\n"
            f"{nhan_display}\n"
            f"{giap_display}\n"
            f"🧤 Tay: Cấp {eq.get('Tay', 0)}\n"
            f"👢 Ủng: Cấp {eq.get('Ủng', 0)}"
        )
        embed.add_field(name="📦 Trang Bị", value=trang_bi_str, inline=True)
        
        # Linh thú và Ấn đế
        extra_str = (
            f"🐾 **{pet_name or 'Chưa có'}**\n"
            f"👑 **{an_display}**"
        )
        embed.add_field(name="🦄 Linh Thú & Ấn", value=extra_str, inline=True)

        embeds_to_send = [embed]

        # 6. Gửi Danh Ngôn nếu là cấp cao
        if level >= 81:
            quote_embed = discord.Embed(
                description=f"💬 *\"{random.choice(DANH_NGON)}\"*",
                color=embed_color
            )
            quote_embed.set_author(name=f"Khẩu Quyết Đại Năng - {interaction.user.display_name}")
            embeds_to_send.append(quote_embed)

        await interaction.followup.send(embeds=embeds_to_send)

    except Exception as e:
        print(f"❌ Lỗi lệnh check: {e}")
        try: await interaction.followup.send("⚠️ Linh lực hỗn loạn, không thể xem hồ sơ!")
        except: pass
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
        if not current_user_tg and not got_tg_this_turn and random.random() <= 0.004:
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
                    tg_msg = f"\n\n🧥 **THÁNH VẬT XUẤT THẾ: [{new_tg}]**"
                    final_color = 0xFFD700
            except Exception as e:
                print(f"Lỗi Gacha Thánh Giáp: {e}")

        # 2. LOGIC LINH THÚ (0.1% - Mỗi người chỉ mang 1 con)
        # Điều kiện: User chưa có Linh thú trên người AND chưa trúng con nào trong lượt x10 này
        if not current_user_pet and not got_pet_this_turn and random.random() <= 0.001:
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
                special_msg = f"🌌 **KHÍ VẬN NGHỊCH THIÊN!** {winner_name} mặc **{winner_tg}**, tay cầm **{winner_tk}**, đồng hành cùng **{winner_pet}** quét sạch bát hoang!"

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
@bot.tree.command(name="dotpha", description="Đột phá cảnh giới (Cần Tiên Thạch từ cấp 80+)")
async def dotpha(interaction: discord.Interaction):
    # ƯU TIÊN SỐ 1: Phản hồi Discord ngay lập tức để tránh lỗi 404 Unknown Interaction
    await interaction.response.defer()
    
    uid = str(interaction.user.id)
    
    try:
        # 1. Truy xuất dữ liệu (Sau khi đã defer)
        u = await users_col.find_one({"_id": uid})
        if not u: 
            return await interaction.followup.send("❌ Đạo hữu chưa có hồ sơ tu tiên!")

        lv = u.get("level", 1)
        linh_thach = u.get("linh_thach", 0)
        tien_thach = u.get("tien_thach", 0)
        exp = u.get("exp", 0)
        luck_bonus = u.get("luck_bonus", 0) 

        # 2. Kiểm tra điều kiện đỉnh phong
        if lv % 10 != 0:
            return await interaction.followup.send(f"❌ Cần đạt đỉnh phong cấp {lv//10*10+10} để đột phá. Hiện tại: **Cấp {lv}**")

        # Kiểm tra EXP (Sử dụng hàm của đạo hữu)
        needed = exp_needed(lv)
        if exp < needed:
            return await interaction.followup.send(f"❌ Tu vi chưa đủ! (Cần {int(exp)}/{needed} EXP)")

        # Phí tài nguyên
        required_lt = 3 if lv < 30 else (10 if lv < 60 else (15 if lv < 80 else 20))
        needs_tien_thach = (lv >= 80)
        
        if linh_thach < required_lt:
            return await interaction.followup.send(f"❌ Cần **{required_lt} Linh thạch**.")
        
        if needs_tien_thach and tien_thach < 1:
            return await interaction.followup.send(f"❌ Cảnh giới cao cần thêm **1 Tiên Thạch** 🔮!")

        # 3. Quét trang bị tính Buff (Sử dụng globals().get để tránh NameError)
        equipment_map = [
            ("pet", globals().get('PET_CONFIG', {}), "🐾"),
            ("an_de", globals().get('AN_DE_DATA', {}), "👑"),
            ("thanh_giap", globals().get('THANH_GIAP_CONFIG', {}), "🛡️"),
            ("thanh_nhan", globals().get('THANH_NHAN_CONFIG', {}), "💍"),
            ("than_khi", globals().get('THAN_KHI_CONFIG', {}), "🌟")
        ]
        
        total_break_buff = 0
        total_risk_reduce = 0.0
        protection_sources = []

        for field, config, icon in equipment_map:
            item_name = u.get(field)
            if item_name and item_name in config:
                item_data = config[item_name]
                total_break_buff += item_data.get("break_buff", 0)
                red = item_data.get("risk_reduce", 0.0)
                if red > 0:
                    total_risk_reduce += red
                    protection_sources.append(f"{icon} {item_name}")

        # 4. Tính toán tỉ lệ thành công
        realm_index = lv // 10
        base_rate = max(5, 90 - (realm_index * 10))
        final_rate = base_rate + total_break_buff + luck_bonus
        
        # Thực hiện quay số
        success = random.randint(1, 100) <= final_rate

        # Cấu trúc query update phí
        update_query = {"$inc": {"linh_thach": -required_lt}}
        if needs_tien_thach:
            update_query["$inc"]["tien_thach"] = -1

        # 5. Xử lý kết quả
        if success:
            # THÀNH CÔNG
            update_query["$set"] = {"level": lv + 1, "exp": 0, "luck_bonus": 0}
            await users_col.update_one({"_id": uid}, update_query)
            
            try:
                new_realm_name = get_realm(lv + 1)
            except:
                new_realm_name = f"Cảnh giới mới (Cấp {lv + 1})"

            embed = discord.Embed(
                title="🔥 ĐỘT PHÁ THÀNH CÔNG 🔥",
                description=(
                    f"🎉 **{interaction.user.display_name}** đã phi thăng lên **{new_realm_name}**!\n"
                    f"✨ Tỉ lệ: `{final_rate}%` (Buff: +{total_break_buff}%)"
                ),
                color=discord.Color.gold()
            )
            await interaction.followup.send(embed=embed)
                
        else:
            # THẤT BẠI
            base_tut = 1
            loi_kiep_msg = ""
            if lv >= 30 and random.randint(1, 100) <= 30:
                base_tut = random.randint(2, 5)
                loi_kiep_msg = "\n⚡ **LÔI KIẾP BẤT NGỜ!** Đạo tâm bị chấn động!"

            # Giảm rủi ro (Tối đa 90%)
            total_risk_reduce = min(total_risk_reduce, 0.9)
            tut_cap = max(1, int(base_tut * (1 - total_risk_reduce)))
            new_luck = luck_bonus + 5
            
            update_query["$set"] = {"level": max(1, lv - tut_cap), "luck_bonus": new_luck}
            await users_col.update_one({"_id": uid}, update_query)

            prot_msg = f"\n🛡️ **Bảo hộ:** {', '.join(protection_sources)} đã giảm nhẹ phản phệ!" if protection_sources else ""
            
            fail_embed = discord.Embed(
                title="💥 ĐỘT PHÁ THẤT BẠI 💥",
                description=(
                    f"😔 **{interaction.user.display_name}** đã gục ngã!{loi_kiep_msg}{prot_msg}\n"
                    f"📉 Khấu trừ: **{tut_cap} cấp**\n"
                    f"🛡️ **BẢO HIỂM:** Tỉ lệ lần tới tăng: **+{new_luck}%**\n"
                    f"💸 Mất: `{required_lt} LT`" + (f" và `1 Tiên Thạch`" if needs_tien_thach else "")
                ),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=fail_embed)

    except Exception as e:
        # Log lỗi ra Render để đạo hữu kiểm tra
        print(f"CRITICAL ERROR: {e}")
        try:
            await interaction.followup.send(f"⚠️ Pháp trận nhiễu loạn! Lỗi: `{e}`")
        except:
            pass
@bot.tree.command(name="huongdan", description="Xem bí kíp tu tiên - Hướng dẫn chi tiết cách chơi")
async def huongdan(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 THÁI THƯỢNG BÍ KÍP - HƯỚNG DẪN TU TIÊN",
        description="Chào mừng đạo hữu bước chân vào con đường nghịch thiên cải mệnh. Hãy nắm vững các quy tắc sau để sớm ngày phi thăng!",
        color=discord.Color.from_rgb(255, 215, 0) # Màu Vàng Kim
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    # 1. Cơ chế Linh Khí (EXP)
    embed.add_field(
        name="🧘 1. Tu Luyện (Nhận EXP)",
        value=(
            "- **Nhắn tin**: Mỗi tin nhắn > 7 ký tự nhận được Linh Khí.\n"
            "- **Hồi chiêu**: 20 giây giữa mỗi lần nhắn.\n"
            "- **Thiên Đạo Trợ Lực**: Tu sĩ cấp thấp nhận x2 EXP."
        ),
        inline=True
    )
    # 2. Cảnh Giới & Đột Phá
    embed.add_field(
        name="⚡ 2. Cảnh Giới & Đột Phá",
        value=(
            "- Các mốc bảo mệnh: **11, 21, 31...**\n"
            "- Khi đạt mốc này, nếu thất bại chỉ bị reset EXP về 0 chứ không rớt cấp cũ."
        ),
        inline=True
    )
    # 3. Tài Nguyên Cao Cấp (MỚI)
    embed.add_field(
        name="💎 3. Linh Thạch & Tiên Thạch",
        value=(
            "- **Linh Thạch**: Tiền tệ phổ thông dùng mua trang bị, đúc Ấn bước đầu.\n"
            "- **Tiên Thạch**: Tài nguyên cực hiếm, dùng để đúc Ấn giai đoạn cuối (bước 8-10) và nâng cấp Thánh Vật."
        ),
        inline=False
    )
    # 4. Hệ Thống Đúc Ấn (MỚI)
    embed.add_field(
        name="👑 4. Lò Luyện Ấn Đế (Đế Cách)",
        value=(
            "- Sử dụng `/ducan` để tích lũy tiến độ (10 tầng).\n"
            "- **Tiến độ 1-7**: Tốn 15 Linh Thạch/lần.\n"
            "- **Tiến độ 8-10**: Tốn 1 Tiên Thạch/lần.\n"
            "- Khi đủ 10/10, ngẫu nhiên nhận 1 trong **Ngũ Đại Ấn**: Thương Long, Bạch Hổ, Chu Tước, Huyền Vũ hoặc **Kỳ Lân Đế Ấn** (Cực phẩm)."
        ),
        inline=False
    )
    # 5. Hái Dược (MỚI)
    embed.add_field(
        name="🌿 5. Hái Dược & Thảo Dược",
        value=(
            "- Sử dụng `/haiduoc` tại các linh sơn.\n"
            "- Nhận được thảo dược dùng để luyện đan hoặc bán lấy Linh Thạch.\n"
            "- Cẩn thận: Có xác suất gặp yêu quái canh giữ dược điền!"
        ),
        inline=False
    )
    # 6. Trang Bị & Lực Chiến
    embed.add_field(
        name="⚔️ 6. Trang Bị Cực Phẩm",
        value=(
            "- **Thần Khí / Thánh Giáp / Thánh Nhẫn**: Trang bị có tên riêng, tăng chỉ số vượt trội.\n"
            "- **Ấn Đế**: Trang bị duy nhất tăng cả Tấn Công và Sinh Mệnh theo phần trăm cực lớn."
        ),
        inline=False
    )
    # 7. Lệnh Thường Dùng (CẬP NHẬT)
    embed.add_field(
        name="🛠️ 7. Các Lệnh Cần Nhớ",
        value=(
            "`/check`: Xem hồ sơ & Ấn Đế.\n"
            "`/ducan`: Luyện đúc Đế Cách.\n"
            "`/haiduoc`: Tìm kiếm thảo dược.\n"
            "`/gacha`: Quay tầm bảo.\n"
            "`/diemdanh`: Nhận quà hàng ngày."
        ),
        inline=False
    )
    embed.set_footer(text="Chúc đạo hữu khí vận hanh thông, sớm ngày đắc đạo!")
    await interaction.response.send_message(embed=embed)
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
    additional_buff = 0
    pet_aura = ""

    # Kiểm tra buff từ Linh thú (Tiểu Hỏa Phượng)
    if u.get("pet") == "Tiểu Hỏa Phượng":
        additional_buff = 0.25
        pet_aura = "✨ *Hỏa Phượng minh khiết, thiên vận gia thân!*"

    # Tính toán tỷ lệ rơi cuối cùng
    final_drop_rate = drop_rate + additional_buff
    
    # BẮT ĐẦU ROLL RƠI ĐỒ
    if random.random() <= final_drop_rate:
        eq_type = random.choice(EQ_TYPES)
        eq_lv = random.randint(*eq_range)
        
        # Lấy trang bị hiện tại để so sánh
        current_eq = await eq_col.find_one({"_id": uid}) or {}
        old_lv = current_eq.get(eq_type, 0)
        
        # KIỂM TRA ĐIỀU KIỆN NHẬN ĐỒ (Sửa lỗi Syntax tại đây)
        if eq_lv > old_lv:
            # TRƯỜNG HỢP 1: Đồ mới mạnh hơn -> Cập nhật trang bị
            await eq_col.update_one({"_id": uid}, {"$set": {eq_type: eq_lv}}, upsert=True)
            drop_msg = f"\n{pet_aura}\n🎁 **VẬN MAY!** Nhận được: `{eq_type} Cấp {eq_lv}`"
        else:
            # TRƯỜNG HỢP 2: Đồ yếu hơn hoặc bằng -> Tự rã lấy EXP
            # Lưu ý: Ta cộng dồn vào exp_gain hiện tại để update DB một lần ở cuối
            exp_from_gear = eq_lv * 10
            exp_gain += exp_from_gear 
            drop_msg = f"\n{pet_aura}\n🗑️ Rơi ra `{eq_type} Cấp {eq_lv}`, tự rã nhận **{exp_from_gear} EXP**."
   # 7. TÍNH TOÁN SỐ LƯỢT MỚI (Xử lý hồi lượt từ Thôn Phệ Thú)
    actual_count_inc = 1
    refund_msg = ""
    if pet_name == "Tiểu Hỏa Phượng" and random.randint(1, 100) <= 30:
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
    def __init__(self, sender, receiver, amount, resource_type, label):
        super().__init__(timeout=30)
        self.sender = sender      # Người gửi (Member object)
        self.receiver = receiver  # Người nhận (Member object)
        self.amount = amount
        self.resource_type = resource_type
        self.label = label

    @discord.ui.button(label="Xác Nhận", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 1. Chỉ người gửi mới có quyền nhấn nút
        if interaction.user.id != self.sender.id:
            return await interaction.response.send_message("❌ Đây không phải pháp trận của đạo hữu!", ephemeral=True)

        # 2. Kiểm tra lại số dư thực tế trong DB một lần cuối (phòng trường hợp người chơi spam)
        uid = str(self.sender.id)
        u_data = await users_col.find_one({"_id": uid})
        if not u_data or u_data.get(self.resource_type, 0) < self.amount:
            return await interaction.response.edit_message(content="❌ Giao dịch thất bại: Số dư của đạo hữu đã thay đổi!", view=None)

        # 3. Thực hiện chuyển tài nguyên
        # Trừ người gửi
        await users_col.update_one({"_id": uid}, {"$inc": {self.resource_type: -self.amount}})
        # Cộng người nhận (Tạo mới profile nếu người nhận chưa có - upsert)
        await users_col.update_one({"_id": str(self.receiver.id)}, {"$inc": {self.resource_type: self.amount}}, upsert=True)

        # 4. Thông báo thành công
        await interaction.response.edit_message(
            content=f"✅ **GIAO DỊCH THÀNH CÔNG**\nĐạo hữu **{self.sender.mention}** đã chuyển thành công `{self.amount}` {self.label} cho **{self.receiver.mention}**.",
            view=None
        )
        self.stop()

    @discord.ui.button(label="Hủy", style=discord.ButtonStyle.red, emoji="✖️")
    async def cancel_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.sender.id:
            return await interaction.response.send_message("❌ Chỉ người gửi mới có thể hủy!", ephemeral=True)
            
        await interaction.response.edit_message(content="🗑️ Giao dịch đã bị hủy bỏ.", view=None)
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
from discord import app_commands

@bot.tree.command(name="give", description="Chuyển tài nguyên (Linh Thạch/Tiên Thạch) cho đạo hữu khác")
@app_commands.describe(
    member="Đạo hữu nhận tài nguyên", 
    resource_type="Loại tài nguyên muốn chuyển",
    amount="Số lượng muốn chuyển"
)
@app_commands.choices(resource_type=[
    app_commands.Choice(name="Linh Thạch 💎", value="linh_thach"),
    app_commands.Choice(name="Tiên Thạch 🔮", value="tien_thach")
])
async def give(interaction: discord.Interaction, member: discord.Member, resource_type: str, amount: int):
    # 1. Các kiểm tra cơ bản
    if amount <= 0:
        return await interaction.response.send_message("❌ Số lượng chuyển phải lớn hơn 0!", ephemeral=True)
    if member.id == interaction.user.id:
        return await interaction.response.send_message("❌ Đạo hữu không thể tự chuyển cho chính mình!", ephemeral=True)
    if member.bot:
        return await interaction.response.send_message("❌ Không thể chuyển tài nguyên cho thực thể nhân tạo!", ephemeral=True)

    uid = str(interaction.user.id)
    tid = str(member.id)
    
    # Lấy dữ liệu người gửi
    u = await users_col.find_one({"_id": uid})
    if not u:
        return await interaction.response.send_message("❌ Đạo hữu chưa có hồ sơ tu tiên!", ephemeral=True)

    # 2. Kiểm tra số dư theo loại tài nguyên đã chọn
    current_balance = u.get(resource_type, 0)
    label = "Linh Thạch 💎" if resource_type == "linh_thach" else "Tiên Thạch 🔮"
    
    if current_balance < amount:
        return await interaction.response.send_message(f"❌ Đạo hữu không đủ {label} (Hiện có: `{current_balance}`)", ephemeral=True)

    # 3. Khởi tạo giao diện xác nhận (Cần cập nhật Class ConfirmTransfer phía dưới)
    view = ConfirmTransfer(interaction.user, member, amount, resource_type, label)
    await interaction.response.send_message(
        f"📜 **XÁC NHẬN GIAO DỊCH**\n"
        f"Đạo hữu **{interaction.user.mention}** muốn chuyển **{amount} {label}** cho **{member.mention}**.\n"
        f"*(Nút bấm sẽ hết hạn sau 30 giây)*",
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
#BOSS
# --- 1. QUẢN LÝ TRẠNG THÁI ---
active_battles = globals().get('active_battles', set())

# --- 2. GIAO DIỆN CHIẾN ĐẤU (VIEW) ---
class BossInviteView(discord.ui.View):
    def __init__(self, target_id, initiator_id, ten_boss, win_rate, config, member_obj):
        super().__init__(timeout=60)
        self.ids = [str(initiator_id), str(target_id)]
        self.target_id = target_id
        self.ten_boss = ten_boss
        self.win_rate = win_rate
        self.config = config
        self.member_obj = member_obj 
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
            
            # --- LẤY DỮ LIỆU CẢ 2 NGƯỜI ĐỂ CHECK PET ---
            u1, u2 = await asyncio.gather(
                users_col.find_one({"_id": self.ids[0]}),
                users_col.find_one({"_id": self.ids[1]})
            )
            users_data = {self.ids[0]: u1, self.ids[1]: u2}

            if is_win:
                reward_lt_base = random.randint(*self.config['reward'])
                reward_exp = self.config.get('exp', 50)
                
                tien_thach_msg = ""
                # Logic Tiên Thạch cho Boss cuối
                if self.ten_boss == "Mục Dã Di" and random.random() < 0.20:
                    tien_thach_msg = "\n🔮 **CHÍ TÔN BẢO VẬT:** Cả hai nhận được **1 Tiên Thạch**!"

                # Cập nhật từng người để tính Buff riêng biệt
                for uid in self.ids:
                    user_info = users_data.get(uid)
                    lt_final = reward_lt_base
                    fox_msg = ""

                    # Check Buff Hồ Ly (🦊 +20%)
                    if user_info and user_info.get("pet") == "Hóa Hình Hồ Ly":
                        fox_cfg = globals().get("PET_CONFIG", {}).get("Hóa Hình Hồ Ly", {})
                        bonus = int(reward_lt_base * fox_cfg.get("lt_buff", 0.2))
                        lt_final += bonus
                        fox_msg = f" (🦊 +{bonus})"

                    # Build query update cho từng cá nhân
                    upd = {
                        "$inc": {"linh_thach": lt_final, "exp": reward_exp},
                        "$set": {"last_boss": today}
                    }
                    if tien_thach_msg:
                        upd["$inc"]["tien_thach"] = 1

                    await users_col.update_one({"_id": uid}, upd)
                    
                    # Check Level Up
                    member = interaction.guild.get_member(int(uid))
                    name = member.display_name if member else "Tu sĩ"
                    await check_level_up(uid, interaction.channel, f"{name}{fox_msg}")

                msg = f"🎉 **THÀNH CÔNG:** Tiêu diệt {self.ten_boss}!\n🎁 Thưởng cơ bản: `+{reward_exp}` EXP, `+{reward_lt_base}` 💎.{tien_thach_msg}"
                color = discord.Color.gold()
            else:
                # THẤT BẠI
                penalty = self.config['penalty']
                await users_col.update_many(
                    {"_id": {"$in": self.ids}}, 
                    {"$inc": {"exp": -penalty}, "$set": {"last_boss": today}}
                )
                for uid in self.ids: await check_level_down(uid)
                
                msg = f"💀 **BẠI TRẬN:** {self.ten_boss} quá mạnh, cả hai tổn thất `-{penalty:,}` EXP!"
                color = discord.Color.red()

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

    @discord.ui.button(label="❌ Từ Chối", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_id:
            return await interaction.response.send_message("❌ Lệnh này không phải của bạn!", ephemeral=True)
        await interaction.response.edit_message(content="❌ Lời mời bị khước từ.", view=None)
        active_battles.difference_update(self.ids)
        self.stop()

# --- 3. LỆNH BOSS CHÍNH ---
@bot.tree.command(name="boss", description="Thảo phạt Ma Thần (Tổ đội 2 người)")
@app_commands.describe(member="Đồng đội", ten_boss="Chọn Ma Thần")
@app_commands.choices(ten_boss=[app_commands.Choice(name=k, value=k) for k in BOSS_CONFIG.keys()])
async def boss_hunt(interaction: discord.Interaction, member: discord.Member, ten_boss: str):
    await interaction.response.defer()
    
    uid1, uid2 = str(interaction.user.id), str(member.id)
    
    # Check lỗi cơ bản
    if uid1 == uid2:
        return await interaction.followup.send("❌ Không thể tự mời chính mình!")
    if uid1 in active_battles or uid2 in active_battles:
        return await interaction.followup.send("❌ Một trong hai đạo hữu đang trong trạng thái giao tranh!")

    # Lấy dữ liệu 2 người
    u1, u2 = await asyncio.gather(
        users_col.find_one({"_id": uid1}), 
        users_col.find_one({"_id": uid2})
    )
    today = datetime.now().strftime("%Y-%m-%d")

    if not u1 or not u2: 
        return await interaction.followup.send("⚠️ Một trong hai tu sĩ chưa có hồ sơ tu tiên!")
    
    # Check lượt đánh
    if u1.get("last_boss") == today:
        return await interaction.followup.send(f"❌ **{interaction.user.display_name}** đã hết lượt thảo phạt hôm nay.")
    if u2.get("last_boss") == today:
        return await interaction.followup.send(f"❌ **{member.display_name}** đã hết lượt thảo phạt hôm nay.")

    # Đưa vào trạng thái bận
    active_battles.update([uid1, uid2])
    cfg = BOSS_CONFIG[ten_boss]
    
    # Tính Lực chiến & Tỷ lệ thắng
    p1 = await calc_power(uid1)
    p2 = await calc_power(uid2)
    p_total = p1 + p2
    
    boss_p = int((800 * cfg['multiplier']) + cfg['base'])
    win_rate = max(0.01, min(0.95, p_total / (p_total + boss_p)))

    # Tạo View và gửi lời mời
    view = BossInviteView(member.id, interaction.user.id, ten_boss, win_rate, cfg, member)
    view.message = await interaction.followup.send(
        f"⚔️ **{interaction.user.display_name}** mời **{member.mention}** cùng thảo phạt **{ten_boss}**!\n"
        f"👿 LC Boss: `{boss_p:,}` | 📈 Tỷ lệ thắng tổ đội: `{win_rate*100:.1f}%`", 
        view=view
    )

@bot.tree.command(name="thanthu", description="Thần thú thị uy chân ngôn (Chỉ dành cho người có linh thú)")
async def pet_show(interaction: discord.Interaction):
    # 1. Khởi động pháp trận (Defer)
    await interaction.response.defer()
    uid = str(interaction.user.id)
    
    # 2. Truy vấn dữ liệu tu sĩ
    u = await users_col.find_one({"_id": uid})
    pet_name = u.get("pet") if u else None

    # 3. Kiểm tra xem có Pet hợp lệ trong PET_CONFIG không
    # Nếu không có pet hoặc pet đó chưa được định nghĩa trong CONFIG
    if not pet_name or pet_name not in PET_CONFIG:
        embed_none = discord.Embed(
            title="⚠️ LINH THÚ CÁC THÔNG BÁO",
            description=(
                "Đạo hữu hiện tại đơn thương độc mã, bên mình không có linh thú hộ vệ.\n\n"
                "*Hãy nỗ lực tu luyện hoặc tìm kiếm cơ duyên để thu phục Thần Thú!*"
            ),
            color=discord.Color.light_gray()
        )
        return await interaction.followup.send(embed=embed_none)

    # 4. Lấy cấu hình trực tiếp từ PET_CONFIG
    cfg = PET_CONFIG[pet_name]
    
    # Lấy ngẫu nhiên 1 câu thoại
    random_quote = random.choice(cfg["quotes"])
    
    # 5. Tạo Embed hiển thị
    embed = discord.Embed(
        title=f"{cfg['icon']} CHÂN NGÔN THẦN THÚ: {pet_name}",
        description=f"**\"{random_quote}\"**",
        color=cfg["color"]
    )
    
    # Thêm thông tin người gọi lệnh cho uy tín
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
    embed.set_footer(text="✨ Thần thú hộ chủ - Uy trấn bát phương")
    
    # Gửi kết quả
    await interaction.followup.send(embed=embed)
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
@bot.tree.command(name="phongthanbang", description="Bảng phong thần: Vinh danh chủ nhân báu vật")
async def phong_than_bang(interaction: discord.Interaction):
    await interaction.response.defer()
    
    try:
        # Sử dụng query tối ưu hơn
        # Lưu ý: Đảm bảo đã chạy Bước 1 (Tạo Index) thì lệnh này mới nhanh
        cursor = users_col.find({
            "$or": [
                {"than_khi": {"$exists": True, "$ne": None}},
                {"thanh_giap": {"$exists": True, "$ne": None}},
                {"pet": {"$exists": True, "$ne": None}}
            ]
        })
        
        # Giới hạn lấy 50 người để tránh timeout
        users_list = await cursor.to_list(length=50)
        
        if not users_list:
            return await interaction.followup.send("🥀 Chưa có tu sĩ nào sở hữu báu vật.")

        leaderboard = []
        for u in users_list:
            tk = u.get("than_khi")
            tg = u.get("thanh_giap")
            pet = u.get("pet")
            
            details = []
            if tk: details.append(f"⚔️ `{tk}`")
            if tg: details.append(f"🛡️ `{tg}`")
            if pet: details.append(f"🐾 `{pet}`")
            
            if details:
                leaderboard.append({
                    "id": u["_id"],
                    "count": len(details),
                    "details": " | ".join(details)
                })

        # Sắp xếp
        leaderboard.sort(key=lambda x: x["count"], reverse=True)

        embed = discord.Embed(title="✨ PHONG THẦN BẢNG ✨", color=0xFFD700)
        top_str = ""
        
        # Chỉ hiển thị Top 15
        for i, entry in enumerate(leaderboard[:15]):
            try:
                # Dùng fetch_member nếu get_member (cache) thất bại, nhưng để tránh chậm thì dùng fallback
                member = interaction.guild.get_member(int(entry["id"]))
                name = member.display_name if member else f"Ẩn danh ({entry['id'][-4:]})"
            except:
                name = f"Tu sĩ ({entry['id'][-4:]})"

            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"**#{i+1}**"
            top_str += f"{medal} **{name}**\n╰ {entry['details']}\n\n"

        if not top_str: top_str = "Chưa có dữ liệu hiển thị."
        
        embed.description = top_str
        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Lỗi Phong Thần Bảng: {e}")
        await interaction.followup.send("⚠️ Lỗi hệ thống, vui lòng thử lại sau.")
@bot.tree.command(name="bicanh", description="Khám phá Bí Cảnh (Trợ chiến không tốn lượt, dính bẫy cùng chịu)")
@app_commands.describe(dong_doi="Mời đồng đội trợ chiến")
async def bicanh(interaction: discord.Interaction, dong_doi: discord.Member = None):
    uid = str(interaction.user.id)
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. Kiểm tra Người mời (Chủ phòng)
    u_data = await users_col.find_one({"_id": uid})
    if not u_data: 
        return await interaction.response.send_message("❌ Đạo hữu chưa có hồ sơ tu tiên!", ephemeral=True)
    
    u_bc = u_data.get("bicanh_daily", {"date": "", "count": 0, "trong_thuong": False})
    
    if u_bc.get("date") != today:
        u_bc = {"date": today, "count": 0, "trong_thuong": False}

    if u_bc.get("trong_thuong") is True:
        return await interaction.response.send_message("❌ Đạo hữu đang trọng thương do dính bẫy, cần tịnh dưỡng qua ngày mai!", ephemeral=True)
    if u_bc["count"] >= 3:
        return await interaction.response.send_message("❌ Đạo hữu đã hết lượt tự thám hiểm hôm nay!", ephemeral=True)

    # 2. Kiểm tra Đồng đội
    tid = str(dong_doi.id) if dong_doi else None
    if tid:
        if tid == uid: return await interaction.response.send_message("❌ Không thể tự mời mình!", ephemeral=True)
        t_data = await users_col.find_one({"_id": tid})
        if not t_data: return await interaction.response.send_message(f"❌ {dong_doi.display_name} chưa tu hành!", ephemeral=True)
        
        t_bc = t_data.get("bicanh_daily", {"date": "", "count": 0, "trong_thuong": False})
        if t_bc.get("date") != today:
            t_bc = {"date": today, "count": 0, "trong_thuong": False}

        if t_bc.get("trong_thuong") is True:
            return await interaction.response.send_message(f"❌ {dong_doi.display_name} đang trọng thương, không thể trợ chiến!", ephemeral=True)

    # --- VIEW CHỌN BÍ CẢNH ---
    class BiCanhSelectView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)

        @discord.ui.select(
            placeholder="Chọn Bí Cảnh để khởi hành...",
            options=[discord.SelectOption(label=v["name"], value=k) for k, v in BI_CANH_CONFIG.items()]
        )
        async def callback(self, i: discord.Interaction, select: discord.ui.Select):
            if str(i.user.id) != uid: 
                return await i.response.send_message("❌ Đây không phải pháp trận của đạo hữu!", ephemeral=True)
            
            choice = select.values[0]
            cfg = BI_CANH_CONFIG[choice]
            await i.response.defer()

            p1_pwr = await calc_power(uid)
            p2_pwr = await calc_power(tid) if tid else 0
            total_pwr = p1_pwr + p2_pwr

            roll = random.random()
            new_count = u_bc["count"] + 1
            msg, color = "", discord.Color.blue()

            # --- A. DÍNH BẪY ---
            if roll < cfg["trap_chance"]:
                penalty = cfg["trap_penalty"]
                await users_col.update_one(
                    {"_id": uid}, 
                    {"$inc": {"exp": -penalty}, "$set": {"bicanh_daily": {"date": today, "count": 3, "trong_thuong": True}}}
                )
                if tid:
                    await users_col.update_one(
                        {"_id": tid}, 
                        {"$set": {"bicanh_daily.date": today, "bicanh_daily.trong_thuong": True}}
                    )
                await check_level_down(uid)
                msg = f"💥 **ĐẠI NẠN:** Dính cạm bẫy tổn thất `{penalty}` EXP. \n💀 **HẬU QUẢ:** Cả hai bị trọng thương, không thể tiếp tục thám hiểm hôm nay!"
                color = discord.Color.red()

            # --- B. CHIẾN BOSS (Có Buff Hồ Ly) ---
            elif roll < (cfg["trap_chance"] + cfg["boss_chance"]):
                win_rate = min(total_pwr / (cfg["boss_power"] * 1.0), 0.9)
                if random.random() < win_rate:
                    # TÍNH TOÁN BUFF HỒ LY
                    fox_bonus = 0
                    if u_data.get("pet") == "Hóa Hình Hồ Ly":
                        fox_cfg = globals().get("PET_CONFIG", {}).get("Hóa Hình Hồ Ly", {})
                        fox_bonus = int(cfg["lt"] * fox_cfg.get("lt_buff", 0.2))

                    total_lt = cfg["lt"] + fox_bonus
                    drop_msg = ""
                    
                    if random.random() < cfg.get("tien_thach_chance", 0):
                        amt = cfg.get("tien_thach_amount", 1)
                        await users_col.update_one({"_id": uid}, {"$inc": {"tien_thach": amt}})
                        drop_msg = f"\n🔮 **CƠ DUYÊN:** Chủ phòng nhặt được `{amt}` Tiên Thạch!"

                    await users_col.update_one(
                        {"_id": uid}, 
                        {"$inc": {"exp": cfg["exp"], "linh_thach": total_lt}, "$set": {"bicanh_daily.count": new_count}}
                    )
                    await check_level_up(uid, i.channel, i.user.display_name)
                    
                    fox_info = f" (🦊 +{fox_bonus})" if fox_bonus > 0 else ""
                    msg = f"⚔️ **THẮNG BOSS:** Chủ phòng nhận `+{cfg['exp']}` EXP, `+{total_lt}` 💎{fox_info}.{drop_msg}"
                    color = discord.Color.green()
                else:
                    penalty = cfg["trap_penalty"] // 2
                    await users_col.update_one({"_id": uid}, {"$inc": {"exp": -penalty}, "$set": {"bicanh_daily.count": new_count}})
                    await check_level_down(uid)
                    msg = f"💀 **BẠI TRẬN:** Boss quá mạnh, chủ phòng tổn thất `-{penalty}` EXP!"
                    color = discord.Color.dark_red()

            # --- C. KHO BÁU / LANG THANG ---
            else:
                await users_col.update_one({"_id": uid}, {"$inc": {"exp": cfg["exp"]}, "$set": {"bicanh_daily.count": new_count}})
                msg = f"✨ **THÀNH CÔNG:** Khám phá bí cảnh nhận `+{cfg['exp']}` EXP."
                color = discord.Color.gold()

            await i.edit_original_response(content=None, embed=discord.Embed(title=f"🏔️ {cfg['name']}", description=msg, color=color), view=None)

    # --- VIEW XÁC NHẬN MỜI ĐỒNG ĐỘI ---
    class ConfirmView(discord.ui.View):
        def __init__(self, interaction: discord.Interaction):
            super().__init__(timeout=30)
            self.interaction = interaction

        @discord.ui.button(label="Đồng Ý", style=discord.ButtonStyle.green, emoji="⚔️")
        async def confirm(self, i: discord.Interaction, btn: discord.ui.Button):
            if str(i.user.id) != tid: return
            await i.response.edit_message(content=f"✅ **{dong_doi.display_name}** đã gia nhập pháp trận!", view=None)
            await self.interaction.edit_original_response(view=BiCanhSelectView())

        @discord.ui.button(label="Từ Chối", style=discord.ButtonStyle.red)
        async def cancel(self, i: discord.Interaction, btn: discord.ui.Button):
            if str(i.user.id) != tid: return
            await i.response.edit_message(content=f"❌ **{dong_doi.display_name}** đã từ chối trợ chiến.", view=None)

    # KHỞI CHẠY LỆNH
    if dong_doi:
        await interaction.response.send_message(content=f"📜 {interaction.user.mention} mời {dong_doi.mention} trợ chiến Bí Cảnh!\n*(Hỗ trợ không tốn lượt, dính bẫy dính họa chung)*", view=ConfirmView(interaction))
    else:
        await interaction.response.send_message(content="🏔️ Chọn Bí Cảnh thám hiểm:", view=BiCanhSelectView())
#full lệnh hái dược
@bot.tree.command(name="haiduoc", description="Khởi hành vào Linh Sơn hái thuốc")
async def haiduoc(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    user_data = await users_col.find_one({"_id": uid})
    
    if not user_data:
        return await interaction.response.send_message("❌ Đạo hữu chưa có hồ sơ tu tiên!", ephemeral=True)

    now = time.time()
    finish_time = user_data.get("haiduoc_time", 0)

    # Kiểm tra xem có đang đi hái thuốc dở dang không
    if finish_time > 0:
        if now < finish_time:
            remaining = int((finish_time - now) / 60)
            return await interaction.response.send_message(f"🧗 Đạo hữu đang trong rừng rồi, vui lòng đợi thêm **{remaining} phút** nữa mới có thể dùng `/thuhoach`!", ephemeral=True)
        else:
            return await interaction.response.send_message(f"🌿 Đạo hữu đã hái đầy gùi thuốc rồi! Hãy dùng lệnh `/thuhoach` để trở về nhận thưởng.", ephemeral=True)

    # Nếu chưa đi, bắt đầu đặt thời gian chờ (30 phút = 1800 giây)
    COOLDOWN = 3600 
    new_finish_time = now + COOLDOWN
    
    await users_col.update_one({"_id": uid}, {"$set": {"haiduoc_time": new_finish_time}})
    
    await interaction.response.send_message(
        f"🧗 **KHỞI HÀNH:** Đạo hữu đã đeo gùi tiến vào Linh Sơn.\n"
        f"Dự kiến thám hiểm mất **60 phút**. Sau thời gian này, hãy dùng lệnh `/thuhoach` để nhận linh thạch!"
    )
@bot.tree.command(name="thuhoach", description="Trở về từ Linh Sơn và bán thảo dược")
async def thuhoach(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    user_data = await users_col.find_one({"_id": uid})
    
    if not user_data:
        return await interaction.response.send_message("❌ Đạo hữu chưa có hồ sơ tu tiên!", ephemeral=True)

    now = time.time()
    finish_time = user_data.get("haiduoc_time", 0)

    # 1. Kiểm tra xem đã dùng lệnh /haiduoc chưa
    if finish_time == 0:
        return await interaction.response.send_message("❌ Đạo hữu hiện không có thuốc để thu hoạch. Hãy dùng `/haiduoc` trước!", ephemeral=True)

    # 2. Kiểm tra xem đã đủ thời gian chưa
    if now < finish_time:
        remaining = int((finish_time - now) / 60)
        return await interaction.response.send_message(f"⏳ Thuốc chưa chín hoặc gùi chưa đầy! Cần thêm khoảng **{remaining} phút** nữa.", ephemeral=True)

    # 3. Đủ thời gian -> Phát thưởng
    lt_reward = random.choices([1, 2], weights=[70, 30], k=1)[0]
    exp_reward = random.randint(0, 300)
    
    rare_msg = ""
    # 1% tỉ lệ rơi Tiên Thạch
    if random.random() < 0.01:
        await users_col.update_one({"_id": uid}, {"$inc": {"tien_thach": 1}})
        rare_msg = "\n🔮 **CƠ DUYÊN:** Đạo hữu nhặt được một viên **Tiên Thạch** ẩn dưới gốc linh chi!"

    # Cập nhật database: Cộng quà và reset haiduoc_time về 0
    await users_col.update_one(
        {"_id": uid}, 
        {
            "$inc": {"linh_thach": lt_reward, "exp": exp_reward},
            "$set": {"haiduoc_time": 0} 
        }
    )
    
    # Gọi hàm check lên cấp (nếu có)
    await check_level_up(uid, interaction.channel, interaction.user.display_name)
    
    await interaction.response.send_message(
        f"✅ **THU HOẠCH THÀNH CÔNG**\n"
        f"Đạo hữu đã trở về an toàn và bán thảo dược cho hiệu thuốc:\n"
        f"💎 `+{lt_reward}` Linh Thạch\n"
        f"✨ `+{exp_reward}` Kinh nghiệm{rare_msg}"
    )
@bot.tree.command(name="ducan", description="Đúc Ấn Đế: Tiến độ 1-7 tốn Linh Thạch, 8-10 tốn Tiên Thạch")
async def ducan(interaction: discord.Interaction):
    await interaction.response.defer()
    uid = str(interaction.user.id)
    # 1. Lấy dữ liệu người dùng
    u = await users_col.find_one({"_id": uid})
    if not u:
        return await interaction.followup.send("⚠️ Đạo hữu chưa có hồ sơ tu tiên!")
    current_progress = u.get("duc_an_progress", 0)
    # 2. Xác định loại phí dựa trên tiến độ hiện tại
    # Nếu tiến độ từ 0-6 (đang đúc lên bước 1-7): Tốn Linh Thạch
    # Nếu tiến độ từ 7-9 (đang đúc lên bước 8-10): Tốn Tiên Thạch
    if current_progress < 7:
        # Từ 0->1 đến 6->7: Tốn 15 Linh Thạch
        cost_type = "linh_thach"
        cost_value = 15
        cost_name = "Linh Thạch"
    elif current_progress == 7:
        # Từ 7 lên 8: Tốn 1 Tiên Thạch
        cost_type = "tien_thach"
        cost_value = 1
        cost_name = "Tiên Thạch"
    elif current_progress == 8:
        # Từ 8 lên 9: Tốn 2 Tiên Thạch
        cost_type = "tien_thach"
        cost_value = 2
        cost_name = "Tiên Thạch"
    else:
        # Từ 9 lên 10: Tốn 3 Tiên Thạch
        cost_type = "tien_thach"
        cost_value = 3
        cost_name = "Tiên Thạch"
    # 3. Kiểm tra tài sản tương ứng
    user_balance = u.get(cost_type, 0)
    if user_balance < cost_value:
        return await interaction.followup.send(f"⚠️ Không đủ tài nguyên! Để đạt tiến độ tiếp theo đạo hữu cần **{cost_value} {cost_name}**.")
    # 4. Xử lý tiến độ
    new_progress = current_progress + 1
    # Cập nhật Database: Trừ đúng loại tiền và tăng tiến độ
    await users_col.update_one(
        {"_id": uid}, 
        {
            "$inc": {cost_type: -cost_value}, 
            "$set": {"duc_an_progress": new_progress}
        }
    )

    # 5. Kiểm tra nếu đủ điểm nhận Ấn (Mốc 10)
    if new_progress >= 10:
        an_names = list(AN_DE_DATA.keys())
        an_weights = [info["weight"] for info in AN_DE_DATA.values()]
        received_an = random.choices(an_names, weights=an_weights)[0]
        an_info = AN_DE_DATA[received_an]

        await users_col.update_one(
            {"_id": uid},
            {"$set": {"duc_an_progress": 0, "an_de": received_an}}
        )

        embed = discord.Embed(
            title="🔨 ĐÚC ẤN THÀNH CÔNG!",
            description=f"Dùng **{cost_value} {cost_name}** cuối cùng làm vật dẫn, đạo hữu đã đúc thành công:\n\n{an_info['icon']} **{received_an}**",
            color=discord.Color.gold() if received_an == "Kỳ Lân Đế Ấn" else discord.Color.green()
        )
        embed.add_field(name="✨ Chỉ số cộng thêm", value=f"Sát thương: `+{an_info['atk']}`\nSinh mệnh: `+{an_info['hp']}`")
        
        if received_an == "Kỳ Lân Đế Ấn":
            try:
                await interaction.channel.send(f"🎊 **THÔNG BÁO:** Đạo hữu **{interaction.user.mention}** đã đúc thành công **{received_an}**!")
            except: pass

        return await interaction.followup.send(embed=embed)

    else:
        # 6. Hiển thị thanh tiến độ
        bar = "▰" * new_progress + "▱" * (10 - new_progress)
        # Gợi ý cho người chơi biết bước tiếp theo tốn gì
        next_step_info = ""
        if new_progress < 7:
            next_step_info = f"\n💰 Chi phí tiếp theo: **15 Linh Thạch**"
        elif new_progress == 7:
            next_step_info = "\n⚠️ **Cảnh báo:** Phôi ấn đã hình thành. Từ bậc này cần **1 Tiên Thạch** để đúc!"
        elif new_progress == 8:
            next_step_info = "\n💎 Chi phí tiếp theo: **2 Tiên Thạch**"
        elif new_progress == 9:
            next_step_info = "\n🔥 **Giai đoạn cuối:** Cần **3 Tiên Thạch** để hoàn tất Ấn Đế!"
        else:
            next_step_info = "" # Đã đạt mốc 10, chuẩn bị nhận ấn
        # ... (Phần trừ tiền và tăng progress bên trên giữ nguyên)

    # ... (Phần xác định cost_type và trừ tiền ở trên)

    if new_progress >= 10:
        # --- PHẦN KHI ĐÚC THÀNH CÔNG (10/10) ---
        an_names = list(AN_DE_DATA.keys())
        an_weights = [info["weight"] for info in AN_DE_DATA.values()]
        received_an = random.choices(an_names, weights=an_weights)[0]
        an_info = AN_DE_DATA[received_an]

        # Reset tiến độ và lưu Ấn mới
        await users_col.update_one(
            {"_id": uid},
            {"$set": {"duc_an_progress": 0, "an_de": received_an}}
        )

        embed = discord.Embed(
            title="🔨 ĐÚC ẤN THÀNH CÔNG!",
            description=f"Dùng **{cost_value} {cost_name}** cuối cùng làm vật dẫn, đạo hữu đã đúc thành công:\n\n{an_info['icon']} **{received_an}**",
            color=discord.Color.gold() if received_an == "Kỳ Lân Đế Ấn" else discord.Color.green()
        )
        embed.add_field(name="✨ Chỉ số cộng thêm", value=f"Sát thương: `+{an_info['atk']}`\nSinh mệnh: `+{an_info['hp']}`")
        
        # Lời bình đặc biệt cho Kỳ Lân Đế Ấn
        if received_an == "Kỳ Lân Đế Ấn":
            embed.add_field(name="📜 Lời bình", value="*Hào quang vạn dặm, khí vận nghịch thiên mới đúc thành công!*", inline=False)
            try:
                await interaction.channel.send(f"🎊 **THÔNG BÁO:** Đạo hữu **{interaction.user.mention}** đã đúc thành công **{received_an}**!")
            except: pass

        return await interaction.followup.send(embed=embed)

    else:
        # --- PHẦN KHI ĐANG TÍCH LŨY (Dưới 10 điểm) ---
        bar = "▰" * new_progress + "▱" * (10 - new_progress)
        
        # Xác định lời nhắc chi phí cho bước kế tiếp
        if new_progress < 7:
            next_step_info = f"\n💰 Chi phí tiếp theo: **15 Linh Thạch**"
        elif new_progress == 7:
            next_step_info = "\n⚠️ **Cảnh báo:** Phôi ấn đã hình thành. Từ bậc này cần **1 Tiên Thạch** để đúc!"
        elif new_progress == 8:
            next_step_info = "\n💎 Chi phí tiếp theo: **2 Tiên Thạch**"
        elif new_progress == 9:
            next_step_info = "\n🔥 **Giai đoạn cuối:** Cần **3 Tiên Thạch** để hoàn tất Ấn Đế!"
        else:
            next_step_info = ""

        embed = discord.Embed(
            title="🔨 ĐANG ĐÚC ẤN...",
            description=f"Đạo hữu tiêu tốn **{cost_value} {cost_name}**.\nTiến độ: **{new_progress}/10**{next_step_info}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Linh Năng Tích Tụ", value=f"`{bar}`")
        return await interaction.followup.send(embed=embed)

keep_alive()
token = os.getenv("DISCORD_TOKEN")
bot.run(token)


































































































































































































