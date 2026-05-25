class MockSmsClient:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def send_sms(self, phone_number: str, message: str) -> None:
        if self.should_fail:
            raise RuntimeError("Mock SMS failure")
