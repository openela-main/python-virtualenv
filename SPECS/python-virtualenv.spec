# python2X and python3X are built form the same module, so we need a conditional
# for python[23] bits the state of the conditional is not important in the spec,
# it is set in modulemd
%bcond_without python2
%bcond_without python3
%bcond_with python36_module

Name:           python-virtualenv
Version:        15.1.0
Release:        22%{?dist}
Summary:        Tool to create isolated Python environments

Group:          Development/Languages
License:        MIT
URL:            http://pypi.python.org/pypi/virtualenv
Source0:        http://pypi.python.org/packages/source/v/virtualenv/virtualenv-%{version}.tar.gz

# virtualenv -p "/usr/bin/python3" venv fails if there are not packages installed
# under /usr/local/lib/pythonX.Y/site-packages. Check if exec_dir exists before
# listing it's content.
Patch0: check-exec_dir.patch

# Don't fail on missing certifi's cert
# https://github.com/pypa/virtualenv/pull/1252
Patch1: dont-fail-on-missing-certifi-cert.patch

# Changes related to RPM wheels:
# 1. Drop support for Python 2.6 because we don't have it in RHEL 8 and we don't want to
#    bundle prehistoric wheels
# 2. Use wheels from /usr/share/python{2,3,38,39,...}-wheels
# 3. Add support for pip 19.3-ish by importing pip.main() from different locations
# 4. Use the importlib module rather than deprecated imp on Python 3
Patch2: rpm-wheels.patch

# Fixes for Python 3.10+
# Backports from upstream virtualenv 16.7:
#
#  Adjusts the code to accept Python minor versions with two (or more) digits
#   https://github.com/pypa/virtualenv/commit/311a909c10
#
#  Use sysconfig.get_default_scheme() where available (added in Python 3.10)
#   https://github.com/pypa/virtualenv/commit/b4aef0a53b
#
#  Remove universal newline flag (removed in Python 3.11)
#   https://github.com/pypa/virtualenv/commit/8b23c8296f
#
# Backports re-created from scratch, due to changes in formatting.
#
# Run bin/rebuild-script.py in %%build to regenerate the base64 embedded files!
Patch3: python3.10.patch

# The way virtualenv < 20 creates virtual environments
# is not compatible with Python 3.11+ "frozen standard library modules"
# https://docs.python.org/3.11/whatsnew/3.11.html#frozen-imports-static-code-objects
#
# This patch makes virtualenv explicitly error and suggest venv instead.
# See https://bugzilla.redhat.com/show_bug.cgi?id=2165702
Patch4: python3.11-error.patch

BuildArch:      noarch

%if %{with python2}
BuildRequires:  python2-devel
BuildRequires:  python2-setuptools

# RPM installed wheels
BuildRequires:  python2-pip-wheel
BuildRequires:  python2-setuptools-wheel
BuildRequires:  python2-wheel-wheel
%endif # with python2

%if %{with python3}
BuildRequires:  python3-sphinx
BuildRequires:  python3-setuptools

# RPM installed wheels
BuildRequires:  python3-pip-wheel
BuildRequires:  python3-setuptools-wheel
BuildRequires:  python3-wheel-wheel

%if %{with python36_module}
BuildRequires:  python36-devel
BuildRequires:  python36-rpm-macros
%else
BuildRequires:  python3-devel
%endif
%endif # with python3

%description
virtualenv is a tool to create isolated Python environments. virtualenv
is a successor to workingenv, and an extension of virtual-python. It is
written by Ian Bicking, and sponsored by the Open Planning Project. It is
licensed under an MIT-style permissive license.


%if %{with python2}
%package -n     python2-virtualenv
Summary:        Tool to create isolated Python environments

Requires:       python2-setuptools
Requires:       python2-devel

# RPM installed wheels
Requires:       python2-pip-wheel
Requires:       python2-setuptools-wheel
Requires:       python2-wheel-wheel
Requires:       (python3-wheel-wheel if python36)
Requires:       (python38-wheel-wheel if python38)
Requires:       (python39-wheel-wheel if python39)

%{?python_provide:%python_provide python2-virtualenv}

%description -n python2-virtualenv
virtualenv is a tool to create isolated Python environments. virtualenv
is a successor to workingenv, and an extension of virtual-python. It is
written by Ian Bicking, and sponsored by the Open Planning Project. It is
licensed under an MIT-style permissive license
%endif


%if %{with python3}
%package -n     python-virtualenv-doc
Summary:        Documentation for python virtualenv

%description -n python-virtualenv-doc
Documentation for python virtualenv.

%package -n     python3-virtualenv
Summary:        Tool to create isolated Python environments

Requires:       python3-setuptools

