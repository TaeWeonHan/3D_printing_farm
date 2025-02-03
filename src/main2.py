# 예시 코드 (run_simulation.py 등 원하는 파일에 작성)
from config_Simpy import * 
from test1 import create_env, simpy_event_processes  # 위 코드가 들어있는 파일에서 import
# config_Simpy.py, log_simpy.py 에 정의된 변수들도 여기서 import 되도록 주의하세요.
# 예: from config_Simpy import SIM_TIME

def main():
    # SimPy 환경과 Customer 객체 생성
    simpy_env, customer = create_env()
    
    # 이벤트 프로세스 등록
    simpy_event_processes(simpy_env, customer)
    
    # 시뮬레이션 실행 (예: SIM_TIME*24 시간까지)
    simpy_env.run(until=SIM_TIME * 24)
    
    # 시뮬레이션 종료 후 최종 Job 리스트 확인
    print("최종 생성된 Job 리스트:", customer.create_job_list)

if __name__ == "__main__":
    main()
