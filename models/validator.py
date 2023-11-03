import pandas as pd
import numpy as np

# Import custom functions from 'models.highlight_errors' (assumed to be defined elsewhere)
from models.highlight_errors import highlight_headers, error_color_css

class Validator():
    def __init__(self, dataframe: pd.DataFrame) -> None:
        """
        Initialize the Validator object with a DataFrame.

        Args:
            dataframe (pd.DataFrame): The DataFrame to be validated.
        """
        self.dataframe = dataframe
        self.all_columns = True
        self.columns_name = [
            'Nome',
            'Descricao',
            'CepInicio',
            'CepFim',
            'PesoInicio',
            'PesoFim',
            'Valor',
            'Prazo',
            'DiaUtil'
        ]
        self.real_columns_name = list(self.dataframe.columns.values)


    def style_dataframe(self) -> None:
        """
        Main method for styling the DataFrame, checking data types, and finding conflicts.
        """
        # Check if the dataframe has all columns
        self._check_columns_quantity()

        # Change data types by replacing ',' with '.'
        self._check_values()

        # Check column names
        self._check_columns_name()


    def _check_columns_quantity(self) -> None:
        """
        Check if the DataFrame has the correct number of columns.
        """
        if len(self.columns_name) != len(self.real_columns_name):
            # Missing columns
            raise IndexError('Missing columns')


    def _check_values(self) -> None:
        """
        Check and update data types, handle conflicts in CEP and Peso columns.
        """
        columns = ['CepInicio', 'CepFim', 'PesoInicio', 'PesoFim', 'Valor', 'Prazo']
        dtype = True

        if all(column in self.dataframe.columns for column in columns):
            for column in columns[2:4]:
                try:
                    self.dataframe[column] = self.dataframe[column].str.replace(',', '.').astype(float)
                except:
                    dtype = False

            if dtype:
                # Check all data types
                self._check_data_types()

                # Find conflicted ranges in CEP
                self.dataframe = self._find_conflited_ranges(columns[:4], peso=False, dataframe=self.dataframe.copy())

                # Find conflicted ranges in Peso by cutting the dataframe in CEP intervals
                cep_interval = self.__get_unique_values(columns[:2], dataframe=self.dataframe.copy())

                # Cut the dataframe by CEP intervals
                complete_dataframe = pd.DataFrame()
                for low_interval, high_interval in cep_interval:
                    cutted_dataframe = self.dataframe.loc[(self.dataframe[columns[0]] == low_interval) & (self.dataframe[columns[1]] == high_interval)].copy()

                    # Search for conflicted ranges in Peso
                    cutted_dataframe = self._find_conflited_ranges(columns[:4], peso=True, dataframe=cutted_dataframe)
                    complete_dataframe = pd.concat([complete_dataframe, cutted_dataframe], axis=0)
                
                self.dataframe = complete_dataframe.sort_index().copy()

            # Color dataframe
            self._check_numbers_errors(columns)
        
        else:
            self.all_columns = False


    def _check_numbers_errors(self, columns: list):
        """
        Apply formatting and highlighting to numeric columns.
        """
        def format_wrong_dtype(row: pd.Series):
            colors = []
            for value in row:
                if row.name in columns:
                    try:
                        float(value.replace(',', '.')) if isinstance(value, str) else float(value)
                        colors.append('')
                    except:
                        colors.append(error_color_css)
                else:
                    colors.append('')
            return colors

        def format_range(row) -> str:
            colors = [''] * len(row)
            if row['Erros na Linha'] != '':
                colors = [error_color_css] * len(row)
            return colors

        def remove_error_icon(item):
            if isinstance(item, str):
                return item.replace('?', '')
            return item

        self.dataframe = self.dataframe.style.apply(format_wrong_dtype).format(precision=3, subset=columns)
        self.dataframe = self.dataframe.apply(format_range, axis=1) # .format(remove_error_icon, subset=columns)


    def _check_data_types(self) -> None:
        """
        Check if column data types match expected data types.
        """
        data_types = [
            object,
            object,
            np.int64,
            np.int64,
            np.float64,
            np.float64,
            np.int64,
            np.int64,
            object,
        ]

        for key, dtype in enumerate(self.dataframe.dtypes.values):
            if data_types[key] != dtype and (key > 1 and key < 6):
                # Wrong dtype
                raise TypeError(f'{self.dataframe.columns[key]!r} is not in the right data type. Expected {data_types[key]} got {dtype}')

    """
    # Old and unused module
    def _check_ranges(self, columns:list, peso:bool) -> pd.DataFrame:
        def get_unique_values(columns:list, dataframe:pd.DataFrame) -> list:
            values = [n for n in dataframe[columns].values.tolist()]
            values = list(set(tuple(element) for element in values))

            return values

        dataframe = self.dataframe.copy()
        auxiliary_dataframe = pd.DataFrame()
        if 'Erros na Linha' not in dataframe.columns:
            dataframe['Erros na Linha'] = ''

        cep = columns[:2]

        if peso:
            intervals = get_unique_values(columns=columns[:2], dataframe=self.dataframe)
            columns = columns[2:]
            complete_dataframe = pd.DataFrame()

        else:
            intervals = [(None, None)]
            columns = columns[:2]

        for low_interval, high_interval in intervals:
            if peso:
                dataframe = self.dataframe.loc[(self.dataframe[cep[0]] == low_interval) & (self.dataframe[cep[1]] == high_interval)].copy()

            values = get_unique_values(columns=columns, dataframe=dataframe)

            duplicated = []

            for low_value, high_value in values:
                for low_value2, high_value2 in values:
                    if high_value < high_value2 and high_value > low_value2:
                        if not (
                            any([value in duplicated for value in (low_value, low_value2, high_value, high_value2)])
                        ):
                            for value in (low_value, high_value, low_value2, high_value2):
                                duplicated.append(value)

            for value in set(duplicated):
                cutted_dataframe = dataframe.loc[((dataframe[columns[0]] == value) | (dataframe[columns[1]] == value))]

                if not peso:
                    if cutted_dataframe.shape[0] == 1 and auxiliary_dataframe.shape[0] == 0:
                        auxiliary_dataframe = pd.concat([auxiliary_dataframe, cutted_dataframe], axis=0)
                        continue

                if not peso:
                    values = cutted_dataframe.index.values
                    if values.shape[0] > 1:
                        index_values = 'RANGE CEP: ' + ', '.join(str(x) for x in values)
                    else:
                        index_values = 'RANGE INVÁLIDO'
                else:
                    index_values = ' + RANGE PESO'
                
                cutted_dataframe['Erros na Linha'] = cutted_dataframe['Erros na Linha'] + index_values
                
                cutted_dataframe[columns] = cutted_dataframe[columns].astype(str).map(lambda x: f'?{x}')

                dataframe.loc[((dataframe[columns[0]] == value) | (dataframe[columns[1]] == value))] = cutted_dataframe
                
            if peso:
                complete_dataframe = pd.concat([complete_dataframe, dataframe], axis=0)

        if not peso:
            print(auxiliary_dataframe.head())

        if peso:
            dataframe = complete_dataframe.sort_index()

        return dataframe
    """

    def _find_conflited_ranges(self, columns: list, peso: bool, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Find conflicted ranges in the specified columns and update the DataFrame accordingly.

        Args:
            columns (list): List of column names to check for conflicts.
            peso (bool): Whether to consider Peso for conflicts.
            dataframe (pd.DataFrame): The DataFrame to be checked and updated.

        Returns:
            pd.DataFrame: The updated DataFrame with conflict information.
        """
        if peso:
            columns = columns[2:]
            message = ' + PESO: '
        else:
            columns = columns[:2]
            message = 'CEP: '

        col1 = columns[0]
        col2 = columns[1]

        if 'Erros na Linha' not in dataframe.columns:
            dataframe['Erros na Linha'] = ''

        for key, value in enumerate(dataframe[[col1, col2]].values):
            column1, column2 = value
            conflicts = dataframe.loc[(column2 > dataframe[col1]) & (dataframe[col2] > column2)].index

            if len(conflicts) > 0:
                dataframe.iloc[key, 9] = dataframe.iloc[key, 9] + message + ', '.join(map(str, conflicts))

        return dataframe


    def _check_columns_name(self) -> pd.DataFrame.style:
        """
        Check and style column names in the DataFrame.

        Returns:
            pd.DataFrame.style: The styled DataFrame.
        """
        if not self.all_columns:
            self.dataframe = self.dataframe.style

        if self.real_columns_name != self.columns_name:
            styled_df = self.dataframe.map_index(
                lambda x: highlight_headers() if x not in self.columns_name else '',
                axis=1
            )
        
        else:
            styled_df = self.dataframe

        self.dataframe = styled_df


    def __get_unique_values(self, columns: list, dataframe: pd.DataFrame) -> list:
        """
        Get unique values from specified columns in the DataFrame.

        Args:
            columns (list): List of column names to extract unique values from.
            dataframe (pd.DataFrame): The DataFrame to extract values from.

        Returns:
            list: List of unique values from the specified columns.
        """
        values = [n for n in dataframe[columns].values.tolist()]
        values = list(set(tuple(element) for element in values))

        return values


    def get_dataframe(self) -> pd.DataFrame.style:
        """
        Get the styled DataFrame.

        Returns:
            pd.DataFrame.style: The styled DataFrame.
        """
        return self.dataframe


    def save_to_excel(self, filename: str = 'output/output.xlsx') -> None:
        """
        Save the DataFrame to an Excel file.

        Args:
            filename (str): The name of the output Excel file.
        """
        self.dataframe.to_excel(filename)