# RPM installed wheels
Requires:       python3-pip-wheel
Requires:       python3-setuptools-wheel
Requires:       python3-wheel-wheel
Requires:       (python2-wheel-wheel if python2)
Requires:       (python38-wheel-wheel if python38)
Requires:       (python39-wheel-wheel if python39)

# Require alternatives version that implements the --keep-foreign flag
Requires(postun): alternatives >= 1.19.1-1
# For alternatives
Requires:       python36
Requires(post): python36
Requires(postun): python36

%if %{with python36_module}
Requires:       python36-devel
%else
Requires:       python3-devel
%endif
%{?python_provide:%python_provide python3-virtualenv}
Provides:       virtualenv = %{version}-%{release}

%description -n python3-virtualenv
virtualenv is a tool to create isolated Python environments. virtualenv
is a successor to workingenv, and an extension of virtual-python. It is
written by Ian Bicking, and sponsored by the Open Planning Project. It is
licensed under an MIT-style permissive license
%endif # with python3


%prep
%setup -q -n virtualenv-%{version}
%{__sed} -i -e "1s|#!/usr/bin/env python||" virtualenv.py 

%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1

# Remove the wheels provided by RPM packages and argparse as it's only required for python 2.6
rm virtualenv_support/pip-*
rm virtualenv_support/setuptools-*
rm virtualenv_support/wheel-*
rm virtualenv_support/argparse-*

%build
# Regenerate base64 embedded files
%{?with_python2:%{__python2} bin/rebuild-script.py}
%{?with_python3:%{__python3} bin/rebuild-script.py}

# Build code
%{?with_python2:%{py2_build}}

# Build docs on Fedora
%if %{with python3}
%{__python3} setup.py build_sphinx
rm -f build/sphinx/html/.buildinfo

%{py3_build}

# Build docs on Fedora
%{__python3} setup.py build_sphinx
rm -f build/sphinx/html/.buildinfo
%endif # with python3

%install
%if %{with python3}
%{py3_install}
# rename binaries to use python3
mv %{buildroot}/%{_bindir}/virtualenv %{buildroot}/%{_bindir}/py3-virtualenv
# The versioned 3.x script was removed from upstream. Add it back.
cp %{buildroot}/%{_bindir}/py3-virtualenv %{buildroot}/%{_bindir}/virtualenv-%{python3_version}
# For alternatives
touch %{buildroot}/%{_bindir}/virtualenv-3
touch %{buildroot}/%{_bindir}/virtualenv
%endif # with python3

%if %{with python2}
%{py2_install}
# The versioned 2.x script was removed from upstream. Add it back.
cp %{buildroot}/%{_bindir}/virtualenv %{buildroot}/%{_bindir}/virtualenv-%{python2_version}
mv %{buildroot}/%{_bindir}/virtualenv %{buildroot}/%{_bindir}/virtualenv-2
%endif


%if %{with python3}
%post -n python3-virtualenv
alternatives --add-slave python3 %{_bindir}/python%{python3_version} \
    %{_bindir}/virtualenv-3 \
    virtualenv-3 \
    %{_bindir}/virtualenv-%{python3_version}
alternatives --add-slave python3 %{_bindir}/python%{python3_version} \
    %{_bindir}/virtualenv \
    virtualenv \
    %{_bindir}/virtualenv-3

%postun -n python3-virtualenv
# Do this only during uninstall process (not during update)
if [ $1 -eq 0 ]; then
    alternatives --keep-foreign --remove-slave python3 %{_bindir}/python%{python3_version} \
        virtualenv-3
    alternatives --keep-foreign --remove-slave python3 %{_bindir}/python%{python3_version} \
        virtualenv
fi
%endif


