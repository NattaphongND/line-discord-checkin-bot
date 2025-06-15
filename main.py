# ✅ ตัวอย่างโค้ด Discord Bot + Google Sheets + LINE Messaging API (Push Message)
# ✅ พร้อมใช้งานบนเครื่อง หรือ Replit โดยไม่ใช้ micropip


import os
import threading
import datetime

import discord
import gspread
import requests
import pytz
from flask import Flask, jsonify
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials


# 🔹 ตั้งค่า ENV (ต้องกำหนด ENV บน Replit หรือใช้ .env บนเครื่องจริง)
DISCORD_TOKEN = "MTM4MzQwMzIxNTgxNDUyOTAzNA.GEvOAc.LobX6gu-l-X0uMlBM2bJ_Im5OX0GWbfNhPW0rg"
LINE_TOKEN = "8JyepaNlwFyJg1fx3HV/Doo0CD1MBHsI5hPIVX6ubchSIsjd0vrGJ/DLNX+h6uuoPTyUMhMn+txyELjOqSjjRh1puS+Ec00X2lvUnZwE4Yb9I1XYk4m5ABA5p9poXO2vWBYSGaMOE4cccICvH61GhQdB04t89/1O/w1cDnyilFU="
LINE_TO = "C57be23d1e8fe30f246d2322fde92f6c9"  # groupId หรือ userId ที่จะส่งข้อความ LINE


# ตรวจสอบว่าถูกตั้งค่าแล้วหรือไม่
if not DISCORD_TOKEN:
    raise EnvironmentError('❌ Environment variable DISCORD_TOKEN is missing')
if not LINE_TOKEN:
    raise EnvironmentError('❌ Environment variable LINE_TOKEN is missing')
if not LINE_TO:
    raise EnvironmentError('❌ Environment variable LINE_TO is missing')

# 🔹 ตั้งค่า Google Sheets API
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]
creds  = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
sheet  = client.open('checkin_log').sheet1

# 🔹 ฟังก์ชันส่งข้อความ LINE (Push Message)
def push_line_message(event_type: str, username: str, timestamp: str):
    # ไอคอนตาม event
    icon  = '📥' if event_type == 'เข้างาน' else '📤'
    title = 'แจ้งเตือนเข้า-ออกงาน 👥'

    # แปลงวันที่ให้เป็นรูปแบบ วัน/เดือน/ปี เวลาไทย
    dt_naive = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    dt_thai  = pytz.timezone('Asia/Bangkok').localize(dt_naive)
    formatted = dt_thai.strftime('%d/%m/%Y %H:%M:%S')

    # ข้อความส่งไป LINE
    text = (
        f"{title}\n"
        f"━━━━━━━━━━━━━━\n"
        f"{icon} {username} {event_type}\n"
        f"🕒 เวลา: {formatted}\n"
        f"━━━━━━━━━━━━━━\n"
        f"📌 ระบบบันทึกอัตโนมัติ"
    )

    url = 'https://api.line.me/v2/bot/message/push'
    headers = {'Authorization': f'Bearer {LINE_TOKEN}', 'Content-Type': 'application/json'}
    payload = {'to': LINE_TO, 'messages': [{'type': 'text', 'text': text}]}
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        print('❌ LINE Error:', resp.status_code, resp.text)

# 🔹 สร้างเว็บเซิร์ฟเวอร์ (Flask) สำหรับ UptimeRobot
app = Flask(__name__)

# รองรับ GET และ HEAD ทั้ง root และทุก path
@app.route('/', methods=['GET', 'HEAD'])
def home():
    return jsonify({'status': 'Bot is alive'}), 200

@app.route('/<path:path>', methods=['GET', 'HEAD'])
def fallback(path):
    return jsonify({'status': 'Bot is alive'}), 200

# จับทุก 404 แล้วตอบว่า Bot still alive
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'status': 'Bot is alive'}), 200

# รัน Flask ใน thread แยกเพื่อไม่บล็อกบอท
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()

# 🔹 ตั้งค่า Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot     = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot online: {bot.user.name}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    now       = datetime.datetime.now(pytz.timezone('Asia/Bangkok'))
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    content   = message.content.strip().lower()

    if content == 'เข้างาน':
        sheet.append_row([message.author.name, 'เข้างาน', timestamp])
        await message.channel.send(f"{message.author.mention} ✅ เข้างานบันทึกแล้ว")
        push_line_message('เข้างาน', message.author.name, timestamp)

    elif content == 'ออกงาน':
        sheet.append_row([message.author.name, 'ออกงาน', timestamp])
        await message.channel.send(f"{message.author.mention} ✅ ออกงานบันทึกแล้ว")
        push_line_message('ออกงาน', message.author.name, timestamp)

    await bot.process_commands(message)

# 🔹 เริ่มรันบอท
bot.run(DISCORD_TOKEN)

