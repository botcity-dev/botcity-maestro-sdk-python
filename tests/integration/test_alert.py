# type: ignore

from botcity.maestro import AlertType, AutomationTask, BotMaestroSDK

# TODO: Create test to send message


def test_create_alert_info(maestro: BotMaestroSDK, task: AutomationTask):
    maestro.alert(
        task_id=str(task.id),
        title="Info Alert",
        message="This is an info alert",
        alert_type=AlertType.INFO
    )


def test_create_alert_warn(maestro: BotMaestroSDK, task: AutomationTask):
    maestro.alert(
        task_id=str(task.id),
        title="Info Warn",
        message="This is an info warn",
        alert_type=AlertType.WARN
    )


def test_create_alert_error(maestro: BotMaestroSDK, task: AutomationTask):
    maestro.alert(
        task_id=str(task.id),
        title="Info Error",
        message="This is an info error",
        alert_type=AlertType.ERROR
    )
