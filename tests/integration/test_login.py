# type: ignore

import pytest

import conftest
from botcity.maestro import BotMaestroSDK


def test_login_error_server_not_found(maestro_test_to_login: BotMaestroSDK):
    with pytest.raises(ValueError):
        maestro_test_to_login.login(server="testing", login=conftest.LOGIN, key=conftest.KEY)


def test_login_error_in_login(maestro_test_to_login: BotMaestroSDK):
    with pytest.raises(ValueError):
        maestro_test_to_login.login(server=conftest.SERVER, login="testing", key=conftest.KEY)


def test_login_error_in_key(maestro_test_to_login: BotMaestroSDK):
    with pytest.raises(ValueError):
        maestro_test_to_login.login(server=conftest.SERVER, login=conftest.LOGIN, key="testing")


def test_login_error_in_server_none(maestro_test_to_login: BotMaestroSDK):
    with pytest.raises(ValueError):
        maestro_test_to_login.login(login=conftest.LOGIN, key=conftest.KEY)


def test_login_error_in_login_none(maestro_test_to_login: BotMaestroSDK):
    with pytest.raises(ValueError):
        maestro_test_to_login.login(server=conftest.SERVER, key=conftest.KEY)


def test_login_error_in_key_none(maestro_test_to_login: BotMaestroSDK):
    with pytest.raises(ValueError):
        maestro_test_to_login.login(server=conftest.SERVER, login=conftest.LOGIN)


def test_login_success(maestro_test_to_login: BotMaestroSDK):
    maestro_test_to_login.login(server=conftest.SERVER, login=conftest.LOGIN, key=conftest.KEY)
    assert maestro_test_to_login.access_token
    assert maestro_test_to_login.is_online
