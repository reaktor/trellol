Trellol
================

This is a module which uses Trello's (https://trello.com/) API and allows to move Trello cards with Leap Motion gestures as an alternative to using mouse. User can use tap gestures to select one card at a time and move selected card onto a new location. The changes that are made using Trellol UI update corresponding Trello board cards. 

Trellol is written in Python and UI is implemented with PyQt. Leap Motion gesture control should work on most Linux systems. 

## DOCUMENTATION

Leap motion mouse control depends on pymouse. It is a cross-platform python module which can be found at https://github.com/SavinaRoja/PyUserInput. 

Trellol also uses Python wrapper Trolly (https://github.com/plish/Trolly) for Trello API calls. 

## SETUP

This software requires python v.2.7.2?? or higher, PyQt4 and httplib2 installed.

You will need several things from Trello to get started:
	Application key (used by Trello to identify the application making the request) (https://trello.com/docs/gettingstarted/index.html#getting-a-token-from-a-user)
	Read/write user authorization token (https://trello.com/docs/gettingstarted/index.html#getting-an-application-key)
	Board id 

These configuration values should be set in conf file in Trellol.

* Linux setup
   
   Install Xlib

   Install Leap Motion SDK, particularly the leap motion daemon, 'leapd'
   > sudo apt-get install python-dev python-sip python-qt4
   > sudo pip install Trolly 

* OS X setup

   Make sure you have Quartz, AppKit installed
   > sudo python setup.py install

##LAUNCH

To run the program open Trellol in terminal and run:
	> ./launch

Note: If you are running program under Linux, first make sure you have leap motion daemon running:
   > leapd & 

## LICENSE

This program is licensed under ??? license