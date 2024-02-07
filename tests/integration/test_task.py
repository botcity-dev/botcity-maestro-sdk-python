# type: ignore
import datetime
from random import randint

import pytest

from botcity.maestro import (AutomationTask, AutomationTaskFinishStatus,
                             BotMaestroSDK)


def test_create_task(maestro: BotMaestroSDK):
    parameters = {
        "test_to_test": "testing",
        "integer_to_test": 123,
        "double_to_test": 1.0
    }
    task = maestro.create_task(activity_label="TestCI", parameters=parameters,
                               min_execution_date=datetime.datetime.now() + datetime.timedelta(hours=1),
                               priority=randint(0, 10))
    assert task


def test_get_task(maestro: BotMaestroSDK, task: AutomationTask):
    task = maestro.get_task(task_id=str(task.id))
    assert isinstance(task, AutomationTask)


def test_interrupting_task(maestro: BotMaestroSDK, task: AutomationTask):
    maestro.interrupt_task(task_id=str(task.id))


def test_finish_task_to_success(maestro: BotMaestroSDK, task: AutomationTask):
    maestro.finish_task(
        task_id=str(task.id),
        message="Task Finished with Success.",
        status=AutomationTaskFinishStatus.SUCCESS
    )
    task = maestro.get_task(task_id=str(task.id))
    assert task.finish_status == AutomationTaskFinishStatus.SUCCESS


def test_finish_task_to_partially_completed(maestro: BotMaestroSDK, task: AutomationTask):
    maestro.finish_task(
        task_id=str(task.id),
        message="Task Finished with partially completed.",
        status=AutomationTaskFinishStatus.PARTIALLY_COMPLETED
    )
    task = maestro.get_task(task_id=str(task.id))
    assert task.finish_status == AutomationTaskFinishStatus.PARTIALLY_COMPLETED


def test_finish_task_to_failed(maestro: BotMaestroSDK, task: AutomationTask):
    maestro.finish_task(
        task_id=str(task.id),
        message="Task Finished with failed.",
        status=AutomationTaskFinishStatus.FAILED
    )
    task = maestro.get_task(task_id=str(task.id))
    assert task.finish_status == AutomationTaskFinishStatus.FAILED

def test_finish_task_report_no_items(maestro: BotMaestroSDK, task: AutomationTask):
    maestro.finish_task(
        task_id=str(task.id),
        message="Task Finished OK.",
        status=AutomationTaskFinishStatus.SUCCESS,
    )
    task = maestro.get_task(task_id=str(task.id))
    assert task.finish_status == AutomationTaskFinishStatus.SUCCESS
    assert task.total_items == 0
    assert task.processed_items == 0
    assert task.failed_items == 0

def test_finish_task_report_items(maestro: BotMaestroSDK, task: AutomationTask):
    maestro.finish_task(
        task_id=str(task.id),
        message="Task Finished with success.",
        status=AutomationTaskFinishStatus.SUCCESS,
        total_items=10,
        processed_items=5,
        failed_items=5
    )
    task = maestro.get_task(task_id=str(task.id))
    assert task.finish_status == AutomationTaskFinishStatus.SUCCESS
    assert task.total_items == 10
    assert task.processed_items == 5
    assert task.failed_items == 5


def test_finish_task_report_total_and_processed(maestro: BotMaestroSDK, task: AutomationTask):
    maestro.finish_task(
        task_id=str(task.id),
        message="Task Finished with success.",
        status=AutomationTaskFinishStatus.SUCCESS,
        total_items=10,
        processed_items=5
    )
    task = maestro.get_task(task_id=str(task.id))
    assert task.finish_status == AutomationTaskFinishStatus.SUCCESS
    assert task.total_items == 10
    assert task.processed_items == 5
    assert task.failed_items == 5


def test_finish_task_report_total_and_failed(maestro: BotMaestroSDK, task: AutomationTask):
    maestro.finish_task(
        task_id=str(task.id),
        message="Task Finished with success.",
        status=AutomationTaskFinishStatus.SUCCESS,
        total_items=10,
        failed_items=5
    )
    task = maestro.get_task(task_id=str(task.id))
    assert task.finish_status == AutomationTaskFinishStatus.SUCCESS
    assert task.total_items == 10
    assert task.processed_items == 5
    assert task.failed_items == 5


def test_finish_task_report_processed_and_failed(maestro: BotMaestroSDK, task: AutomationTask):
    maestro.finish_task(
        task_id=str(task.id),
        message="Task Finished with success.",
        status=AutomationTaskFinishStatus.SUCCESS,
        processed_items=5,
        failed_items=5
    )
    task = maestro.get_task(task_id=str(task.id))
    assert task.finish_status == AutomationTaskFinishStatus.SUCCESS
    assert task.total_items == 10
    assert task.processed_items == 5
    assert task.failed_items == 5


def test_finish_task_report_error_invalid_total_items(maestro: BotMaestroSDK, task: AutomationTask):
    with pytest.raises(ValueError):
        maestro.finish_task(
            task_id=str(task.id),
            message="Task Finished with success.",
            status=AutomationTaskFinishStatus.SUCCESS,
            total_items=10,
            processed_items=6,
            failed_items=5
        )
