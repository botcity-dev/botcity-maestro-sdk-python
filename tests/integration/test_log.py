# type: ignore

import datetime

import pytest

import conftest
from botcity.maestro import BotMaestroSDK, Column

columns = [
    Column(name="Date/Time", label="timestamp", width=300),
    Column(name="# Records", label="records", width=200),
    Column(name="Status", label="status", width=100),
]


def test_create_log(maestro: BotMaestroSDK):
    maestro.new_log(
        activity_label=conftest.ACTIVITY_LABEL_TO_LOG,
        columns=columns
    )


def test_new_log_entry(maestro: BotMaestroSDK):
    maestro.new_log_entry(
        activity_label=conftest.ACTIVITY_LABEL_TO_LOG,
        values={
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"),
            "records": "10",
            "status": "SUCCESS"
        }
    )


@pytest.mark.depends(name="test_new_log_entry")
def test_get_log(maestro: BotMaestroSDK):
    instant = (datetime.datetime.now() - datetime.timedelta(days=30))
    date = instant.strftime("%d/%m/%Y")
    data = maestro.get_log(activity_label=conftest.ACTIVITY_LABEL_TO_LOG, date=date)
    assert len(data) > 0


@pytest.mark.depends(on=["test_create_log", "test_get_log"])
def test_delete_log(maestro: BotMaestroSDK):
    maestro.delete_log(activity_label=conftest.ACTIVITY_LABEL_TO_LOG)
