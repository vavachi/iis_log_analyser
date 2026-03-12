import pandas as pd
import re

class IISLogParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.dataframe = None
        self.fields = []
        
    def parse(self):
        """
        Parses the IIS log file. Extracts the #Fields line to use as columns
        and loads the rest into a pandas DataFrame.
        """
        # Read the file to find the Fields line and count comments
        fields_line = None
        skip_rows = []
        
        with open(self.filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                if line.startswith('#Fields:'):
                    fields_line = line.strip()
                    skip_rows.append(i) # Also skip the Fields line for pandas read_csv data
                elif line.startswith('#'):
                    skip_rows.append(i)
                else:
                    # Once we hit data, we don't need to keep reading the whole file line by line
                    # We assume #Fields comes before data.
                    # We only check first few hundred lines to be safe but usually they are at top.
                    if len(skip_rows) > 100: 
                        pass
        
        if not fields_line:
            raise ValueError("Could not find '#Fields:' directive in the log file.")
            
        # Parse fields from `#Fields: date time s-ip cs-method ...`
        self.fields = fields_line.replace('#Fields: ', '').strip().split(' ')
        
        # Load the data using pandas, skipping the comment rows
        self.dataframe = pd.read_csv(
            self.filepath,
            sep=r'\s+', # IIS logs are space-separated
            skiprows=skip_rows,
            names=self.fields,
            na_values=["-"], # IIS uses hyphens for null values
            engine='python',
            # handle lines that might be malformed (very rare in standard IIS logs but possible)
            on_bad_lines='skip' 
        )
        
        # Add Device-Type classification
        if 'cs(User-Agent)' in self.dataframe.columns:
            self.dataframe['Device-Type'] = self.dataframe['cs(User-Agent)'].apply(self._classify_device)
        
        # Add Datetime column for time-series charting
        if 'date' in self.dataframe.columns and 'time' in self.dataframe.columns:
            self.dataframe['Datetime'] = pd.to_datetime(self.dataframe['date'] + ' ' + self.dataframe['time'], errors='coerce')
        
        return self.dataframe

    def _classify_device(self, ua):
        if pd.isna(ua):
            return 'Unknown'
        ua_str = str(ua).lower()
        if any(x in ua_str for x in ['mobile', 'android', 'iphone', 'ipad', 'windows phone', 'iemobile']):
            return 'Mobile'
        elif any(x in ua_str for x in ['bot', 'crawler', 'spider', 'slurp', 'bing']):
            return 'Bot'
        else:
            return 'Web'

    def filter_data(self, filters):
        """
        Apply dictionary of filters to the dataframe.
        Format: {'column_name': 'value', 'column_name2': 'value2'}
        """
        if self.dataframe is None:
            return None
            
        filtered_df = self.dataframe.copy()
        for col, value in filters.items():
            if not value: # skip empty filters
                continue
            if col in filtered_df.columns:
                # Need to convert to string to ensure partial matching works across all col types
                filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(value, case=False, na=False)]
                
        return filtered_df
        
    def get_summary_stats(self):
        """
        Returns basic summary statistics for the dashboard/sidebar.
        """
        if self.dataframe is None or self.dataframe.empty:
            return {}
            
        stats = {}
        stats['Total Requests'] = len(self.dataframe)
        
        if 'c-ip' in self.dataframe.columns:
            stats['Top IPs'] = self.dataframe['c-ip'].value_counts().head(5).to_dict()
            
        if 'sc-status' in self.dataframe.columns:
            stats['Status Codes'] = self.dataframe['sc-status'].value_counts().head(5).to_dict()
            
        if 'cs-method' in self.dataframe.columns:
            stats['Top Methods'] = self.dataframe['cs-method'].value_counts().head(5).to_dict()
            
        return stats
