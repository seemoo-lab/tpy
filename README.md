# TPy: A Python Framework to Automate Distributed Network Research Experiments

This project contains scripts to remotely control networked devices to run network experiments.
The project essentially consists of two components a generic **node** and a **controller** component, which are designed to run on the network devices and a central orchestrator, respectively.
The **node** is modularized so that it can support generic testbeds with different wireless hardware (e.g., regular Wi-Fi cards, or even WiGig links) and software (e.g., routing protocols, measurement tools such as `iperf` or `ping`, and special operating systems such as OpenWrt).
The code requires Python3, and a working SSH connection from the **controller** to the **node** devices.

## WARNING
We do not take any responsibility of what could happen to your devices by running our commands. Some configurations are known to cause damage to your hardware. It is your responsibility to get familiar with your devices and judge the risks of running TPy.

## Installation

In the project root directory, simply run

```bash
make
```

This will build and package the **node** and install the **controller** as a Python package.
The installable **node** package is put in the **controller** package as a resource, so that the **controller** can deploy (see below) the package on the devices. 


## Quick Start Guide

For a minimal working example, we need to configure (a) the **controller** as well as (b) the **node**s, (c) start the **node** instances,
(d) connect the **controller** to the **nodes**, and finally (e) start interacting with them.

### Configure the *Controller*

Create a device configuration that represents your testbed (see `default-devices.conf`).
The most basic configuration file consists of a node `name` (section title) and a `host`:`port` pair under which the **node** will be reachable. Example:

```
[DEFAULT]                     # Default settings for all nodes, can be overridden in node-specific section
port = 42337                  # Listening port of the nodes

[NODE1]                       # the 'name' of the first node
host = 10.0.0.1               # the node's external IP address

[NODE2]                       # the 'name' of the second node
host = hostname2.example.org  # can also be a resolvable DNS name
```

### Configure the *Node*s

Each **node** instance will start with its own configuration.
This is how a sample `node.conf` file could look like:

```
[TPyNode]                       # Section for the generic node component
logfile = /var/log/tpynode.log  # Path to the log file
pidfile = /var/run/tpynode.pid  # Path to the pid file
host = 0.0.0.0                  # Listening interface, if set to '0.0.0.0' will listen on all network interfaces
port = 42337                    # Listening port

[Ping]                          # a module without any configuration
module = Ping                   # if module 'name' is the same, this is redundant 

[AdHoc1]                        # control an ad hoc Wi-Fi interface
module = AdHocInterface         # module 'name'
interface = wlp1s0              # name of the Wi-Fi interface
ipaddress = 10.0.0.1            # IP address of the interface
channel = 1                     # channel of the ad hoc network
bssid = c0:ff:ee:c0:ff:ee       # fixed BSSID
ssid = erlab                    # SSID of the network

[AdHoc2]                        # a second ad hoc interface
module = AdHocInterface         # module 'name'
interface = wlp5s0              # name of the Wi-Fi interface
...
```

Note that modules need to be explicitly configured in the `node.conf`.
If the configuration file is empty, no modules will be available. 

### Deploy and Start the *Node*s

The **controller** installs with a command line tool that allows for deploying and (re)starting the Python node instance. 

```bash
tpy deploy -d devices.conf
tpy restart -d devices.conf
```

If you are developing new modules, simply prepend a `make` to the above two commands.

### Connect to the *Node*s

To establish a connection from Python, run

```python
import tpycontrol as tpy

# read the device configuration
devices = tpy.Devices('devices.conf')

# connect to the devices and initialize the controller
tc = tpy.TPyControl(devices)
```

### Interact with the *Node*s

After initializing the **controller**, we can start interacting with the remote **nodes**. Example:

```python
# start ad hoc interface on all nodes
for n in tc.nodes.values():
    # the exported modules (e.g., AdHoc1) are accessible via properties of the remote node instance
    n.AdHoc1.up()

# Access a single node
tc.node('NODE2').Ping.ping('10.0.0.1')
```



## Code Structure

