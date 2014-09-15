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
	uninstall uninstall-notmodule \
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
	@mkdir -p $(WORKDIR)/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
	git archive --format=tar --prefix=$(PKGNAME)-$(VERSION)/ HEAD | gzip -9 > $(WORKDIR)/SOURCES/$(PKGNAME)-$(VERSION).tar.gz
	@echo "Done."

srpm: prep
	@echo
	@echo "Building source rpm..."
	rpmbuild --define="%_usrsrc $$PWD/$(WORKDIR)" --define="%_topdir %{_usrsrc}" -bs redhat/*.spec
	cp $(WORKDIR)/SRPMS/$(PKGNAME)-$(VERSION)-*.src.rpm $$PWD
	@echo "Done."

rpm: prep srpm
	@echo
	@echo "Building rpm..."
	rpmbuild --rebuild --define="%_usrsrc $$PWD/$(WORKDIR)" --define="%_topdir %{_usrsrc}" yumbootstrap-*.src.rpm
	cp $(WORKDIR)/RPMS/$(RPMARCH)/$(PKGNAME)-$(VERSION)-*.$(RPMARCH).rpm $$PWD
	@echo "Done."

install: prep1
	@if [ ! -f $(WORKDIR)/RPMS/$(RPMARCH)/$(PKGNAME)-$(VERSION)-*.$(RPMARCH).rpm ]; then \
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
	@echo "Installing $(PKGNAME)-$(VERSION)..."
	yum localinstall --nogpgcheck $(WORKDIR)/RPMS/$(RPMARCH)/$(PKGNAME)-$(VERSION)-*.$(RPMARCH).rpm

install-notmodule: prep1
	@if test $(RUNUSER) != "root"; then \
		echo; \
		echo "Install (notmodule) failed: You must be root user to install."; \
		exit 1; \
	fi;
	@echo
	@echo "Installing (notmodule) $(PKGNAME)-$(VERSION)..."
	install -D -m 755 bin/yumbootstrap $(DESTDIR)$(BINDIR)/yumbootstrap
	install -d -m 755 $(DESTDIR)$(SYSCONFDIR)/yumbootstrap/suites
	cp -R distros/* $(DESTDIR)$(SYSCONFDIR)/yumbootstrap/suites
	@echo "Done."

uninstall: prep1
	@if [[ ! "$(shell rpm -q $(PKGNAME)-$(VERSION) 2>/dev/null)" =~ ^($(PKGNAME)-$(VERSION)) ]]; then \
		echo; \
		echo "Uninstall failed: $(PKGNAME)-$(VERSION) RPM not installed."; \
		exit 1; \
	fi;
	@if [ $(RUNUSER) != "root" ]; then \
		echo; \
		echo "Uninstall failed: You must be root user to uninstall."; \
		exit 1; \
	fi;
	@echo
	@echo "Uninstalling $(PKGNAME)-$(VERSION)..."
	yum erase $(PKGNAME)-$(VERSION)
	@echo "Done."

uninstall-notmodule: prep1
	@if [ $(RUNUSER) != "root" ]; then \
		echo; \
		echo "Uninstall (notmodule) failed: You must be root user to uninstall."; \
		exit 1; \
	fi;
	@echo
	@echo "Uninstalling (notmodule) $(PKGNAME)-$(VERSION)..."
	-rm $(DESTDIR)$(BINDIR)/yumbootstrap
	-rm -rf $(DESTDIR)$(SYSCONFDIR)/yumbootstrap
	@echo "Done."

mostlyclean: prep1
	@echo
	@echo "Cleaning up work files..."
	python setup.py clean --all
	-rm -rf dist lib/*.egg-info 2>/dev/null || true
	-rm -rf $(WORKDIR) 2>/dev/null || true

clean-rpm: prep1
	@echo
	@echo -n "Removing rpms... "
	@-rm $(WORKDIR)/RPMS/$(RPMARCH)/*.$(RPMARCH).rpm 2>/dev/null || true
	@-rm $(PWD)/*.$(RPMARCH).rpm 2>/dev/null || true
	@echo "Done."

clean-srpm: prep1
	@echo
	@echo -n "Removing srpms... "
	@-rm $(WORKDIR)/SRPMS/*.src.rpm 2>/dev/null || true
	@-rm $(PWD)/*.src.rpm 2>/dev/null || true
	@echo "Done."

clean: clean-rpm clean-srpm mostlyclean
	@echo
	@echo "All clean."
	@echo

done-build:
	@echo
	@echo "Done building."
	@echo