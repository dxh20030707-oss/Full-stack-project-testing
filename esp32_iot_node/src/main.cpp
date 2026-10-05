#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// 1. Wi-Fi 配置
const char* ssid = "9828";
const char* password = "12345678";

// 2. MQTT Broker 配置（电脑局域网 IPv4）
const char* mqtt_server = "192.168.157.223"; 
const int mqtt_port = 1883;

// ESP32-C3 SuperMini 等最小板的板载 LED 通常接在 GPIO 8（低电平点亮）
const int LED_PIN = 8; 

WiFiClient espClient;
PubSubClient client(espClient);

// 处理网页下发的控制指令
void callback(char* topic, byte* payload, unsigned int length) {
  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, payload, length);

  if (!error) {
    if (doc.containsKey("led")) {
      int state = doc["led"];
      if (state == 1) {
        digitalWrite(LED_PIN, LOW); // 低电平点亮板载 LED
        Serial.println("[指令响应] 收到开灯 -> 板载 LED 已点亮");
      } else {
        digitalWrite(LED_PIN, HIGH); // 高电平熄灭
        Serial.println("[指令响应] 收到关灯 -> 板载 LED 已熄灭");
      }
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("尝试连接 Mosquitto Broker (192.168.3.12)...");
    String clientId = "ESP32C3-Node-" + String(random(0xffff), HEX);
    if (client.connect(clientId.c_str())) {
      Serial.println(" 连接成功！");
      // 订阅 Web 端发送控制命令的主题
      client.subscribe("device/led/set");
    } else {
      Serial.print(" 失败, 错误代码 rc=");
      Serial.print(client.state());
      Serial.println("，2 秒后重试...");
      delay(2000);
    }
  }
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH); // 默认灭灯
  Serial.begin(115200);

  Serial.println("\n正在连接 WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi 已连接！");
  Serial.print("ESP32-C3 分配到的 IP: ");
  Serial.println(WiFi.localIP());

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

unsigned long lastMsg = 0;

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // 每 3 秒上报一次温湿度数据
  unsigned long now = millis();
  if (now - lastMsg > 3000) {
    lastMsg = now;

    // 模拟温湿度波动（后续可直接换成传感器真实读数）
    float temp = 26.0 + (random(-15, 15) / 10.0);
    float humi = 58.0 + (random(-25, 25) / 10.0);

    JsonDocument doc;
    doc["temp"] = temp;
    doc["humi"] = humi;

    char buffer[128];
    serializeJson(doc, buffer);

    Serial.print("[数据上报] 主题 sensor/data -> ");
    Serial.println(buffer);

    client.publish("sensor/data", buffer);
  }
}