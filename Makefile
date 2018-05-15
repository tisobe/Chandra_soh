# -*- makefile -*-

TASK = chandra_soh
VERSION = 1.0

ROOT = /home/mta/proj

# Define generic installation paths
ifndef INSTALL
  INSTALL = $(ROOT)
endif

ifndef TASK
  TASK = share
endif

ifndef INSTALL_PERLLIB
  INSTALL_PERLLIB = $(INSTALL)/lib/perl
endif

ifndef INSTALL_IDL
  INSTALL_IDL = $(INSTALL)/idl
endif

ifndef INSTALL_SHARE
  INSTALL_SHARE = $(INSTALL)/share/$(TASK)
endif

ifndef INSTALL_CONFIG
  INSTALL_CONFIG = $(INSTALL)/share/$(TASK)/config
endif

SHARE = copy_data_from_occ.py
CONFIG = config/.*wait config/.*alert
IDL = idl/*.pro
PERLLIB = snap.pm snap_format.pm comps.pm check_state.pm check_state_test.pm check_state_alerts.pm check_state_noalerts.pm


# Installation
ifdef SHARE
	mkdir -p $(INSTALL_SHARE)
	rsync --times --cvs-exclude $(SHARE) $(INSTALL_SHARE)/
endif
ifdef CONFIG
	mkdir -p $(INSTALL_SHARE)
	rsync --times --cvs-exclude $(CONFIG) $(INSTALL_CONFIG)/
endif
ifdef PERLLIB
	mkdir -p $(INSTALL_PERLLIB)
	rsync --times --cvs-exclude $(PERLLIB) $(INSTALL_PERLLIB)/
endif
ifdef IDL
	mkdir -p $(INSTALL_IDL)
	rsync --times --cvs-exclude $(IDL) $(INSTALL_IDL)/
endif

	mkdir -p /home/mta/chandra_soh-share

# Create a distribution tar file for this program
dist:
        mkdir $(TASK)-$(VERSION)
        rsync -aruvz --cvs-exclude --exclude $(TASK)-$(VERSION) * $(TASK)-$(VERSION)
        tar cvf $(TASK)-$(VERSION).tar $(TASK)-$(VERSION)
        gzip --best $(TASK)-$(VERSION).tar
        rm -rf $(TASK)-$(VERSION)/

