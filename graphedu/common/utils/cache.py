"""缓存工具"""

from datetime import timedelta

# ========== 极短期（秒级） ==========
# 适用于：高频热数据、防重复提交、限流窗口等
OneSecond = timedelta(seconds=1)
FiveSeconds = timedelta(seconds=5)
ThirtySeconds = timedelta(seconds=30)

# ========== 短期（分钟级） ==========
# 适用于：实时数据、会话锁、验证码、热点查询等
OneMinute = timedelta(minutes=1)
FiveMinutes = timedelta(minutes=5)
FifteenMinutes = timedelta(minutes=15)
ThirtyMinutes = timedelta(minutes=30)

# ========== 中期（小时级） ==========
# 适用于：配置数据、字典数据、用户权限、菜单树等
OneHour = timedelta(hours=1)
SixHours = timedelta(hours=6)
TwelveHours = timedelta(hours=12)

# ========== 长期（天级） ==========
# 适用于：静态资源、用户信息、统计数据等
OneDay = timedelta(days=1)
ThreeDays = timedelta(days=3)
OneWeek = timedelta(days=7)
ThirtyDays = timedelta(days=30)

# ========== 永久 ==========
# 适用于：字典配置、静态枚举等几乎不变的数据
Forever = timedelta(days=365)
