#
# Copyright (C) 2014-2020 Red Hat, Inc.
#
# Cockpit is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# Cockpit is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Cockpit; If not, see <http://www.gnu.org/licenses/>.
#

#
# This file is maintained at the following location:
# https://github.com/cockpit-project/cockpit/blob/main/tools/cockpit.spec
#
# If you are editing this file in another location, changes will likely
# be clobbered the next time an automated release is done.
#
# Check first cockpit-devel@lists.fedorahosted.org
#

# earliest base that the subpackages work on; the instances of this get computed/updated
# by tools/gen-spec-dependencies during "make dist", but keep a hardcoded fallback
%define required_base 122

# we generally want CentOS packages to be like RHEL; special cases need to check %{centos} explicitly
%if 0%{?centos}
%define rhel %{centos}
%endif

%define _hardened_build 1

%define __lib lib

%if %{defined _pamdir}
%define pamdir %{_pamdir}
%else
%define pamdir %{_libdir}/security
%endif

Name:           cockpit
Summary:        Web Console for Linux servers

License:        LGPL-2.1-or-later
URL:            https://cockpit-project.org/

Version:        271
Release:        0
Source0:        cockpit-%{version}.tar
Source1:        cockpit.pam
Source2:        cockpit-rpmlintrc
Source99:       README.packaging
Source98:       package-lock.json
Source97:       node_modules.spec.inc
%include        %{_sourcedir}/node_modules.spec.inc
Patch1:         0001-selinux-allow-login-to-read-motd-file.patch
Patch2:         hide-docs.patch
Patch3:         suse-microos-branding.patch
Patch4:         css-overrides.patch
Patch5:         storage-btrfs.patch
Patch6:         kdump-close.patch
Patch7:         kdump-refactor.patch
Patch8:         kdump-suse.patch
# SLE Micro specific patches
Patch100:       remove-pwscore.patch
Patch101:       hide-pcp.patch

# in RHEL 8 the source package is duplicated: cockpit (building basic packages like cockpit-{bridge,system})
# and cockpit-appstream (building optional packages like cockpit-{pcp})
# This split does not apply to EPEL/COPR.
# In Fedora ELN/RHEL 9+ there is just one source package, which ships rpms in both BaseOS and AppStream
# We also provide an override mechanism if you want to build all packages.
%define build_all 0
%if 0%{?rhel} == 8 && 0%{?epel} == 0 && !%{build_all}

%if "%{name}" == "cockpit"
%define build_basic 1
%define build_optional 0
%else
%define build_basic 0
%define build_optional 1
%endif

%else
%define build_basic 1
%define build_optional 1
%endif

# Ship custom SELinux policy (but not for cockpit-appstream)
%if 0%{?rhel} >= 9 || 0%{?fedora} || 0%{?suse_version}
%if "%{name}" == "cockpit"
%define selinuxtype targeted
%define selinux_configure_arg --enable-selinux-policy=%{selinuxtype}
%endif
%endif

BuildRequires: gcc
BuildRequires: pkgconfig(gio-unix-2.0)
BuildRequires: pkgconfig(json-glib-1.0)
BuildRequires: pkgconfig(polkit-agent-1) >= 0.105
BuildRequires: pam-devel

BuildRequires: autoconf automake
BuildRequires: make
BuildRequires: /usr/bin/python3
%if 0%{?rhel} && 0%{?rhel} <= 8
# RHEL 8's gettext does not yet have metainfo.its
BuildRequires: gettext >= 0.19.7
BuildRequires: libappstream-glib-devel
%else
BuildRequires: gettext >= 0.21
%endif
%if 0%{?build_basic}
BuildRequires: libssh-devel >= 0.8.5
%endif
BuildRequires: openssl-devel
BuildRequires: gnutls-devel >= 3.4.3
BuildRequires: zlib-devel
BuildRequires: pkgconfig(krb5) >= 1.11
BuildRequires: libxslt-devel
BuildRequires: glib-networking
BuildRequires: sed

BuildRequires: glib2-devel >= 2.50.0
# this is for runtimedir in the tls proxy ace21c8879
BuildRequires: pkgconfig(libsystemd) >= 235
%if 0%{?suse_version}
BuildRequires: distribution-release
BuildRequires: libpcp-devel
BuildRequires: pcp-devel
BuildRequires: libpcp3
BuildRequires: libpcp_import1
BuildRequires: openssh
BuildRequires: distribution-logos
BuildRequires: wallpaper-branding
# needed for /var/lib/pcp directory ownership
BuildRequires: pcp
%else
BuildRequires: pcp-libs-devel
BuildRequires: openssh-clients
BuildRequires: docbook-style-xsl
%endif
BuildRequires: krb5-server
BuildRequires: gdb

