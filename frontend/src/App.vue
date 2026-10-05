<template>
  <div style="max-width: 800px; margin: 30px auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 0 20px;">
    <h2 style="text-align: center; color: #333;">单片机 IoT 物联网控制台</h2>
    
    <!-- 实时数据卡片展示 -->
    <div style="display: flex; gap: 20px; margin: 25px 0;">
      <div style="flex: 1; padding: 20px; background: #e6f7ff; border: 1px solid #91d5ff; border-radius: 8px; text-align: center;">
        <div style="color: #0050b3; font-size: 16px;">实时温度</div>
        <div style="font-size: 36px; font-weight: bold; margin-top: 10px; color: #1890ff;">
          {{ latest.temperature }} ℃
        </div>
      </div>
      <div style="flex: 1; padding: 20px; background: #f6ffed; border: 1px solid #b7eb8f; border-radius: 8px; text-align: center;">
        <div style="color: #135200; font-size: 16px;">实时湿度</div>
        <div style="font-size: 36px; font-weight: bold; margin-top: 10px; color: #52c41a;">
          {{ latest.humidity }} %
        </div>
      </div>
    </div>

    <!-- 远程硬件控制 (MQTT 下发) -->
    <div style="padding: 20px; background: #fafafa; border: 1px solid #e8e8e8; border-radius: 8px; margin-bottom: 25px;">
      <h3 style="margin-top: 0;">硬件远程控制 (MQTT 下发)</h3>
      <button @click="sendControl(1)" style="padding: 10px 24px; margin-right: 15px; background: #1890ff; color: white; border: none; border-radius: 4px; font-size: 15px; cursor: pointer;">
        开灯 (LED ON)
      </button>
      <button @click="sendControl(0)" style="padding: 10px 24px; background: #ff4d4f; color: white; border: none; border-radius: 4px; font-size: 15px; cursor: pointer;">
        关灯 (LED OFF)
      </button>
      <span style="margin-left: 20px; color: #888; font-size: 14px;">上报时间: {{ latest.timestamp }}</span>
    </div>

    <!-- 历史趋势折线图 -->
    <div id="chart" style="width: 100%; height: 360px; background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding-top: 10px;"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

const latest = ref({ temperature: 0, humidity: 0, timestamp: '等待接收中...' })
let myChart = null

// 1. 获取最新一笔温湿度
const fetchLatest = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/sensor/latest')
    latest.value = res.data
  } catch (err) {
    console.error('获取实时数据失败', err)
  }
}

// 2. 获取数据库最近 10 笔历史数据并渲染折线图
const fetchHistory = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/sensor/history')
    const data = res.data
    const times = data.map(item => item.timestamp.split(' ')[1] || item.timestamp)
    const temps = data.map(item => item.temperature)

    myChart.setOption({
      title: { text: '最近温度变化趋势', left: 'center' },
      tooltip: { trigger: 'axis' },
      grid: { left: '5%', right: '5%', bottom: '10%', containLabel: true },
      xAxis: { type: 'category', data: times },
      yAxis: { type: 'value', name: '℃' },
      series: [{
        data: temps,
        type: 'line',
        smooth: true,
        color: '#1890ff',
        areaStyle: { color: 'rgba(24, 144, 255, 0.1)' }
      }]
    })
  } catch (err) {
    console.error('获取历史数据失败', err)
  }
}

// 3. 点击按钮下发指令给硬件
const sendControl = async (state) => {
  try {
    await axios.post('http://127.0.0.1:8000/api/device/led', { state })
    alert(state === 1 ? '开灯指令已下发！' : '关灯指令已下发！')
  } catch (err) {
    alert('控制指令下发失败，请确认后端 uvicorn 仍在运行')
  }
}

onMounted(() => {
  myChart = echarts.init(document.getElementById('chart'))
  fetchLatest()
  fetchHistory()
  
  // 每 3 秒自动轮询后端刷新一次数据
  setInterval(() => {
    fetchLatest()
    fetchHistory()
  }, 3000)
})
</script>