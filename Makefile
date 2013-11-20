#PREFIX = `python -c "from invenio.config import CFG_PREFIX; print CFG_PREFIX"`
PREFIX = $(CFG_INVENIO_PREFIX)
LIBDIR = $(PREFIX)/lib
ETCDIR = $(PREFIX)/etc
WWWDIR = $(PREFIX)/var/www
#APACHE = `python -c "from invenio.bibtask import guess_apache_process_user; print guess_apache_process_user()"`
APACHE = wziolek
INSTALL = install -g $(APACHE) -m 775

scoap3dtdsdir = $(ETCDIR)/scoap3dtds
scoap3dtds_DATA = ja5_art510.zip ja5_art520.zip si510.zip

scoap3utils = scoap3utils.py
scoap3tests = scoap3_unit_tests.py


install:
	$(INSTALL) -d $(scoap3dtdsdir)
	$(INSTALL) -t $(scoap3dtdsdir) $(scoap3dtds_DATA)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(scoap3utils)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(scoap3tests)
	$(INSTALL) -t $(WWWDIR) robots.txt
	$(INSTALL) -t $(WWWDIR)/img scoap3_logo.png favicon.ico invenio_scoap3.css

install-conf:
	$(INSTALL) -t $(ETCDIR) invenio-local.conf