# For documentation
BuildRequires: xmlto

BuildRequires:  selinux-policy
BuildRequires:  selinux-policy-%{selinuxtype}
BuildRequires:  selinux-policy-devel

# for rebuilding nodejs bits
BuildRequires: npm
BuildRequires: sassc
BuildRequires: local-npm-registry

# This is the "cockpit" metapackage. It should only
# Require, Suggest or Recommend other cockpit-xxx subpackages

Requires: cockpit-bridge
Requires: cockpit-ws
Requires: cockpit-system

# Optional components
Recommends: (cockpit-storaged if udisks2)
Recommends: (cockpit-packagekit if dnf)
Suggests: cockpit-pcp

%if 0%{?rhel} == 0
Recommends: (cockpit-networkmanager if NetworkManager)
Suggests: cockpit-selinux
%endif
%if 0%{?rhel} && 0%{?centos} == 0
Requires: subscription-manager-cockpit
%endif

%prep
%setup -q -n cockpit-%{version}
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1
%patch7 -p1
%patch8 -p1

%if 0%{?sle_version}
%patch100 -p1
%patch101 -p1
%endif

cp %SOURCE1 tools/cockpit.pam
#
local-npm-registry %{_sourcedir} install --also=dev --legacy-peer-deps

%build
find node_modules -name \*.node -print -delete
touch node_modules/.stamp

exec 2>&1
PKG_NAME="Cockpit"
echo "m4_define(VERSION_NUMBER, %version)" > version.m4
autoreconf -fvi -I tools
#
%configure \
    %{?selinux_configure_arg} \
    --with-cockpit-user=cockpit-ws \
    --with-cockpit-ws-instance-user=cockpit-wsinstance \
%if 0%{?suse_version}
    --docdir=%_defaultdocdir/%{name} \
%endif
    --with-pamdir='%{pamdir}' \
%if 0%{?build_basic} == 0
    --disable-ssh \
%endif

%make_build

%check
make -j$(nproc) check

