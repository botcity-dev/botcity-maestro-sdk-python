# type: ignore

import os
import shutil
import tempfile
from uuid import uuid4

import pytest

from botcity.maestro import BotMaestroSDK

SERVER = os.getenv("BOTCITY_SERVER")
LOGIN = os.getenv("BOTCITY_LOGIN")
KEY = os.getenv("BOTCITY_KEY")


@pytest.fixture
def path_screenshot() -> str:
    return os.path.join('tests', 'screenshot.png')


@pytest.fixture
def tmp_folder() -> str:
    folder = tempfile.mkdtemp()
    yield folder
    shutil.rmtree(folder)


@pytest.fixture
def file(tmp_folder: str) -> str:
    filepath = f'{tmp_folder}/test.txt'
    with open(f'{tmp_folder}/test.txt', 'w') as file:
        file.write('Create a new text file!')
    yield filepath


@pytest.fixture
def maestro_test_to_login():
    sdk = BotMaestroSDK()
    yield sdk
    sdk.logoff()


@pytest.fixture(scope="session")
def maestro():
    sdk = BotMaestroSDK()
    sdk.login(server=SERVER, login=LOGIN, key=KEY)
    yield sdk
    sdk.logoff()


@pytest.fixture(scope="session")
def credential_label():
    label = f"testing-{uuid4()}"
    yield label


@pytest.fixture(scope="session")
def credential_key():
    label = f"testing-{uuid4()}"
    yield label


@pytest.fixture(scope="session")
def task(maestro: BotMaestroSDK, activity_label: str):
    parameters = {
        "test_to_test": "testing",
        "integer_to_test": 123,
        "double_to_test": 1.0
    }
    task = maestro.create_task(activity_label=activity_label, parameters=parameters)
    yield task


@pytest.fixture(scope="session")
def activity_label():
    return 'TestCI'


@pytest.fixture(scope="session")
def activity_label_to_log():
    return f'TestCI-{uuid4()}'
