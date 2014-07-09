yumbootstrap
============

yumbootstrap is a tool for installing Yum-based distributions (Red Hat,
CentOS, Fedora) in a chroot directory. Idea behind it is stolen from Debian's
debootstrap. It's planned for yumbootstrap to work along with templates for
`lxc-create`.

There is another project of similar purpose:
[Rinse](http://www.steve.org.uk/Software/rinse/), but seems unmaintained and
I generally didn't like its architecture and configuration.

Limitations/known issues
------------------------

  * Can't install release 4 of Red Hat/CentOS, because it didn't provide Yum
    repositories. Workaround for this is to create custom metadata for RPMs.
  * Can't use RHN as a repository. Or can, but it would be very troublesome.
  * Workaround is to 
  * Can't install RHEL6 under RHEL5. Yum changed some internals, so the one
    from RHEL5 can't use repositories prepared for RHEL6.
  * Can't install Fedora {17,18} under Debian Squeeze. This seems like a bug
    in Debian's version of Yum. No workaround found yet.
  * Fedora's repository URL often redirects to unreliable mirrors.
