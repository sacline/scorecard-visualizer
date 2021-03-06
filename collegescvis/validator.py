"""
validator.py
Copyright (C) <2017>  <S. Cline>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import json


class Validator(object):
    """Checks data from input files.

    The Validator class contains static methods for checking the input files
    needed to properly run the visualizer interface. It will raise errors if
    there is incorrect formatting that will prevent other parts of the program
    from working.
    """

    @staticmethod
    def check_data_types(data_types_file):
        """Check data_types files generated by the decoder script.

        Args:
            data_types: File object containing data types.

        Raises:
            TypeError: If the data in the file is the improper type.
            ValueError: If the data in the file is improperly formatted.
        """
        data_types = json.loads(data_types_file.readline())
        for data_type in data_types:
            if len(data_type) != 3:
                raise ValueError(
                    'Incorrect number of data types in ', data_type)
            if not isinstance(data_type[0], str):
                raise TypeError(
                    'First value in', data_type, 'is not a string.')
            if not isinstance(data_type[1], str):
                raise TypeError(
                    'Second value in', data_type, 'is not a string.')
            if data_type[1] not in ['INTEGER', 'REAL', 'TEXT']:
                raise ValueError('Data type in', data_type, 'is invalid.')
            if not isinstance(data_type[2], int):
                raise TypeError(
                    'Third value in', data_type, 'is not an integer.')
        data_types_file.seek(0)

    @staticmethod
    def check_raw_data(raw_data_file):
        """Check for correct formatting in the specified raw data file.

        Args:
            raw_data_file: File object of College Scorecard raw data.

        Raises:
            ValueError: If the data is incorrectly formatted.
        """
        raw_data_lines = raw_data_file.readlines()
        entries = len(raw_data_lines[0].split(','))
        for line in raw_data_lines:
            length = len(line.split(','))
            if length != entries:
                raise ValueError(
                    'Incorrect number of entries in raw data line.')
        raw_data_file.seek(0)
