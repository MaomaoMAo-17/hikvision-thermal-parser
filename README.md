# hikvision-thermal-parser
Lightweight thermal camera parser via ISAPI, no SDK needed.

# 🌡️ Hikvision Thermal Camera Temperature Extraction Tool (ISAPI, No SDK Required)

This project provides a lightweight Python-based solution to extract **thermal images** and **temperature matrices** from Hikvision dual-spectrum thermal cameras using the **ISAPI interface** — no need for any C-based SDK.

It supports parsing multipart HTTP streams to retrieve thermal and visible-light JPEG images and Celsius temperature matrices, along with pseudocolor visualization and hotspot annotation.

---

## ✨ Features

- 🎯 **No SDK Required**: Pure Python requests + stream parsing, no compiled libraries
- 📷 Extract thermal and visible-light images (JPEG format)
- 🌡️ Decode temperature matrices (int16 or float32 format)
- 🎨 Visualize with pseudocolor map and max-temperature marker
- 🧱 Stream-based `multipart/form-data` parsing via [`streaming_multipart.py`](https://github.com/rckclmbr/streaming_multipart)

---

## 🔗 Example Interface (ISAPI)

Typical API endpoint:

```http
GET /ISAPI/Thermal/channels/2/thermometry/jpegPicWithAppendData?format=json
```

Basic usage:

```python
url = f'{URL}/ISAPI/Thermal/channels/2/thermometry/jpegPicWithAppendData?format=json'
session = requests.Session()
session.auth = HTTPDigestAuth(USR, PWD)
response = session.get(url, stream=True)
```


The response is a multipart data stream with the following structure:

```
--boundary
Content-Type: application/json       --> Metadata (image size, length, etc.)
--boundary
Content-Type: image/jpeg             --> Thermal image
--boundary
Content-Type: application/octet-stream --> Raw temperature matrix (binary)
--boundary
Content-Type: image/jpeg             --> Visible-light image
```

Dependencies

```
pip install requests numpy opencv-python matplotlib
```
