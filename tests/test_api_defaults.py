import os
import unittest
from html.parser import HTMLParser
from unittest.mock import patch

from app import app


class ApiInputs(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.fields = {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "input" and attrs.get("id", "").startswith("test-api-"):
            self.fields[attrs["id"]] = attrs


class ApiDefaultsTest(unittest.TestCase):
    def render(self, base_url="", model=""):
        with patch.dict(os.environ, {
            "MODELTRACE_API_BASE_URL": base_url,
            "MODELTRACE_API_MODEL": model,
            "MODELTRACE_API_KEY": "not-a-real-secret-marker",
        }):
            response = app.test_client().get("/")
        self.assertEqual(response.status_code, 200)
        return response.get_data(as_text=True)

    def test_configured_route_is_rendered_without_a_key(self):
        html = self.render("http://gateway.example/v1", "cx/gpt-6.1-sol")
        fields = ApiInputs(html).fields
        self.assertEqual(fields["test-api-base"].get("value"), "http://gateway.example/v1")
        self.assertEqual(fields["test-api-model"].get("value"), "cx/gpt-6.1-sol")
        self.assertEqual(fields["test-api-key"].get("value", ""), "")
        self.assertNotIn("not-a-real-secret-marker", html)

    def test_unconfigured_route_remains_empty_and_required(self):
        fields = ApiInputs(self.render()).fields
        for name in ("test-api-base", "test-api-model"):
            self.assertEqual(fields[name].get("value", ""), "")
            self.assertIn("required", fields[name])

    def test_defaults_are_html_escaped(self):
        model = 'cx/example" onfocus="alert(1)'
        fields = ApiInputs(self.render("http://gateway.example/v1", model)).fields
        self.assertEqual(fields["test-api-model"].get("value"), model)
        self.assertNotIn("onfocus", fields["test-api-model"])


if __name__ == "__main__":
    unittest.main()
