import simpy
import numpy as np
from config_Simpy import *  # 설정 파일 (JOB_TYPES, PRINTERS, PRINTERS_INVEN 등)
from log_simpy import *  # 로그 파일 (DAILY_EVENTS 등)


# Customer 클래스: 지속적으로 Job(작업)을 생성
class Customer:
    def __init__(self, env, shortage_cost):
        self.env = env  # SimPy 환경 객체
        self.current_job_id = 0  # Job ID 초기값
        self.last_assigned_printer = -1  # 마지막으로 할당된 프린터 ID
        self.unit_shortage_cost = shortage_cost  # Shortage cost
        self.create_job_list = []

    def create_jobs_continuously(self):
        """지속적으로 Job을 생성하고 프린터에 할당"""
        
        while True:
            # SIM_TIME 이후에는 Job 생성 중단
            if self.env.now >= SIM_TIME * 24:
                break

            # 현재 날짜 계산
            day = int(self.env.now // 24) + 1

            # Job 생성
            job = Job(self.env, self.current_job_id, JOB_TYPES["DEFAULT"])
            self.current_job_id += 1
            # JOB_LOG에 Job 기록 추가
            JOB_LOG.append({
                'day': day,
                'job_id': job.job_id,
                'width': job.width,
                'height': job.height,
                'depth': job.depth,
                'create_time': job.create_time,
                'volume': job.volume,
                'build_time': job.build_time,
                'post_processing_time': job.post_processing_time,
                'packaging_time': job.packaging_time
            })
            # 적합한 프린터 검색
            suitable_printers = []
            for printer_id, printer in PRINTERS.items():
                if job.width <= printer["WIDTH"] and job.height <= printer["HEIGHT"] and job.depth <= printer["DEPTH"]:  # Job의 볼륨이 프린터 용량 이하인지 확인
                    suitable_printers.append(printer_id)
                    
            # 적합한 프린터 정보를 Job 객체에 저장
            job.suitable_printers = suitable_printers
            print(job.suitable_printers)
            # 프린터 할당
            if suitable_printers:
                self.create_job_list.append(job)

            else:
                # Shortage cost 발생
                job.shortage = 1  # Shortage는 한 번에 한 프린터가 부족할 때 1로 설정

            # 다음 Job 생성 간격 (지수 분포 사용)
            interval = np.random.exponential(JOB_CREATION_INTERVAL)
            print(self.create_job_list)
            yield self.env.timeout(interval)

# Job 클래스: Job의 속성을 정의
class Job:
    def __init__(self, env, job_id, config):
        self.env = env  # SimPy 환경 객체
        self.job_id = job_id  # Job ID
        self.create_time = env.now  # Job 생성 시간 기록
        self.suitable_printers = []
        self.height = np.random.randint(*config["HEIGHT_RANGE"])
        self.width = np.random.randint(*config["WIDTH_RANGE"])
        self.depth = np.random.randint(*config["DEPTH_RANGE"])
        self.volume = (
                         self.height
                       * self.width
                       * self.depth
                       )# Job 볼륨
        self.build_time = int(round(self.volume / (config["BUILD_SPEED"] 
                                         * 3.14 
                                         * (config["FILAMENT_DIAMETER"]/2)**2
                                         )))  # 제작 시간        
        self.post_processing_time = np.mean([self.height, self.width, self.depth]) // (config["POST_PROCESSING_TIME_COEFFICIENT"])  # 후처리 시간

        if self.volume <= (LENGHT_RANGE["WIDTH"]["MAX"] * LENGHT_RANGE["HEIGHT"]["MAX"] * LENGHT_RANGE["DEPTH"]["MAX"])/2:
            self.packaging_time = np.random.randint(*config["SMALL_PACKAGING_TIME_RANGE"])  # 포장 시간

        elif ((LENGHT_RANGE["WIDTH"]["MAX"] * LENGHT_RANGE["HEIGHT"]["MAX"] * LENGHT_RANGE["DEPTH"]["MAX"])/2 + 1 
              <= self.volume 
              <= (LENGHT_RANGE["WIDTH"]["MAX"] * LENGHT_RANGE["HEIGHT"]["MAX"] * LENGHT_RANGE["DEPTH"]["MAX"])):
            self.packaging_time = np.random.randint(*config["LARGE_PACKAGING_TIME_RANGE"])  # 포장 시간

        # 추가: 비용 항목들 초기화
        self.printing_cost = 0
        self.post_processing_cost = 0
        self.packaging_cost = 0
        self.delivery_cost = 0
        self.shortage_cost = 0
        self.shortage = 0  # 부족 수량 (Shortage Cost 계산용)

# 환경 생성 함수
def create_env():
    """
    SimPy 환경 및 객체를 생성하고 초기화합니다.
    """
    simpy_env = simpy.Environment()  # SimPy 환경 생성


    customer = Customer(simpy_env, COST_TYPES[0]['SHORTAGE_COST'])

    # 초기화된 환경 및 객체 반환
    return simpy_env, customer


def simpy_event_processes(simpy_env, customer):
    """
    SimPy 이벤트 프로세스를 설정합니다.
    """
    # Day 추적 및 Job 생성 프로세스 추가
    simpy_env.process(customer.create_jobs_continuously())
