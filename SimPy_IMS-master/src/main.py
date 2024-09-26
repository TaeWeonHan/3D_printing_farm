from config_SimPy import *
from log_SimPy import *
import environment as env
import pandas as pd
import Visualization

def initialize_simpy_environment():
    """
    시뮬레이터 환경을 초기화하고 필요한 객체들을 반환하는 함수.
    """
    # 시뮬레이터 환경을 생성
    simpy_env, inventoryList, procurementList, productionList, sales, customer, supplierList, daily_events = env.create_env(
        I, P, DAILY_EVENTS)
    
    return simpy_env, inventoryList, procurementList, productionList, sales, customer, supplierList, daily_events

# 시뮬레이터 환경 초기화
simpy_env, inventoryList, procurementList, productionList, sales, customer, supplierList, daily_events = initialize_simpy_environment()

# SimPy 이벤트 프로세스를 실행
env.simpy_event_processes(simpy_env, inventoryList, procurementList,
                          productionList, sales, customer, supplierList, daily_events, I)

# 시뮬레이션 실행
if PRINT_SIM_EVENTS:
    print(f"============= Initial Inventory Status =============")
    for inventory in inventoryList:
        print(
            f"Day 1 - {I[inventory.item_id]['NAME']} Inventory: {inventory.on_hand_inventory} units")

    print(f"============= SimPy Simulation Begins =============")

for x in range(SIM_TIME):
    daily_events.append(f"\nDay {(simpy_env.now) // 24+1} Report:")
    simpy_env.run(until=simpy_env.now+24)
    # daily_total_cost = env.cal_daily_cost(inventoryList, procurementList, productionList, sales)

    if PRINT_SIM_EVENTS:
        # 매일 이벤트를 출력
        for log in daily_events:
            print(log)
        # print("[Daily Total Cost] ", daily_total_cost)
    daily_events.clear()

    # 일일 보고서 업데이트
    env.update_daily_report(inventoryList)
    if PRINT_SIM_REPORT:
        for id in range(len(inventoryList)):
            print(DAILY_REPORTS[x][id])

    # 비용 로그 업데이트
    env.Cost.update_cost_log(inventoryList)
    if PRINT_SIM_COST:
        for key in DAILY_COST_REPORT.keys():
            print(f"{key}: {DAILY_COST_REPORT[key]}")
        print(f"Total cost: {sum(COST_LOG)}")
    env.Cost.clear_cost()

# 일일 보고서 내보내기
export_Daily_Report = DAILY_REPORTS
if VISUALIAZTION != False:
    Visualization.visualization(export_Daily_Report)

daily_reports = pd.DataFrame(export_Daily_Report)

# 열 이름 설정
columns_list = []
for keys in I.keys():
    columns_list.append("DAY")
    columns_list.append(f"{I[keys]['NAME']}'s NAME")
    columns_list.append(f"{I[keys]['NAME']}'s TYPE")
    columns_list.append(f"{I[keys]['NAME']}'s START")
    columns_list.append(f"{I[keys]['NAME']}'s INCOME")
    columns_list.append(f"{I[keys]['NAME']}'s OUTCOME")
    columns_list.append(f"{I[keys]['NAME']}'s END")

daily_reports.columns = columns_list
daily_reports.to_csv("./Daily_Report.csv")
