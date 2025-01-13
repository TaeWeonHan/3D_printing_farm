from config_Simpy import *  # 시뮬레이션 설정 및 구성 정보
import environment as env  # 환경 생성 및 프로세스 정의
from log_simpy import *  # 로그 및 이벤트 기록
import pandas as pd  # 데이터 분석 및 저장
import visualization

# Step 1: 환경 및 객체 초기화
simpy_env, packaging, post_processor, customer, display, printers, daily_events, satisfication = env.create_env(DAILY_EVENTS)

# Step 2: SimPy 이벤트 프로세스 설정
env.simpy_event_processes(simpy_env, packaging, post_processor, customer, display, printers, daily_events)

# Step 3: 시뮬레이션 실행
for day in range(SIM_TIME):  # 시뮬레이션을 설정된 기간 동안 실행
    simpy_env.run(until=simpy_env.now + 24)  # 하루 단위로 실행

    if PRINT_SIM_EVENTS:
        # 하루 동안의 이벤트 로그 출력
        for log in daily_events:
            print(log)  # 이벤트 로그 출력

    if PRINT_SIM_COST:  # 비용 출력
        print("\n===== Daily Cost Report for Day", day + 1, "=====")
        for cost_type, cost_value in DAILY_COST_REPORT.items():
            print(f"{cost_type}: ${cost_value:.2f}")  # 각 비용 항목 출력

    # 하루 동안 생성된 Job 정보 출력
    print("\n===== JOB LOG for Day", day + 1, "=====")
    for job in JOB_LOG:
        if job['day'] == day + 1:  # 현재 Day의 Job만 출력
            print(f"Job {job['job_id']} | Width: {job['width']} x Height: {job['height']} x Depth: {job['depth']} = Volume: {job['volume']} | "
                  f"Creation Time: {job['create_time']:.4f} | "
                  f"Build Time: {job['build_time']} | Post-Processing Time: {job['post_processing_time']} | "
                  f"Packaging Time: {job['packaging_time']}")
            
    if PRINT_SATISFICATION:
        "SATISFICATION_LOG에 저장된 만족도를 누적해서 출력"
        print(f"\n===== Total Satisfication for Day {day + 1}: {satisfication.total_satisfication:.4f} =====\n")

    daily_events.clear()  # 로그 초기화
    env.Cost.clear_cost()  # 비용 초기화

day = SIM_TIME + 1

# 남은 작업 처리
while any(printer.inventory for printer in printers) or post_processor.queue or packaging.queue:

    simpy_env.run(until=simpy_env.now + 24)

    if PRINT_SIM_EVENTS:
        # 추가 작업 처리 중 이벤트 로그 출력
        for log in daily_events:
            print(log)

    if PRINT_SIM_COST:  # 비용 출력
        print("\n===== Additional Cost Report for Day", day, "=====")
        for cost_type, cost_value in DAILY_COST_REPORT.items():
            print(f"{cost_type}: ${cost_value:.2f}")

    # 남은 작업 처리 중 JOB_LOG 출력
    print("\n===== JOB LOG for Additional Day", day, "=====")
    for job in JOB_LOG:
        if job['day'] == day:  # 현재 Day의 Job만 출력
            print(f"Job {job['job_id']} | Volume: {job['volume']:.2f} | "
                  f"Build Time: {job['build_time']} | Post-Processing Time: {job['post_processing_time']} | "
                  f"Packaging Time: {job['packaging_time']}")
            
    if PRINT_SATISFICATION:
        "SATISFICATION_LOG에 저장된 만족도를 누적해서 출력"
        print(f"\n===== Total Satisfication for Day {day}: {satisfication.total_satisfication:.4f} =====\n")

    daily_events.clear()  # 로그 초기화
    env.Cost.clear_cost()  # 비용 초기화

    day += 1

# 시뮬레이션 종료 후 전체 JOB_LOG 출력
print("\n============= Final JOB LOG =============")
for job in JOB_LOG:
    print(f"Day {job['day']} | Job {job['job_id']} | Volume: {job['volume']:.2f} | "
          f"Build Time: {job['build_time']} | Post-Processing Time: {job['post_processing_time']} | "
          f"Packaging Time: {job['packaging_time']}")

# DAILY_REPORTS 데이터를 DataFrame으로 변환
print(DAILY_REPORTS)
export_Daily_Report = []
for record in DAILY_REPORTS:
    if record['process'] == 'Printing':
        export_Daily_Report.append({
            "DAY": int(record['start_time'] // 24) + 1,
            "JOB_ID": record['job_id'],
            "ASSIGNED_PRINTER": record.get('printer_id', None),
            "PRINTING_START": record['start_time'],
            "PRINTING_FINISH": record['end_time'],
            "ASSIGNED_POSTPROCESS_WORKER": None,
            "POSTPROCESSING_START": None,
            "POSTPROCESSING_FINISH": None,
            "ASSIGNED_PACKAGING_WORKER": None,
            "PACKAGING_START": None,
            "PACKAGING_FINISH": None
        })
    elif record['process'] == 'Post-Processing':
        for item in export_Daily_Report:
            if item['JOB_ID'] == record['job_id']:
                item["ASSIGNED_POSTPROCESS_WORKER"] = record.get('worker_id', None)
                item["POSTPROCESSING_START"] = record['start_time']
                item["POSTPROCESSING_FINISH"] = record['end_time']
    elif record['process'] == 'Packaging':
        for item in export_Daily_Report:
            if item['JOB_ID'] == record['job_id']:
                item["ASSIGNED_PACKAGING_WORKER"] = record.get('worker_id', None)
                item["PACKAGING_START"] = record['start_time']
                item["PACKAGING_FINISH"] = record['end_time']
print(export_Daily_Report)
# DataFrame 생성
daily_reports = pd.DataFrame(export_Daily_Report)

# CSV 파일로 저장
daily_reports.to_csv("./Daily_Report.csv", index=False)

if VISUALIZATION != False:
    visualization.visualization(export_Daily_Report)
