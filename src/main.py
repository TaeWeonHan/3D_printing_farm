from config_Simpy import *
import environment as env
from log_simpy import *
import pandas as pd

# 환경 및 객체 초기화
simpy_env, packaging, post_processor, customer, display, printers, daily_events = env.create_env(DAILY_EVENTS)

# 시뮬레이션 실행
for x in range(SIM_TIME):
    simpy_env.run(until=simpy_env.now + 24)
    if PRINT_SIM_EVENTS:
        # 하루 동안의 이벤트 로그 출력
        for log in daily_events:
            print(log)
    daily_events.clear()
