# ppo_train.py

import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from Gymwrapper import SimpyInventoryEnv  # 수정된 환경 사용

# 환경 초기화
env = SimpyInventoryEnv()

# 벡터화된 환경으로 래핑 (PPO는 벡터화된 환경을 필요로 합니다)
env = DummyVecEnv([lambda: env])

# PPO 모델 초기화
model = PPO(
    "MlpPolicy",  # 다층 퍼셉트론 정책 사용
    env,  # 학습할 환경
    verbose=1,  # 학습 과정 출력
    learning_rate=0.001,  # 학습률 설정
    gamma=0.99,  # 할인율 (미래 보상에 대한 중요도)
    n_steps=2048,  # 매 업데이트 전 수행할 스텝 수
    batch_size=64,  # 배치 크기
    ent_coef=0.01,  # 엔트로피 보상 계수 (탐험 강도 조절)
    clip_range=0.2  # PPO 클리핑 범위
)

# PPO 모델 학습
model.learn(total_timesteps=100000)  # 100,000 스텝 동안 학습

# 학습된 모델 저장
model.save("ppo_inventory_management")

# 학습된 모델을 사용해 에피소드 진행 및 평가
obs = env.reset()
for _ in range(1000):  # 1000 스텝 동안 실행
    action, _states = model.predict(obs)  # 학습된 모델로 행동 예측
    obs, reward, done, info = env.step(action)  # 행동 적용 후 결과 반환
    env.render()  # 상태 출력 (필요시)
    if done:
        obs = env.reset()  # 에피소드가 끝나면 환경 재설정
