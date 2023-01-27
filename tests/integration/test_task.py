# type: ignore

from botcity.maestro import (AutomationTask, AutomationTaskFinishStatus,
                             BotMaestroSDK)


def test_create_task(maestro: BotMaestroSDK):
    parameters = {
        "test_to_test": "testing",
        "integer_to_test": 123,
        "double_to_test": 1.0
    }
    task = maestro.create_task(activity_label="TestCI", parameters=parameters)
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
