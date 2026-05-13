"""
Testes unitários para TextExtractor.
Execute com: pytest tests/test_text_extractor.py -v
"""

from unittest.mock import Mock, patch

import pytest

from src.extractors.text_extractor import TextExtractor, TextPageResult


class TestTextExtractor:
    def setup_method(self):
        self.extractor = TextExtractor()

    @patch("os.path.exists", return_value=False)
    def test_extract_file_not_found(self, mock_exists):
        with pytest.raises(FileNotFoundError):
            self.extractor.extract("nonexistent.pdf")

    @patch("src.extractors.text_extractor.PdfReader")
    def test_extract_single_page(self, mock_pdf_reader):
        mock_page = Mock()
        mock_page.extract_text.return_value = "Texto da página 1"

        mock_reader = Mock()
        mock_reader.pages = [mock_page]

        mock_pdf_reader.return_value = mock_reader

        result = self.extractor.extract("test.pdf")

        assert len(result) == 1
        assert result[0].page_number == 1
        assert result[0].text_content == "Texto da página 1"

    @patch("src.extractors.text_extractor.PdfReader")
    def test_extract_multiple_pages(self, mock_pdf_reader):
        mock_pages = [
            Mock(extract_text_return_value=f"Texto página {i}")
            for i in range(1, 4)
        ]

        mock_reader = Mock()
        mock_reader.pages = mock_pages

        mock_pdf_reader.return_value = mock_reader

        result = self.extractor.extract("test.pdf")

        assert len(result) == 3
        assert result[0].page_number == 1
        assert result[1].page_number == 2
        assert result[2].page_number == 3

    @patch("src.extractors.text_extractor.PdfReader")
    def test_extract_empty_text_returns_empty_string(self, mock_pdf_reader):
        mock_page = Mock()
        mock_page.extract_text.return_value = None

        mock_reader = Mock()
        mock_reader.pages = [mock_page]

        mock_pdf_reader.return_value = mock_reader

        result = self.extractor.extract("test.pdf")

        assert result[0].text_content == ""

    def test_extract_as_dict_returns_correct_format(self):
        mock_page = TextPageResult(page_number=1, text_content="Test")
        expected_dict = {"page_number": 1, "text_content": "Test"}

        with patch.object(self.extractor, "extract", return_value=[mock_page]):
            result = self.extractor.extract_as_dict("test.pdf")
            assert result == [expected_dict]
