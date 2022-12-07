# type: ignore

import pytest

from botcity.maestro import BotMaestroSDK


def test_create_credential(maestro: BotMaestroSDK, credential_label, credential_key):
    maestro.create_credential(label=credential_label, key=credential_key, value="testing")


@pytest.mark.depends(on=["test_create_credential"])
def test_get_credential(maestro: BotMaestroSDK, credential_label, credential_key):
    credential = maestro.get_credential(label=credential_label, key=credential_key)
    assert credential == 'testing'
