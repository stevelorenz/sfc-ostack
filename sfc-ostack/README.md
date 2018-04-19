# **SFC-Ostack**: Simple Research Framework for SFC on OpenStack #

**TODO**: Add descriptions here.

## Getting Started ##

### Installing

1. Download the repository

```
$ git clone https://github.com/stevelorenz/sfc-ostack.git
```

2. The **SFC-Ostack** can be installed using setup.py, currently not uploaded to PyPi.

```
$ python3  sfc-ostack/sfc-ostack/setup.py
```

3. Check the installation via pip

```
$ pip list | grep sfc-ostack
```

### Examples

- An example of configuration template (in YAML format) can be found in **./share/sfcostack_tpl_sample.yaml**

- Examples of initial scripts for service function programs (SFPGs) can be found in **./share/*.sh**.

    1. **init_lk_forwarding.sh**: Init-script for Linux Kernel IP forwarding.
    2. **init_raw_sock.sh**: Init-script for handling sfc-packets with raw sockets.

- An example of implementing raw sockets based SFPG can be found in **./demo/sfp/fwd_forback.py**

- A demo of sfc-ostack basic functionalities can be found in **./demo/show_func/show_func.py**

## Contributing ##

**TODO**

## Authors ##

- Zuo Xiang (xianglinks@gmail.com)
