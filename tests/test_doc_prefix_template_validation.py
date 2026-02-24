import unittest

import doc_prefix


class DocPrefixTemplateValidationTests(unittest.TestCase):
    def test_validate_prefix_template_error_mentions_all_supported_placeholders(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            doc_prefix.validate_prefix_template("{bad}")

        message = str(ctx.exception)
        placeholders = getattr(doc_prefix, "SUPPORTED_PREFIX_PLACEHOLDERS", None)
        if placeholders is None:
            placeholders = tuple(
                f"{{{name}}}" for name in doc_prefix.SUPPORTED_PREFIX_TEMPLATE_FIELDS
            )

        for token in placeholders:
            self.assertIn(token, message)


if __name__ == "__main__":
    unittest.main()
