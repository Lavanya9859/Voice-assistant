import unittest
from unittest.mock import patch

from assistant_core import WEBSITE_CATEGORIES, WEBSITE_LINKS, VoiceAssistant


class WebsiteRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assistant = VoiceAssistant.__new__(VoiceAssistant)

    def test_categories_cover_each_supported_site_once(self) -> None:
        categorized_sites = [
            site
            for category_sites in WEBSITE_CATEGORIES.values()
            for site in category_sites
        ]

        self.assertEqual(len(categorized_sites), len(set(categorized_sites)))
        self.assertEqual(set(categorized_sites), set(WEBSITE_LINKS))

    def test_weather_and_maps_appear_in_available_sites(self) -> None:
        response = self.assistant._get_websites_list()

        self.assertIn("Weather & Maps: weather, google maps", response)

    def test_weather_and_maps_shortcuts_open_expected_urls(self) -> None:
        shortcuts = {
            "weather": "https://weather.com",
            "google maps": "https://maps.google.com",
        }

        for target, expected_url in shortcuts.items():
            with self.subTest(target=target), patch("assistant_core.webbrowser.open") as open_url:
                response = self.assistant._open_website(target)

            open_url.assert_called_once_with(expected_url)
            self.assertTrue(response.text.startswith("Opening "))


if __name__ == "__main__":
    unittest.main()
