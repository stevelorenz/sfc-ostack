# Test Demo for networking_sfc  #

Used for testing the functionality of the OpenStack networking_sfc extension.

## Usage ##

This demo use [openstack-pythonsdk](https://wiki.openstack.org/wiki/SDK-Development/PythonOpenStackSDK) to work with
OpenStack's services. The [HEAT template](https://docs.openstack.org/heat/latest/template_guide/hot_guide.html) is used
to create the test topology. Following python scripts should run in the correct order to setup the test demo.

#### 1. Modify ./conf.py

Contains all essential config-parameters for cloud and tests.

#### 2. Run ./pre_build_topo.py

Run pre-steps before building the test topology. Including creation of a ubuntu-cloud image, a key-pair and a security
group.

#### 3. Run ./build_topo.py

Use HEAT client and ./test_topo.yaml HOT template to create the test topology, Including instances, networks, floating
IPs and neutron ports.

#### 4. When the topology(called stacks in HEAT) is already built(Check with HEAT Orchestration label). Run ./post_build_topo.py

Run configs after finishing building the test topology

1. Get and store all floating IPs of instances(./remote_instance.txt), used for SSH
2. Config VMs for chaining via SSH, Check the `_config_chn_ins` function: Enable kernel IP forwarding and add static
   routing rules.

#### 5. Run ./test_sfc_demo.py to create flow classifier and port chain

Command line tool to create and delete SFC resources. For example `./test_sfc_demo.py -fc` will create a UDP traffic
flow classifier with destination port 9999.

#### 6. Run bash ./tmux-instance.sh to create a new instance access session
