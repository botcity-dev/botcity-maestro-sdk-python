# type: ignore

import pytest

from botcity.maestro import BotMaestroSDK


def test_create_credential(maestro: BotMaestroSDK, credential_label, credential_key):
    maestro.create_credential(label=credential_label, key=credential_key, value="testing")


@pytest.mark.depends(on=["test_create_credential"])
def test_get_credential(maestro: BotMaestroSDK, credential_label, credential_key):
    credential = maestro.get_credential(label=credential_label, key=credential_key)
    assert credential == 'testing'

@pytest.mark.depends(on=["test_get_credential"])
def test_update_credential(maestro: BotMaestroSDK, credential_label, credential_key):
    maestro.update_credential(label=credential_label, key=credential_key, new_value="testing-update")
    credential = maestro.get_credential(label=credential_label, key=credential_key)
    assert credential == 'testing-update'

@pytest.mark.depends(on=["test_update_credential"])
def test_remove_credential(maestro: BotMaestroSDK, credential_label, credential_key):
    maestro.remove_credential(label=credential_label, key=credential_key)
    with pytest.raises(ValueError):
        maestro.get_credential(label=credential_label, key=credential_key)
