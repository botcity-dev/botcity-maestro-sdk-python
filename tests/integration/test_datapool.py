import pytest

from botcity.maestro import BotMaestroSDK, DataPool, DataPoolEntry
from botcity.maestro.datapool.enums import StateEnum
from conftest import DATAPOOL_LABEL


def test_create_datapool(maestro: BotMaestroSDK, pool: DataPool):
    pool = maestro.create_datapool(pool=pool)
    assert pool.is_activated()


@pytest.mark.depends(name="test_create_datapool")
def test_get_datapool(maestro: BotMaestroSDK, pool: DataPool):
    new_pool = maestro.get_datapool(label=DATAPOOL_LABEL)
    assert pool.datapool_id == new_pool.datapool_id


@pytest.mark.depends(name="test_get_datapool")
def test_deactivate(pool: DataPool):
    pool.deactivate()
    assert pool.active is False


@pytest.mark.depends(name="test_deactivate")
def test_activate(pool: DataPool):
    pool.activate()
    assert pool.active is True


@pytest.mark.depends(name="test_activate")
def test_is_activated(pool: DataPool):
    assert pool.active is True


@pytest.mark.depends(name="test_is_activated")
def test_create_entry(pool: DataPool, datapool_entry: DataPoolEntry):
    entry = pool.create_entry(entry=datapool_entry)
    assert entry.get("dataPoolLabel") == pool.label
    assert entry.get("state") == StateEnum.PENDING
    assert entry.get("values") == datapool_entry.values
    assert entry.get("priority") == datapool_entry.priority


@pytest.mark.depends(name="test_create_entry")
def test_summary(pool: DataPool):
    summary = pool.summary()
    assert summary.get("countPending") == 1


@pytest.mark.depends(name="test_summary")
def test_is_empty(pool: DataPool):
    assert pool.is_empty() is False


@pytest.mark.depends(name="test_is_empty")
def test_next(pool: DataPool):
    entry = pool.next(task_id=123)
    entry.state = "DONE"
    entry.save()
