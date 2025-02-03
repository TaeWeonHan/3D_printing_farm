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
        
class Customer:
    def __init__(self, env, shortage_cost, daily_events, satisfication):
        self.env = env  # SimPy 환경 객체
        self.daily_events = daily_events  # 일별 이벤트 로그 리스트
        self.current_job_id = 0  # Job ID 초기값
        self.last_assigned_printer = -1  # 마지막으로 할당된 프린터 ID
        self.unit_shortage_cost = shortage_cost  # Shortage cost
        self.satisfication = satisfication
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

            # 프린터 할당
            if suitable_printers:
                self.create_job_list.append(job)

            else:
                # Shortage cost 발생: 적합한 프린터가 없을 때
                self.daily_events.append(
                    f"Job {job.job_id} could not be assigned: No suitable printer available (Job size: {job.volume:.2f})"
                )
                # Shortage cost 발생
                job.shortage = 1  # Shortage는 한 번에 한 프린터가 부족할 때 1로 설정
                
                Cost.cal_cost(job, "Shortage cost")
                
                # 고객 만족도 계산
                self.satisfication.cal_satisfication(job, self.env.now)

            # 다음 Job 생성 간격 (지수 분포 사용)
            interval = np.random.exponential(JOB_CREATION_INTERVAL)
            yield self.env.timeout(interval)


# Printer 클래스: 프린터의 작업 처리
class Printer:
    def __init__(self, env, printing_cost, daily_events, printer_id, width, height, depth, post_processor):
        self.env = env  # SimPy 환경 객체
        self.daily_events = daily_events  # 일별 이벤트 로그 리스트
        self.printer_id = printer_id  # 프린터 ID
        self.width = width # 프린터의 최대 처리 너비
        self.height = height # 프린터의 최대 처리 높이
        self.depth = depth # 프런티의 최대 처리 깊이이
        self.is_busy = False  # 프린터 상태 (초기값: 비활성)
        self.job_list = []  # 대기열
        self.post_processor = post_processor  # PostProcessing 객체 참조
        self.unit_printing_cost = printing_cost
        self.last_assigned_printer

    def assign_job(self):
        if customer.create_job_list and len(self.job_list) == 0: 
            # 적합한 프린터 중 작동 가능한 프린터를 라운드로빈 방식으로 선택
            for job in customer.create_job_list:
                for printer_id in job.suitable_printers:
                    if PRINTERS[printer_id]["is_busy"] is False:
                        # 프린터가 사용 가능하면 즉시 작업을 처리
                        self.is_busy = True
                        customer.create_job_list.remove(job)
                        PRINTERS[printer_id]["is_busy"] = True
                        self.daily_events.append(
                            f"Job {job.job_id} assigned to Printer {self.printer_id} at {self.env.now}."
                        )
                        # 작업 처리 시작
                        self.env.process(self.process_job(job))
                        return
            # 모든 프린터가 바쁠 경우 대기열에 저장
            self.daily_events.append("All printers are busy. Job added to the queue.")
        else:
            # 대기열에 추가
            appending_job = customer.create_job_list[0]
            self.job_list.append(appending_job)
            customer.create_job_list.remove(appending_job)

    def process_jobs(self):
        """프린터의 Job 처리"""
        while True:
            if self.inventory:  # 대기열에 Job이 있는 경우
                job = self.inventory.pop(0)
                self.is_busy = True
                start_time = self.env.now
                self.daily_events.append(
                    f"{int(self.env.now % 24)}:{int((self.env.now % 1) * 60):02d} - Job {job.job_id} is printed on Printer {self.printer_id} (Print)"
                )
                # Printing 비용 계산
                Cost.cal_cost(job, "Printing cost")
                
                yield self.env.timeout(job.build_time / 60)  # 작업 처리 시간 대기
                end_time = self.env.now
                self.is_busy = False
                self.daily_events.append(
                    f"{int(self.env.now % 24)}:{int((self.env.now % 1) * 60):02d} - Job {job.job_id} is finishing on Printer {self.printer_id} (Print)"
                )
                # DAILY_REPORTS에 기록
                DAILY_REPORTS.append({
                    'job_id': job.job_id,
                    'printer_id': self.printer_id,
                    'start_time': start_time,
                    'end_time': end_time,
                    'process': 'Printing'
                })
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
    satisfication = Satisfication(simpy_env, daily_events)
    packaging = Packaging(simpy_env, COST_TYPES[0]['PACKAGING_COST'], daily_events, satisfication)
    post_processor = PostProcessing(simpy_env, COST_TYPES[0]['POSTPROCESSING_COST'], daily_events, packaging)
    customer = Customer(simpy_env, COST_TYPES[0]['SHORTAGE_COST'], daily_events, satisfication)
    display = Display(simpy_env, daily_events)
    

    # 각 프린터 생성
    printers = [
        Printer(simpy_env, COST_TYPES[0]['PRINTING_COST'], daily_events, pid, details["WIDTH"], details["HEIGHT"], details["DEPTH"], post_processor)
        for pid, details in PRINTERS.items()
    ]

    # 초기화된 환경 및 객체 반환
    return simpy_env, packaging, post_processor, customer, display, printers, daily_events, satisfication


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