# -*- coding: utf-8 -*-
import requests
import struct
import numpy as np
import matplotlib.pyplot as plt
import cv2
import json
from requests.auth import HTTPDigestAuth
from io import BufferedReader
from streaming_multipart import MultipartReader
import re
import io
from requests import Response
import base64

BOUNDARY = 'boundary'

def parse_thermal_response(response: Response):
    """
    Parse ISAPI multipart response to extract thermal image, visible image, and temperature matrix

    Args:
        response: Response object from requests.get(..., stream=True)

    Returns:
        thermal_img (bytes): Thermal JPEG image
        visible_img (bytes): Visible-light JPEG image
        temp_matrix (np.ndarray): Temperature matrix in Celsius
        width, height: Size of the temperature matrix
    """
    # Extract boundary string
    content_type = response.headers.get("Content-Type", "")
    match = re.search(r'boundary=(.*)', content_type)
    if not match:
        raise ValueError("Boundary not found in Content-Type header")
    boundary = match.group(1)

    # Read full HTTP body
    raw_data = response.raw.read()

    # Optional: save raw multipart content for debugging
    with open("raw_multipart_dump.http", "wb") as f:
        f.write(raw_data)

    # Construct stream-based multipart parser
    stream = BufferedReader(io.BytesIO(raw_data))
    reader = MultipartReader(stream, boundary)

    # First part: JSON metadata
    json_part = reader.next_part()
    metadata = json.loads(json_part.read())
    meta = metadata['JpegPictureWithAppendData']

    width = meta['jpegPicWidth']
    height = meta['jpegPicHeight']
    jpeg_len = meta['jpegPicLen']
    temp_len = meta['temperatureDataLength']
    p2p_len = meta['p2pDataLen']

    # 16-bit matrix requires scaling and offset
    if temp_len == 2:
        scale = float(meta['scale'])
        offset = float(meta['offset'])
    else:
        scale = offset = None

    # Second part: thermal JPEG
    jpeg_part = reader.next_part()
    thermal_img = jpeg_part.read(jpeg_len)

    # Third part: temperature binary data
    temp_part = reader.next_part()
    temp_data = b""
    while len(temp_data) < p2p_len:
        chunk = temp_part.read(p2p_len - len(temp_data))
        if not chunk:
            break
        temp_data += chunk

    # Convert to Celsius matrix
    if temp_len == 2:
        # int16 + scale + offset + Kelvin to Celsius
        temp_raw = np.frombuffer(temp_data, dtype=np.int16).reshape((height, width))
        temp_matrix = temp_raw.astype(np.float32) / scale + offset - 273.15
    else:
        # float32, already in Celsius
        temp_matrix = np.frombuffer(temp_data, dtype=np.float32).reshape((height, width))

    # Fourth part: visible-light JPEG
    visible_part = reader.next_part()
    visible_img = visible_part.read()

    return thermal_img, visible_img, temp_matrix, width, height

def extract_global_thermal(USR, PWD, URL):
    """
    Get full-frame thermal/visible images and global temperature data

    Args:
        USR, PWD: Camera login credentials
        URL: Camera base address (e.g. http://192.168.1.122)

    Returns:
        thermal_b64: Base64 of thermal image
        visible_b64: Base64 of visible image
        global_temp: [max_temp, x, y, min_temp, x, y, mean_temp]
        temp_matrix: Celsius temperature matrix
    """
    url = f'{URL}/ISAPI/Thermal/channels/2/thermometry/jpegPicWithAppendData?format=json'
    session = requests.Session()
    session.auth = HTTPDigestAuth(USR, PWD)
    response = session.get(url, stream=True)

    thermal_img, visible_img, temp_matrix, temp_width, temp_height = parse_thermal_response(response)

    # Encode images to base64
    thermal_b64 = base64.b64encode(thermal_img).decode('utf-8')
    visible_b64 = base64.b64encode(visible_img).decode('utf-8')

    # Temperature statistics
    max_temp = temp_matrix.max()
    min_temp = temp_matrix.min()
    mean_temp = temp_matrix.mean()

    max_pos = np.unravel_index(np.argmax(temp_matrix), temp_matrix.shape)
    min_pos = np.unravel_index(np.argmin(temp_matrix), temp_matrix.shape)

    global_temp = [max_temp, max_pos[1], max_pos[0], min_temp, min_pos[1], min_pos[0], mean_temp]

    return thermal_b64, visible_b64, global_temp, temp_matrix

