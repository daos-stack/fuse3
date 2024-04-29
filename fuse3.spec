%if 0%{?suse_version}
%global ninja ninja
%else
%global ninja ninja-build
%endif
%global xyz_version 3.16.2
%global xy_version %(sed 's/\\(.*\\)\\..*/\\1/'<<<%{xyz_version})

Name:		fuse3
Version:	%{xyz_version}
Release:	1%{?dist}
Summary:	File System in Userspace (FUSE) v3 utilities
License:	GPL+
URL:		http://fuse.sf.net
Source0:	https://github.com/libfuse/libfuse/releases/download/fuse-%{version}/fuse-%{version}.tar.gz
Source1:	https://github.com/libfuse/libfuse/releases/download/fuse-%{version}/fuse-%{version}.tar.gz.sig
Source2:	https://raw.githubusercontent.com/libfuse/libfuse/master/signify/fuse-%{xy_version}.pub
Source3:	fuse.conf
Patch0:		fuse3-gcc11.patch
Patch1:		fuse-install-fix.patch
Patch16:	fuse-3.17.0-Pass-FUSE_PARALLEL_DIROPS-to-kernel-861.patch
Patch17:	fuse-3.17.0-Don-t-set-FUSE_CAP_PARALLEL_DIROPS-by-default.patch

BuildRequires:	fdupes
BuildRequires:	signify
BuildRequires:	which
%if ! 0%{?el6}
Conflicts:	filesystem < 3
%endif
BuildRequires:	libselinux-devel
BuildRequires:	meson, %ninja, gcc, gcc-c++
%if ! 0%{?el6} && ! 0%{?el7} && ! 0%{?suse_version}
BuildRequires:	systemd-udev
%endif
%if 0%{?el6}
BuildRequires:	udev, kernel-devel
%else
Requires:	%{_sysconfdir}/fuse.conf
%endif
%if ! 0%{?el8}
# fuse-common 3.4.2-3 had the fuse & fuse3 man pages in it
Conflicts:	fuse-common < 3.4.2-4
%endif

%if ! 0%{?suse_version}
# The dependency from fuse3 to fuse3-libs is already implicit through
# the generated library dependency, but unless we force the exact
# version then we risk mixing different fuse3 & fuse3-libs versions
# which is not likely to be a well-tested situation upstream.
Requires:	%{name}-libs = %{version}-%{release}
%endif

%if 0%{?suse_version}
%global __debug_package 1
%global _debuginfo_subpackages 0
%debug_package
%endif

%description
With FUSE it is possible to implement a fully functional filesystem in a
userspace program. This package contains the FUSE v3 userspace tools to
mount a FUSE filesystem.

%if 0%{?suse_version}
%package -n libfuse3-3
Summary:		Library of FUSE, the User space File System for GNU/Linux and BSD
Group:			System/Filesystems

%description -n libfuse3-3
FUSE (Filesystem in Userspace) is an interface by the Linux kernel
for userspace programs to export a filesystem to the kernel.

A FUSE file system is typically implemented as a standalone
application that links with libfuse. libfuse provides a C API over
the raw kernel interface.

%package doc
Summary:	Documentation for the FUSE library version 3
Group:		Documentation/HTML

%description doc
This package contains the documentation for FUSE (userspace filesystem).
%else
%package libs
Summary:	File System in Userspace (FUSE) v3 libraries
License:	LGPLv2+
%if ! 0%{?el6}
Conflicts:	filesystem < 3
%endif

%description libs
Devel With FUSE it is possible to implement a fully functional filesystem in a
userspace program. This package contains the FUSE v3 libraries.
%endif

%package devel
Summary:	File System in Userspace (FUSE) v3 devel files
%if 0%{?suse_version}
Group:		Development/Languages/C and C++
Requires:	fuse3 = %{version}
Requires:	glibc-devel
Requires:	libfuse3-3 = %{version}
%else
Requires:	%{name}-libs = %{version}-%{release}
%endif
Requires:	pkgconfig
License:	LGPLv2+
%if ! 0%{?el6}
Conflicts:	filesystem < 3
%endif

%description devel
With FUSE it is possible to implement a fully functional filesystem in a
userspace program. This package contains development files (headers,
pgk-config) to develop FUSE v3 based applications/filesystems.

%if ! 0%{?el6} && ! 0%{?el7}
%package -n fuse-common
Summary:	Common files for File System in Userspace (FUSE) v2 and v3
License:	GPL+
# the distro fuse package has a history of Requires exactly fuse-common = $someversion
# so let this package mimic those
#Conflicts: fuse < 3
Provides: fuse-common = 3.3.0

%description -n fuse-common
Common files for FUSE v2 and FUSE v3.
%endif

%prep
# Fuse is using signify rather than PGG since 3.15.1 For more details see:
#	https://github.com/libfuse/libfuse/releases/tag/fuse-3.15.1
signify -V -m  '%{SOURCE0}' -p '%{SOURCE2}'

%setup -q -n fuse-%{version}
%patch0 -p1
%if 0%{?suse_version}
%patch1 -p1
%endif
%patch16 -p1
%patch17 -p1

