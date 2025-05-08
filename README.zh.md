# 🌡️ 海康威视红外双光谱摄像头温度提取工具（ISAPI，无需SDK）

本项目用于通过海康威视摄像头的 **ISAPI 接口**，实现无需 SDK 的红外图像 + 温度矩阵提取与展示。  
支持解析 multipart 数据流，提取红外图像、可见光图像和摄氏度温度矩阵，可视化并标注最热点。

---

## ✨ 特性

- 🎯 **无需 SDK**：纯 Python 请求 + 解析，无 C 库依赖
- 📷 提取红外图像 / 可见光图像（JPEG 编码）
- 🌡️ 解析温度矩阵（int16 或 float32）
- 🎨 支持温度伪彩色图与最热点标注
- 🧱 基于 `streaming_multipart.py` 进行流式解析（来自 [rckclmbr](https://github.com/rckclmbr/streaming_multipart)）

---

## 🔗 示例接口（ISAPI）

摄像头接口形如：

```http
GET /ISAPI/Thermal/channels/2/thermometry/jpegPicWithAppendData?format=json

你只需：

url = f'{URL}/ISAPI/Thermal/channels/2/thermometry/jpegPicWithAppendData?format=json'
session = requests.Session()
session.auth = HTTPDigestAuth(USR, PWD)
response = session.get(url, stream=True)

摄像头返回的是 multipart 数据流，结构如下：
--boundary
Content-Type: application/json      --> 图像元信息（分辨率、长度等）
--boundary
Content-Type: image/jpeg            --> 红外图像
--boundary
Content-Type: application/octet-stream --> 温度矩阵（二进制）
--boundary
Content-Type: image/jpeg            --> 可见光图像

安装依赖：
pip install requests numpy opencv-python matplotlib
