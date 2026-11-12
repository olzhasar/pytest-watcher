from __future__ import annotations

import logging
from typing import List, Optional

from watchdog import events
from watchdog.utils.patterns import match_any_paths

from .trigger import Trigger

logger = logging.getLogger(__name__)
trigger = Trigger()


def _at_any_depth(patterns: List[str]) -> List[str]:
    """
    Keep the meaning relative patterns had before watchdog 7.

    watchdog < 7 matched patterns with PurePath.match(), which matches a relative
    pattern from the right, so "*.py" matched "tests/test_app.py".
    watchdog >= 7 uses PurePath.full_match(), which matches the whole path,
    so "*.py" only matches files in the watched directory itself.
    Adding a "**/" variant of every relative pattern gives the same result on both.
    """
    result = []
    for pattern in patterns:
        result.append(pattern)
        if not pattern.startswith(("/", "**/")):
            result.append("**/" + pattern)
    return result


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
        self._match_patterns = _at_any_depth(self._patterns)
        self._match_ignore_patterns = _at_any_depth(self._ignore_patterns)
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
            included_patterns=self._match_patterns,
            excluded_patterns=self._match_ignore_patterns,
        )

    def dispatch(self, event: events.FileSystemEvent) -> None:
        if self._is_event_watched(event):
            self._trigger.emit()
            if hasattr(event, "dest_path"):
                logger.info(
                    "Detected %s: %s -> %s",
                    event.event_type,
                    event.src_path,
                    event.dest_path,
                )
            else:
                logger.info("Detected %s: %s", event.event_type, event.src_path)
        else:
            logger.debug("Ignored event %s for %s", event.event_type, event.src_path)