%build
export LC_ALL=en_US.UTF-8
%if ! 0%{?_vpath_srcdir:1}
%global _vpath_srcdir .
%endif
%if ! 0%{?_vpath_builddir:1}
%global _vpath_builddir build
%endif
%if 0%{?el6}
%if ! 0%{?__global_ldflags:1}
%global __global_ldflags ""
%endif
%meson -D udevrulesdir=%{_udevrulesdir}
%else
%if 0%{?flatpak}
%meson -D udevrulesdir=%{_udevrulesdir}
%else
%meson
%endif
%endif

(cd %{_vpath_builddir}
%if 0%{?el6}
meson configure -D c_args=-I"`ls -d /usr/src/kernels/*/include|head -1`"
%endif
%if 0%{?el6} || 0%{?el7}
meson configure -D examples=false
%endif
# don't have root for installation
meson configure -D useroot=false
%ninja reconfigure
)
%meson_build

%install
export MESON_INSTALL_DESTDIR_PREFIX=%{buildroot}%{_prefix} %meson_install
find %{buildroot} .
find %{buildroot} -type f -name "*.la" -exec rm -f {} ';'
# change from 4755 to 0755 to allow stripping -- fixed later in files
chmod 0755 %{buildroot}/%{_bindir}/fusermount3

# Get rid of static libs
rm -f %{buildroot}/%{_libdir}/*.a
# No need to create init-script
rm -f %{buildroot}%{_sysconfdir}/init.d/fuse3
# This path is hardcoded:
# https://github.com/libfuse/libfuse/blob/master/util/install_helper.sh#L43
# so flatpaks will fail unless we delete it below.
rm -f %{buildroot}/etc/init.d/fuse3


%if 0%{?el6} || 0%{?el7}
# This is in the fuse package on el7 and there's no default on el6
rm -f %{buildroot}%{_sysconfdir}/fuse.conf
%else
# Install config-file
install -p -m 0644 %{SOURCE3} %{buildroot}%{_sysconfdir}
%endif

# Delete pointless udev rules (brc#748204)
rm -f %{buildroot}%{_udevrulesdir}/99-fuse3.rules

%if 0%{?suse_version}
# Remove unneeded stuff
rm -rfv %{buildroot}/%{_prefix}/lib/udev %{buildroot}/%{_initddir}
%fdupes -s doc

%post
%set_permissions %{_bindir}/fusermount3

%verifyscript
%verify_permissions -e %{_bindir}/fusermount3

%post -n libfuse3-3 -p /sbin/ldconfig
%postun -n libfuse3-3 -p /sbin/ldconfig
%else
%if 0%{?el6} || 0%{?el7}
%post -p /sbin/ldconfig libs
%postun -p /sbin/ldconfig libs
%ldconfig_scriptlets libs
%endif
%endif

%{!?_licensedir:%global license %%doc}

%files
%license LICENSE GPL2.txt
%doc AUTHORS ChangeLog.rst README.md
%if 0%{?suse_version}
%verify(not mode) %attr(4750,root,trusted) %{_bindir}/fusermount3
%{_sbindir}/mount.fuse3
%config %{_sysconfdir}/fuse3.conf
%{_mandir}/man1/fusermount3.1%{?ext_man}
%{_mandir}/man8/mount.fuse3.8%{?ext_man}
%else
%{_sbindir}/mount.fuse3
%attr(4755,root,root) %{_bindir}/fusermount3
%{_mandir}/man1/*
%{_mandir}/man8/*
%if 0%{?el6}
%{_udevrulesdir}/*
%endif
%endif

%if 0%{?suse_version}
%files -n libfuse3-3
%{_libdir}/libfuse3.so.3*

%files doc
%doc example doc

%else
%files libs
%license LGPL2.txt
%{_libdir}/libfuse3.so.*
%endif

%files devel
%{_libdir}/libfuse3.so
%{_libdir}/pkgconfig/fuse3.pc
%{_includedir}/fuse3/

%if ! 0%{?el6} && ! 0%{?el7}
%files -n fuse-common
%config(noreplace) %{_sysconfdir}/fuse.conf
%endif

%changelog
* Mon Apr 22 2024 Brian J. Murrell <brian.murrell@intel.com> - 3.16.2-1
- Update to 3.16.2
- Add:
  - fuse-3.17.0-Pass-FUSE_PARALLEL_DIROPS-to-kernel-861.patch
  - fuse-3.17.0-Don-t-set-FUSE_CAP_PARALLEL_DIROPS-by-default.patch
- Rebase with upstreams
- Build debuginfo packages on SUSE

* Wed Aug 09 2023 Pavel Reichl <preichl@redhat.com> - 3.16.1-1
- update to 3.16.1
- Add tarball signature verification

* Wed Jul 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 3.14.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Mon Jun 26 2023 Richard W.M. Jones <rjones@redhat.com> - 3.14.1-2
- Force fuse3 and fuse3-libs versions to be identical
  https://lists.fedoraproject.org/archives/list/devel@lists.fedoraproject.org/thread/LYQUYUAS7FG6FFGJBBWP7XEV563V4LBS/

* Mon Apr  3 2023 Tom Callaway <spot@fedoraproject.org> - 3.14.1-1
- update to 3.14.1

* Tue Feb 28 2023 Richard W.M. Jones <rjones@redhat.com> - 3.14.0-1
- Update to 3.14.0

* Wed Feb  8 2023 Tom Callaway <spot@fedoraproject.org> - 3.13.1-1
- update to 3.13.1

* Fri Jan 20 2023 Tom Callaway <spot@fedoraproject.org> - 3.13.0-1
- update to 3.13.0

* Thu Jan 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 3.12.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Fri Sep  9 2022 Tom Callaway <spot@fedoraproject.org> - 3.12.0-1
- update to 3.12.0

* Thu Jul 21 2022 Fedora Release Engineering <releng@fedoraproject.org> - 3.10.5-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild

* Mon Feb 21 2022 Tom Callaway <spot@fedoraproject.org> - 3.10.5-4
- force udevrulesdir option for flatpak builds

* Wed Feb 16 2022 Tom Callaway <spot@fedoraproject.org> - 3.10.5-3
- fix flatpak issues

* Thu Jan 20 2022 Fedora Release Engineering <releng@fedoraproject.org> - 3.10.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild

* Thu Sep 16 2021 Tom Callaway <spot@fedoraproject.org> - 3.10.5-1
- update to 3.10.5

* Wed Jul 21 2021 Fedora Release Engineering <releng@fedoraproject.org> - 3.10.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild

* Tue Jun 15 2021 Tom Callaway <spot@fedoraproject.org> - 3.10.4-1
- update to 3.10.4

* Thu May  6 2021 Tom Callaway <spot@fedoraproject.org> - 3.10.3-1
- update to 3.10.3

* Fri Feb  5 2021 Tom Callaway <spot@fedoraproject.org> - 3.10.2-1
- update to 3.10.2

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 3.10.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Mon Dec  7 2020 Tom Callaway <spot@fedoraproject.org> - 3.10.1-1
- update to 3.10.1

* Wed Oct 14 2020 Jeff Law <law@redhat.com> - 3.10.0-2
- Add missing #include for gcc-11

* Mon Oct 12 2020 Tom Callaway <spot@fedoraproject.org> - 3.10.0-1
- update to 3.10.0
- enable lto

* Mon Aug 10 2020 Tom Callaway <spot@fedoraproject.org> - 3.9.4-1
- update to 3.9.4

* Mon Jul 27 2020 Fedora Release Engineering <releng@fedoraproject.org> - 3.9.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Wed Jul  1 2020 Jeff Law <law@redhat.com> - 3.9.2-2
- Disable LTO

* Thu Jun 18 2020 Tom Callaway <spot@fedoraproject.org> - 3.9.2-1
- update to 3.9.2

* Thu Mar 19 2020 Tom Callaway <spot@fedoraproject.org> - 3.9.1-1
- update to 3.9.1

* Tue Jan 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 3.9.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Mon Dec 16 2019 Tom Callaway <spot@fedoraproject.org> - 3.9.0-1
- update to 3.9.0

* Mon Nov  4 2019 Tom Callaway <spot@fedoraproject.org> - 3.8.0-1
- update to 3.8.0

* Fri Sep 27 2019 Tom Callaway <spot@fedoraproject.org> - 3.7.0-1
- update to 3.7.0

* Sun Sep  1 2019 Peter Lemenkov <lemenkov@gmail.com> - 3.6.2-1
- Update to 3.6.2

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 3.6.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Wed Jul 03 2019 Dave Dykstra <dwd@fedoraproject.org> - 3.6.1-3
- Update to the final version of pr #421

* Wed Jul 03 2019 Dave Dykstra <dwd@fedoraproject.org> - 3.6.1-2
- Update to newer version of pr #421
- Disable building examples on el7

* Thu Jun 13 2019 Tom Callaway <spot@fedoraproject.org> - 3.6.1-1
- Update to 3.6.1

* Fri May 24 2019 Dave Dykstra <dwd@fedoraproject.org> - 3.5.0-1
- Upgrade to upstream 3.5.0

* Sat May 04 2019 Dave Dykstra <dwd@fedoraproject.org> - 3.4.2-7
- Fix building on el6

* Wed May 01 2019 Dave Dykstra <dwd@fedoraproject.org> - 3.4.2-6
- Need Conflicts: fuse-common < 3.4.2-4, because <= 3.4.2-3 isn't quite
  enough.

* Wed May 01 2019 Dave Dykstra <dwd@fedoraproject.org> - 3.4.2-5
- Update the Conflicts: fuse-common <= version to 3.4.2-3

* Wed May 01 2019 Dave Dykstra <dwd@fedoraproject.org> - 3.4.2-4
- Bump release number in order to larger than a rebuild of fuse package
  done before separation pull request was merged.

* Mon Apr 08 2019 Dave Dykstra <dwd@fedoraproject.org> - 3.4.2-3
- Separate out from fuse package
