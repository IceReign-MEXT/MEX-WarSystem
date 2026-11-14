import unittest

from preflight import validate_environment


VALID = {
    "BOT_TOKEN": "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi",
    "ADMIN_ID": "123456789",
    "MASTER_WALLET": "11111111111111111111111111111111",
    "HELIUS_API_KEY": "test-key-not-a-real-secret",
    "WEBHOOK_URL": "https://example.onrender.com",
}


class PreflightTests(unittest.TestCase):
    def test_valid_configuration_passes(self):
        self.assertEqual(validate_environment(VALID), [])

    def test_missing_values_are_reported_without_exposing_values(self):
        errors = validate_environment({})
        self.assertEqual(len(errors), 5)
        self.assertTrue(all("Missing required" in item for item in errors))

    def test_invalid_admin_id_is_rejected(self):
        env = {**VALID, "ADMIN_ID": "not-a-number"}
        self.assertTrue(any("ADMIN_ID" in item for item in validate_environment(env)))

    def test_http_webhook_is_rejected(self):
        env = {**VALID, "WEBHOOK_URL": "http://example.com"}
        self.assertTrue(any("WEBHOOK_URL" in item for item in validate_environment(env)))

    def test_webhook_path_is_rejected(self):
        env = {**VALID, "WEBHOOK_URL": "https://example.com/bot"}
        self.assertTrue(any("WEBHOOK_URL" in item for item in validate_environment(env)))

    def test_invalid_wallet_is_rejected(self):
        env = {**VALID, "MASTER_WALLET": "not-a-wallet"}
        self.assertTrue(any("MASTER_WALLET" in item for item in validate_environment(env)))


if __name__ == "__main__":
    unittest.main()
