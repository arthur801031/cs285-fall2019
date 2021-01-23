import numpy as np
import torch
from collections import OrderedDict

from cs285.policies.MLP_policy import MLPPolicyAC
from cs285.critics.bootstrapped_continuous_critic import BootstrappedContinuousCritic
from cs285.infrastructure.replay_buffer import ReplayBuffer
from cs285.infrastructure.utils import *

class ACAgent:
    def __init__(self, env, agent_params):
        super(ACAgent, self).__init__()

        self.env = env
        self.agent_params = agent_params
        self.num_critic_updates_per_agent_update = agent_params['num_critic_updates_per_agent_update']
        self.num_actor_updates_per_agent_update = agent_params['num_actor_updates_per_agent_update']
        self.device = agent_params['device']

        self.gamma = self.agent_params['gamma']
        self.standardize_advantages = self.agent_params['standardize_advantages']

        self.actor = MLPPolicyAC(self.agent_params['ac_dim'],
                               self.agent_params['ob_dim'],
                               self.agent_params['n_layers'],
                               self.agent_params['size'],
                               self.agent_params['device'],
                               discrete=self.agent_params['discrete'],
                               learning_rate=self.agent_params['learning_rate'],
                               )
        # introduced in actor-critic to improve advantage function.
        self.critic = BootstrappedContinuousCritic(self.agent_params)

        self.replay_buffer = ReplayBuffer()

    def estimate_advantage(self, ob_no, next_ob_no, re_n, terminal_n):
        ob, next_ob, rew, done = map(lambda x: torch.from_numpy(x).to(self.device), [ob_no, next_ob_no, re_n, terminal_n])

        # DoneTODO Implement the following pseudocode:
            # 1) query the critic with ob_no, to get V(s)
            # 2) query the critic with next_ob_no, to get V(s')
            # 3) estimate the Q value as Q(s, a) = r(s, a) + gamma*V(s')
            # HINT: Remember to cut off the V(s') term (ie set it to 0) at terminal states (ie terminal_n=1)
            # 4) calculate advantage (adv_n) as A(s, a) = Q(s, a) - V(s)

        v_s = self.critic.value_func(ob)
        v_s_prime = self.critic.value_func(next_ob).squeeze()
        v_s_prime[done >= 1] = 0
        estimated_q = rew + self.gamma * v_s_prime
        adv_n = estimated_q - v_s
        adv_n = adv_n.cpu().detach().numpy()

        if self.standardize_advantages:
            adv_n = (adv_n - np.mean(adv_n)) / (np.std(adv_n) + 1e-8)
        return adv_n

    def train(self, ob_no, ac_na, re_n, next_ob_no, terminal_n):

        # DoneTODO Implement the following pseudocode:
            # for agent_params['num_critic_updates_per_agent_update'] steps,
            #     update the critic

            # advantage = estimate_advantage(...)

            # for agent_params['num_actor_updates_per_agent_update'] steps,
            #     update the actor

        loss = OrderedDict()

        for i in range(self.num_critic_updates_per_agent_update):
            loss['Critic_Loss'] = self.critic.update(ob_no, next_ob_no, re_n, terminal_n)
        
        adv = self.estimate_advantage(ob_no, next_ob_no, re_n, terminal_n)

        for i in range(self.num_actor_updates_per_agent_update):
            loss['Actor_Loss'] = self.actor.update(ob_no, ac_na, adv)

        return loss

    def add_to_replay_buffer(self, paths):
        self.replay_buffer.add_rollouts(paths)

    def sample(self, batch_size):
        return self.replay_buffer.sample_recent_data(batch_size)
