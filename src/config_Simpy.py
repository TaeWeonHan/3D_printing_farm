
import numpy as np  # numpy 모듈로 수정
import random

#### 시뮬레이션 설정 ###########################################################
# SIM_TIME: 시뮬레이션이 진행될 총 기간 (일 단위)
# 예시: SIM_TIME = 7 -> 시뮬레이션이 7일 동안 진행됨
#### Job 생성 파라미터 설정 ####################################################
# JOB_ARRIVAL_RATE: 포아송 분포의 λ 값, 단위 시간당 평균 Job 발생 수를 의미함
# JOB_INTERVAL: Job 생성 간격 (시간 단위), 기본은 24시간 (하루에 한 번 Job 생성)
# JOB_CREATION_INTERVAL: Job 생성 간격의 평균값 (시간 단위)
#### 주문 관련 설정 ###########################################################
# ORDER_CYCLE: 주문이 반복되는 주기, 매일 주문이 발생하도록 설정 (일 단위)
# ORDER_QUANTITY_RANGE: 주문 수량의 최소 및 최대 범위를 지정 (랜덤 값으로 생성)
#### Job의 속성 정의 ##########################################################
# JOB_TYPES: Job의 속성 정의 사전, 기본 Job 유형의 다양한 속성 범위를 포함함
# - VOLUME_RANGE: Job 볼륨의 최소/최대 범위 (예: 1에서 45)
# - BUILD_TIME_RANGE: Job 제작 시간 범위 (예: 1에서 5일)
# - POST_PROCESSING_TIME_RANGE: 후처리 시간 범위
# - PACKAGING_TIME_RANGE: 포장 시간 범위
#### 후처리 작업자 설정 ########################################################
# POST_PROCESSING_WORKER: 작업자 정보 설정, 각 작업자의 ID를 포함
# 작업자가 동시에 처리할 수 있는 Job은 1개로 제한됨
#### 수요량 설정 ##############################################################
# DEMAND_QTY_MIN: 하루 수요량의 최소값
# DEMAND_QTY_MAX: 하루 수요량의 최대값
# DEMAND_QTY_FUNC(): 하루 수요량을 결정하는 함수, 최소값과 최대값 사이에서 랜덤 선택
#### 3D 프린터 정보 설정 #######################################################
# PRINTERS: 각 프린터의 정보 설정 (ID와 최대 처리 용량)
# PRINTERS_INVEN: 각 프린터별 Job 대기열을 저장하는 리스트

# 시뮬레이션 설정
SIM_TIME = 2  # 시뮬레이션 기간 (일 단위)

# Job 생성 파라미터 설정
JOB_ARRIVAL_RATE = 2  # 단위 시간당 평균 Job 발생 수 (포아송 분포의 λ 값)
JOB_INTERVAL = 24  # Job 생성 간격 (시간 단위), 예: 매일 Job 생성

# 주문 관련 설정
ORDER_CYCLE = 1  # 매일 주문 주기
ORDER_QUANTITY_RANGE = (1, 8)  # 주문 수량 범위

# Job의 속성 정의
JOB_TYPES = {
    "default": {
        "VOLUME_RANGE": (1, 45),  # Job 볼륨 범위
        "BUILD_TIME_RANGE": (1, 5),  # 제작 시간 범위
        "POST_PROCESSING_TIME_RANGE": (1, 3),  # 후처리 시간 범위
        "PACKAGING_TIME_RANGE": (10, 30)  # 포장시간 범위
    }
}

COST_TYPES = {
    0: {
        'HOLDING_COST': 0.1,
        'PRINTING_COST': 1,
        'POSTPROCESSING_COST': 1,
        'PACKAGING_COST': 1,
        'DELIVERY_COST': 1,
        'SHORTAGE_COST' : 1
    }
}
DEMAND_QTY_MIN = 1
DEMAND_QTY_MAX = 7
# 하루 동안 주문 수량 결정
def DEMAND_QTY_FUNC():
    DAILY_DEMAND = random.randint(DEMAND_QTY_MIN, DEMAND_QTY_MAX)
    return DAILY_DEMAND

# 3D 프린터 정보 설정
PRINTERS = {
    0: {"ID": 0, "VOL": 24},
    1: {"ID": 1, "VOL": 27},
    2: {"ID": 2, "VOL": 20},
    3: {"ID": 3, "VOL": 16.78},
    4: {"ID": 4, "VOL": 42.875}
}
PRINTERS_INVEN = {
    0:[],
    1:[],
    2:[],
    3:[],
    4:[]
}

POST_PROCESSING_WORKER = {
    0: {'ID': 0},
    1: {'ID': 1},
    2: {"ID": 2},
    3: {"ID": 3}
}

PACKAGING_MACHINE = {
    0: {"ID": 0},
    1: {"ID": 1},
    2: {"ID": 2}
}

JOB_CREATION_INTERVAL = 1  # 평균 1시간 간격으로 Job 생성
VISUALIZATION = True
PRINT_SIM_EVENTS = True
PRINT_SIM_COST = True  # True로 설정하면 비용이 출력됨, False로 설정하면 출력되지 않음