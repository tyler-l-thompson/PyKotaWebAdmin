True# PyKotaWebAdmin

PyKotaWebAdmin is a web interface for administering PyKota

see http://www.pykota.com/

This tool is a python flask web app built for use at Western Michigan University, but can be used in any PyKota environment. 


## Installation
Before installing PyKotaWebAdmin you must already have cups and PyKota setup on the server you want to run it on.
	PyKota installation documentation: http://www.pykota.com/wiki/how-to-install-pykota-on-ubuntu-10-04-x86


#### OS Requirements
Only been tested on Ubuntu Server 10.04 or greater, but others may work


#### Dependencies
See PyKotaWebAdmin/config/apt-packages.txt
and PyKotaWebAdmin/config/pip-packages.txt
		
Install pakages in these files manually. Installer script coming soon!


#### Setup
1.Once PyKota, Cups and all dependencies have been installed, put the program in the /opt directory

`cd /opt`
	
`git clone https://octlabs.org/tyler/PykotaWebAdmin.git`

2.Then symlink the init script so that the program runs at startup

`chmod 755 /opt/PyKotaWebAdmin/pykotawebadmin.init`
	
`ln -s /opt/PyKotaWebAdmin/configs/pykotawebadmin.init /etc/init.d/pykotawebadmin`
	
`update-rc.d pykotawebadmin defaults`

3.Start the service

`service pykotawebadmin start`


## Updating
Currently updates must be initiated manually, but the init scripts can do it for you.

```service pykotawebadmin update```
	
or
	
```/opt/PyKotaWebAdmin/configs/pykotawebadmin.init update```
		

## Config
PyKotaWebAdmin/config/webadmin.conf

Edit variables in this file to match your specific setup
#### Defaults:

Web Port: 80

SSL: disabled

Web Login Username: admin

Web Login Password: admin


## Bugs
Bug reports can be sent to tyler.l.thompson@wmich.edu
