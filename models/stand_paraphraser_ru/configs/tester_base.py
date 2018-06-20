# Copyright 2017 Neural Networks and Deep Learning lab, MIPT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import json
import requests
import copy
import traceback
from abc import ABC, abstractmethod
from multiprocessing import Process


class TesterBase(ABC, Process):
    """Base abstract class for further implementations of KPIs testing agents with agent-specific methods

    Properties:
        input_queue:
        output_queue:
        agent: KPI's model agent object
        config: dict object initialised with config.json and modified with run script
        opt: dict object with optional agent and KPI testing parameters
        kpi_name: string with KPI name
        session_id: string with testing session ID received from the testing system
        numtasks: integer with tasks number
        tasks: dict object initialised with tasks JSON received from the testing system
        observations: list object with observation set, prepared for the agent
        predictions: list object with results of agent inference on observations set
        answers: list object prepared for dumping into JSON payload of POST request according testing the system API
        score: string with result of agent predictions scoring by testing system
        response_code: string with the code of the testing system POST request response

    Public methods:
        init_agent(self): [abstract] initiates model agent
        update_config(self, config, init_agent=False): updates Tester instance config
        set_numtasks(self, numtasks): updates Tester instance tasks number
        run_test(self, init_agent=True): evokes full cycle of KPI testing sequence with current config and tasks number
    """

    def __init__(self, config, opt, input_queue, output_queue):
        """Tester class constructor

        Args:
            :param config: dict object initialised with config.json and modified with run script
            :type config: dict
            :param opt: dict object with optional agent and KPI testing parameters
            :type opt: dict
            :param opt:
            :type opt: multiprocessing.Queue
            :param opt:
            :type opt: multiprocessing.Queue
        """
        super(TesterBase, self).__init__()
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.agent = None
        self.config = copy.deepcopy(config)
        self.opt = copy.deepcopy(opt)
        self.kpi_name = self.config['kpi_name']
        self.session_id = None
        self.numtasks = None
        self.tasks = None
        self.observations = None
        self.agent_params = None
        self.predictions = None
        self.answers = None
        self.score = None
        self.response_code = None

    @abstractmethod
    def init_agent(self):
        """Initiate model agent

        Abstract method for further implementations of KPI agent instance initialization with KPI specific parameters
        """

    def update_config(self, config, init_agent=False):
        """Update Tester instance configuration dict

        Args:
            :param config: dict object initialised with config.json and modified with run script
            :type config: dict
            :param init_agent: integer flag (0, 1), turns off/on agent [re]initialising
            :type init_agent: int
        """
        self.config = config
        if init_agent:
            self.init_agent()

    def set_numtasks(self, numtasks):
        """Update Tester instance number of tasks, requested during the next testing session

        Args:
            :param numtasks: integer with tasks number
            :type numtasks: int
        Method is used when need in tasks number different to provided in config arises.
        In order to reset tasks number to config value, evoke this method with numtasks==0
        """
        self.numtasks = numtasks

    def _get_tasks(self):
        """Send GET request to testing system and get tasks set

        Returns:
            :return: dict object initialised with tasks JSON received from the testing system
            :rtype: dict
        """
        get_url = self.config['kpis'][self.kpi_name]['settings_kpi']['rest_url']
        if self.numtasks in [None, 0]:
            test_tasks_number = self.config['kpis'][self.kpi_name]['settings_kpi']['test_tasks_number']
        else:
            test_tasks_number = self.numtasks
        get_params = {'stage': 'netest', 'quantity': test_tasks_number}
        get_response = requests.get(get_url, params=get_params)
        tasks = json.loads(get_response.text)
        return tasks

    @abstractmethod
    def _make_observations(self, tasks, human_input):
        """Prepare observation set according agent API

        Args:
            :param tasks: dict object initialised with tasks JSON received from the testing system
            :type tasks: dict
        Returns:
            :return: list object containing observations in format, compatible with agent API
            :rtype: list
        Abstract method for further implementations of making observations set according KPI agent API
        """

    @abstractmethod
    def _get_predictions(self, observations):
        """Process observations with agent's model and get predictions on them

        Args:
            :param observations: list object containing observations in format, compatible with agent API
            :type observations: list
        Returns:
            :return: list object containing predictions in raw agent format
            :rtype: list
        Abstract method for further implementations KPI agent inference on observations set
        """

    @abstractmethod
    def _make_answers(self, observations, predictions, human_input):
        """Prepare answers dict for the JSON payload of the POST request

        Args:
            :param observations: list object containing observations in format, compatible with agent API
            :type observations: list
            :param predictions: list object containing predictions in raw agent format
            :type predictions: list
        Returns:
            :return: dict object containing answers to task, compatible with test system API for current KPI
            :rtype: dict
        Abstract method for further implementations of making answers set according KPI API
        """

    def _get_score(self, answers):
        """Prepare POST request with answers, send to the KPI endpoint and get score

        Args:
            :param answers: dict object containing answers to task, compatible with test system API for current KPI
            :type answers: dict
        Returns:
            :return: dict object containing
                text: string with score information
                status_code: int with POST request response code
            :rtype: dict
        """
        post_headers = {'Accept': '*/*'}
        rest_response = requests.post(self.config['kpis'][self.kpi_name]['settings_kpi']['rest_url'],
                                      json=answers,
                                      headers=post_headers)
        return {'text': rest_response.text, 'status_code': rest_response.status_code}

    def run_test(self, init_agent=True):
        """Rune full cycle of KPI testing sequence

        Args:
            :param init_agent: bool flag, turns on/off agent [re]initialising before testing sequence
            :type init_agent: bool
        """
        if init_agent or self.agent is None:
            self.init_agent()

        tasks = self._get_tasks()
        session_id = tasks['id']
        numtasks = tasks['total']
        self.tasks = tasks
        self.session_id = session_id
        self.numtasks = numtasks

        observations = self._make_observations(tasks)
        self.observations = observations

        predictions = self._get_predictions(observations)
        self.predictions = predictions

        answers = self._make_answers(observations, predictions)
        self.answers = answers

        score_response = self._get_score(answers)
        self.score = score_response['text']
        self.response_code = score_response['status_code']

    def run_score(self, observation):
        observations = self._make_observations(observation, human_input=True)
        self.observations = observations
        predictions = self._get_predictions(observations)
        self.predictions = predictions
        answers = self._make_answers(observations, predictions, human_input=True)
        self.answers = answers

    def run(self):
        if self.agent is None:
            self.init_agent()

        while True:
            #try:
                input_q = self.input_queue.get()
                print("Run %s, received input: %s" % (self.kpi_name, str(input_q)))
                if isinstance(input_q, list):
                    print("%s human input mode..." % self.kpi_name)
                    self.run_score(input_q)
                    result = copy.deepcopy(self.answers)
                    print("%s action result:  %s" % (self.kpi_name, result))
                    self.output_queue.put(result)
                elif isinstance(input_q, int):
                    print("%s API mode..." % self.kpi_name)
                    self.set_numtasks(input_q)
                    self.run_test(init_agent=False)
                    print("%s score: %s" % (self.kpi_name, self.score))
                    result = copy.deepcopy(self.tasks)
                    result.update(copy.deepcopy(self.answers))
                    self.output_queue.put(result)
                else:
                    self.output_queue.put({"ERROR":
                                               "{} parameter error - {} belongs to unknown type".format(self.kpi_name,
                                                                                                        str(input_q))})
            #except Exception as e:
            #    self.output_queue.put({"ERROR": "{}".format(traceback.extract_stack())})
