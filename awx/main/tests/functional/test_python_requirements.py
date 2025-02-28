import os
import re
import pytest

from django.conf import settings


def test_bootstrap_consistent():
    with open('Makefile', 'r') as f:
        mk_data = f.read()
    bootstrap_reqs = None
    for line in mk_data.split('\n'):
        if line.startswith('VENV_BOOTSTRAP'):
            parts = line.split()
            bootstrap_reqs = parts[parts.index('?=') + 1 :]
            break
    else:
        raise RuntimeError('Cound not find bootstrap line')

    req_data = None
    with open('requirements/requirements.txt', 'r') as f:
        req_data = f.read()

    different_requirements = []
    for req in bootstrap_reqs:
        boot_req_name, _ = req.split('=', 1)
        for line in req_data.split('\n'):
            if '=' not in line:
                continue
            req_name, _ = line.split('=', 1)
            if req_name == boot_req_name:
                if req != line:
                    different_requirements.append((req, line))
                break

    assert not different_requirements


@pytest.mark.skip(reason="This test needs some love")
def test_env_matches_requirements_txt():
    from pip.operations import freeze

    def check_is_in(src, dests):
        if src not in dests:
            print("%s not in" % src)
            return False
        return True

    def skip_line(line):
        return (
            line == ''
            or line.strip().startswith('#')
            or line.strip().startswith('git')
            or line.startswith('-e')
            or '## The following requirements were added by pip freeze' in line
        )

    base_dir = settings.BASE_DIR
    requirements_path = os.path.join(base_dir, '../', 'requirements/requirements.txt')

    reqs_actual = []
    xs = freeze.freeze(local_only=True)
    for x in xs:
        if skip_line(x):
            continue
        x = x.lower()
        (pkg_name, pkg_version) = x.split('==')
        reqs_actual.append([pkg_name, pkg_version])

    reqs_expected = []
    with open(requirements_path) as f:
        for line in f:
            line = line.partition('#')[0]
            line = line.rstrip().lower()
            # TODO: process git requiremenst and use egg
            if skip_line(line):
                continue

            '''
            Special case pkg_name[pkg_subname]==version
            For this case, we strip out [pkg_subname]
            '''
            (pkg_name, pkg_version) = line.split('==')
            pkg_name = re.sub(r'\[.*\]', '', pkg_name)
            reqs_expected.append([pkg_name, pkg_version])

    not_found = []
    for r in reqs_expected:
        res = check_is_in(r, reqs_actual)
        if res is False:
            not_found.append(r)

    if len(not_found) > 0:
        raise RuntimeError("%s not found in \n\n%s" % (not_found, reqs_actual))
