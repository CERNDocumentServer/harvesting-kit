PREFIX = `python -c "from invenio.config import CFG_PREFIX; print CFG_PREFIX"`
LIBDIR = $(PREFIX)/lib
ETCDIR = $(PREFIX)/etc
WWWDIR = $(PREFIX)/var/www
APACHE = `python -c "from invenio.bibtask import guess_apache_process_user; print guess_apache_process_user()"`
# APACHE = www-data
# APACHE = wziolek
INSTALL = install -g $(APACHE)

scoap3dtdsdir = $(ETCDIR)/scoap3dtds
scoap3dtds_DATA = ja5_art501.zip ja5_art510.zip ja5_art520.zip si510.zip si520.zip A++V2.4.zip jats-archiving-dtd-1.0.zip journal-publishing-dtd-2.3.zip

scoap3utils = scoap3utils.py
scoap3tests = scoap3_unit_tests.py
contrast_out = contrast_out.py
contrast_out_utils = contrast_out_utils.py
pkg = elsevier_package.py springer_package.py oup_package.py
hindawi_bibfilter = hindawi_bibfilter.py
configs = contrast_out_config.py springer_config.py oup_config.py
templates = websearch_templates_scoap3.py webstyle_templates_scoap3.py webinterface_layout.py
utils = jats_utils.py minidom_utils.py nlm_utils.py app_utils.py
bibtasklets = bst_springer.py bst_elsevier.py bst_oxford.py bst_doi_timestamp.py
bibcheck_plugins = crossref_timestamp.py iop_issn.py iop_arxive_fix.py arxiv_prefix.py
bibcheck_rules = rules.cfg
bibformat_elements = bfe_publi_info.py
bibformat_templates = Default_HTML_actions.bft Default_HTML_detailed.bft Default_HTML_brief.bft
www_scripts = nations.py

elsevier_data_files = $(PREFIX)/var/data/scoap3/elsevier
elsevier_ready_packages = $(PREFIX)/var/data/scoap3/elsevier/ready_pkgs
elsevier_tar_files = $(PREFIX)/var/data/scoap3/elsevier/tar_files
springer_data_files = $(PREFIX)/var/data/scoap3/springer
springer_tar_files = $(PREFIX)/var/data/scoap3/springer/tar_files
springer_epjc_files = $(PREFIX)/var/data/scoap3/springer/tar_files/EPJC
springer_jhep_files = $(PREFIX)/var/data/scoap3/springer/tar_files/JHEP
oxford_data_files = $(PREFIX)/var/data/scoap3/oxford
oxford_tar_files = $(PREFIX)/var/data/scoap3/oxford/tar_files
oxford_unpacked_files = $(PREFIX)/var/data/scoap3/oxford/unpacked_files


install:
	$(INSTALL) -d $(scoap3dtdsdir)
	$(INSTALL) -t $(scoap3dtdsdir) $(scoap3dtds_DATA)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(scoap3utils)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(scoap3tests)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(contrast_out)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(contrast_out_utils)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(pkg)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(configs)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(hindawi_bibfilter)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(templates)
	$(INSTALL) -t $(LIBDIR)/python/invenio $(utils)
	$(INSTALL) -t $(LIBDIR)/python/invenio/bibsched_tasklets $(bibtasklets)
	$(INSTALL) -t $(LIBDIR)/python/invenio/bibcheck_plugins $(bibcheck_plugins)
	$(INSTALL) -t $(ETCDIR)/bibcheck $(bibcheck_rules)
	$(INSTALL) -t $(ETCDIR)/bibformat/format_templates $(bibformat_templates)
	$(INSTALL) -t $(LIBDIR)/python/invenio/bibformat_elements $(bibformat_elements)

	$(INSTALL) -t $(WWWDIR) robots.txt
	$(INSTALL) -t $(WWWDIR) $(www_scripts)
	$(INSTALL) -t $(WWWDIR)/img scoap3_logo.png favicon.ico invenio_scoap3.css
	$(INSTALL) -d $(elsevier_data_files)
	$(INSTALL) -d $(elsevier_ready_packages)
	$(INSTALL) -d $(elsevier_tar_files)
	$(INSTALL) -d $(springer_data_files)
	$(INSTALL) -d $(springer_tar_files)
	$(INSTALL) -d $(springer_epjc_files)
	$(INSTALL) -d $(springer_jhep_files)
	$(INSTALL) -d $(oxford_data_files)
	$(INSTALL) -d $(oxford_tar_files)
	$(INSTALL) -d $(oxford_unpacked_files)

install-conf:
	$(INSTALL) -t $(ETCDIR) invenio-local.conf
