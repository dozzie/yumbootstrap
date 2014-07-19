Limitations/known issues
========================

### Red Hat Enterprise Linux 4

This release was maintained with `up2date` and Yum was yet to come. To enable
installation with yumbootstrap, you need to prepare Yum metadata. After this,
installation should go just fine.

CentOS just works on this matter, though. CentOS 4
([http://vault.centos.org/](vault.centos.org)) already provides Yum metadata,
along with yum package.

### Red Hat Network

yumbootstrap can't use RHN as a repository. A workaround is to clone
repository from RHN with `reposync` (*yum-utils*).

### RHEL 6 guest under RHEL 5 host

Yum changed some repository internals, so installing RHEL6 doesn't work under
RHEL5 (older Yum can't find some files).

### Fedora guest under Debian Squeeze host

Installing Fedora under Debian 6 (Squeeze) fails due to a bug (probably in
*python-rpm*). Installation under Debian 7 (Wheezy) works correctly.

### Fedora repositories

Fedora's repository URL often redirects to poorly maintained mirrors (missing
files, incorrect permissions etc.), causing installation to fail. A workaround
is to figure a good mirror and replace URL with that.
