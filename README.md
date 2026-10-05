# ESP32-C3 全栈物联网环境监控与反向控制系统 · Full-Stack IoT System

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

### English Overview

A complete end-to-end IoT closed-loop system built on **ESP32-C3 (RISC-V)**. The hardware node collects ambient temperature and humidity data, formats it into JSON packets, and publishes them over Wi-Fi to an **Eclipse Mosquitto MQTT Broker**. A **Python FastAPI** backend consumes the telemetry stream, persists records into an embedded **SQLite** database, and provides RESTful APIs. The **Vue 3 + Vite + ECharts** frontend visualizes real-time sensor dynamics and dispatches remote reverse-control commands back to the hardware GPIOs, achieving a full-stack engineering loop across firmware, middleware, backend, and frontend.



## 系统架构

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
    API -->|HTTP GET /api/sensor| UI
    API -->|HTTP GET /api/sensor/history| CHART
    BTN -->|HTTP POST /api/control/led| API
    API -->|MQTT Publish| TOPIC_SUB
    TOPIC_SUB --> PORT
    PORT -->|MQTT Receive| FW
    FW --> ACT
