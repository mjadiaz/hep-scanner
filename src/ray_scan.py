from hepaid.hepread import SLHA, LesHouches
from hepaid.hepread import HiggsBoundsResults, HiggsSignalsResults
from hepaid.heptools import Spheno, HiggsBounds, HiggsSignals
from omegaconf import OmegaConf, DictConfig

import numpy as np
import os
import ray
import shutil
import pandas as pd


class Space:
	def __init__(self, config):
		self.block = config.model.parameters.lhs.block
		self.index = config.model.parameters.lhs.index
		self.low_lim = config.model.parameters.low_lim
		self.high_lim = config.model.parameters.high_lim

		self.sample_dim = len(self.index)

	def sample(self):
		sample_point = np.zeros(self.sample_dim)
		for i, limits in enumerate(zip(self.low_lim, self.high_lim)):
			low, high = limits
			sample_point[i] = np.random.uniform(low,high)
		return sample_point

class Sampler:
	def __init__(self,
			sampler_id: int,
			config: DictConfig,
			lhs: LesHouches = None
			):
		'''Initialize the HEP tools to run a serial scan'''
		self.hp = config
		self.scan_dir = self.hp.directories.scan_dir
		self.sampler_id_dir = os.path.join(
			self.scan_dir, str(sampler_id)
			)

		# Parameter information 
		self.block = self.hp.model.parameters.lhs.block
		self.index = self.hp.model.parameters.lhs.index

		self.current_lhs = 'LesHouches.in.Step'
		self.current_spc = 'Spheno.spc.Step'

		self.space = Space(config)


		self.spheno = Spheno(
			spheno_dir = self.hp.directories.spheno,
			work_dir = self.sampler_id_dir,
			model_name = self.hp.model.name,
			)
		self.higgs_bounds = HiggsBounds(
			higgs_bounds_dir = self.hp.directories.higgsbounds,
			work_dir = self.sampler_id_dir,
			neutral_higgs = self.hp.model.neutral_higgs,
			charged_higgs = self.hp.model.charged_higgs,
			)
		self.higgs_signals = HiggsSignals(
			higgs_signals_dir = self.hp.directories.higgssignals,
			work_dir = self.sampler_id_dir,
			neutral_higgs = self.hp.model.neutral_higgs,
			charged_higgs = self.hp.model.charged_higgs,
			)
		if lhs is None:
			self.lhs = LesHouches(
				file_dir = self.hp.directories.reference_lhs,
				work_dir = self.sampler_id_dir,
				model =  self.hp.model.name,
				)
		else:
			self.lhs = lhs

	def create_dir(self, run_name: str):
		if not(os.path.exists(self.sampler_id_dir)):
			os.makedirs(self.sampler_id_dir)

	def get_lhs(self):
		return self.lhs

	def sample(self):

		param_card = None

		sample_point = self.space.sample()
		# To iterate on each block name, parameter index and
		# the sampled value respectively
		params_iterate = zip(
			self.block,
			self.index,
			self.hp.model.parameters.name,
			sample_point
			)
		parameters = {}
		for params in params_iterate:
			block, index, name, value = params
			self.lhs.block(block).set(index, value)
			parameters[name] = value

		# Create new lhs file with the parameter values
		self.lhs.new_file(self.current_lhs)
		# Run spheno with the new lhs file
		param_card, spheno_stdout = self.spheno.run(
			self.current_lhs,
			self.current_spc
			)
		if param_card is not None:
			self.higgs_bounds.run()
			self.higgs_signals.run()
			higgs_signals_results = HiggsSignalsResults(
				self.sampler_id_dir,
				model = self.hp.model.name
				).read()
			higgs_bounds_results = HiggsBoundsResults(
				self.sampler_id_dir,
				model=self.hp.model.name
				).read()

		observable_name = self.hp.model.observation.name
		observations = {}
		for obs_name in observable_name:
			if param_card is not None:
				if obs_name in higgs_bounds_results.keys():
					value = float(higgs_bounds_results[obs_name])
				if obs_name in higgs_signals_results.keys():
					value = float(higgs_signals_results[obs_name])
				observations[obs_name] = value
			else:
				observations[obs_name] = None

		params_obs = {**parameters,** observations}
		return params_obs

	def close(self):
		shutil.rmtree(self.sampler_id_dir)

@ray.remote
class RemoteSampler(Sampler):
	def __init__(self, scanner, sampler_id, config, lhs=None):
		super().__init__(sampler_id, config, lhs)
		self.scanner = scanner

	def send_sample(self):
		params_obs = self.sample()
		params_obs = np.fromiter(
			params_obs.values(),
			dtype=float
			)
		print(params_obs)
		self.scanner.add_data.remote(params_obs)

	def run(self):
		while not ray.get(self.scanner.stop.remote()):
			self.send_sample()


@ray.remote
class Scanner:
	def __init__(self,
			config: DictConfig,
			lhs: LesHouches = None
			):
		self.config = config
		self.max_samples = self.config.scanner.max_samples
		self.n_workers = self.config.scanner.n_workers
		self.observables = config.model.observation.name
		self.parameters = config.model.parameters.name

		self.parameters_dimension = len(self.parameters)
		self.observation_dimension = len(self.observables)
		self.data = np.zeros((
				self.max_samples,
				self.observation_dimension + self.parameters_dimension
				))
		self.counter = 0
		self._stop = False

	def increment_counter(self):
		self.counter += 1
		if self.counter == self.max_samples:
			self._stop = True
	
	def get_counter(self):
		return self.counter

	def stop(self):
		return self._stop

	def add_data(self , sample_point):
		idx = self.counter
		self.data[idx] = sample_point
		self.increment_counter()

	def get_data(self, save=False):
		columns = self.parameters + self.observables
		df = pd.DataFrame(self.data, columns = columns)
		return df

@ray.remote
class Reporter:
	def __init__(self, scanner):
		self.scanner = scanner
		self._data = None
		self.update_rate = 20
		self.last_counter = 0

	def update_data(self):
		data = ray.get(self.scanner.get_data.remote())
		self._data = data

	def data(self):
		return self._data
	def save_csv(self):
		self._data.to_csv('data.csv', index=False)

	def run(self):
		while not ray.get(self.scanner.stop.remote()):
			self.last_counter = ray.get(self.scanner.get_counter.remote())
			if self.last_counter % self.update_rate == 0:
				self.update_data()
				print(self.data())
				self.save_csv()