* `controller/`  the **controller** component
  * `tpycontrol/` the Python code
    * `utils/` utilities that facilitiate common interaction tasks with the **node**s
    * `cli.py` command line wrapper for `deploy.py`
    * `deploy.py` scripts to deploy and restart **node**s via SSH
    * `devices.py` parses a `devices.conf`
    * `tpycontrol.py` the **controller**
    * `tpyremotemodule.py` proxy to a **node**'s remote module
    * `tpyremotenode.py` proxy to a remote **node** that has remote modules
* `node/` the **node** component
  * `tpynode/` the Python code
    * `data/` arbitrary files that will be installed with the node component
      * `sample.conf` an exemplary node configuration file
    * `modules/` specific functionality that the node will be able to provide
      * `__init.py__` exports all modules (*need to add new modules here!*)
      * `abstractmodule.py` the superclass of all modules
      * `ping.py` a wrapper for the `ping` tool
      * ...
    * `daemon.py` runs `tpynode.py` as a daemon 
    * `tpynode.py` the node implementation
* `default-devices.conf` an example device configuration
* `Makefile` to build/package/(un)install/... this project 

## Talon Tools
This software has been released as part of [Talon Tools: The Framework for Practical IEEE 802.11ad Research](https://seemoo.de/talon-tools/). Any use of it, which results in an academic publication or other publication which includes a bibliography is encouraged to appreciate this work and include a citation the Talon Tools project and any of our papers. You can find more information on the [project page](https://seemoo.de/talon-tools/).

## Our papers using the TPy Framework
* Daniel Steinmetzer, Milan Stute, and Matthias Hollick.
  **TPy: A Lightweight Framework for Agile Distributed Network Experiments.** 
  *12th International Workshop on Wireless Network Testbeds, Experimental evaluation & CHaracterization (WiNTECH ’18)*, October 2018, New Delhi, India.

## Reference the TPy Project
Any use of the Software which results in an academic publication or other publication which includes a bibliography must include citations to our project. The project should be cited with our paper as follows:

```
@inproceedings{Steinmetzer2018,
  author = {Steinmetzer, Daniel and Stute, Milan and Hollick, Matthias},
  title = {{TPy: A Lightweight Framework for Agile Distributed Network Experiments}},
  booktitle = {12th International Workshop on Wireless Network Testbeds, Experimental evaluation {\&} CHaracterization (WiNTECH '18)},
  month = {10},
  year = {2018}
  publisher = {ACM},
  address = {New Delhi, India},
}

```

## Give us Feedback
We want to learn how people use this software and what aspects we might improve. Please report any issues or comments using the bug-tracker and do not hesitate to approach us via e-mail.

## Contact
* [Daniel Steinmetzer](https://seemoo.tu-darmstadt.de/dsteinmetzer) <<dsteinmetzer@seemoo.tu-darmstadt.de>>
* [Milan Stute](https://seemoo.tu-darmstadt.de/mstute) <<mstute@seemoo.tu-darmstadt.de>>

## Powered By
<a href="https://www.seemoo.tu-darmstadt.de">![SEEMOO logo](https://seemoo-lab.github.io/talon-tools/logos/seemoo.png)</a> &nbsp;
<a href="https://www.nicer.tu-darmstadt.de">![NICER logo](https://seemoo-lab.github.io/talon-tools/logos/nicer.png)</a> &nbsp;
<a href="https://www.crossing.tu-darmstadt.de">![CROSSING logo](https://seemoo-lab.github.io/talon-tools/logos/crossing.jpg)</a>&nbsp;
<a href="https://www.crisp-da.de">![CRSIP logo](https://seemoo-lab.github.io/talon-tools/logos/crisp.jpg)</a>&nbsp;
<a href="http://www.maki.tu-darmstadt.de/">![MAKI logo](https://seemoo-lab.github.io/talon-tools/logos/maki.png)</a> &nbsp;
<a href="https://www.cysec.tu-darmstadt.de">![CYSEC logo](https://seemoo-lab.github.io/talon-tools/logos/cysec.jpg)</a>&nbsp;
<a href="https://www.tu-darmstadt.de/index.en.jsp">![TU Darmstadt logo](https://seemoo-lab.github.io/talon-tools/logos/tudarmstadt.png)</a>&nbsp;
