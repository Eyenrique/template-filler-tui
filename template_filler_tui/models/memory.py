"""Session memory for placeholder values — temporary, not persisted."""


class Memory:
    """Manages placeholder value storage for the current session.

    Session values are temporary — they last for the duration of the app
    and are lost when it closes. Persistent values are managed through the
    Placeholder Registry's Value column, not through this class.
    """

    def __init__(self):
        self._session: dict[str, str] = {}

    def get(self, name: str) -> str | None:
        """Look up a session value."""
        return self._session.get(name)

    def set_session(self, name: str, value: str):
        """Store a value for the current session."""
        self._session[name] = value
