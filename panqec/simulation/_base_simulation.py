"""
API for running simulations.
"""
from abc import ABCMeta, abstractmethod
import os
import json
from json import JSONDecodeError
import datetime
import numpy as np
import gzip
from panqec.codes import StabilizerCode
from panqec.error_models import BaseErrorModel

from ..utils import NumpyEncoder


class BaseSimulation(metaclass=ABCMeta):
    """Quantum Error Correction Simulation."""

    start_time: datetime.datetime
    code: StabilizerCode
    error_model: BaseErrorModel
    label: str
    _results: dict = {}
    rng = None

    def __init__(
        self,
        code: StabilizerCode,
        error_model: BaseErrorModel,
        compress: bool = True,
        verbose=True,
        rng=None
    ):
        self.code = code
        self.error_model = error_model
        self.compress = compress
        self.verbose = verbose
        self.rng = rng
        self.label = 'results'

        self._results = {
            'n_runs': 0,
            'wall_time': 0,
        }
        self._inputs = {
            'code': {
                'name': self.code.id,
                'parameters': self.code.params,
                'n': self.code.n,
                'k': self.code.k,
                'd': self.code.d,
            },
            'error_model': {
                'name': self.error_model.id,
                'parameters':  self.error_model.params
            }
        }

    @property
    def wall_time(self):
        return self._results['wall_time']

    @property
    def n_results(self):
        return self._results['n_runs']

    @property
    def results(self):
        res = self._results
        return res

    @property
    def file_name(self) -> str:
        if self.compress:
            extension = '.json.gz'
        else:
            extension = '.json'
        file_name = self.label + extension
        return file_name

    def run(self, n_runs: int):
        self.start_time = datetime.datetime.now()

        self._run(n_runs)

        finish_time = datetime.datetime.now() - self.start_time
        self._results['wall_time'] += finish_time.total_seconds()

    def _find_current_simulation(self, data: list) -> dict:
        for sim in data:
            if sim['inputs'] == self._inputs:
                return sim
        return {}

    def load_results(self, output_file: str):
        """Load previously written results from directory."""

        # Find the alternative compressed file path if it doesn't exist.
        try:
            if os.path.exists(output_file):
                if os.path.splitext(output_file)[-1] == '.gz':
                    with gzip.open(output_file, 'rb') as gz:
                        data = json.loads(gz.read().decode('utf-8'))
                else:
                    with open(output_file) as json_file:
                        data = json.load(json_file)

                data_simulation = self._find_current_simulation(data)

                if data_simulation != {}:
                    self.load_results_from_dict(data_simulation)

        except JSONDecodeError as err:
            print(f'Error loading existing results file {output_file}')
            print('Starting this from scratch')
            print(err)

    def load_results_from_dict(self, data):
        for key in self._results.keys():
            if key in data['results'].keys():
                self._results[key] = data['results'][key]
                if (
                    isinstance(self.results[key], list)
                    and len(self.results[key]) > 0
                    and isinstance(self._results[key][0], list)
                ):
                    self._results[key] = [
                        np.array(array_value)
                        for array_value in self._results[key]
                    ]

    def get_results_to_save(self):
        data = {
            'results': self._results,
            'inputs': self._inputs
        }

        return data

    def save_results(self, output_file: str):
        """Save results to directory."""
        data = self.get_results_to_save()
        if self.compress:
            with gzip.open(output_file, 'wb') as gz:
                gz.write(json.dumps(data, cls=NumpyEncoder).encode('utf-8'))
        else:
            with open(output_file, 'w') as json_file:
                json.dump(data, json_file, indent=4, cls=NumpyEncoder)

    @abstractmethod
    def get_results(self):
        pass

    @abstractmethod
    def _run(self, n_runs: int):
        pass

    def postprocess(self):
        pass
