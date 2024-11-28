from config_Simpy import *  # 시뮬레이션 설정 및 구성 정보
import environment as env  # 환경 생성 및 프로세스 정의
from log_simpy import *  # 로그 및 이벤트 기록
import pandas as pd  # 데이터 분석 및 저장

# Step 1: 환경 및 객체 초기화
simpy_env, packaging, post_processor, customer, display, printers, daily_events = env.create_env(DAILY_EVENTS)

# Step 2: SimPy 이벤트 프로세스 설정
env.simpy_event_processes(simpy_env, packaging, post_processor, customer, display, printers, daily_events)

# Step 3: 시뮬레이션 실행
for day in range(SIM_TIME):  # 시뮬레이션을 설정된 기간 동안 실행
    simpy_env.run(until=simpy_env.now + 24)  # 하루 단위로 실행
    if PRINT_SIM_EVENTS:
        # 하루 동안의 이벤트 로그 출력
        for log in daily_events:
            print(log)  # 이벤트 로그 출력
    daily_events.clear()  # 로그 초기화

