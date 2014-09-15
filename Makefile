#!/usr/bin/make -f
#
# Makefile for yumbootstrap.
#
DESTDIR =
PREFIX = /usr/local
BINDIR = $(PREFIX)/sbin
SYSCONFDIR = $(PREFIX)/etc

all: srpm rpm done-build

.PHONY: all default tarball egg prep prep1 prep2 srpm rpm \
	install install-notmodule \
	mostlyclean clean-rpm clean-srpm clean done-build

default: tarball

tarball:
	python setup.py sdist --formats=zip

egg:
	python setup.py bdist_egg

prep: prep1 prep2

prep1:
	$(eval VERSION := $(shell awk '$$1 == "%define" && $$2 == "_version" {print $$3}' redhat/*.spec))
	$(eval PKGNAME := $(shell awk 'tolower($$1) ~ /^name:/ {print $$2}' redhat/*.spec))
	$(eval RPMARCH := $(shell awk 'tolower($$1) ~ /^buildarch:/ {print $$2}' redhat/*.spec))
	$(eval WORKDIR := rpm-build)
	$(eval RUNUSER := $(shell whoami))
	@if test -z $(PKGNAME); then \
		echo; \
		echo "Build failed: Can't determine PKGNAME (Package Name)."; \
		exit 1; \
	fi;
	@if test -z $(VERSION); then \
		echo; \
		echo "Build failed: Can't determine VERSION (Package Version)."; \
		exit 1; \
	fi;
	@if test -z $(RPMARCH); then \
		echo; \
		echo "Build failed: Can't determine RPMARCH (RPM architecture)."; \
		exit 1; \
	fi;
	@echo "BUILD PACKAGE: $(PKGNAME)-$(VERSION) ($(RPMARCH))"

prep2: prep1
	@echo
	@echo "Setting up build environment..."
	@-rm -rf $(WORKDIR) 2>/dev/null || true
	@mkdir -p $(WORKDIR)/rpm/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
	@# extract HEAD from local repo, output as a tar with a prefix directory of
	@# PKGNAME-VERSION (e.g. yumbootstrap-0.0.03) then gzip archive and save into
	@# rpm-build/rpm/SOURCES directory.
	git archive --format=tar --prefix=$(PKGNAME)-$(VERSION)/ HEAD | gzip -9 > $(WORKDIR)/rpm/SOURCES/$(PKGNAME)-$(VERSION).tar.gz
	@sleep 1
	@echo "Done."

srpm: prep
	@echo
	@echo "Building source rpm..."
	rpmbuild --define="%_usrsrc $$PWD/$(WORKDIR)" --define="%_topdir %{_usrsrc}/rpm" -bs redhat/*.spec
	cp rpm-build/rpm/SRPMS/$(PKGNAME)-$(VERSION)-*.src.rpm $$PWD
	@sleep 1
	@echo "Done."

rpm: prep srpm
	@echo
	@echo "Building rpm..."
	rpmbuild --rebuild --define="%_usrsrc $$PWD/$(WORKDIR)" --define="%_topdir %{_usrsrc}/rpm" yumbootstrap-*.src.rpm
	cp rpm-build/rpm/RPMS/noarch/$(PKGNAME)-$(VERSION)-*.$(RPMARCH).rpm $$PWD
	@sleep 1
	@echo "Done."

install: prep1
	@if [ ! -f $(WORKDIR)/rpm/RPMS/noarch/$(PKGNAME)-$(VERSION)-*.$(RPMARCH).rpm ]; then \
		echo; \
		echo "Install failed: Run \"make rpm\" first."; \
		exit 1; \
	fi;
	@if test $(RUNUSER) != "root"; then \
		echo; \
		echo "Install failed: You must be root user to install."; \
		exit 1; \
	fi;
	@echo
	@echo "Installing yumbootstrap..."
	yum localinstall --nogpgcheck rpm-build/rpm/RPMS/noarch/$(PKGNAME)-$(VERSION)-*.$(RPMARCH).rpm

install-notmodule: prep1
	install -D -m 755 bin/yumbootstrap $(DESTDIR)$(BINDIR)/yumbootstrap
	install -d -m 755 $(DESTDIR)$(SYSCONFDIR)/yumbootstrap/suites
	cp -R distros/* $(DESTDIR)$(SYSCONFDIR)/yumbootstrap/suites

mostlyclean: prep1
	@echo
	@echo "Cleaning up work files..."
	python setup.py clean --all
	-rm -rf dist lib/*.egg-info 2>/dev/null || true
	-rm -rf $(WORKDIR) 2>/dev/null || true

clean-rpm: prep1
	@echo
	@echo -n "Removing rpms... "
	@-rm $(WORKDIR)/rpm/RPMS/noarch/*.rpm 2>/dev/null || true
	@-rm $(PWD)/*.rpm 2>/dev/null || true
	@sleep 1
	@echo "Done."

clean-srpm: prep1
	@echo
	@echo -n "Removing srpms... "
	@-rm $(WORKDIR)/rpm/SRPMS/*.srpm 2>/dev/null || true
	@-rm $(PWD)/*.srpm 2>/dev/null || true
	@sleep 1
	@echo "Done."

clean: clean-rpm clean-srpm mostlyclean
	@echo
	@echo "All clean."
	@echo

done-build:
	@echo
	@echo "Done building."
	@echo