Sumo + Twisted
==============

This is a simple project which provides a web interface to control a Sumo Drone.

[Parrot documentation]: (http://developer.parrot.com/docs/SDK3/)

Requirements:
-------------

	Twisted >= 15.5.0

Run:
----

	# Turn Sumo on
	sudo connect.sh # Establish a Wifi connection with Sumo
	python sumo.py # Start Twisted server and interface


The main module sends a JSON payload to trigger a UDP communication with the drone.
It also parses data received from the drone, and sends new data to the drone.
The device.py module is use to generate data sent to the Sumo.
The iface.py module regroups the HTTP resources used for the web interface.
