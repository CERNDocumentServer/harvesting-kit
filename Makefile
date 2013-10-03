PREFIX = `python -c "from invenio.config import CFG_PREFIX; print CFG_PREFIX"`
LIBDIR = $(PREFIX)/lib
ETCDIR = $(PREFIX)/etc
WWWDIR = $(PREFIX)/www
APACHE = `python -c "from invenio.bibtask import guess_apache_process_user; print guess_apache_process_user()"`
INSTALL = install -g $(APACHE) -m 775

scoap3dtdsdir = $(ETCDIR)/scoap3dtds
scoap3dtds_DATA = ja5_art510.zip ja5_art520.zip si510.zip

scoap3utils = scoap3utils.py


install:
	$(INSTALL) -m 664 $(scoap3dtds_DATA) $(scoap3dtdsdir)
	$(INSTALL) -m 664 $(scoap3utils) $(LIBDIR)/invenio
	$(INSTALL) -m 664 robots.txt $(WWWDIR)
	$(INSTALL) -m 664 scoap3_logo.png favicon.ico invenio_scoap3.css $(WWWDIR)/img

install-conf:
	$(INSTALL) -m 664 invenio-local.conf $(ETCDIR)
