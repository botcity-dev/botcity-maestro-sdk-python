# type: ignore

import os

import pytest

from botcity.maestro import AutomationTask, BotMaestroSDK


def test_post_artifact(maestro: BotMaestroSDK, file: str, task: AutomationTask):
    maestro.post_artifact(
        task_id=task.id,
        artifact_name="My Artifact",
        filepath=file
    )


@pytest.mark.depends(name="test_post_artifact")
def test_list_artifacts(maestro: BotMaestroSDK):
    list_artifact = maestro.list_artifacts()
    assert len(list_artifact) > 0


@pytest.mark.depends(name="test_list_artifacts")
def test_get_artifact(maestro: BotMaestroSDK, tmp_folder: str):
    list_artifact = maestro.list_artifacts()
    name, content = maestro.get_artifact(artifact_id=list_artifact[0].id)
    filepath = f"{tmp_folder}/{name}"

    with open(filepath, "wb") as file:
        file.write(content)
    assert os.path.exists(filepath) and os.path.getsize(filepath) > 0
