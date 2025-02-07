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
        Check that the external CSS file applied to the page includes the Google Font (e.g. 'Roboto').
        """
        # Get the index page
        response = self.client.get('/')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Ensure there is a link tag that references the external CSS file
        css_link_tag = soup.find("link", rel="stylesheet", href=lambda href: href and "static/css/style.css" in href)
        self.assertIsNotNone(css_link_tag, "External CSS file link not found on index page")
        
        # Fetch the CSS file using the test client
        css_response = self.client.get(css_link_tag["href"])
        self.assertEqual(css_response.status_code, 200, "Failed to load external CSS file")
        
        css_content = css_response.get_data(as_text=True)
        # Check that the CSS contains the Google Font definition for the body element.
        self.assertIn("font-family: 'Roboto'", css_content, "Expected 'Roboto' font not found in external CSS")

    def test_color_palette_light_theme(self):
        """
        Verify that the CSS variables for the light theme are defined correctly.
        The test fetches the external stylesheet and checks that the CSS variables
        (for background, text, and accent colors) are defined with the expected values.
        """
        response = self.client.get('/')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Locate the link to the external stylesheet.
        css_link_tag = soup.find("link", rel="stylesheet", href=lambda href: href and "static/css/style.css" in href)
        self.assertIsNotNone(css_link_tag, "External CSS file link not found on index page")
        
        # Retrieve the external CSS file.
        css_response = self.client.get(css_link_tag["href"])
        self.assertEqual(css_response.status_code, 200, "Failed to load external CSS file")
        css_content = css_response.get_data(as_text=True)
        
        # Verify the expected light theme variable definitions.
        self.assertIn("--bg-primary: #ffffff", css_content, "Light theme background color not found")
        self.assertIn("--text-primary: #0a0a23", css_content, "Light theme text color not found")
        self.assertIn("--accent-color", css_content, "Accent color variable not found in light theme")

    def test_color_palette_dark_theme(self):
        """
        Verify that the CSS variables for the dark theme are defined correctly.
        For example, ensuring the dark background, light text, and accent colors are present
        in the external stylesheet.
        """
        response = self.client.get('/')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Locate the link to the external stylesheet.
        css_link_tag = soup.find("link", rel="stylesheet", href=lambda href: href and "static/css/style.css" in href)
        self.assertIsNotNone(css_link_tag, "External CSS file link not found on index page")
        
        # Retrieve the external CSS file.
        css_response = self.client.get(css_link_tag["href"])
        self.assertEqual(css_response.status_code, 200, "Failed to load external CSS file")
        css_content = css_response.get_data(as_text=True)
        
        # Check that the dark theme variables are present in the CSS file.
        # For example, you may check for a dark theme block or specific variable definitions.
        self.assertIn('[data-theme="dark"]', css_content, "Dark theme CSS block not found")
        self.assertIn("--bg-primary: #0a0a23", css_content, "Dark theme background color not found")
        self.assertIn("--text-primary: #f5f6f7", css_content, "Dark theme text color not found")
        self.assertIn("--accent-color", css_content, "Accent color variable not found in dark theme")

if __name__ == '__main__':
    unittest.main()