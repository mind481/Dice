import cv2
import numpy as np
import pygame
import threading
import time

from db import init_db, add_roll

con = init_db()
# 웹캠 연결 (0번 장치)
cap = cv2.VideoCapture(0)

# Load Sound File
pygame.mixer.init()
sounds = {
    # 'start': pygame.mixer.Sound("sounds/start.wav"),
    'correct': pygame.mixer.Sound("sounds/correct.wav"),
    'wrong': pygame.mixer.Sound("sounds/wrong.wav"),
    # '1': pygame.mixer.Sound("sounds/1.wav"),
    # '2': pygame.mixer.Sound("sounds/2.wav"),
    # '3': pygame.mixer.Sound("sounds/3.wav"),
    # '4': pygame.mixer.Sound("sounds/4.wav"),
    # '5': pygame.mixer.Sound("sounds/5.wav"),
    # '6': pygame.mixer.Sound("sounds/6.wav")
}

prev_value = None
stable_since = None
fixed = False
start_time = None
blue_detected = False

def play_sound(key):
    if key not in sounds:
        print(f"해당하는 사운드 파일이 없습니다.({key})")
        return
    def run():
        sounds[key].play()
    threading.Thread(target=run, daemon=True).start()

def pre_processing(frame):
    # HSV 색상 범위 설정 (파란색)
    lower_blue = np.array([90, 50, 50])
    upper_blue = np.array([200, 255, 255])

    # 주사위 인식 범위 제한    
    height, width = frame.shape[:2]
    frame = frame[0:height-200, 0:width]

    # 색상 범위 필터링 (BGR → HSV → Mask)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    masked = cv2.bitwise_and(frame, frame, mask=mask)

    # 그레이스케일로 변환 후 블러 처리
    gray = cv2.cvtColor(masked, cv2.COLOR_BGR2GRAY)
    gray_blurred = cv2.medianBlur(gray, 5)

    return gray_blurred

while True:
    ret, frame = cap.read()
    if not ret:
        break

    output = pre_processing(frame)

    # 파란 물체(주사위) 인식
    blue_pixel_count = cv2.countNonZero(output)
    if blue_pixel_count > 10000:  # 파란 물체가 있는 경우
        blue_detected = True
        cv2.putText(output, "Blue Detected", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        if start_time is None: # 타이머 시작
            start_time = time.time()
        else: # 타이머가 이미 시작된 경우
            elapsed = time.time() - start_time
            if elapsed > 7 and not fixed: # 주사위 눈이 7초 이상 결정되지 않은 경우
                print("다시 던져주세요!")
                play_sound('wrong')
                start_time = time.time() # 타이머 초기화
                stable_since = None
    else: # 파란 물체 없는 경우
        blue_detected = False
        start_time = None
        fixed = False

    # HoughCircles를 이용한 원 검출
    circles = cv2.HoughCircles(
        output,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=30,
        param1=100,
        param2=20, # 원 감지 임계값
        minRadius=10,
        maxRadius=20
    )

    # 검출된 눈의 개수와 검출 시점 저장
    current_value = 0
    if circles is not None:
        current_value = len(circles[0])
    now = time.time()
    
    # 값이 바뀌었으면 타이머 초기화
    if current_value != prev_value:
        print("value changed!")
        stable_since = now
        prev_value = current_value
    else:
        # 값이 3초 이상 유지된 경우 출력
        if stable_since and (now - stable_since > 3) and current_value != 0:
            if not fixed:
                print(f"주사위 눈: {current_value}")
                fixed = True
                if 1 <= current_value <= 6:
                    play_sound('correct')
                    add_roll(con, current_value)
                else:
                    print("다시 던져주세요!")
                    start_time = time.time() # 타이머 초기화
                    stable_since = None
                    play_sound('wrong')
                    fixed = False



    if circles is not None:
        circles = np.uint16(np.around(circles))
        count = len(circles[0, :])
        for i in circles[0, :]:
            # 원 그리기
            cv2.circle(output, (i[0], i[1]), i[2], (0, 255, 0), 2)
            # 중심점 표시
            cv2.circle(output, (i[0], i[1]), 2, (0, 0, 255), 3)

    # 화면에 개수 표시
    cv2.putText(output, f"Circles: {current_value}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # 화면 출력
    cv2.imshow("Circle Detection", output)

    # 종료 조건 (esc 키)
    if cv2.waitKey(1) & 0xFF == 27:
        break

con.close()
cap.release()
cv2.destroyAllWindows()