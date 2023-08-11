# type: ignore

import os
import random
import shutil
import tempfile
from datetime import datetime, timedelta
from random import randint
from uuid import uuid4

import pytest

from botcity.maestro import *

SERVER = os.getenv("BOTCITY_SERVER")
LOGIN = os.getenv("BOTCITY_LOGIN")
KEY = os.getenv("BOTCITY_KEY")
ACTIVITY_LABEL_TO_LOG = f'TestCI-{uuid4()}'
DATAPOOL_LABEL = f"testing-{uuid4()}"


@pytest.fixture
def path_screenshot() -> str:
    return os.path.abspath(os.path.join('tests', 'screenshot.png'))


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
def pool(activity_label: str, maestro: BotMaestroSDK) -> DataPool:
    pool = DataPool(label=DATAPOOL_LABEL, default_automation=activity_label)
    yield pool
    pool._delete()


@pytest.fixture(scope="session")
def task(maestro: BotMaestroSDK, activity_label: str):
    parameters = {
        "test_to_test": "testing",
        "integer_to_test": 123,
        "double_to_test": 1.0
    }
    task = maestro.create_task(activity_label=activity_label, parameters=parameters,
                               min_execution_date=datetime.now() + timedelta(hours=1),
                               priority=randint(0, 10)
                               )
    yield task


@pytest.fixture(scope="session")
def activity_label():
    return 'TestCI'


@pytest.fixture()
def datapool_entry():
    integration_test_value = random.randint(0, 100)
    priority = random.randint(0, 10)
    yield DataPoolEntry(values={"integration_test_value": integration_test_value}, priority=priority)
