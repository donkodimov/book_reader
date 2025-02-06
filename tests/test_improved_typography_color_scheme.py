import unittest
from app import app
from bs4 import BeautifulSoup

class ImprovedTypographyColorSchemeTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_google_fonts_link_exists(self):
        """
        Ensure that a Google Fonts link is included in the index page for improved typography.
        (e.g., a link to https://fonts.googleapis.com for 'Roboto')
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.data, 'html.parser')
        google_font_link = soup.find('link', href=lambda href: href and 'fonts.googleapis.com' in href)
        self.assertIsNotNone(google_font_link, "Google Fonts link not found in index page")

    def test_body_font_family_contains_google_font(self):
        """
        Check that the body element’s font-family is updated to use a Google Font (e.g. 'Roboto').
        """
        response = self.client.get('/')
        soup = BeautifulSoup(response.data, 'html.parser')
        style_tag = soup.find('style')
        self.assertIsNotNone(style_tag, "Style tag not found in index page")
        style_content = style_tag.string
        # Expect the new typography CSS to include the Google Font in the body style.
        self.assertIn("font-family: 'Roboto'", style_content, "Expected 'Roboto' font not found in CSS")

    def test_color_palette_light_theme(self):
        """
        Verify that the CSS variables for the light theme are defined correctly.
        For example, ensuring the background and text colors have sufficient contrast.
        """
        response = self.client.get('/')
        soup = BeautifulSoup(response.data, 'html.parser')
        style_tag = soup.find('style')
        self.assertIsNotNone(style_tag, "Style tag not found in index page")
        style_content = style_tag.string
        
        # Check common light theme variables
        self.assertIn("--bg-primary: #ffffff", style_content, "Light theme background color not found")
        self.assertIn("--text-primary: #333333", style_content, "Light theme text color not found")
        self.assertIn("--accent-color", style_content, "Accent color variable not found in light theme")

    def test_color_palette_dark_theme(self):
        """
        Verify that the CSS variables for the dark theme are defined correctly.
        For example, ensuring the dark background, light text, and accent colors are present.
        """
        response = self.client.get('/')
        soup = BeautifulSoup(response.data, 'html.parser')
        style_tag = soup.find('style')
        self.assertIsNotNone(style_tag, "Style tag not found in index page")
        style_content = style_tag.string
        
        # Check that the dark theme block exists and contains the variables
        self.assertIn('[data-theme="dark"]', style_content, "Dark theme CSS block not found")
        self.assertIn("--bg-primary: #1a1a1a", style_content, "Dark theme background color not found")
        self.assertIn("--text-primary: #ffffff", style_content, "Dark theme text color not found")
        self.assertIn("--accent-color", style_content, "Accent color variable not found in dark theme")

if __name__ == '__main__':
    unittest.main()