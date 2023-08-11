import json
from dataclasses import dataclass, field
from typing import Optional

import requests

from .enums import StateEnum


@dataclass
class DataPoolEntry:
    priority: int = 0
    values: dict = field(default_factory=lambda: {})
    datapool_label: str = None
    state: str = None
    entry_id: str = None
    task_id: int = None
    parent: str = None
    child: str = None
    date_register: str = None
    date_processing: str = None
    date_finished: str = None
    maestro: 'BotMaestroSDKInterface' = None  # noqa: F821

    def to_json(self) -> str:
        """
        Get properties class in dict.

        Returns: str

        """
        data = {"priority": self.priority, "values": self.values}
        return json.dumps(data)

    def json_to_update(self) -> str:
        """
        Create Json by properties to update.

        Returns: str

        """
        data = {
            "priority": self.priority,
            "values": self.values,
            "dataPoolLabel": self.datapool_label,
            "state": self.state,
            "taskId": self.task_id,
            "parent": self.parent,
            "child": self.child,
        }
        return json.dumps(data)

    def update_from_json(self, payload: bytes) -> 'DataPoolEntry':
        """

        Update properties by response endpoint Maestro.
        Args:
            payload: Response to endpoint Maestro.

        Returns: DataPoolEntry

        """
        values = json.loads(payload)
        self.entry_id = values.get("id")
        self.datapool_label = values.get('dataPoolLabel')
        self.state = values.get("state")
        self.values = values.get("values")
        self.task_id = values.get("taskId")
        self.priority = values.get("priority")
        self.parent = values.get("parent")
        self.child = values.get('child')
        self.date_register = values.get("dateRegister")
        self.date_processing = values.get("dateProcessing")
        self.date_finished = values.get("dateFinished")
        return self

    def get_value(self, key: str, default: Optional[str] = None) -> str:
        """
        Get value by key.

        Args:
            key: Key to get value.
            default: Default value if key not exists.

        Returns: str

        """
        return self.values.get(key, default)

    def __setattr__(self, key, value):
        if key == 'state':
            self._verify_state(state=value)
        self.__dict__[key] = value

    def __getitem__(self, item):
        if item in self.values:
            return self.values[item]
        return getattr(self, item)

    def __setitem__(self, key, value):
        if key in self.values:
            self.values[key] = value
            return
        setattr(self, key, value)

    def _verify_state(self, state: str):
        if self.state is None:
            return

        if self.state == StateEnum.PENDING:
            states = [StateEnum.PROCESSING]
            if state not in [StateEnum.PROCESSING]:
                raise ValueError(f"In state {state}, only change to states {','.join(states)} is allowed.")

        if self.state == StateEnum.PROCESSING:
            states = [StateEnum.TIMEOUT, StateEnum.DONE, StateEnum.ERROR]
            if state not in states:
                raise ValueError(f"In state {state}, only change to states {','.join(states)} is allowed.")

        if self.state == StateEnum.TIMEOUT:
            states = [StateEnum.DONE, StateEnum.ERROR]
            if state not in states:
                raise ValueError(f"In state {state}, only change to states {','.join(states)} is allowed.")

    def save(self) -> 'DataPoolEntry':
        """
        Update Entry in DataPool.

        Returns: dict
        """
        url = f'{self.maestro.server}/api/v2/datapool/{self.datapool_label}/entry/{self.entry_id}'
        data = self.json_to_update()
        with requests.post(url, data=data, headers=self.maestro._headers(), timeout=self.maestro.timeout) as req:
            if req.ok:
                self.update_from_json(payload=req.content)
                return self.update_from_json(req.content)
            req.raise_for_status()

    def _report(self, state: str):
        self.state = state
        self.save()

    def report_done(self):
        """
        Report state DONE to DataPool Entry.
        Returns: None

        """
        self._report(state=StateEnum.DONE)

    def report_error(self):
        """
        Report state ERROR to DataPool Entry.
        Returns: None

        """
        self._report(state=StateEnum.ERROR)
