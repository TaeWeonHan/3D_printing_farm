# Gymwrapper.py

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from main import initialize_simpy_environment  # main.py에서 환경 초기화 함수 가져오기
from config_SimPy import *  # 설정 파일에서 I, P, SIM_TIME 가져오기
from log_SimPy import DAILY_EVENTS  # 로그 파일에서 DAILY_EVENTS 가져오기
from environment import Cost  # environment.py에서 Cost 클래스 가져오기

class SimpyInventoryEnv(gym.Env):
    """
    GymWrapper for SimPy-based inventory management environment.
    SimPy 시뮬레이터에서 발생하는 데이터를 감싸고, 이를 강화학습 알고리즘에 전달합니다.
    """
    def __init__(self):
        super(SimpyInventoryEnv, self).__init__()

        # main.py에서 초기화된 시뮬레이터 환경을 가져옴
        self.simpy_env, self.inventoryList, self.procurementList, self.productionList, \
            self.sales, self.customer, self.supplierList, self.daily_events = initialize_simpy_environment()

        # 상태 공간 정의 (재고 수준, 수요 등 상태 변수 포함)
        self.observation_space = spaces.Box(
            low=0, high=np.inf, shape=(len(self.inventoryList) + 1,), dtype=np.float32
        )  # 재고 수준 및 수요

        # 행동 공간 정의 (주문량과 재주문 임계값)
        action_space_size = 2 * len(self.procurementList) if len(self.procurementList) > 0 else 2  # 각 자재에 대해 주문량과 재주문 임계값
        self.action_space = spaces.Box(
            low=np.array([0] * action_space_size),  # 최소값
            high=np.array([10] * action_space_size),  # 최대값
            dtype=np.float32
        )

        # 초기 상태 설정
        self.state = self._get_state()

        # 시뮬레이션 시간을 설정
        self.current_time = 0
        self.max_time = SIM_TIME  # 시뮬레이션 시간 설정

    def _get_state(self):
        """
        현재 시뮬레이터 상태를 반환합니다.
        재고 수준과 수요량을 포함합니다.
        """
        inventory_levels = [inventory.on_hand_inventory for inventory in self.inventoryList]
        
        # 수요량을 Customer 객체에서 가져옴 (demand_qty 사용)
        demand_quantity = I[0]["DEMAND_QUANTITY"] if "DEMAND_QUANTITY" in I[0] else 0
        
        state = inventory_levels + [demand_quantity]
        return np.array(state, dtype=np.float32)

    def step(self, action):
        """
        주어진 행동을 적용하여 환경을 한 단계 진행시키고, 새로운 상태, 보상, 종료 여부를 반환합니다.
        """
        # 행동 적용: 자재별 주문량과 재주문 임계값 업데이트
        if len(self.procurementList) > 0:
            order_qty = action[:len(self.procurementList)]
            reorder_level = action[len(self.procurementList):]

            for i, procurement in enumerate(self.procurementList):
                procurement.order_qty = order_qty[i]
                procurement.reorder_level = reorder_level[i]
        else:
            print("Warning: procurementList is empty, skipping action.")

        # SimPy 환경에서 하루 동안 시뮬레이션 진행
        self.simpy_env.run(until=self.simpy_env.now + 24)

        # 각 비용 항목을 합산하여 보상 계산
        holding_cost = sum(inventory.unit_holding_cost * inventory.on_hand_inventory for inventory in self.inventoryList)
        process_cost = sum(production.unit_processing_cost for production in self.productionList)
        delivery_cost = self.sales.unit_delivery_cost
        order_cost = sum(procurement.unit_purchase_cost * procurement.order_qty for procurement in self.procurementList)
        shortage_cost = self.sales.unit_shortage_cost * self.sales.num_shortages

        # 총 비용을 계산하고 보상을 음수로 설정 (비용 최소화를 목표로 함)
        total_cost = holding_cost + process_cost + delivery_cost + order_cost + shortage_cost
        reward = -total_cost

        # 상태 업데이트
        self.state = self._get_state()

        # 종료 조건 확인
        self.current_time += 1
        done = self.current_time >= self.max_time

        return self.state, reward, done, {}

    def reset(self):
        """
        환경을 초기화하고 초기 상태를 반환합니다.
        """
        self.simpy_env, self.inventoryList, self.procurementList, self.productionList, \
            self.sales, self.customer, self.supplierList, self.daily_events = initialize_simpy_environment()
        self.current_time = 0
        self.state = self._get_state()
        return self.state

    def render(self, mode="human"):
        """
        시뮬레이션 상태를 출력합니다.
        """
        print(f"Day {self.simpy_env.now // 24}:")
        for i, inven in enumerate(self.inventoryList):
            print(f"{I[inven.item_id]['NAME']} - On-hand: {inven.on_hand_inventory}, In-transit: {inven.in_transition_inventory}")

if __name__ == "__main__":
    env = SimpyInventoryEnv()
    print("Initial state:", env.reset())

    # Day 1부터 마지막 Day까지 순차적으로 실행
    for day in range(env.max_time):  # 최대 시뮬레이션 시간만큼 반복
        print(f"\n=== Day {day + 1} ===")
        
        # 임의의 행동을 선택하는 대신 매일 주문량과 재주문 임계값을 동일하게 설정 (테스트용으로 일관된 행동을 설정)
        if len(env.procurementList) > 0:
            # 각 자재에 대해 최소 주문량을 설정하고 재주문 임계값을 설정
            action = np.array([5] * len(env.procurementList) + [2] * len(env.procurementList))  # 테스트를 위한 일관된 행동

        # 행동을 적용하고 결과를 확인
        state, reward, done, info = env.step(action)
        
        # 상태, 보상 및 종료 여부를 출력
        print(f"State: {state}, Reward: {reward}, Done: {done}")

        # Inventory 상태를 상세히 출력 (수정 사항 반영)
        for inventory in env.inventoryList:
            print(f"{I[inventory.item_id]['NAME']} - On-hand: {inventory.on_hand_inventory}, In-transit: {inventory.in_transition_inventory}")
        
        # 시뮬레이션이 종료되면 반복을 멈춤
        if done:
            break
