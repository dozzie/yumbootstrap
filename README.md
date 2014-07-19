yumbootstrap
============

yumbootstrap is a tool for installing Yum-based distributions (Red Hat,
CentOS, Fedora) in a chroot directory. Idea behind it is stolen from Debian's
debootstrap. It's planned for yumbootstrap to work along with templates for
`lxc-create`.

There is another project of similar purpose:
[Rinse](http://www.steve.org.uk/Software/rinse/), but seems unmaintained and
I generally didn't like its architecture and configuration.

Examples of use
---------------

Listing available suites:

    # /usr/sbin/yumbootstrap --list-suites
    centos-5
    centos-6
    ...
    fedora-19
    fedora-20

Installing *centos-6* suite to `/mnt/chroot/centos-6-chroot`:

    # /usr/sbin/yumbootstrap --verbose centos-6 /mnt/chroot/centos-6-chroot

Installing *centos-6* suite, including some custom packages:

    # /usr/sbin/yumbootstrap --verbose \
        --include=openssh-server --group=Core \
        centos-6 /mnt/chroot/centos-6-chroot

Installing *centos-6* suite, installing custom packages by hand from parent OS:

    # CHROOT=/mnt/chroot/centos-6-chroot
    # /usr/sbin/yumbootstrap --verbose --no-scripts centos-6 $CHROOT
    # yum --installroot=$CHROOT -c $CHROOT/yumbootstrap/yum.conf install ...
    # /usr/sbin/yumbootstrap --verbose --just-scripts $CHROOT

Installing yumbootstrap
-----------------------

For Debian-based distributions, *dpkg-dev* and *fakeroot* are required.

    dpkg-buildpackage -b -uc
    dpkg -i ../yumbootstrap*.deb

For Red Hat derivatives you need *rpm-build*.

    make srpm
    rpmbuild --rebuild yumbootstrap-*.src.rpm
    yum localinstall --nogpgcheck /usr/src/redhat/RPMS/*/yumbootstrap-*.rpm
