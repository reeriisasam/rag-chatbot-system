#!/usr/bin/env python3
"""
แก้ไขปัญหา logging format
"""

import os
from pathlib import Path

print("🔧 กำลังแก้ไขปัญหา logging...")

# ลบไฟล์ log เก่า
log_file = Path("logs/app.log")
if log_file.exists():
    try:
        os.remove(log_file)
        print(f"✓ ลบไฟล์ log เก่า: {log_file}")
    except Exception as e:
        print(f"⚠️  ไม่สามารถลบไฟล์: {e}")

# ทดสอบ logging ใหม่
print("\n📝 ทดสอบ logging...")

from loguru import logger

# ลบ handler เก่า
logger.remove()

# เพิ่ม handler ใหม่
logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
)

logger.add(
    lambda msg: print(msg, end=""),
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>\n"
)

# ทดสอบ
logger.info("✓ Logging ทำงานปกติแล้ว")
logger.warning("⚠️  นี่คือ warning")
logger.error("❌ นี่คือ error")

print("\n✅ แก้ไขเสร็จแล้ว!")
print("ลองรัน: python main_gui.py")