PREFIX = `python -c "from invenio.config import CFG_PREFIX; print CFG_PREFIX"`
LIBDIR = $(PREFIX)/lib
ETCDIR = $(PREFIX)/etc
WWWDIR = $(PREFIX)/var/www
APACHE = `python -c "from invenio.bibtask import guess_apache_process_user; print guess_apache_process_user()"`
# APACHE = www-data
# APACHE = wziolek
INSTALL = install -g $(APACHE)

scoap3dtdsdir = $(ETCDIR)/scoap3dtds
scoap3dtds_DATA = ja5_art501.zip ja5_art510.zip ja5_art520.zip si510.zip si520.zip A++V2.4.zip jats-archiving-dtd-1.0.zip

scoap3utils = scoap3utils.py
scoap3tests = scoap3_unit_tests.py
contrast_out = contrast_out.py
contrast_out_config = contrast_out_config.py
contrast_out_utils = contrast_out_utils.py
elsevier_pkg = elsevier_package.py
springer_pkg = springer_package.py
hindawi_bibfilter = hindawi_bibfilter.py
springer_config = springer_config.py
templates = websearch_templates_scoap3.py webstyle_templates_scoap3.py

elsevier_data_files = $(PREFIX)/var/data/scoap3/elsevier
elsevier_ready_packages = $(PREFIX)/var/data/scoap3/elsevier/ready_pkgs
elsevier_tar_files = $(PREFIX)/var/data/scoap3/elsevier/tar_files
springer_data_files = $(PREFIX)/var/data/scoap3/springer
springer_tar_files = $(PREFIX)/var/data/scoap3/springer/tar_files


install:
	$(INSTALL) -d $(scoap3dtdsdir)
	$(INSTALL) -t $(scoap3dtdsdir) $(scoap3dtds_DATA)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(scoap3utils)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(scoap3tests)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(contrast_out)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(contrast_out_config)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(contrast_out_utils)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(elsevier_pkg)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(springer_pkg)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(springer_config)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(hindawi_bibfilter)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(templates)
	$(INSTALL) -t $(WWWDIR) robots.txt
	$(INSTALL) -t $(WWWDIR)/img scoap3_logo.png favicon.ico invenio_scoap3.css
	$(INSTALL) -d $(elsevier_data_files)
	$(INSTALL) -d $(elsevier_ready_packages)
	$(INSTALL) -d $(elsevier_tar_files)
	$(INSTALL) -d $(springer_data_files)
	$(INSTALL) -d $(springer_tar_files)

install-conf:
	$(INSTALL) -t $(ETCDIR) invenio-local.conf
