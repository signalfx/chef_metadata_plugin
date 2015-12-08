# chef_metadata_plugin

This python program queries Chef Server API to get the metadata about the nodes in the Chef cluster and forwards the configured values to the Signalfx through its REST API. The metadata includes chef environment and other attributes listed on your Chef server web UI.

When you install the Chef cookbook provided by Signalfx to send metrics, a custom dimension called 'ChefUniqueId' is created and sent from each of your nodes. The format of the custom dimension is <*your-organization-name*>_<*node-name*>

The program will query Chef Server API to get the organization name and node names. It will recreate the custom dimensions and then attaches the metadata to this dimension on Signalfx. Check [this](https://support.signalfx.com/hc/en-us/articles/201270489-Use-the-SignalFx-REST-API#metadata) to know how it's done.

You can configure the attached metadata by listing the Chef attributes in configuration.txt (Follow the instructions inside configuration.txt to correctly list your needs)

Before executing this command, ensure that you have the Signalfx Chef Cookbook (> set released version no. here) installed on your Chef cluster. Execute the below command as root to start the program.

```
python ChefMetadata.py -t <your-access-token>
```

A use case can be described as below:
Suppose, you are sending metrics to Signalfx from your Chef cluster nodes and you want to design charts on Signalfx Dashboard using filters such as the Chef environment of the nodes, tags applied to the nodes or any Chef metadata, then this program will come in handy.
