import pytest

from botcity.maestro import BotMaestroSDK, DataPool, DataPoolEntry
from botcity.maestro.datapool.enums import StateEnum
from conftest import DATAPOOL_LABEL


def test_create_datapool(maestro: BotMaestroSDK, pool: DataPool):
    pool = maestro.create_datapool(pool=pool)
    assert pool.is_active()


@pytest.mark.depends(name="test_create_datapool")
def test_get_datapool(maestro: BotMaestroSDK, pool: DataPool):
    new_pool = maestro.get_datapool(label=DATAPOOL_LABEL)
    assert pool.label == new_pool.label


@pytest.mark.depends(name="test_get_datapool")
def test_deactivate(pool: DataPool):
    pool.deactivate()
    assert pool.active is False
    assert pool.is_active() is False


@pytest.mark.depends(name="test_deactivate")
def test_activate(pool: DataPool):
    pool.activate()
    assert pool.active is True
    assert pool.is_active() is True


@pytest.mark.depends(name="test_activate")
def test_is_activated(pool: DataPool):
    assert pool.active is True
    assert pool.is_active() is True


@pytest.mark.depends(name="test_is_activated")
def test_create_entry(pool: DataPool, datapool_entry: DataPoolEntry):
    entry = pool.create_entry(entry=datapool_entry)
    assert entry.datapool_label == pool.label
    assert entry.state == StateEnum.PENDING
    assert entry.values == datapool_entry.values
    assert entry.priority == datapool_entry.priority


@pytest.mark.depends(name="test_create_entry")
def test_summary(pool: DataPool):
    summary = pool.summary()
    assert summary.get("countPending") == 1


@pytest.mark.depends(name="test_summary")
def test_is_empty(pool: DataPool):
    assert pool.is_empty() is False
    assert pool.has_next() is True


@pytest.mark.depends(name="test_is_empty")
def test_next(pool: DataPool):
    entry = pool.next(task_id=123)

    assert entry.get_value("integration_test_value") == entry["integration_test_value"]
    assert entry.task_id == "123"

    entry.report_done()