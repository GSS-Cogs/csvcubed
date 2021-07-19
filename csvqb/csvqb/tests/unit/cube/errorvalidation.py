import unittest
import pandas as pd
from typing import List

from csvqb.models.cube import *
from csvqb.tests.unit.unittestbase import UnitTestBase


class InternalApiLoaderTests(UnitTestBase):

    def test_column_not_configured_error(self):
        """
            If the CSV data contains a column which is not defined, we get an error.
        """

        data = pd.DataFrame({
            "Some Dimension": ["A", "B", "C"]
        })

        metadata = CatalogMetadata("Some Dataset")
        columns = []
        cube = Cube(metadata, data, columns)
        validation_errors = cube.validate()

        self.assertEqual(1, len(validation_errors))
        error = validation_errors[0]
        self.assertTrue("Some Dimension" in error.message)

    def test_column_title_wrong_error(self):
        """
            If the Cube object contains a column title which is not defined in the CSV data, we get an error.
        """

        data = pd.DataFrame()

        metadata = CatalogMetadata("Some Dataset")
        columns: List[CsvColumn] = [
            SuppressedCsvColumn("Some Column Title")
        ]
        cube = Cube(metadata, data, columns)
        validation_errors = cube.validate()

        self.assertEqual(1, len(validation_errors))
        error = validation_errors[0]
        self.assertTrue("Some Column Title" in error.message)


if __name__ == '__main__':
    unittest.main()
