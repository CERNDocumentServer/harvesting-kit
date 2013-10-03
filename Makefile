PREFIX = `python -c "from invenio.config import CFG_PREFIX; print CFG_PREFIX"`
# PREFIX = /opt/invenio
LIBDIR = $(PREFIX)/lib
ETCDIR = $(PREFIX)/etc
WWWDIR = $(PREFIX)/var/www
APACHE = `python -c "from invenio.bibtask import guess_apache_process_user; print guess_apache_process_user()"`
# APACHE = www-data
INSTALL = install -g $(APACHE) -m 775

scoap3dtdsdir = $(ETCDIR)/scoap3dtds
scoap3dtds_DATA = ja5_art510.zip ja5_art520.zip si510.zip

scoap3utils = scoap3utils.py


install:
	$(INSTALL) -d $(scoap3dtdsdir)
	$(INSTALL) -t $(scoap3dtdsdir) $(scoap3dtds_DATA)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(scoap3utils)
	$(INSTALL) -t $(WWWDIR) robots.txt
	$(INSTALL) -t $(WWWDIR)/img scoap3_logo.png favicon.ico invenio_scoap3.css

install-conf:
	$(INSTALL) -t $(ETCDIR) invenio-local.conf
