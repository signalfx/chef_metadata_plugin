from chef import autoconfigure, Node
from time import sleep
import logging
import sys
import requests
import copy
import re
import pickle
import os
import argparse

DEFAULT_CONFIG_FILE = 'configuration.txt'
DEFAULT_LOG_FILE = '/tmp/ChefMetadata.log'
DEFAULT_SIGNALFX_REST_API = 'http://lab-api.corp.signalfuse.com:8080'
DEFAULT_PICKLE_FILE = 'pk_metadata.pk'
DEFAULT_SLEEP_DURATION = 60
DEFAULT_ENV_VARIABLE_NAME = 'SIGNALFX_API_TOKEN'
DEFAULT_LOG_HANDLER = 'logfile'


class Metadata(object):
    """
    Collect metadata of a chef node
    """

    def __init__(self,
                 SIGNALFX_API_TOKEN,
                 CONFIG_FILE=DEFAULT_CONFIG_FILE,
                 LOG_FILE=DEFAULT_LOG_FILE,
                 SIGNALFX_REST_API=DEFAULT_SIGNALFX_REST_API,
                 PICKLE_FILE=DEFAULT_PICKLE_FILE,
                 SLEEP_DURATION=DEFAULT_SLEEP_DURATION,
                 LOG_HANDLER=DEFAULT_LOG_HANDLER):
        self.api = autoconfigure()
        self.SIGNALFX_API_TOKEN = SIGNALFX_API_TOKEN
        self.CONFIG_FILE = CONFIG_FILE
        self.LOG_FILE = LOG_FILE
        self.SIGNALFX_REST_API = SIGNALFX_REST_API + '/v1/dimension'
        self.PICKLE_FILE = PICKLE_FILE
        self.SLEEP_DURATION = SLEEP_DURATION

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if LOG_HANDLER == 'logfile':
            self.handler = logging.FileHandler(DEFAULT_LOG_FILE)
        else:
            self.handler = logging.StreamHandler(sys.stdout)
        self.handler.setLevel(logging.INFO)
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)

        self.property_name_pattern = re.compile('^[a-zA-Z_][a-zA-Z0-9_-]*$')
        self.config = []
        self.organization = ''
        self.nodes_metadata = []

    def run(self):
        """
        Read the configuration file
        Collect metadata from Chef Server API
        Send metadata to Signalfx
        Save the metadata for future comparisions
        """
        self.nodes_metadata = []
        self.read_config()
        self.collect_metadata_from_chef()
        for node_information in self.nodes_metadata:
            self.send_metadata_to_signalfx(node_information)
        self.save_metadata()

    def save_metadata(self):
        """
        Save the metadata as Python pickle
        """
        pickle_data = {}
        for node_information in self.nodes_metadata:
            pickle_data[node_information['chefUniqueId']] = node_information
            pickle_data[node_information['chefUniqueId']].pop('chefUniqueId')
        output = open(self.PICKLE_FILE, 'wb')
        pickle.dump(pickle_data, output)
        self.logger.info('Saved updated metadata to ' + self.PICKLE_FILE)
        output.close()

    def send_metadata_to_signalfx(self, node_information):
        """
        Get ObjectID for the chefUniqueId dimension from Signalfx
        Check for changes between newly collected metadata and last run's data
        If there are any updates, send those changes to Signalfx
        """
        headers = {
            'X-SF-Token': self.SIGNALFX_API_TOKEN,
        }
        resp = self.get_signalfx_objectid(node_information, headers)
        if len(resp.json()['rs']) == 0:
            self.logger.info('Signalfx does not have an object '
                             + 'for your dimension chefUniqueId:'
                             + node_information['chefUniqueId'])
            return
        signalfx_objectid = resp.json()['rs'][0]
        self.logger.info("ObjectID for " + node_information['chefUniqueId']
                         + " is " + signalfx_objectid)
        new_metadata = self.check_for_updates_in_metadata(
            copy.deepcopy(node_information))
        if new_metadata:
            resp = requests.patch(
                self.SIGNALFX_REST_API + '/' + signalfx_objectid,
                params=new_metadata, headers=headers)
        else:
            self.logger.info('No new metadata is found for ' +
                             node_information['chefUniqueId'])

    def check_for_updates_in_metadata(self, current_data):
        """
        Read the data saved in the last run
        Compare it with the current metadata and pop unchanged items

        return: updated metadata
        """
        input_pickle = open(self.PICKLE_FILE, 'rb')
        self.logger.info('Reading previous metadata from ' + self.PICKLE_FILE)
        saved_metadata = pickle.load(input_pickle)
        input_pickle.close()
        if current_data['chefUniqueId'] not in saved_metadata:
            return current_data
        previous_data = saved_metadata[current_data['chefUniqueId']]
        for key in previous_data.keys():
            if key in current_data and current_data[key] == previous_data[key]:
                current_data.pop(key)
        current_data.pop('chefUniqueId')
        return current_data

    def get_signalfx_objectid(self, node_information, headers):
        """
        Get ObjectID for the chefUniqueId dimension from Signalfx

        return: the api response
        """
        params = {
            'query': 'chefUniqueId:' + node_information['chefUniqueId'],
            'getIDs': 'true'
        }
        resp = requests.get(self.SIGNALFX_REST_API,
                            params=params, headers=headers)
        if resp.status_code != 200:
            self.logger.error('Unable to get ID of' +
                              'chefUniqueId object from Signalfx')
            print(resp.raise_for_status())
            self.exit_now()
        return resp

    def read_config(self):
        """
        Read the configuration file
        """
        self.config = []
        with open(self.CONFIG_FILE, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if not line.startswith("#") and line != '\n':
                    attribute = line.rstrip('\n')
                    if self.check_property_name_syntax(attribute
                                                       .replace('.', '_')):
                        self.config.append(attribute)

    def check_property_name_syntax(self, attribute):
        """
        Check if the attribute name from the configuration file
        follows the pattern expected by Signalfx

        return: True or False
        """
        if not self.property_name_pattern.match(attribute):
            self.logger.error('Invalid attribute name '
                              + attribute
                              + '. Attribute names should follow '
                              + 'the regex pattern ^[a-zA-Z_][a-zA-Z0-9_-]*$')
            return False
        return True

    def exit_now(self):
        """
        Exit from the program with a message on the console
        """
        print("Error occured: logged into " + DEFAULT_LOG_FILE +
              "! Exiting...")
        sys.exit(1)

    def chef_api_get_request(self, endpoint):
        """
        Execute the Chef Server api's GET request for given endpoint
        """
        value = None
        try:
            value = self.api.api_request('GET', endpoint)
        except Exception:
            self.logger.error(
                'Unable to perform Chef api GET request', exc_info=True)
            self.exit_now()
        return value

    def collect_metadata_from_chef(self):
        """
        Get the current organization name and its nodes
        Get the metadata for each node
        """
        organization_details = self.chef_api_get_request('')
        self.organization = organization_details['name']
        nodes = self.chef_api_get_request('/nodes')
        for node_name in nodes.keys():
            self.get_node_information(node_name)

    def get_node_information(self, node_name):
        """
        Get node attributes(metadata) using Node.attributes of PyChef
        Store the values of the attributes selected by the user for each node
        """
        chefUniqueId = self.organization + "_" + node_name
        node_details = Node(node_name)
        node_information = {}
        node_information['chefUniqueId'] = chefUniqueId
        node_information['chef_environment'] = node_details.chef_environment
        for attribute in self.config:
            attribute_value = self.get_attribute_value(
                attribute, node_details)
            if attribute_value:
                attribute = self.adjust_attribute_name(attribute)
                node_information[attribute] = attribute_value
        self.nodes_metadata.append(node_information)

    def adjust_attribute_name(self, attribute):
        """
        Replace '.' by '_' in the attributes listed in the configuration file
        and return it
        """
        attribute = attribute.replace('.', '_')
        attribute = attribute.replace(' ', '')
        if not attribute.startswith('chef_'):
            attribute = 'chef_' + attribute
        return attribute

    def get_attribute_value(self, attribute, node_details):
        """
        Return the value of the given attribute
        """
        tokens = attribute.split('.')
        temp_value = node_details
        for token in tokens:
            try:
                temp_value = temp_value[token]
            except Exception:
                self.logger.error('Invalid attribute ' + attribute +
                                  ' is listed in '
                                  + self.CONFIG_FILE, exc_info=True)
                return None
        if isinstance(temp_value, dict):
            self.logger.error('Attribute value for ' +
                              attribute + ' cannot be a dictionary!')
            return None
        if isinstance(temp_value, list) and not (
                any(isinstance(x, dict) for x in temp_value)):
            return '$'.join(temp_value)
        return str(temp_value)


def get_argument_parser():
    """
    Create a parser object

    return: argparse.ArgumentParser() object
    """
    parser = argparse.ArgumentParser(description='Collects the metadata ' +
                                     'about Chef nodes and forwards' +
                                     'it to SignalFx.', add_help=True)

    parser.add_argument('--env-variable-name', action='store',
                        dest='ENV_VARIABLE_NAME',
                        default=DEFAULT_ENV_VARIABLE_NAME,
                        help='Set SIGNALFX_API_TOKEN with your ' +
                        'SIGNALFX_API_TOKEN as value in your environment ' +
                        'variables. You can change the environment variable ' +
                        'name to look for, using this option.' +
                        'Default is ' + DEFAULT_ENV_VARIABLE_NAME, type=str)
    parser.add_argument('--config-file', action='store',
                        dest='CONFIG_FILE',
                        default=DEFAULT_CONFIG_FILE,
                        help='File with the list of attributes to be ' +
                        'attached to \'ChefUniqueId\' on SignalFx. ' +
                        'Default is ' + DEFAULT_CONFIG_FILE, type=str)
    parser.add_argument('--log-file', action='store',
                        dest='LOG_FILE',
                        default=DEFAULT_LOG_FILE,
                        help='Log file to store the messages. ' +
                        'Default is ' + DEFAULT_LOG_FILE, type=str)
    parser.add_argument('--log-handler', action='store',
                        dest='LOG_HANDLER',
                        default=DEFAULT_LOG_HANDLER,
                        choices=('stdout', 'logfile'),
                        help='Choose between \'stdout\' and \'logfile\'' +
                        'to redirect log messages. ' +
                        'Use --log-file to change the default log file ' +
                        ' location. Default to this option is ' +
                        DEFAULT_LOG_HANDLER, type=str)
    parser.add_argument('--signalfx-rest-api', action='store',
                        dest='SIGNALFX_REST_API',
                        default=DEFAULT_SIGNALFX_REST_API,
                        help='SignalFx REST API endpoint. ' +
                        'Default is ' + DEFAULT_SIGNALFX_REST_API, type=str)
    parser.add_argument('--pickle-file', action='store',
                        dest='PICKLE_FILE',
                        default=DEFAULT_PICKLE_FILE,
                        help='Pickle file to store the last retrieved ' +
                        'metadata. Default is ' + DEFAULT_PICKLE_FILE,
                        type=str)
    parser.add_argument('--sleep-duration', action='store',
                        dest='SLEEP_DURATION',
                        default=DEFAULT_SLEEP_DURATION,
                        help='Specify the sleep duration. Default is 60' +
                        'Default is ' + str(DEFAULT_SLEEP_DURATION), type=int)
    parser.add_argument('--use-cron', action="store_true",
                        default=False,
                        help='use this option if you want to run the ' +
                        ' program using Cron. Default is False, meaning ' +
                        'that program will use sleep(SLEEP_DURATION) ' +
                        'instead of cron')

    return parser


def main(argv):
    """
    Parse command line arguments and start the program.
    """
    parser = get_argument_parser()
    user_args = vars(parser.parse_args(argv))

    # Get the SIGNALFX_API_TOKEN from environment variables
    try:
        SIGNALFX_API_TOKEN = os.environ[user_args['ENV_VARIABLE_NAME']]
    except Exception:
        print("Error: Unable to find a variable with the name \"" +
              user_args['ENV_VARIABLE_NAME'] + "\" in your environment")
        print("For help, look for --env-variable-name option in the guide\n")
        parser.print_help()
        sys.exit(1)

    user_args.pop('ENV_VARIABLE_NAME')
    user_args['SIGNALFX_API_TOKEN'] = SIGNALFX_API_TOKEN
    use_cron = user_args.pop('use_cron', False)

    m = Metadata(**user_args)
    if use_cron:
        m.run()
    else:
        while True:
            m.run()
            sleep(m.SLEEP_DURATION)

if __name__ == "__main__":
    main(sys.argv[1:])
