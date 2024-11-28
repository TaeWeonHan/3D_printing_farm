import simpy
import numpy as np
from config_Simpy import *  # 설정 파일 (JOB_TYPES, PRINTERS, PRINTERS_INVEN 등)
from log_simpy import *  # 로그 파일 (DAILY_EVENTS 등)

# Display 클래스: 시뮬레이션 시간(일 단위)을 추적하고 일별 보고서를 기록
class Display:
    def __init__(self, env, daily_events):
        self.env = env  # SimPy 환경 객체
        self.daily_events = daily_events  # 일별 이벤트 로그 리스트

    def track_days(self):
        """현재 날짜를 추적하여 DAILY_EVENTS에 기록"""
        while True:
            day = int(self.env.now // 24) + 1  # 현재 시뮬레이션 시간을 일 단위로 계산
            self.daily_events.append(f"\n===== Day {day} Report: =====")  # 일별 보고서 제목 추가
            yield self.env.timeout(24)  # 24시간(1일)마다 실행

# Customer 클래스: 지속적으로 Job(작업)을 생성
class Customer:
    def __init__(self, env, daily_events):
        self.env = env  # SimPy 환경 객체
        self.daily_events = daily_events  # 일별 이벤트 로그 리스트
        self.current_job_id = 0  # Job ID 초기값
        self.last_assigned_printer = -1  # 마지막으로 할당된 프린터 ID

    def create_jobs_continuously(self):
        """지속적으로 Job을 생성하고 프린터에 할당"""
        while True:
            # 현재 날짜 계산
            day = int(self.env.now // 24) + 1

            # Job 생성
            job = Job(self.env, self.current_job_id, JOB_TYPES["default"])
            self.current_job_id += 1

            # 적합한 프린터 검색
            suitable_printers = []
            for printer_id, printer in PRINTERS.items():
                if job.volume <= printer["VOL"]:  # Job의 볼륨이 프린터 용량 이하인지 확인
                    suitable_printers.append(printer_id)

            # 프린터 할당
            if suitable_printers:
                self.last_assigned_printer = (self.last_assigned_printer + 1) % len(suitable_printers)
                printer_id = suitable_printers[self.last_assigned_printer]
                PRINTERS_INVEN[printer_id].append(job)
                self.daily_events.append(
                    f"{int(self.env.now % 24)}:{int((self.env.now % 1) * 60):02d} - Job {job.job_id} is assigned to Printer {printer_id}"
                )
            else:
                self.daily_events.append(
                    f"Job {job.job_id} could not be assigned: No suitable printer available (Job size: {job.volume:.2f})"
                )

            # 다음 Job 생성 간격 (지수 분포 사용)
            interval = np.random.exponential(JOB_CREATION_INTERVAL)
            yield self.env.timeout(interval)

# PostProcessing 클래스: 후처리 작업을 관리
class PostProcessing:
    def __init__(self, env, daily_events, packaging):
        self.env = env  # SimPy 환경 객체
        self.daily_events = daily_events  # 일별 이벤트 로그 리스트
        self.workers = {worker_id: {"is_busy": False} for worker_id in POST_PROCESSING_WORKER.keys()}
        self.queue = []  # 대기열
        self.packaging = packaging  # Packaging 객체 참조

    def assign_job(self, job):
        """작업자에게 Job을 할당"""
        for worker_id, worker in self.workers.items():
            if not worker["is_busy"]:
                worker["is_busy"] = True
                self.daily_events.append(
                    f"{int(self.env.now % 24)}:{int((self.env.now % 1) * 60):02d} - Job {job.job_id} is starting on Worker {worker_id} (Post-processing)"
                )
                self.env.process(self.process_job(worker_id, job))
                return True
        self.queue.append(job)  # 모든 작업자가 바쁠 경우 대기열에 추가
        return False

    def process_job(self, worker_id, job):
        """Job 처리"""
        yield self.env.timeout(job.post_processing_time)  # 후처리 시간 대기
        self.daily_events.append(
            f"{int(self.env.now % 24)}:{int((self.env.now % 1) * 60):02d} - Job {job.job_id} is finishing on Worker {worker_id} (Post-processing)"
        )
        self.workers[worker_id]["is_busy"] = False

        # 후처리 완료 후 포장 작업에 전달
        self.packaging.assign_job(job)

        # 대기열에 Job이 있으면 다음 작업 처리
        if self.queue:
            next_job = self.queue.pop(0)
            self.daily_events.append(
                f"{int(self.env.now % 24)}:{int((self.env.now % 1) * 60):02d} - Job {next_job.job_id} is starting on Worker {worker_id} (Post-processing)"
            )
            self.env.process(self.process_job(worker_id, next_job))

# Packaging 클래스: 포장 작업을 관리
class Packaging:
    def __init__(self, env, daily_events):
        self.env = env  # SimPy 환경 객체
        self.daily_events = daily_events  # 일별 이벤트 로그 리스트
        self.workers = {worker_id: {"is_busy": False} for worker_id in PACKAGING_MACHINE.keys()}
        self.queue = []  # 대기열

    def assign_job(self, job):
        """포장 작업자에게 Job을 할당"""
        for worker_id, worker in self.workers.items():
            if not worker["is_busy"]:
                worker["is_busy"] = True
                self.daily_events.append(
                    f"{int(self.env.now % 24)}:{int((self.env.now % 1) * 60):02d} - Job {job.job_id} is starting on Worker {worker_id} (Packaging)"
                )
                self.env.process(self.process_job(worker_id, job))
                return True
        self.queue.append(job)  # 모든 작업자가 바쁠 경우 대기열에 추가
        return False

    def process_job(self, worker_id, job):
        """Job 포장 처리"""
        yield self.env.timeout(job.packaging_time / 60)  # 포장 시간을 시간 단위로 변환
        self.daily_events.append(
            f"{int(self.env.now % 24)}:{int((self.env.now % 1) * 60):02d} - Job {job.job_id} is finishing on Worker {worker_id} (Packaging)"
        )
        self.workers[worker_id]["is_busy"] = False

        # 대기열에서 다음 Job 처리
        if self.queue:
            next_job = self.queue.pop(0)
            self.daily_events.append(
                f"{int(self.env.now % 24)}:{int((self.env.now % 1) * 60):02d} - Job {next_job.job_id} is starting on Worker {worker_id} (Packaging)"
            )
            self.env.process(self.process_job(worker_id, next_job))

# Job 클래스: Job의 속성을 정의
class Job:
    def __init__(self, env, job_id, config):
        self.env = env  # SimPy 환경 객체
        self.job_id = job_id  # Job ID
        self.volume = np.random.uniform(*config["VOLUME_RANGE"])  # Job 볼륨
        self.build_time = np.random.randint(*config["BUILD_TIME_RANGE"])  # 제작 시간
        self.post_processing_time = np.random.randint(*config["POST_PROCESSING_TIME_RANGE"])  # 후처리 시간
        self.packaging_time = np.random.randint(*config["PACKAGING_TIME_RANGE"])  # 포장 시간

# Printer 클래스: 프린터의 작업 처리
class Printer:
    def __init__(self, env, daily_events, printer_id, volume, post_processor):
        self.env = env  # SimPy 환경 객체
        self.daily_events = daily_events  # 일별 이벤트 로그 리스트
        self.printer_id = printer_id  # 프린터 ID
        self.volume = volume  # 프린터의 최대 처리 용량
        self.is_busy = False  # 프린터 상태 (초기값: 비활성)
        self.inventory = PRINTERS_INVEN[printer_id]  # 프린터 작업 대기열
        self.post_processor = post_processor  # PostProcessing 객체 참조

    def process_jobs(self):
        """프린터의 Job 처리"""
        while True:
            if self.inventory:  # 대기열에 Job이 있는 경우
                job = self.inventory.pop(0)
                self.is_busy = True
                self.daily_events.append(
                    f"{int(self.env.now % 24)}:{int((self.env.now % 1) * 60):02d} - Job {job.job_id} is printed on Printer {self.printer_id} (Print)"
                )
                yield self.env.timeout(job.build_time)  # 작업 처리 시간 대기
                self.is_busy = False
                self.daily_events.append(
                    f"{int(self.env.now % 24)}:{int((self.env.now % 1) * 60):02d} - Job {job.job_id} is finishing on Printer {self.printer_id} (Print)"
                )
                self.post_processor.assign_job(job)  # 후처리 작업으로 전달
            else:
                yield self.env.timeout(1)  # 대기열이 비었을 경우 대기

# 환경 생성 함수
def create_env(daily_events):
    """
    SimPy 환경 및 객체를 생성하고 초기화합니다.
    """
    simpy_env = simpy.Environment()  # SimPy 환경 생성

    # 각 객체 생성
    packaging = Packaging(simpy_env, daily_events)
    post_processor = PostProcessing(simpy_env, daily_events, packaging)
    customer = Customer(simpy_env, daily_events)
    display = Display(simpy_env, daily_events)

    # 각 프린터 생성
    printers = [
        Printer(simpy_env, daily_events, pid, details["VOL"], post_processor)
        for pid, details in PRINTERS.items()
    ]

    # 초기화된 환경 및 객체 반환
    return simpy_env, packaging, post_processor, customer, display, printers, daily_events

def simpy_event_processes(simpy_env, packaging, post_processor, customer, display, printers, daily_events):
    """
    SimPy 이벤트 프로세스를 설정합니다.
    """
    # Day 추적 및 Job 생성 프로세스 추가
    simpy_env.process(display.track_days())
    simpy_env.process(customer.create_jobs_continuously())

    # 각 프린터의 작업 처리 프로세스 추가
    for printer in printers:
        simpy_env.process(printer.process_jobs())
