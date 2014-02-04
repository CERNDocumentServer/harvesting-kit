harvesting-kit
==============

A kit containing various utilities and scripts related to content harvesting used in Invenio Software (http://invenio-software.org) instances such as INSPIRE and SCOAP3.

Requires most recent version of Invenio Software (http://invenio-software.org) installed.

INSTALL
=======

$ python setup.py install

CONFIGURATION
=============

Optional config variables can be overwritten in invenio-local.conf:

CFG_CONTRASTOUT_DOWNLOADDIR = /opt/invenio/var/data/scoap3/elsevier
CFG_SPRINGER_DOWNLOADDIR = /opt/invenio/var/data/scoap3/springer
CFG_OXFORD_DOWNLOADDIR = /opt/invenio/var/data/scoap3/oxford
