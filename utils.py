# Parser
import requests
import json
import pandas as pd
from collections import defaultdict

class EnergiAPI:
    """
    This class is used for repeated SQL Queries from the energidataservice API.
    The functions returns a pandas dataframe of the parsed SQL Query.
    """

    def __init__(self):
        self.sqlurl = "https://www.energidataservice.dk/proxy/api/datastore_search_sql?sql="
   

    def sql_to_df(self, query):
        """
        Example Query:
        " SELECT column1, column2 FROM dataset WHERE column2 >= Y "
        Some queries might require backslash for escaping characters.
        """

        response = requests.get(self.sqlurl + query)
        raw = json.loads(response.content)
        records = raw["result"]["records"]
        _dict = defaultdict(list)
        for record in records:
            for key in list(records[0].keys()):
                _dict[key].append(record[key])
        return pd.DataFrame.from_dict(_dict)

