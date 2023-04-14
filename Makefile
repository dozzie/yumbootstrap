#!/usr/bin/make -f

DESTDIR =
PREFIX = /usr/local
BINDIR = $(PREFIX)/sbin
SYSCONFDIR = $(PREFIX)/etc

.PHONY: default install-notmodule tarball egg clean srpm

default: tarball

install-notmodule:
	install -D -m 755 bin/yumbootstrap $(DESTDIR)$(BINDIR)/yumbootstrap
	install -d -m 755 $(DESTDIR)$(SYSCONFDIR)/yumbootstrap/suites
	cp -R distros/* $(DESTDIR)$(SYSCONFDIR)/yumbootstrap/suites

tarball:
	python3 setup.py sdist --formats=zip

egg:
	python3 setup.py bdist_egg

clean:
	python3 setup.py clean --all
	rm -rf dist lib/*.egg-info
#	rm -rf $(SPHINX_DOCTREE) $(SPHINX_OUTPUT)

#SPHINX_DOCTREE = doc/doctrees
#SPHINX_SOURCE = doc
#SPHINX_OUTPUT = doc/html

#.PHONY: doc html
#doc: html

#html:
#	sphinx-build -b html -d $(SPHINX_DOCTREE) $(SPHINX_SOURCE) $(SPHINX_OUTPUT)

srpm: VERSION=$(shell awk '$$1 == "%define" && $$2 == "_version" {print $$3}' redhat/*.spec)
srpm: PKGNAME=$(shell awk '$$1 ~ /^[Nn][Aa][Mm][Ee]:/ {print $$2}' redhat/*.spec)
srpm:
	rm -rf rpm-build
	mkdir -p rpm-build/rpm
	cd rpm-build/rpm && mkdir BUILD RPMS SOURCES SPECS SRPMS
	git archive --format=tar --prefix=$(PKGNAME)-$(VERSION)/ HEAD | gzip -9 > rpm-build/rpm/SOURCES/$(PKGNAME)-$(VERSION).tar.gz
	rpmbuild --define="%_usrsrc $$PWD/rpm-build" --define="%_topdir %{_usrsrc}/rpm" -bs redhat/*.spec
	mv rpm-build/rpm/SRPMS/$(PKGNAME)-*.src.rpm .
	rm -r rpm-build
