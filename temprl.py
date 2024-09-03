import gym
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random
import matplotlib.pyplot as plt

# 환경 설정
class CoolingEnv(gym.Env):
    def __init__(self):
        super(CoolingEnv, self).__init__()
        self.action_space = gym.spaces.Discrete(5)  # 5가지 행동
        self.observation_space = gym.spaces.Box(low=np.array([0, -10, 0, 0, 0]),
                                                high=np.array([50, 40, 24, 24, 100]), dtype=np.float32)
        self.state = None
        self.t = 0  # 외부 온도 변화를 위한 시간 변수
        self.reset()

        # 시스템의 물리적 특성 (임의의 값)
        self.R = 0.1  # 열 저항
        self.C = 10.0  # 열 용량
        self.dt = 1.0  # 시간 간격

    def step(self, action):
        T_in, T_out, T_set, _, E = self.state

        # 외부 온도의 변화 (하루 주기로 변동)
        T_out += np.sin(self.t / 24 * 2 * np.pi)  # 24시간 주기(하루)로 외부 온도 변동
        
        # 시스템의 물리적 모델에 따라 온도 변화 계산
        T_in += (1/(self.R * self.C)) * (T_out - T_in) * self.dt + (action - 2) / self.C

        # 에너지 소비량 계산 (단순화된 예시)
        delta_E = abs(action - 2) * 10  # 온도 변화량에 비례하여 에너지 소비

        # 보상 계산
        comfort_cost = (T_set - T_in) ** 2
        energy_cost = delta_E
        reward = - (energy_cost + comfort_cost)

        # 상태 업데이트
        self.state = np.array([T_in, T_out, T_set, action, E + delta_E], dtype=np.float32)

        # 시간 증가
        self.t = (self.t + 1) % 24  # 24시간을 넘어가면 다시 0으로

        done = False  # 특정 조건이 되면 True로 설정
        return self.state, reward, done, {}

    def reset(self):
        self.state = np.array([24, 20, 22, 0, 0], dtype=np.float32)
        self.t = 0  # 리셋할 때 시간도 초기화
        return self.state

# Q-Network 정의
class QNetwork(nn.Module):
    def __init__(self, state_size, action_size):
        super(QNetwork, self).__init__()
        self.fc1 = nn.Linear(state_size, 24)
        self.fc2 = nn.Linear(24, 24)
        self.fc3 = nn.Linear(24, action_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)

# 하이퍼파라미터 설정
state_size = 5
action_size = 5
batch_size = 64
gamma = 0.99
epsilon = 1.0
epsilon_min = 0.01
epsilon_decay = 0.995
learning_rate = 0.001
target_update = 10
memory_size = 2000
num_episodes = 1000

# 환경 및 네트워크 초기화
env = CoolingEnv()
q_network = QNetwork(state_size, action_size)
target_network = QNetwork(state_size, action_size)
target_network.load_state_dict(q_network.state_dict())
optimizer = optim.Adam(q_network.parameters(), lr=learning_rate)
memory = deque(maxlen=memory_size)

# 시각화를 위한 기록
episode_rewards = []

# DQN 학습
for episode in range(num_episodes):
    state = env.reset()
    state = torch.FloatTensor(state).unsqueeze(0)
    total_reward = 0

    for t in range(200):
        # Epsilon-greedy policy
        if np.random.rand() <= epsilon:
            action = np.random.randint(action_size)
        else:
            with torch.no_grad():
                action = q_network(state).argmax().item()

        next_state, reward, done, _ = env.step(action)
        next_state = torch.FloatTensor(next_state).unsqueeze(0)
        reward = torch.FloatTensor([reward])

        # 메모리에 저장
        memory.append((state, action, reward, next_state, done))
        state = next_state
        total_reward += reward.item()

        # Replay memory에서 샘플링하고 학습
        if len(memory) > batch_size:
            batch = random.sample(memory, batch_size)
            states, actions, rewards, next_states, dones = zip(*batch)

            states = torch.cat(states)
            actions = torch.LongTensor(actions).unsqueeze(1)
            rewards = torch.cat(rewards).unsqueeze(1)
            next_states = torch.cat(next_states)
            dones = torch.FloatTensor(dones).unsqueeze(1)

            # 현재 Q 값과 타겟 Q 값 계산
            q_values = q_network(states).gather(1, actions)
            next_q_values = target_network(next_states).max(1)[0].detach().unsqueeze(1)
            targets = rewards + (gamma * next_q_values * (1 - dones))

            loss = nn.MSELoss()(q_values, targets)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        if done:
            break

    # Epsilon 감소
    epsilon = max(epsilon_min, epsilon_decay * epsilon)
    
    # 타겟 네트워크 업데이트
    if episode % target_update == 0:
        target_network.load_state_dict(q_network.state_dict())

    episode_rewards.append(total_reward)
    print(f"Episode: {episode+1}, Total Reward: {total_reward:.2f}, Epsilon: {epsilon:.2f}")

print("Training complete.")

# 결과 시각화
plt.figure(figsize=(12, 5))
plt.plot(episode_rewards)
plt.xlabel('Episode')
plt.ylabel('Total Reward')
plt.title('Total Reward per Episode')
plt.show()
