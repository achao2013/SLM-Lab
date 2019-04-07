from slm_lab.env.base import BaseEnv, ENV_DATA_NAMES
from slm_lab.env.wrapper import make_env, wrap_atari, wrap_deepmind
from slm_lab.env.vec_wrapper import make_venv
from slm_lab.env.registration import register_env
from slm_lab.lib import logger, util
from slm_lab.lib.decorator import lab_api
import numpy as np
import pydash as ps

logger = logger.get_logger(__name__)

_NUM_PROCESSES = 4


def guard_reward(reward):
    '''Some gym environments have buggy format and reward is in a np array'''
    if np.isscalar(reward):
        return reward
    else:  # some gym envs have weird reward format
        assert len(reward) == 1
        return reward[0]


class OpenAIEnv(BaseEnv):
    '''
    Wrapper for OpenAI Gym env to work with the Lab.

    e.g. env_spec
    "env": [{
      "name": "CartPole-v0",
      "max_t": null,
      "max_tick": 150,
    }],
    '''

    def __init__(self, spec, e=None, env_space=None):
        super(OpenAIEnv, self).__init__(spec, e, env_space)
        try:
            # register any additional environments first. guard for re-registration
            register_env(spec)
        except Exception as e:
            pass
        # TODO hard-set here
        self.num_processes = _NUM_PROCESSES
        stack_len = ps.get(spec, 'agent.0.memory.stack_len')
        dummy_env = make_env(self.name, stack_len)
        env = make_venv(self.name, seed=0, num_processes=self.num_processes)
        self.u_env = env
        self._set_attr_from_u_env(self.u_env)
        self.max_t = self.max_t or dummy_env.spec.max_episode_steps
        assert self.max_t is not None
        if env_space is None:  # singleton mode
            pass
        else:
            self.space_init(env_space)
        logger.info(util.self_desc(self))

    @lab_api
    def reset(self):
        # _reward = np.nan
        _reward = np.full(self.num_processes, np.nan)
        state = self.u_env.reset()
        # self.done = done = False
        self.done = done = np.zeros(self.num_processes)
        if util.to_render():
            self.u_env.render()
        logger.debug(f'Env {self.e} reset reward: {_reward}, state: {state}, done: {done}')
        return _reward, state, done

    @lab_api
    def step(self, action):
        if not self.is_discrete:  # guard for continuous
            action = np.array([action])
        state, reward, done, _info = self.u_env.step(action)
        # reward = guard_reward(reward)
        if self.reward_scale is not None:
            # TODO put into a wrapper
            reward *= self.reward_scale
        if util.to_render():
            self.u_env.render()
        # if self.max_t is not None:
        #     done = done or self.clock.t > self.max_t
        self.done = done
        logger.debug(f'Env {self.e} step reward: {reward}, state: {state}, done: {done}')
        return reward, state, done

    @lab_api
    def close(self):
        self.u_env.close()

    # NOTE optional extension for multi-agent-env

    @lab_api
    def space_init(self, env_space):
        '''Post init override for space env. Note that aeb is already correct from __init__'''
        self.env_space = env_space
        self.aeb_space = env_space.aeb_space
        self.observation_spaces = [self.observation_space]
        self.action_spaces = [self.action_space]

    @lab_api
    def space_reset(self):
        _reward_e, state_e, done_e = self.env_space.aeb_space.init_data_s(ENV_DATA_NAMES, e=self.e)
        for ab, body in util.ndenumerate_nonan(self.body_e):
            state = self.u_env.reset()
            state_e[ab] = state
            done_e[ab] = self.done = False
        if util.to_render():
            self.u_env.render()
        logger.debug(f'Env {self.e} reset reward_e: {_reward_e}, state_e: {state_e}, done_e: {done_e}')
        return _reward_e, state_e, done_e

    @lab_api
    def space_step(self, action_e):
        action = action_e[(0, 0)]  # single body
        if self.done:  # space envs run continually without a central reset signal
            return self.space_reset()
        if not self.is_discrete:
            action = np.array([action])
        state, reward, done, _info = self.u_env.step(action)
        # reward = guard_reward(reward)
        reward *= self.reward_scale
        if util.to_render():
            self.u_env.render()
        self.done = done = done or self.clock.t > self.max_t
        reward_e, state_e, done_e = self.env_space.aeb_space.init_data_s(ENV_DATA_NAMES, e=self.e)
        for ab, body in util.ndenumerate_nonan(self.body_e):
            reward_e[ab] = reward
            state_e[ab] = state
            done_e[ab] = done
        logger.debug(f'Env {self.e} step reward_e: {reward_e}, state_e: {state_e}, done_e: {done_e}')
        return reward_e, state_e, done_e