def extract_region_thermal(USR, PWD, URL, region_list):
    """
    Get temperature data in specified regions

    Args:
        region_list: [(x, y, w, h), ...] format

    Returns:
        Base64-encoded images and region-wise temperature stats
    """
    url = f'{URL}/ISAPI/Thermal/channels/2/thermometry/jpegPicWithAppendData?format=json'
    session = requests.Session()
    session.auth = HTTPDigestAuth(USR, PWD)
    response = session.get(url, stream=True)

    thermal_img, visible_img, temp_matrix, temp_width, temp_height = parse_thermal_response(response)

    thermal_b64 = base64.b64encode(thermal_img).decode('utf-8')
    visible_b64 = base64.b64encode(visible_img).decode('utf-8')

    region_temp_list = []

    for region in region_list:
        region_x1, region_y1, region_w, region_h = region
        if region_x1 >= temp_width or region_y1 >= temp_height:
            continue

        region_x2 = min(region_x1 + region_w, temp_width)
        region_y2 = min(region_y1 + region_h, temp_height)

        temp_region = temp_matrix[region_y1:region_y2, region_x1:region_x2]

        max_temp = temp_region.max()
        min_temp = temp_region.min()
        mean_temp = temp_region.mean()

        max_pos = np.unravel_index(np.argmax(temp_region), temp_region.shape)
        min_pos = np.unravel_index(np.argmin(temp_region), temp_region.shape)

        temp_result = [max_temp, max_pos[1], max_pos[0], min_temp, min_pos[1], min_pos[0], mean_temp]
        region_temp_list.append(temp_result)

    return thermal_b64, visible_b64, region_temp_list

def main():
    USR = 'admin'
    PWD = 'yourpassword'
    URL = 'http://xxx.xxx.x.xxx'

    # Get images and temperature matrix
    thermal_img, visible_img, temp_list, temp_matrix = extract_global_thermal(USR, PWD, URL)

    # Decode base64 image bytes
    thermal_img_bytes = base64.b64decode(thermal_img)
    visible_img_bytes = base64.b64decode(visible_img)

    thermal_cv = cv2.imdecode(np.frombuffer(thermal_img_bytes, np.uint8), cv2.IMREAD_COLOR)
    visible_cv = cv2.imdecode(np.frombuffer(visible_img_bytes, np.uint8), cv2.IMREAD_COLOR)

    # Display thermal and visible images
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    plt.title("Thermal Image")
    plt.imshow(cv2.cvtColor(thermal_cv, cv2.COLOR_BGR2RGB))
    plt.axis("off")

    plt.subplot(1, 2, 2)
    plt.title("Visible Image")
    plt.imshow(cv2.cvtColor(visible_cv, cv2.COLOR_BGR2RGB))
    plt.axis("off")

    plt.tight_layout()
    plt.show()

    # Normalize and apply pseudocolor to temperature matrix
    norm_temp = cv2.normalize(temp_matrix, None, 0, 255, cv2.NORM_MINMAX)
    norm_temp = norm_temp.astype(np.uint8)
    color_temp = cv2.applyColorMap(norm_temp, cv2.COLORMAP_JET)

    # Find hottest point
    max_val = np.max(temp_matrix)
    max_loc = np.unravel_index(np.argmax(temp_matrix), temp_matrix.shape)
    y, x = max_loc

    # Display pseudocolor map with hotspot
    plt.figure(figsize=(5, 4))
    plt.title("Thermal Matrix (Pseudocolor)")
    plt.imshow(cv2.cvtColor(color_temp, cv2.COLOR_BGR2RGB))
    plt.scatter([x], [y], color='white', s=40, marker='o', edgecolors='black')
    plt.text(x + 5, y - 5, f"{max_val:.1f}°C", color='white', fontsize=10,
             bbox=dict(facecolor='black', alpha=0.5, boxstyle='round,pad=0.2'))
    plt.axis("off")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
