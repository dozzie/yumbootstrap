%define _version 0.0.3
%define _release 1
%define _packager Stanislaw Klekot <dozzie@jarowit.net>

%{!?__python3: %global __python3 /usr/bin/python3}
%{!?python3_sitelib: %global python3_sitelib %(%{__python3} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Summary: yumbootstrap - chroot installer for Red Hat derivatives
Name: yumbootstrap
Version: %{_version}
Release: %{_release}%{?dist}
Group: Development/Tools
License: GPL v3
Source0: yumbootstrap-%{_version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-root
URL: http://dozzie.jarowit.net/trac/wiki/yumbootstrap
BuildArch: noarch
Packager: %{_packager}
Prefix: %{_prefix}
BuildRequires: python3-setuptools
Requires: yum >= 3.0
%{?el7:Requires: python36-bsddb3}
%{?el8:Requires: python3-bsddb3}

%description
yumbootstrap is a tool for installing Yum-based distributions (Red Hat,
CentOS, Fedora) in a chroot directory. Idea behind it is stolen from Debian's
debootstrap. 

%prep
%setup -q

%build
CFLAGS="$RPM_OPT_FLAGS" %{__python3} setup.py build

%install
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf "$RPM_BUILD_ROOT"
%{__python3} setup.py install --root "$RPM_BUILD_ROOT"
make install-notmodule \
  DESTDIR="$RPM_BUILD_ROOT" \
  BINDIR=%{_sbindir} SYSCONFDIR=%{_sysconfdir}
mkdir -p "$RPM_BUILD_ROOT/%{_docdir}/yumbootstrap-%{_version}"
cp KNOWN_ISSUES.md LICENSE README.md SUITES.md TODO \
   "$RPM_BUILD_ROOT/%{_docdir}/yumbootstrap-%{_version}"


# %clean
# no %clean section


%files
%defattr(-,root,root,-)
%{_sbindir}/yumbootstrap
%{_sysconfdir}/yumbootstrap
#%{_mandir}/man8
%{_docdir}/yumbootstrap-%{_version}
%{python3_sitelib}/yumbootstrap
%{python3_sitelib}/yumbootstrap-*.egg-info


# %changelog
# no %changelog section
