import unittest
import collect_chef_metadata
import os


class Test_collect_chef_metadata(unittest.TestCase):

    def test_SIGNALFX_API_TOKEN_IN_ENV(self):
        """
        Testing for the absense of SIGNALFX_API_TOKEN
        in the environment variables.
        We will get help on the stdout here.
        """
        with self.assertRaises(SystemExit) as cm:
            collect_chef_metadata.main([])
        self.assertEqual(cm.exception.code, 1)

    # @unittest.skip("temporarily disabled")
    def test_argument_parser_for_default_parameters(self):
        """
        Check if the parser is correctly setting the default parameters
        """
        os.environ['SIGNALFX_API_TOKEN'] = 'abcdefghijk'
        argv = []
        parser = collect_chef_metadata.getArgumentParser()
        args = vars(parser.parse_args(argv))
        self.assertNotEqual(args, None)
        self.assertEqual(args['CONFIG_FILE'],
                         collect_chef_metadata.DEFAULT_CONFIG_FILE)
        self.assertEqual(args['LOG_FILE'],
                         collect_chef_metadata.DEFAULT_LOG_FILE)
        self.assertEqual(args['SIGNALFX_REST_API'],
                         collect_chef_metadata.DEFAULT_SIGNALFX_REST_API)
        self.assertEqual(args['PICKLE_FILE'],
                         collect_chef_metadata.DEFAULT_PICKLE_FILE)
        self.assertEqual(args['SLEEP_DURATION'],
                         collect_chef_metadata.DEFAULT_SLEEP_DURATION)
        self.assertEqual(args['ENV_VARIABLE_NAME'],
                         collect_chef_metadata.DEFAULT_ENV_VARIABLE_NAME)
        self.assertEqual(args['LOG_HANDLER'],
                         collect_chef_metadata.DEFAULT_LOG_HANDLER)

    # @unittest.skip("temporarily disabled")
    def test_argument_parser_for_custom_parameters(self):
        os.environ['MY_SIGNALFX_API_TOKEN'] = 'abcdefghijk'
        custom_argv = ['--config-file', 'my_configuration.txt',
                       '--log-file', '/tmp/dummy_log_file',
                       '--signalfx-rest-api',
                       'http://lab-api.corp.signalfuse.com:8080',
                       '--pickle-file', 'my_pk_metadata.pk',
                       '--sleep-duration', '10',
                       '--env-variable-name', 'MY_SIGNALFX_API_TOKEN',
                       '--log-handler', 'stdout'
                       ]
        parser = collect_chef_metadata.getArgumentParser()
        args = vars(parser.parse_args(custom_argv))
        self.assertNotEqual(args, None)
        self.assertEqual(args['CONFIG_FILE'], 'my_configuration.txt')
        self.assertEqual(args['LOG_FILE'], '/tmp/dummy_log_file')
        self.assertEqual(args['SIGNALFX_REST_API'],
                         'http://lab-api.corp.signalfuse.com:8080')
        self.assertEqual(args['PICKLE_FILE'], 'my_pk_metadata.pk')
        self.assertEqual(args['SLEEP_DURATION'], 10)
        self.assertEqual(args['ENV_VARIABLE_NAME'], 'MY_SIGNALFX_API_TOKEN')
        self.assertEqual(args['LOG_HANDLER'], 'stdout')


if __name__ == '__main__':
    unittest.main()
