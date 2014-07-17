#!/usr/bin/make -f

DESTDIR =
PREFIX = /usr/local
BINDIR = $(PREFIX)/sbin
SYSCONFDIR = $(PREFIX)/etc

.PHONY: default install-notmodule tarball egg clean

default: tarball

install-notmodule:
	install -D -m 755 bin/yumbootstrap $(DESTDIR)$(BINDIR)/yumbootstrap
	install -d -m 755 $(DESTDIR)$(SYSCONFDIR)/yumbootstrap/suites
	cp -R distros/* $(DESTDIR)$(SYSCONFDIR)/yumbootstrap/suites

tarball:
	python setup.py sdist --formats=zip

egg:
	python setup.py bdist_egg

clean:
	python setup.py clean --all
	rm -rf dist
#	rm -rf $(SPHINX_DOCTREE) $(SPHINX_OUTPUT)

#SPHINX_DOCTREE = doc/doctrees
#SPHINX_SOURCE = doc
#SPHINX_OUTPUT = doc/html

#.PHONY: doc html
#doc: html

#html:
#	sphinx-build -b html -d $(SPHINX_DOCTREE) $(SPHINX_SOURCE) $(SPHINX_OUTPUT)
