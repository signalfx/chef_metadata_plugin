# Collect-Chef-Metadata

CollectChefMetadata.py collects the metadata about Chef nodes and forwards it
to SignalFx.

It queries Chef server API to collect the metadata and forwards only the
selected data to SignalFx using its REST API.

The metadata includes chef environment and other attributes listed on your
Chef server web UI.

## How to use

Install the Chef cookbook(> set released version no. here) provided by
SignalFx to send your metrics

By default, a custom dimension called as 'ChefUniqueId' is created and sent
from each of your nodes. The format of the custom dimension value is
<*your-organization-name*>_<*node-name*>

Then, run the program

```shell
python CollectChefMetadata.py -t <SIGNALFX_API_TOKEN>
```

Select the Chef attributes of your choice by listing them in configuration.txt
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