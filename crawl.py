import csv
import requests
import json
import time
from html import unescape
import threading
from queue import Queue

MAX_RETRIES = 5
TIMEOUT = 10
### 
def extract_score(subject, score_string):
    score = next((s.split(':')[1].strip() for s in score_string.split(';') if subject in s), "N/A")
    return score 

def process_score(formatted_x):
    url = "https://hxa7mnvs1a.execute-api.ap-southeast-1.amazonaws.com/go/" + formatted_x
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            if response.ok and response.text.strip():
                info = response.json()
                diem_info = unescape(info['Diem'])

                diem_van = extract_score("Ngữ văn", diem_info)
                diem_ngoai_ngu = extract_score("Ngoại ngữ", diem_info)
                diem_toan = extract_score("Toán", diem_info)
                diem_tong = extract_score("Tổng điểm XT", diem_info)
                diem_chuyen = extract_score("Chuyên 1", diem_info)
                diem_chuyen2 = extract_score("Chuyên 2", diem_info)

                diem = [
                    info['Id'],
                    info['MaHs'],
                    diem_van,
                    diem_ngoai_ngu,
                    diem_toan,
                    diem_tong
                ]
                if diem_chuyen != "N/A":
                    diem.append(diem_chuyen)
                if diem_chuyen2 != "N/A":
                    diem.append(diem_chuyen2)

                return diem
        except requests.RequestException:
            time.sleep(2**attempt)  # Exponential backoff
    return None  # Failed after retries

def worker(queue, output_file):
    while True:
        formatted_x = queue.get()
        if formatted_x is None:
            break
        score = process_score(formatted_x)
        if score is not None:
            formatted_score = ' '.join(score)
            print(formatted_score)  # print the result
            output_file.write(formatted_score + '\n')  # write the result to file
        queue.task_done()

def main():
    formatted_xs = [str(x).zfill(6) for x in range(1001, 202048)]

    with open("diemthiTHPTQG.txt", 'w') as f:
        f.write('Id MaHs DiemVan DiemNgoaiNgu DiemToan DiemTong DiemChuyen1 DiemChuyen2\n')
        queue = Queue()
        threads = []
        for _ in range(100):
            t = threading.Thread(target=worker, args=(queue, f))
            t.start()
            threads.append(t)
        for x in formatted_xs:
            queue.put(x)
        queue.join()
        for _ in range(100):
            queue.put(None)
        for t in threads:
            t.join()

if __name__ == '__main__':
    main()
