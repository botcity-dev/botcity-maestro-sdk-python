# type: ignore

from botcity.maestro import AutomationTask, BotMaestroSDK


def test_create_error(maestro: BotMaestroSDK, task: AutomationTask, path_screenshot: str):
    try:
        div = 0 / 0
        print(div)
    except Exception as error:
        maestro.error(task_id=task.id, exception=error, tags={"custom": "tag"}, attachments=[path_screenshot],
                      screenshot=path_screenshot)
