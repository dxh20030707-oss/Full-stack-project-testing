# 🌐 ESP32-C3 全栈物联网环境监控与反向控制系统 · Full-Stack IoT System

**一个打通「ESP32-C3 硬件传感驱动 + Mosquitto 消息中间件 + FastAPI 异步后端 + SQLite 数据持久化 + Vue 3 实时大屏交互」的端到端物联网全链路闭环项目。**

![MCU](https://img.shields.io/badge/MCU-ESP32--C3%20(RISC--V)-red)
![Framework](https://img.shields.io/badge/Framework-Arduino%20%7C%20PlatformIO-orange)
![Protocol](https://img.shields.io/badge/Protocol-MQTT%20v3.1.1%20%7C%20RESTful%20API-blue)
![Backend](https://img.shields.io/badge/Backend-Python%20%7C%20FastAPI-green)
![Frontend](https://img.shields.io/badge/Frontend-Vue%203%20%7C%20Vite%20%7C%20ECharts-42b883)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 📌 30 秒速览

| 维度 | 说明 |
| :--- | :--- |
| **做了什么** | 搭建了一套从物理感知到云端监控的完整物联网闭环：ESP32-C3 节点通过 Wi-Fi 将温湿度上报至 Mosquitto Broker，FastAPI 服务端自动消费并落库 SQLite，Vue 3 网页看板实时渲染波动曲线，并支持反向远程控制板载 LED |
| **技术亮点 1** | **端到端协议解耦**：采用轻量级 MQTT 发布/订阅模型，下位机遥测（`sensor/data`）与上位机控制（`device/led/set`）双向完全异步解耦，单节点故障不影响全局服务 |
| **技术亮点 2** | **异步高并发后端中枢**：基于 FastAPI 的事件驱动生命周期（Lifespan）管理后台 MQTT 监听线程与 REST API，实现“数据即来、即入库、即响应” |
| **技术亮点 3** | **响应式数据可视化**：前端利用 Vue 3 Composition API 与 ECharts 封装动态曲线引擎，实现传感数据平滑右移动画与毫秒级反向控灯反馈 |
| **技术亮点 4** | **工业级局域网穿透调试方案**：总结并攻克了 Windows 端口抢占（PID 冲突）、Defender 公用网络防火墙阻断、路由器 AP 隔离等多项网络实战难题 |
| **代码构成** | 固件层（C/C++ PlatformIO）+ 服务端（Python FastAPI + Paho-MQTT）+ 网页端（Vue 3 + Vite） |
| **角色** | 嵌入式固件开发、网络通信架构设计、FastAPI 后端开发、Vue 3 前端大屏构建、系统联调与文档编写 |

---

## 🏛️ 系统架构

```mermaid
flowchart TD
    subgraph NODE["底层硬件节点 (ESP32-C3 SuperMini)"]
        SENS["温湿度传感采集<br/>3000ms 周期采样"]
        ACT["板载 LED 驱动<br/>GPIO 8 (低电平触发)"]
        FW["PlatformIO 固件引擎<br/>PubSubClient + ArduinoJson"]
    end

    subgraph BROKER["消息代理中间件 (Eclipse Mosquitto)"]
        PORT["监听端口 1883<br/>绑定 0.0.0.0"]
        TOPIC_PUB["上报主题: sensor/data"]
        TOPIC_SUB["控制主题: device/led/set"]
    end

    subgraph BACKEND["后端服务层 (Python FastAPI)"]
        PAHO["Paho-MQTT 后台监听线程"]
        API["RESTful API 引擎<br/>Uvicorn ASGI"]
        DB[(本地 SQLite 数据库<br/>iot.db)]
    end

    subgraph FRONTEND["前端展示层 (Vue 3 + Vite)"]
        UI["实时卡片展示"]
        CHART["ECharts 动态折线图"]
        BTN["远程开灯 / 关灯按钮"]
    end

    SENS --> FW
    FW -->|MQTT Publish| TOPIC_PUB
    TOPIC_PUB --> PORT
    PORT -->|MQTT Ingest| PAHO
    PAHO --> DB
    DB --> API
    API -->|HTTP GET /api/sensor/latest| UI
    API -->|HTTP GET /api/sensor/history| CHART
    BTN -->|HTTP POST /api/control/led| API
    API -->|MQTT Publish| TOPIC_SUB
    TOPIC_SUB --> PORT
    PORT -->|MQTT Receive| FW
    FW --> ACT
```

---

## 🎯 核心功能与模块职责

### 1. 固件感知与驱动层 (`esp32_iot_node/`)
* **网络自愈连接**：开机自动连接 Wi-Fi，内置网络断线自动轮询与 MQTT 重连保护状态机。
* **数据序列化**：通过 `ArduinoJson` 动态封装标准 JSON 报文并发布至 `sensor/data` 主题。
* **双向指令监听**：订阅 `device/led/set`，接收来自云端的控制包，执行反向 GPIO 电平翻转。

### 2. 消息代理中间件 (`Mosquitto`)
* **局域网解耦**：采用 MQTT 3.1.1 协议，作为连接异构系统（微控制器与 Web 服务）的核心管道。
* **无状态路由**：实现数据生产者（ESP32）与数据消费者（FastAPI）在时序与物理网络上的彻底解耦。

### 3. 后端服务与持久层 (`main.py`)
* **异步生命周期托管**：在 FastAPI `lifespan` 中无缝运行 Paho-MQTT 守护线程，避免阻塞主 Web 循环。
* **持久化落盘**：接收温湿度报文并自动追加写入 `iot.db` 关系型表，支持按时间戳倒序索引。
* **双向路由分发**：
  * `GET /api/sensor/latest`：获取最新实时遥测指标。
  * `GET /api/sensor/history`：按时间序列获取最近历史数据列表。
  * `POST /api/control/led`：接受 Web 请求并转发 MQTT 硬件控制指令。

### 4. 前端交互大屏 (`frontend/`)
* **数据动态渲染**：每 3 秒自动轮询后端接口，实现温湿度动态跳变与 ECharts 曲线无缝平滑推移动画。
* **硬件反向联动**：提供高反馈的开灯/关灯交互面板，操作延迟通常在 100ms 以内。

---

## 📡 通信协议规范 (Protocol Specifications)

### 1. 遥测数据上报 (Telemetry Uplink)
* **Topic**: `sensor/data`
* **协议**: MQTT QoS 0
* **Payload (JSON 格式)**:
```json
{
  "temp": 25.8,
  "humi": 57.0
}
```

### 2. 硬件控制下发 (Command Downlink)
* **Topic**: `device/led/set`
* **协议**: MQTT QoS 0
* **Payload (JSON 格式)**:
```json
{
  "led": 1
}
```
*(说明: `1` 为开灯/GPIO 8 输出低电平，`0` 为关灯/GPIO 8 输出高电平)*

---

## 🛠️ 技术难点与解决方案

| # | 踩坑场景 | 根因剖析 | 解决方案 | 实测效果 |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **单片机连接 MQTT 报 `rc=-2`** | Mosquitto 默认仅监听本地回环 `127.0.0.1`，拒绝一切局域网外部 IP 访问 | 编写自定义配置文件添加 `listener 1883 0.0.0.0` 及 `allow_anonymous true` | 局域网各节点可正常握手建立连接 |
| **2** | **1883 端口冲突与多实例竞争** | 系统后台自启的 Mosquitto Windows 服务（PID 31336）占用回环端口，导致前台带配置的新进程（PID 29000）失效 | 使用 `services.msc` 将自启服务改为手动停止，使用 `taskkill /F /PID` 清空残留进程，统一从前台带参数启动 | 端口唯一绑定，多端报文分发恢复正常 |
| **3** | **Windows 防火墙丢包** | Windows 将热点及部分 Wi-Fi 归类为“公用网络”，安全策略丢弃所有未经放行的外部入站 TCP 握手包 | 将当前 Wi-Fi 网络配置由“公用”切换为“专用网络”，并在 Windows Defender 高级安全中显式放行 TCP 1883 入站 | 单片机与宿主机网络握手耗时从超时转为即时通过 |
| **4** | **烧录串口提示 `PermissionError(13)`** | Windows 下串口资源独占，VS Code 打开的串口监视器进程未释放句柄 | 在执行 PlatformIO Upload 前主动注销监视器终端，并在固件中加入软重启去抖保护 | 彻底根除固件烧录时的端口冲突死锁 |

---

## 🔌 硬件物料与引脚矩阵

| 硬件部件 | 型号 / 规格 | 引脚 / 协议 | 说明 |
| :--- | :--- | :--- | :--- |
| **主控板** | ESP32-C3 SuperMini / DevKit | 单核 RISC-V @160MHz | 板载 2.4GHz Wi-Fi + BLE 5.0 |
| **执行器** | 板载贴片蓝色 LED | GPIO 8 | 低电平有效（Sink Current 驱动） |
| **烧录通信** | Type-C 数据线 | USB CDC / UART | 固件烧写及 115200 波特率日志输出 |
| **运行环境** | Windows 11 PC | 本地网卡 / 手机热点 | 作为 Broker、后端与前端的服务承载端 |

---

## ⚡ 快速开始 (Quick Start)

### 1. 启动 MQTT Broker (Mosquitto)
在 Mosquitto 目录下新建或确认配置文件 `mosquitto.conf`：
```text
listener 1883 0.0.0.0
allow_anonymous true
```
在 Mosquitto 所在目录的 CMD 窗口中运行（保持窗口开启）：
```cmd
mosquitto -c mosquitto.conf -v
```

### 2. 运行 Python 后端服务
在工程根目录安装依赖并启动应用：
```bash
pip install fastapi uvicorn paho-mqtt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 运行前端大屏
进入 `frontend` 目录安装依赖并开启热重载服务器：
```bash
cd frontend
npm install
npm run dev
```
启动成功后，浏览器访问 `http://localhost:5173`。

### 4. 烧录单片机固件
1. 用 VS Code 打开 `esp32_iot_node` 工程。
2. 打开 `src/main.cpp`，修改 Wi-Fi 账密及电脑局域网 IP（`ipconfig` 获取）：
```cpp
const char* ssid = "你的WiFi名称";
const char* password = "你的WiFi密码";
const char* mqtt_server = "192.168.xxx.xxx";
```
3. 编译并烧录固件：
```bash
pio run --target upload
pio device monitor
```

---

## 📁 目录结构

```text
Full-stack-project/
├── esp32_iot_node/              # ESP32-C3 嵌入式工程 (PlatformIO)
│   ├── src/
│   │   └── main.cpp             # 固件源码 (Wi-Fi/MQTT 连接、数据上报、LED 响应)
│   └── platformio.ini           # 板型配置与依赖库管理
├── frontend/                    # Vue 3 前端工程
│   ├── src/
│   │   ├── App.vue              # 主页面看板 (数据卡片、ECharts 走势图、控制按钮)
│   │   └── main.js
│   ├── package.json             # 前端依赖配置
│   └── vite.config.js
├── main.py                      # FastAPI 后端服务 (MQTT 客户端 + REST API + 数据库管理)
├── iot.db                       # SQLite 数据库文件 (自动创建并持久化传感记录)
└── README.md                    # 本项目技术说明文档
```

---

## 🗺️ 路线图 (Roadmap)

- [x] 完成 ESP32-C3 到 Mosquitto 的 MQTT 遥测数据上报
- [x] 完成 FastAPI 后端数据落库与 RESTful 查询 API
- [x] 完成 Vue 3 前端动态折线图与双向反向开关控制
- [ ] 接入实体 DHT11 / SHT30 真实温湿度传感器驱动
- [ ] 引入 WebSocket 协议替代 HTTP 轮询，实现硬件状态全双工毫秒级推送
- [ ] 增加边缘计算离线策略：单片机端增加温湿度超标本地蜂鸣器警报

---

## 📄 许可证

本项目基于 [MIT](LICENSE) 许可证开源。
