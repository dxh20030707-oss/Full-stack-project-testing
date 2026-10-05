import json
import sqlite3
import threading
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import paho.mqtt.client as mqtt

# ================= 1. 初始化 SQLite 数据库 =================
DB_FILE = "iot.db"

def init_db():    # 初始化数据库函数，用于创建数据库表结构
    conn = sqlite3.connect(DB_FILE)  # 连接到SQLite数据库文件
    cursor = conn.cursor()  # 创建游标对象，用于执行SQL语句
    # 创建历史传感器数据表，包含id、时间戳、温度和湿度字段
    cursor.execute("""  # 执行SQL语句创建表
        CREATE TABLE IF NOT EXISTS sensor_logs (  # 如果表不存在则创建sensor_logs表
            id INTEGER PRIMARY KEY AUTOINCREMENT,  # 自增主键
            timestamp TEXT,  # 时间戳，文本类型
            temperature REAL,  # 温度值，浮点数类型
            humidity REAL  # 湿度值，浮点数类型
        )
    """)
    conn.commit()  # 提交事务，确保表被创建
    conn.close()  # 关闭数据库连接

init_db()

# ================= 2. MQTT 客户端与数据处理 =================
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
TOPIC_SENSOR = "sensor/data"      # 单片机上报主题
TOPIC_CONTROL = "device/led/set"   # 网页控制指令下发主题

latest_data = {"temperature": 0.0, "humidity": 0.0, "timestamp": "无数据"}

def on_connect(client, userdata, flags, rc):
    print(f"[*] 后端成功连接到 Mosquitto Broker! 返回码: {rc}")
    # 连接成功后，自动订阅单片机的数据主题
    client.subscribe(TOPIC_SENSOR)

def on_message(client, userdata, msg):
    global latest_data 
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        temp = payload.get("temp", 0.0)
        humi = payload.get("humi", 0.0)
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        latest_data = {
            "temperature": temp,
            "humidity": humi,
            "timestamp": time_str
        }
        print(f"[收到硬件数据] 温度: {temp}℃ | 湿度: {humi}% | 时间: {time_str}")

        # 存入 SQLite 数据库
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sensor_logs (timestamp, temperature, humidity) VALUES (?, ?, ?)",
            (time_str, temp, humi)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[解析错误] 消息格式非合法 JSON: {e}")

# 创建 MQTT 客户端实例并保持后台运行
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# 在独立后台线程中运行 MQTT 消息循环
threading.Thread(target=mqtt_client.loop_forever, daemon=True).start()

# ================= 3. FastAPI Web 接口服务 =================
app = FastAPI(title="IoT 数据与控制中台")

# 允许前端跨域访问 (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 接口 1: 获取最新的一笔温湿度数据（前端卡片轮询）
@app.get("/api/sensor/latest")
def get_latest_sensor():
    return latest_data

# 接口 2: 获取最近 10 条历史数据（前端折线图展示）
@app.get("/api/sensor/history")
def get_sensor_history():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, temperature, humidity FROM sensor_logs ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    
    # 转换为按时间先后顺序的数组
    history = [
        {"timestamp": r[0], "temperature": r[1], "humidity": r[2]}
        for r in reversed(rows)
    ]
    return history

# 接口 3: 前端点击网页按钮，下发控制指令
class ControlCommand(BaseModel):
    state: int  # 1 为开灯，0 为关灯

@app.post("/api/device/led")
def control_led(cmd: ControlCommand):
    payload = json.dumps({"led": cmd.state})
    mqtt_client.publish(TOPIC_CONTROL, payload)
    print(f"[指令下发] 向硬件发送控制命令: {payload}")
    return {"status": "success", "sent": payload}