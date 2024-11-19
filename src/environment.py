import simpy
import numpy as np
import pandas as pd
from config_Simpy import *  # 설정 파일 (JOB_TYPES, PRINTERS, PRINTERS_INVEN 등)
# test
class Display:
    def __init__(self, env, job_arrival_manager):
        self.env = env
        self.job_arrival_manager = job_arrival_manager

    def track_days(self):
        """Day 출력 및 추적"""
        while True:
            day = int(self.env.now // 24) + 1
            print(f"\n===== Day {day} =====")
            yield self.env.timeout(24)

class Customer:
    def __init__(self, env):
        self.env = env
        self.current_job_id = 0
        self.last_assigned_printer = -1

    def create_jobs_continuously(self):
        """실시간으로 Job 생성"""
        while True:
            # 현재 Day 계산
            day = int(self.env.now // 24) + 1

            # Job 생성
            job = Job(self.env, self.current_job_id, JOB_TYPES["default"])
            self.current_job_id += 1

            # 적합한 프린터를 저장할 리스트를 초기화
            suitable_printers = []

            # PRINTERS 딕셔너리의 각 프린터 정보를 반복
            for printer_id, printer in PRINTERS.items():
                # 현재 Job의 볼륨이 프린터의 처리 용량 이하인 경우
                if job.volume <= printer["VOL"]:
                    suitable_printers.append(printer_id)

            # Job assigns the 3D printer
            if suitable_printers:
                self.last_assigned_printer = (self.last_assigned_printer + 1) % len(suitable_printers)
                printer_id = suitable_printers[self.last_assigned_printer]
                PRINTERS_INVEN[printer_id].append(job)

                hours = int(self.env.now % 24)
                minutes = int((self.env.now % 1) * 60)
                print(f"{hours}:{minutes:02d} - Job {job.job_id} is assigned to Printer {printer_id}")
            else:
                print(f"Job {job.job_id} could not be assigned: No suitable printer available (Job size: {job.volume:.2f})")

            # 다음 Job 생성 간격
            interval = np.random.exponential(JOB_CREATION_INTERVAL)
            yield self.env.timeout(interval)

class PostProcessing:
    def __init__(self, env, packaging):
        self.env = env
        self.workers = {worker_id: {"is_busy": False} for worker_id in POST_PROCESSING_WORKER.keys()}
        self.queue = []
        self.packaging = packaging  # Packaging 객체 참조

    def assign_job(self, job):
        """작업자를 찾아 Job 할당"""
        for worker_id, worker in self.workers.items():
            if not worker["is_busy"]:
                worker["is_busy"] = True
                print(f"{self.env.now % 24}:{int((self.env.now % 1) * 60):02d} - Job {job.job_id} is starting on Worker {worker_id} (Post-processing)")
                self.env.process(self.process_job(worker_id, job))
                return True
        # 모든 작업자가 바쁠 경우 대기열에 추가
        self.queue.append(job)
        return False

    def process_job(self, worker_id, job):
        """작업자가 Job을 처리"""
        yield self.env.timeout(job.post_processing_time)
        print(f"{self.env.now % 24}:{int((self.env.now % 1) * 60):02d} - Job {job.job_id} is finishing on Worker {worker_id} (Post-processing)")
        self.workers[worker_id]["is_busy"] = False

        # Post-processing 후 Packaging 작업 할당
        self.packaging.assign_job(job)

        # 대기열에서 다음 작업 가져오기
        if self.queue:
            next_job = self.queue.pop(0)
            print(f"{self.env.now % 24}:{int((self.env.now % 1) * 60):02d} - Job {next_job.job_id} is starting on Worker {worker_id} (Post-processing)")
            self.env.process(self.process_job(worker_id, next_job))

class Packaging:
    def __init__(self, env):
        self.env = env
        self.workers = {worker_id: {"is_busy": False} for worker_id in PACKAGING_MACHINE.keys()}
        self.queue = []

    def assign_job(self, job):
        """작업 머신을 찾아 Job 할당"""
        for worker_id, worker in self.workers.items():
            if not worker["is_busy"]:
                worker["is_busy"] = True
                print(f"{self.env.now % 24}:{int((self.env.now % 1) * 60):02d} - Job {job.job_id} is starting on Worker {worker_id} (Packaging)")
                self.env.process(self.process_job(worker_id, job))
                return True
        # 모든 머신이 바쁠 경우 대기열에 추가
        self.queue.append(job)
        return False

    def process_job(self, worker_id, job):
        """머신이 Job을 처리"""
        yield self.env.timeout(job.packaging_time / 60)  # 시간을 시간 단위로 변환
        current_time = self.env.now
        hours = int(current_time % 24)  # 소수점 제외한 현재 시각
        minutes = int((current_time % 1) * 60)  # 소수점 부분을 분으로 변환
        print(f"{hours:02d}:{minutes:02d} - Job {job.job_id} is finishing on Worker {worker_id} (Packaging)")
        self.workers[worker_id]["is_busy"] = False

        # 대기열에서 다음 작업 가져오기
        if self.queue:
            next_job = self.queue.pop(0)
            current_time = self.env.now
            hours = int(current_time % 24)
            minutes = int((current_time % 1) * 60)
            print(f"{hours:02d}:{minutes:02d} - Job {next_job.job_id} is starting on Worker {worker_id} (Packaging)")
            self.env.process(self.process_job(worker_id, next_job))


class Job:
    def __init__(self, env, job_id, config):
        self.env = env
        self.job_id = job_id
        self.volume = np.random.uniform(*config["VOLUME_RANGE"])
        self.build_time = np.random.randint(*config["BUILD_TIME_RANGE"])
        self.post_processing_time = np.random.randint(*config["POST_PROCESSING_TIME_RANGE"])
        self.packaging_time = np.random.randint(*config["PACKAGING_TIME_RANGE"])

class Printer:
    def __init__(self, env, printer_id, volume, post_processor):
        self.env = env  # SimPy 환경 객체
        self.printer_id = printer_id  # 프린터 ID
        self.volume = volume  # 프린터의 처리 용량 (volume)
        self.is_busy = False  # 프린터의 초기 상태 (작업 중 여부)
        self.inventory = PRINTERS_INVEN[printer_id]  # 작업 큐 (할당된 작업 리스트)
        self.post_processor = post_processor  # PostProcessing 객체 참조

    def process_jobs(self):
        while True:
            if self.inventory:  # 큐에 작업이 있는 경우
                job = self.inventory.pop(0)  # 작업을 가져옴
                self.is_busy = True
                print(f"{self.env.now % 24}:{int((self.env.now % 1) * 60):02d} - Job {job.job_id} is printed on Printer {self.printer_id} (Print)")
                yield self.env.timeout(job.build_time)  # 작업 시간을 시뮬레이션
                self.is_busy = False
                print(f"{self.env.now % 24}:{int((self.env.now % 1) * 60):02d} - Job {job.job_id} is finishing on Printer {self.printer_id} (Print)")

                # 후처리 단계로 작업 전달
                self.post_processor.assign_job(job)
            else:
                yield self.env.timeout(1)  # 큐가 비었을 경우 1시간 대기

def run_simulation():
    env = simpy.Environment()
    packaging = Packaging(env)  # Packaging 객체 생성
    post_processor = PostProcessing(env, packaging)  # PostProcessing 객체 생성
    customer = Customer(env)
    display = Display(env, customer)
    printers = [Printer(env, pid, details["VOL"], post_processor) for pid, details in PRINTERS.items()]

    # Day 추적 프로세스
    env.process(display.track_days())

    # 실시간 Job 생성 프로세스
    env.process(customer.create_jobs_continuously())

    # 프린터 작업 프로세스
    for printer in printers:
        env.process(printer.process_jobs())
    
    # 시뮬레이션 실행
    env.run(until=SIM_TIME * 24)


run_simulation()
