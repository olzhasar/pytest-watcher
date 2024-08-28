from __future__ import annotations

import logging
from typing import List, Optional

from watchdog import events
from watchdog.utils.patterns import match_any_paths

from .trigger import Trigger

trigger = Trigger()


class EventHandler:
    EVENTS_WATCHED = {
        events.EVENT_TYPE_CREATED,
        events.EVENT_TYPE_DELETED,
        events.EVENT_TYPE_MODIFIED,
        events.EVENT_TYPE_MOVED,
    }

    def __init__(
        self,
        trigger: Trigger,
        patterns: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
    ):
        self._patterns = patterns or ["*.py"]
        self._ignore_patterns = ignore_patterns or []
        self._trigger = trigger

    @property
    def patterns(self) -> List[str]:
        return self._patterns

    @property
    def ignore_patterns(self) -> List[str]:
        return self._ignore_patterns

    def _is_event_watched(self, event: events.FileSystemEvent) -> bool:
        if event.event_type not in self.EVENTS_WATCHED:
            return False

        paths = [event.src_path]
        if hasattr(event, "dest_path"):
            # For file moved type events we are also interested in the destination
            paths.append(event.dest_path)

        return match_any_paths(
            paths,
            included_patterns=self.patterns,
            excluded_patterns=self.ignore_patterns,
        )

    def dispatch(self, event: events.FileSystemEvent) -> None:
        if self._is_event_watched(event):
            self._trigger.emit()
            logging.info(f"{event.src_path} {event.event_type}")
        else:
            logging.debug(f"IGNORED event: {event.event_type} src: {event.src_path}")
