"""Broker error type, kept separate to avoid import cycles."""


class BrokerError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message