%if %{with python2}
%files -n python2-virtualenv
%license LICENSE.txt
%doc docs/*rst PKG-INFO AUTHORS.txt

%{python2_sitelib}/*
%{_bindir}/virtualenv-2
%{_bindir}/virtualenv-%{python2_version}
%endif

%if %{with python3}
# Include sphinx docs on Fedora
%files -n python-virtualenv-doc
%doc build/sphinx/*

%files -n python3-virtualenv
%license LICENSE.txt
%doc docs/*rst PKG-INFO AUTHORS.txt
%{_bindir}/py3-virtualenv
%ghost %{_bindir}/virtualenv
%ghost %{_bindir}/virtualenv-3
%{_bindir}/virtualenv-%{python3_version}
%{python3_sitelib}/virtualenv.py
%{python3_sitelib}/virtualenv_support/
%{python3_sitelib}/virtualenv-*.egg-info/
%{python3_sitelib}/__pycache__/*
%endif  # with python3



%changelog
* Wed Feb 01 2023 Miro HronÄok <mhroncok@redhat.com> - 15.1.0-22
- Add a custom error message when users attempt to create Python 3.11+ virtual environments
- Resolves: rhbz#2165702

* Wed Jul 28 2021 Tomas Orsava <torsava@redhat.com> - 15.1.0-21
- Adjusted the postun scriptlets to enable upgrading to RHEL 9
- Resolves: rhbz#1933055

* Thu Mar 18 2021 Lumír Balhar <lbalhar@redhat.com> - 15.1.0-20
- Use python-version-specific wheels from Python modules
Resolves: rhbz#1917971

* Fri Jun 21 2019 Miro Hrončok <mhroncok@redhat.com> - 15.1.0-19
- Use wheels from RPM packages (rhbz#1659550) (rhbz#1659551)
- Fail with a warning on Python versions < 2.7

* Thu Apr 25 2019 Tomas Orsava <torsava@redhat.com> - 15.1.0-18
- Bumping due to problems with modular RPM upgrade path
- Resolves: rhbz#1695587

* Fri Dec 14 2018 Miro Hrončok <mhroncok@redhat.com> - 15.1.0-17
- Don't fail on missing certifi's cert bundle
- Resolves: rhbz#1659440

* Wed Nov 28 2018 Tomas Orsava <torsava@redhat.com> - 15.1.0-16
- Provide the package name `virtualenv` and the /usr/bin/virtualenv binary
- Resolves: rhbz#1649958

* Thu Oct 04 2018 Lumír Balhar <lbalhar@redhat.com> - 15.1.0-15
- Fix alternatives - post and postun sections only with python3
- Resolves: rhbz#1633534

* Mon Oct 01 2018 Lumír Balhar <lbalhar@redhat.com> - 15.1.0-14
- Add alternatives for virtualenv-3
- Resolves: rhbz#1633534

* Wed Aug 15 2018 Lumír Balhar <lbalhar@redhat.com> - 15.1.0-13
- Remove virtualenv-3 executable. This will be provided by python3 module.
- Resolves: rhbz#1615727

* Wed Aug 08 2018 Lumír Balhar <lbalhar@redhat.com> - 15.1.0-12
- Remove unversioned binaries from python2 subpackage
- Resolves: rhbz#1613343

* Sat Aug 04 2018 Lumír Balhar <lbalhar@redhat.com> - 15.1.0-11
- Fixed conditions

* Tue Jul 31 2018 Lumír Balhar <lbalhar@redhat.com> - 15.1.0-10
- Switch python3 coditions to bcond

* Tue Jul 17 2018 Tomas Orsava <torsava@redhat.com> - 15.1.0-9
- BuildRequire also python36-rpm-macros as part of the python36 module build

* Wed Jul 04 2018 Miro Hrončok <mhroncok@redhat.com> - 15.1.0-8
- Add a bcond for python2

* Thu Jun 14 2018 Tomas Orsava <torsava@redhat.com> - 15.1.0-7
- Switch to using Python 3 version of sphinx

* Mon Apr 30 2018 Tomas Orsava <torsava@redhat.com> - 15.1.0-6
- Require the python36-devel package when building for the python36 module

* Wed Feb 28 2018 Iryna Shcherbina <ishcherb@redhat.com> - 15.1.0-5
- Update Python 2 dependency declarations to new packaging standards
  (See https://fedoraproject.org/wiki/FinalizingFedoraSwitchtoPython3)

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 15.1.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Fri Sep 29 2017 Troy Dawson <tdawson@redhat.com> - 15.1.0-3
- Cleanup spec file conditionals

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 15.1.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Mon Jun 12 2017 Steve Milner <smilner@redhat.com> - 15.1.0-1
- Update to 15.1.0 per https://bugzilla.redhat.com/show_bug.cgi?id=1454962

* Fri Feb 17 2017 Michal Cyprian <mcyprian@redhat.com> - 15.0.3-6
- Check if exec_dir exists before listing it's content during venv create process

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 15.0.3-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Wed Jan  4 2017 Steve Milner <smilner@redhat.com> - 15.0.3-4
- Updated version binaries per discussion at bz#1385240.

* Tue Dec 13 2016 Stratakis Charalampos <cstratak@redhat.com> - 15.0.3-3
- Rebuild for Python 3.6

* Mon Oct 17 2016 Steve Milner <smilner@redhat.com> - 15.0.3-2
- Added MAJOR symlinks per bz#1385240.

* Mon Aug  8 2016 Steve Milner <smilner@redhat.com> - 15.0.3-1
- Update for upstream release.

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 14.0.6-2
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Sun Feb 21 2016 Orion Poplawski <orion@cora.nwra.com> - 14.0.6-1
- Update to 14.0.6

* Tue Feb 2 2016 Orion Poplawski <orion@cora.nwra.com> - 13.1.2-4
- Modernize spec
- Fix python3 package file ownership

* Wed Dec 2 2015 Orion Poplawski <orion@cora.nwra.com> - 13.1.2-3
- Move documentation to separate package (bug #1219139)

* Wed Oct 14 2015 Robert Kuska <rkuska@redhat.com> - 13.1.2-2
- Rebuilt for Python3.5 rebuild

* Mon Aug 24 2015 Steve Milner <smilner@redhat.com> - 13.1.2-1
- Update for upstream release.

* Thu Jun 18 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 12.0.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Mon Mar 16 2015 Matej Stuchlik <mstuchli@redhat.com> - 12.0.7-1
- Update to 12.0.7

* Thu Jan 15 2015 Matthias Runge <mrunge@redhat.com> - 1.11.6-2
- add a python3-package, thanks to Matej Stuchlik (rhbz#1179150)

* Wed Jul 09 2014 Matthias Runge <mrunge@redhat.com> - 1.11.6-1
- update to 1.11.6:
  Upstream updated setuptools to 3.6, updated pip to 1.5.6

* Sun Jun 08 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.10.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Thu Aug 15 2013 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.10.1-1
- Upstream upgraded pip to v1.4.1
- Upstream upgraded setuptools to v0.9.8 (fixes CVE-2013-1633)

* Sun Aug 04 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.9.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Tue May 14 2013 Toshio Kuratomi <toshio@fedoraproject.org> - 1.9.1-1
- Update to upstream 1.9.1 because of security issues with the bundled
  python-pip in older releases.  This is just a quick fix until a
  python-virtualenv maintainer can unbundle the python-pip package
  see: https://bugzilla.redhat.com/show_bug.cgi?id=749378

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.7.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Aug 14 2012 Steve Milner <me@stevemilner.org> - 1.7.2-1
- Update for upstream bug fixes.
- Added path for versioned binary.
- Patch no longer required.

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.7.1.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Wed Mar 14 2012 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.7.1.2-1
- Update for upstream bug fixes.
- Added patch for sphinx building

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Dec 20 2011 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.7-1
- Update for https://bugzilla.redhat.com/show_bug.cgi?id=769067

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.5.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Sat Oct 16 2010 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.5.1-1
- Added _weakrefset requirement for Python 2.7.1.
- Add support for PyPy.
- Uses a proper temporary dir when installing environment requirements.
- Add --prompt option to be able to override the default prompt prefix.
- Add fish and csh activate scripts.

* Thu Jul 22 2010 David Malcolm <dmalcolm@redhat.com> - 1.4.8-4
- Rebuilt for https://fedoraproject.org/wiki/Features/Python_2.7/MassRebuild

* Wed Jul  7 2010 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.4.8-3
- Fixed EPEL installation issue from BZ#611536

* Wed Jun  9 2010 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.4.8-2
- Only replace the python shebang on the first line (Robert Buchholz)

* Wed Apr 28 2010 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.4.8-1
- update pip to 0.7
- move regen-docs into bin/
- Fix #31, make activate_this.py work on Windows (use Lib/site-packages)
unset PYTHONHOME envioronment variable -- first step towards fixing the PYTHONHOME issue; see e.g. https://bugs.launchpad.net/virtualenv/+bug/290844
- unset PYTHONHOME in the (Unix) activate script (and reset it in deactivate())
- use the activate.sh in virtualenv.py via running bin/rebuild-script.py
- add warning message if PYTHONHOME is set

* Fri Apr 2 2010 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.4.6-1
- allow script creation without setuptools
- fix problem with --relocate when bin/ has subdirs (fixes #12)
- Allow more flexible .pth file fixup
- make nt a required module, along with posix. it may not be a builtin module on jython
- don't mess with PEP 302-supplied __file__, from CPython, and merge in a small startup optimization for Jython, from Jython

* Tue Dec 22 2009 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.4.3-1
- Updated for upstream release.

* Thu Nov 12 2009 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.4.2-1
- Updated for upstream release.

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Tue Apr 28 2009 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.3.3-1
- Updated for upstream release.

* Thu Feb 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Thu Dec 25 2008 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.3.2-1
- Updated for upstream release.

* Thu Dec 04 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 1.3.1-4
- Rebuild for Python 2.6

* Mon Dec  1 2008 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.3.1-3
- Added missing dependencies.

* Sat Nov 29 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 1.3.1-2
- Rebuild for Python 2.6

* Fri Nov 28 2008 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.3.1-1
- Updated for upstream release

* Sun Sep 28 2008 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.3-1
- Updated for upstream release

* Sat Aug 30 2008 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.2-1
- Updated for upstream release

* Fri Aug 29 2008 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.1-3
- Updated from review notes

* Thu Aug 28 2008 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.1-2
- Updated from review notes

* Tue Aug 26 2008 Steve 'Ashcrow' Milner <me@stevemilner.org> - 1.1-1
- Initial Version
