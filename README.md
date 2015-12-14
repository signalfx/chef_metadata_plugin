# Collect-Chef-Metadata

CollectChefMetadata.py collects the metadata about Chef nodes and forwards it
to SignalFx.

It queries Chef server API to collect the metadata and forwards only the
selected data to SignalFx using its REST API.

The metadata includes chef environment and other attributes listed on your
Chef server web UI.

## How to use

Steps:

Install the Chef cookbook(> set released version no. here) provided by
SignalFx to send your metrics.
On applying this cookbook, a custom dimension called as 'ChefUniqueId'
is created and sent from each of your nodes to SignalFx. The format of the
custom dimension value is <*your-organization-name*>_<*node-name*>

Set your SIGNALFX_API_TOKEN value in your environment variables. see
--env-variable-name option below for more information

Clone this repository into the directory which holds your '.chef' folder
because this program will search for and use your knife config to query
Chef Server API

Run the program

```shell
$python collect_chef_metadata.py
```

Help is available to customize the program execution

```shell
$python collect_chef_metadata.py -h
usage: collect_chef_metadata.py [-h] [--env-variable-name ENV_VARIABLE_NAME]
                                [--config-file CONFIG_FILE]
                                [--log-file LOG_FILE]
                                [--log-handler {stdout,logfile}]
                                [--signalfx-rest-api SIGNALFX_REST_API]
                                [--pickle-file PICKLE_FILE]
                                [--sleep-duration SLEEP_DURATION] [--use-cron]

Collects the metadata about Chef nodes and forwardsit to SignalFx.

optional arguments:
  -h, --help            show this help message and exit
  --env-variable-name ENV_VARIABLE_NAME
                        Set SIGNALFX_API_TOKEN with your SIGNALFX_API_TOKEN as
                        value in your environment variables. You can change
                        the environment variable name to look for, using this
                        option. Default is SIGNALFX_API_TOKEN
  --config-file CONFIG_FILE
                        File with the list of attributes to be attached to
                        'ChefUniqueId' on SignalFx. Default is
                        ./configuration.txt
  --log-file LOG_FILE   Log file to store the messages. Default is
                        /tmp/ChefMetadata.log
  --log-handler {stdout,logfile}
                        Choose between 'stdout' and 'logfile'to redirect log
                        messages. Use --log-file to change the default log
                        file location. Default to this option is logfile
  --signalfx-rest-api SIGNALFX_REST_API
                        SignalFx REST API endpoint. Default is
                        https://api.signalfx.com
  --pickle-file PICKLE_FILE
                        Pickle file to store the last retrieved metadata.
                        Default is ./pk_metadata.pk
  --sleep-duration SLEEP_DURATION
                        Specify the sleep duration (in seconds).Default is 60
  --use-cron            use this option if you want to run the program using
                        Cron. Default is False, meaning that program will run
                        in a loop using sleep(SLEEP_DURATION) instead of cron
```

Select the Chef attributes that you want to send to SignalFx by listing them
in configuration.txt
(Follow the instructions in configuration.txt to correctly list the attributes)

## How does it work

The program queries Chef Server API to get the organization and node names.
It will recreate the custom dimension 'ChefUniqueId' and then attaches the
selected metadata to this dimension on Signalfx.

Check [this](https://support.signalfx.com/hc/en-us/articles/201270489-Use-the-SignalFx-REST-API#metadata)
for more info on attaching metadata.

## Use Case

You are sending metrics to Signalfx from your Chef cluster nodes
and you want to create charts on Signalfx Dashboard using filters such as
the Chef environment of the nodes, tags applied to them or any Chef attributes.