%install
# In obs we get  write error: stdout
%make_install | tee make_install.log
make install-tests DESTDIR=%{buildroot}
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/pam.d
install -p -m 644 tools/cockpit.pam $RPM_BUILD_ROOT%{_sysconfdir}/pam.d/cockpit
rm -f %{buildroot}/%{_libdir}/cockpit/*.so
install -D -p -m 644 AUTHORS COPYING README.md %{buildroot}%{_docdir}/cockpit/

# only ship deprecated PatternFly API for stable releases
%if 0%{?rhel} == 8
    if [ -f %{buildroot}/%{_datadir}/cockpit/base1/cockpit.css.gz ]; then
        ln -s cockpit.css.gz %{buildroot}/%{_datadir}/cockpit/base1/patternfly.css.gz
    elif [ -f %{buildroot}/%{_datadir}/cockpit/base1/cockpit.css ]; then
        ln -s cockpit.css %{buildroot}/%{_datadir}/cockpit/base1/patternfly.css
    else
        echo >&2 Neither cockpit.css.gz nor cockpit.css exists.
        exit 1
    fi
%endif

# Build the package lists for resource packages
# cockpit-bridge is the basic dependency for all cockpit-* packages, so centrally own the page directory
echo '%dir %{_datadir}/cockpit' > base.list
echo '%dir %{_datadir}/cockpit/base1' >> base.list
echo '%dir %{_datadir}/cockpit/base1/fonts' >> base.list
find %{buildroot}%{_datadir}/cockpit/base1 -type f -o -type l >> base.list
echo '%{_sysconfdir}/cockpit/machines.d' >> base.list
echo %{buildroot}%{_datadir}/polkit-1/actions/org.cockpit-project.cockpit-bridge.policy >> base.list
echo '%dir %{_datadir}/cockpit/ssh' >> base.list
find %{buildroot}%{_datadir}/cockpit/ssh -type f >> base.list
echo '%{_libexecdir}/cockpit-ssh' >> base.list

echo '%dir %{_datadir}/cockpit/pcp' > pcp.list
find %{buildroot}%{_datadir}/cockpit/pcp -type f >> pcp.list

echo '%dir %{_datadir}/cockpit/tuned' > system.list
find %{buildroot}%{_datadir}/cockpit/tuned -type f >> system.list

echo '%dir %{_datadir}/cockpit/shell' >> system.list
find %{buildroot}%{_datadir}/cockpit/shell -type f >> system.list

echo '%dir %{_datadir}/cockpit/systemd' >> system.list
find %{buildroot}%{_datadir}/cockpit/systemd -type f >> system.list

echo '%dir %{_datadir}/cockpit/users' >> system.list
find %{buildroot}%{_datadir}/cockpit/users -type f >> system.list

echo '%dir %{_datadir}/cockpit/metrics' >> system.list
find %{buildroot}%{_datadir}/cockpit/metrics -type f >> system.list

echo '%dir %{_datadir}/cockpit/kdump' > kdump.list
find %{buildroot}%{_datadir}/cockpit/kdump -type f >> kdump.list

echo '%dir %{_datadir}/cockpit/sosreport' > sosreport.list
find %{buildroot}%{_datadir}/cockpit/sosreport -type f >> sosreport.list

echo '%dir %{_datadir}/cockpit/storaged' > storaged.list
find %{buildroot}%{_datadir}/cockpit/storaged -type f >> storaged.list

echo '%dir %{_datadir}/cockpit/networkmanager' > networkmanager.list
find %{buildroot}%{_datadir}/cockpit/networkmanager -type f >> networkmanager.list

echo '%dir %{_datadir}/cockpit/packagekit' > packagekit.list
find %{buildroot}%{_datadir}/cockpit/packagekit -type f >> packagekit.list

echo '%dir %{_datadir}/cockpit/apps' >> packagekit.list
find %{buildroot}%{_datadir}/cockpit/apps -type f >> packagekit.list

echo '%dir %{_datadir}/cockpit/selinux' > selinux.list
find %{buildroot}%{_datadir}/cockpit/selinux -type f >> selinux.list

echo '%dir %{_datadir}/cockpit/playground' > tests.list
find %{buildroot}%{_datadir}/cockpit/playground -type f >> tests.list

echo '%dir %{_datadir}/cockpit/static' > static.list
echo '%dir %{_datadir}/cockpit/static/fonts' >> static.list
find %{buildroot}%{_datadir}/cockpit/static -type f >> static.list

# when not building basic packages, remove their files
%if 0%{?build_basic} == 0
for pkg in base1 branding motd kdump networkmanager selinux shell sosreport ssh static systemd tuned users metrics; do
    rm -r %{buildroot}/%{_datadir}/cockpit/$pkg
    rm -f %{buildroot}/%{_datadir}/metainfo/org.cockpit-project.cockpit-${pkg}.metainfo.xml
done
for data in doc man pixmaps polkit-1; do
    rm -r %{buildroot}/%{_datadir}/$data
done
for lib in systemd tmpfiles.d; do
    rm -r %{buildroot}/%{_prefix}/%{__lib}/$lib
done
for libexec in cockpit-askpass cockpit-session cockpit-ws cockpit-tls cockpit-wsinstance-factory cockpit-client cockpit-client.ui cockpit-desktop cockpit-certificate-helper cockpit-certificate-ensure; do
    rm %{buildroot}/%{_libexecdir}/$libexec
done
rm -r %{buildroot}/%{_libdir}/security %{buildroot}/%{_sysconfdir}/pam.d %{buildroot}/%{_sysconfdir}/motd.d %{buildroot}/%{_sysconfdir}/issue.d
rm %{buildroot}/usr/bin/cockpit-bridge
rm -f %{buildroot}%{_libexecdir}/cockpit-ssh
rm -f %{buildroot}%{_datadir}/metainfo/cockpit.appdata.xml
%endif

# when not building optional packages, remove their files
%if 0%{?build_optional} == 0
for pkg in apps packagekit pcp playground storaged; do
    rm -rf %{buildroot}/%{_datadir}/cockpit/$pkg
done
# files from -tests
rm -r %{buildroot}/%{_prefix}/%{__lib}/cockpit-test-assets
# files from -pcp
rm -r %{buildroot}/%{_libexecdir}/cockpit-pcp %{buildroot}/%{_localstatedir}/lib/pcp/
# files from -storaged
rm -f %{buildroot}/%{_prefix}/share/metainfo/org.cockpit-project.cockpit-storaged.metainfo.xml
%endif

sed -i "s|%{buildroot}||" *.list

%if 0%{?suse_version}
# setroubleshoot not yet in
rm -r %{buildroot}%{_datadir}/cockpit/selinux
rm %{buildroot}/%{_prefix}/share/metainfo/org.cockpit-project.cockpit-selinux.metainfo.xml
# remove brandings with stale symlinks. Means they don't match
# the distro.
pushd %{buildroot}/%{_datadir}/cockpit/branding
ls --hide={default,kubernetes,opensuse,registry,sle-micro} | xargs rm -rv
popd
# need this in SUSE as post build checks dislike stale symlinks
install -m 644 -D /dev/null %{buildroot}/run/cockpit/motd
# remove files of not installable packages
rm -r %{buildroot}%{_datadir}/cockpit/sosreport
rm -f %{buildroot}/%{_prefix}/share/metainfo/org.cockpit-project.cockpit-sosreport.metainfo.xml
rm -f %{buildroot}%{_datadir}/pixmaps/cockpit-sosreport.png
%else
%global _debugsource_packages 1
%global _debuginfo_subpackages 0

%define find_debug_info %{_rpmconfigdir}/find-debuginfo.sh %{?_missing_build_ids_terminate_build:--strict-build-id} %{?_include_minidebuginfo:-m} %{?_find_debuginfo_dwz_opts} %{?_find_debuginfo_opts} %{?_debugsource_packages:-S debugsourcefiles.list} "%{_builddir}/%{?buildsubdir}"

%endif
# /suse_version
rm -rf %{buildroot}/usr/src/debug

# On RHEL kdump, networkmanager, selinux, and sosreport are part of the system package
%if 0%{?rhel}
cat kdump.list sosreport.list networkmanager.list selinux.list >> system.list
rm -f %{buildroot}%{_datadir}/metainfo/org.cockpit-project.cockpit-sosreport.metainfo.xml
rm -f %{buildroot}%{_datadir}/metainfo/org.cockpit-project.cockpit-kdump.metainfo.xml
rm -f %{buildroot}%{_datadir}/metainfo/org.cockpit-project.cockpit-selinux.metainfo.xml
rm -f %{buildroot}%{_datadir}/pixmaps/cockpit-sosreport.png
%endif

mkdir -p %{buildroot}%{_datadir}/cockpit/devel
cp -a pkg/lib %{buildroot}%{_datadir}/cockpit/devel

# -------------------------------------------------------------------------------
# Basic Sub-packages

%if 0%{?build_basic}

%description
The Cockpit Web Console enables users to administer GNU/Linux servers using a
web browser.

It offers network configuration, log inspection, diagnostic reports, SELinux
troubleshooting, interactive command-line sessions, and more.

%files
%{_docdir}/cockpit/AUTHORS
%{_docdir}/cockpit/COPYING
%{_docdir}/cockpit/README.md
%{_datadir}/metainfo/cockpit.appdata.xml
%{_datadir}/pixmaps/cockpit.png
%doc %{_mandir}/man1/cockpit.1.gz


%package bridge
Summary: Cockpit bridge server-side component
Requires: glib-networking
Provides: cockpit-ssh = %{version}-%{release}
# PR #10430 dropped workaround for ws' inability to understand x-host-key challenge
Conflicts: cockpit-ws < 181.x
# 233 dropped jquery.js, pages started to bundle it (commit 049e8b8dce)
Conflicts: cockpit-dashboard < 233
Conflicts: cockpit-networkmanager < 233
Conflicts: cockpit-storaged < 233
Conflicts: cockpit-system < 233
Conflicts: cockpit-tests < 233
Conflicts: cockpit-docker < 233

%description bridge
The Cockpit bridge component installed server side and runs commands on the
system on behalf of the web based user interface.

%files bridge -f base.list
%doc %{_mandir}/man1/cockpit-bridge.1.gz
%{_bindir}/cockpit-bridge
%{_libexecdir}/cockpit-askpass

%package doc
Summary: Cockpit deployment and developer guide
BuildArch: noarch

%description doc
The Cockpit Deployment and Developer Guide shows sysadmins how to
deploy Cockpit on their machines as well as helps developers who want to
embed or extend Cockpit.

%files doc
%exclude %{_docdir}/cockpit/AUTHORS
%exclude %{_docdir}/cockpit/COPYING
%exclude %{_docdir}/cockpit/README.md
%{_docdir}/cockpit

%package system
Summary: Cockpit admin interface package for configuring and troubleshooting a system
BuildArch: noarch
Requires: cockpit-bridge >= %{version}-%{release}
%if !0%{?suse_version}
Requires: shadow-utils
%endif
Requires: grep
%if !0%{?sle_version}
Requires: /usr/bin/pwscore
%endif
Requires: /usr/bin/date
Provides: cockpit-shell = %{version}-%{release}
Provides: cockpit-systemd = %{version}-%{release}
Provides: cockpit-tuned = %{version}-%{release}
Provides: cockpit-users = %{version}-%{release}
Obsoletes: cockpit-dashboard < %{version}-%{release}
%if 0%{?rhel}
Requires: NetworkManager >= 1.6
Requires: kexec-tools
Requires: sos
Requires: sudo
Recommends: PackageKit
Recommends: setroubleshoot-server >= 3.3.3
Suggests: NetworkManager-team
Provides: cockpit-kdump = %{version}-%{release}
Provides: cockpit-networkmanager = %{version}-%{release}
Provides: cockpit-selinux = %{version}-%{release}
Provides: cockpit-sosreport = %{version}-%{release}
%endif
%if 0%{?fedora}
Recommends: (reportd if abrt)
%endif
# NPM modules which are also available as packages
Provides: bundled(xstatic-patternfly-common) = 3.59.5

%description system
This package contains the Cockpit shell and system configuration interfaces.

%files system -f system.list
%dir %{_datadir}/cockpit/shell/images

%package ws
Summary: Cockpit Web Service
Requires: glib-networking
Requires: openssl
Requires: glib2 >= 2.50.0
Requires: (selinux-policy >= %{_selinux_policy_version} if selinux-policy-%{selinuxtype})
Requires(post): (policycoreutils if selinux-policy-%{selinuxtype})
Conflicts: firewalld < 0.6.0-1
Recommends: sscg >= 2.3
Recommends: system-logos
Suggests: sssd-dbus
%if 0%{?suse_version}
Requires(pre): permissions
Requires: distribution-logos
Requires: wallpaper-branding
%endif
# for cockpit-desktop
Suggests: python3

# prevent hard python3 dependency for cockpit-desktop, it falls back to other browsers
%global __requires_exclude_from ^%{_libexecdir}/cockpit-client$

%description ws
The Cockpit Web Service listens on the network, and authenticates users.

If sssd-dbus is installed, you can enable client certificate/smart card
authentication via sssd/FreeIPA.

%files ws -f static.list
%doc %{_mandir}/man1/cockpit-desktop.1.gz
%doc %{_mandir}/man5/cockpit.conf.5.gz
%doc %{_mandir}/man8/cockpit-ws.8.gz
%doc %{_mandir}/man8/cockpit-tls.8.gz
%doc %{_mandir}/man8/pam_ssh_add.8.gz
%dir %{_sysconfdir}/cockpit
%config(noreplace) %{_sysconfdir}/cockpit/ws-certs.d
%config(noreplace) %{_sysconfdir}/pam.d/cockpit
# dir is not owned by pam in openSUSE
%dir %{_sysconfdir}/motd.d
# created in %post, so that users can rm the files
%ghost %{_sysconfdir}/issue.d/cockpit.issue
%ghost %{_sysconfdir}/motd.d/cockpit
%ghost %dir /run/cockpit
%ghost /run/cockpit/motd
%dir %{_datadir}/cockpit/motd
%{_datadir}/cockpit/motd/update-motd
%{_datadir}/cockpit/motd/inactive.motd
%{_unitdir}/cockpit.service
%{_unitdir}/cockpit-motd.service
%{_unitdir}/cockpit.socket
%{_unitdir}/cockpit-wsinstance-http.socket
%{_unitdir}/cockpit-wsinstance-http.service
%{_unitdir}/cockpit-wsinstance-https-factory.socket
%{_unitdir}/cockpit-wsinstance-https-factory@.service
%{_unitdir}/cockpit-wsinstance-https@.socket
%{_unitdir}/cockpit-wsinstance-https@.service
%{_unitdir}/system-cockpithttps.slice
%{_prefix}/%{__lib}/tmpfiles.d/cockpit-tempfiles.conf
%{pamdir}/pam_ssh_add.so
%{pamdir}/pam_cockpit_cert.so
%{_libexecdir}/cockpit-ws
%{_libexecdir}/cockpit-wsinstance-factory
%{_libexecdir}/cockpit-tls
%{_libexecdir}/cockpit-client
%{_libexecdir}/cockpit-client.ui
%{_libexecdir}/cockpit-desktop
%{_libexecdir}/cockpit-certificate-ensure
%{_libexecdir}/cockpit-certificate-helper
%{?suse_version:%verify(not mode) }%attr(4750, root, cockpit-wsinstance) %{_libexecdir}/cockpit-session
%{_datadir}/cockpit/branding
%{_datadir}/selinux/packages/%{selinuxtype}/%{name}.pp.bz2
%{_mandir}/man8/%{name}_session_selinux.8cockpit.*
%{_mandir}/man8/%{name}_ws_selinux.8cockpit.*
%ghost %{_sharedstatedir}/selinux/%{selinuxtype}/active/modules/200/%{name}

%pre ws
getent group cockpit-ws >/dev/null || groupadd -r cockpit-ws
getent passwd cockpit-ws >/dev/null || useradd -r -g cockpit-ws -d /nonexisting -s /sbin/nologin -c "User for cockpit web service" cockpit-ws
getent group cockpit-wsinstance >/dev/null || groupadd -r cockpit-wsinstance
getent passwd cockpit-wsinstance >/dev/null || useradd -r -g cockpit-wsinstance -d /nonexisting -s /sbin/nologin -c "User for cockpit-ws instances" cockpit-wsinstance

if %{_sbindir}/selinuxenabled 2>/dev/null; then
    %selinux_relabel_pre -s %{selinuxtype}
fi

%post ws
if [ -x %{_sbindir}/selinuxenabled ]; then
    %selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/%{name}.pp.bz2
    %selinux_relabel_post -s %{selinuxtype}
fi

# set up dynamic motd/issue symlinks on first-time install; don't bring them back on upgrades if admin removed them
if [ "$1" = 1 ]; then
    mkdir -p /etc/motd.d /etc/issue.d
    ln -s ../../run/cockpit/motd /etc/motd.d/cockpit
    ln -s ../../run/cockpit/motd /etc/issue.d/cockpit.issue
fi
# switch old self-signed cert group from cockpit-wsintance to cockpit-ws on upgrade
if [ "$1" = 2 ]; then
    certfile=/etc/cockpit/ws-certs.d/0-self-signed.cert
    test -f $certfile && stat -c '%G' $certfile | grep -q cockpit-wsinstance && chgrp cockpit-ws $certfile
fi

%if 0%{?suse_version}
%set_permissions %{_libexecdir}/cockpit-session
%endif
%tmpfiles_create cockpit-tempfiles.conf
%systemd_post cockpit.socket cockpit.service
# firewalld only partially picks up changes to its services files without this
test -f %{_bindir}/firewall-cmd && firewall-cmd --reload --quiet || true

# check for deprecated PAM config
if grep --color=auto pam_cockpit_cert %{_sysconfdir}/pam.d/cockpit; then
    echo '**** WARNING:'
    echo '**** WARNING: pam_cockpit_cert is a no-op and will be removed in a'
    echo '**** WARNING: future release; remove it from your /etc/pam.d/cockpit.'
    echo '**** WARNING:'
fi

%preun ws
%systemd_preun cockpit.socket cockpit.service

%postun ws
if [ -x %{_sbindir}/selinuxenabled ]; then
    %selinux_modules_uninstall -s %{selinuxtype} %{name}
    %selinux_relabel_post -s %{selinuxtype}
fi
%systemd_postun_with_restart cockpit.socket cockpit.service

%if 0%{?suse_version}
%verifyscript ws
%verify_permissions -e %{_libexecdir}/cockpit-session
%endif

# -------------------------------------------------------------------------------
# Sub-packages that are part of cockpit-system in RHEL/CentOS, but separate in Fedora

%if 0%{?rhel} == 0

%package kdump
Summary: Cockpit user interface for kernel crash dumping
Requires: cockpit-bridge >= 130
Requires: cockpit-shell >= 130
Requires: kexec-tools
BuildArch: noarch

%description kdump
The Cockpit component for configuring kernel crash dumping.

%files kdump -f kdump.list
%{_datadir}/metainfo/org.cockpit-project.cockpit-kdump.metainfo.xml

%if !0%{?suse_version}
%package sosreport
Summary: Cockpit user interface for diagnostic reports
Requires: cockpit-bridge >= 122
Requires: cockpit-shell >= 122
Requires: sos
BuildArch: noarch

%description sosreport
The Cockpit component for creating diagnostic reports with the
sosreport tool.

%files sosreport -f sosreport.list
%{_datadir}/metainfo/org.cockpit-project.cockpit-sosreport.metainfo.xml
%{_datadir}/pixmaps/cockpit-sosreport.png
%endif

%package networkmanager
Summary: Cockpit user interface for networking, using NetworkManager
Requires: cockpit-bridge >= 186
Requires: cockpit-shell >= 186
Requires: NetworkManager >= 1.6
Conflicts: cockpit-wicked
# Optional components
Recommends: NetworkManager-team
BuildArch: noarch

%description networkmanager
The Cockpit component for managing networking.  This package uses NetworkManager.

%files networkmanager -f networkmanager.list

%endif

%if 0%{?rhel} == 0 && !0%{?suse_version}

%package selinux
Summary: Cockpit SELinux package
Requires: cockpit-bridge >= 122
Requires: cockpit-shell >= 122
Requires: setroubleshoot-server >= 3.3.3
BuildArch: noarch

%description selinux
This package contains the Cockpit user interface integration with the
utility setroubleshoot to diagnose and resolve SELinux issues.

%files selinux -f selinux.list
%{_datadir}/metainfo/org.cockpit-project.cockpit-selinux.metainfo.xml

%endif

#/ build basic packages
%else

# RPM requires this
%description
Dummy package from building optional packages only; never install or publish me.

#/ build basic packages
%endif

# -------------------------------------------------------------------------------
# Sub-packages that are optional extensions

%if 0%{?build_optional}

%package -n cockpit-storaged
Summary: Cockpit user interface for storage, using udisks
Requires: cockpit-shell >= 266
Requires: udisks2 >= 2.9
Requires: %{__python3}
%if 0%{?suse_version}
Requires: libudisks2-0_lvm2 >= 2.9
Recommends: multipath-tools
Requires: python3-dbus-python
%else
Recommends: udisks2-lvm2 >= 2.9
Recommends: udisks2-iscsi >= 2.9
Recommends: device-mapper-multipath
Recommends: clevis-luks
Requires: python3-dbus
%endif
BuildArch: noarch

%description -n cockpit-storaged
The Cockpit component for managing storage.  This package uses udisks.

%files -n cockpit-storaged -f storaged.list
%dir %{_datadir}/cockpit/storaged/images
%{_datadir}/metainfo/org.cockpit-project.cockpit-storaged.metainfo.xml

%package -n cockpit-tests
Summary: Tests for Cockpit
Requires: cockpit-bridge >= 138
Requires: cockpit-system >= 138
Requires: openssh-clients
Provides: cockpit-test-assets = %{version}-%{release}

%description -n cockpit-tests
This package contains tests and files used while testing Cockpit.
These files are not required for running Cockpit.

%files -n cockpit-tests -f tests.list
%{_prefix}/%{__lib}/cockpit-test-assets

%package devel
Summary: Development files for for Cockpit

%description devel
This package contains files used to develop cockpit modules

%files devel
%{_datadir}/cockpit/devel

%package -n cockpit-pcp
Summary: Cockpit PCP integration
Requires: cockpit-bridge >= 238.1.1
Requires: pcp

%description -n cockpit-pcp
Cockpit support for reading PCP metrics and loading PCP archives.

%files -n cockpit-pcp -f pcp.list
%{_libexecdir}/cockpit-pcp
%{_localstatedir}/lib/pcp/config/pmlogconf/tools/cockpit

%post -n cockpit-pcp
systemctl reload-or-try-restart pmlogger

%package -n cockpit-packagekit
Summary: Cockpit user interface for packages
BuildArch: noarch
Requires: cockpit-bridge >= 186
Requires: PackageKit
Recommends: python3-tracer
# HACK: https://bugzilla.redhat.com/show_bug.cgi?id=1800468
Requires: polkit

%description -n cockpit-packagekit
The Cockpit components for installing OS updates and Cockpit add-ons,
via PackageKit.

%files -n cockpit-packagekit -f packagekit.list

#/ build optional extension packages
%endif

# The changelog is automatically generated and merged
%changelog
