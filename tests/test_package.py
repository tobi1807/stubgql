from importlib.metadata import version

import stubgql


def test_version_matches_installed_package_metadata():
    assert stubgql.__version__ == version("stubgql")


def test_errors_share_a_public_base_class():
    assert issubclass(stubgql.StubgqlError, Exception)
