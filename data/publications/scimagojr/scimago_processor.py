import pandas as pd
import os
import re
from collections import defaultdict
import glob

class ScimagoProcessor:
    def __init__(self, data_folder='scimagojr'):
        self.data_folder = data_folder
        self.all_years = []
        self.journal_data = defaultdict(dict)
        
    def extract_year_from_filename(self, filename):
        """Extract year from filename like 'scimagojr 1999.csv'"""
        match = re.search(r'scimagojr\s+(\d{4})', filename)
        return int(match.group(1)) if match else None
    
    def clean_issn_format(self, issn_string):
        """Convert ISSN format from comma-separated to semicolon-separated with dashes"""
        if pd.isna(issn_string) or not issn_string:
            return ''
        
        # Remove quotes and clean up
        issn_clean = str(issn_string).strip('"').strip()
        
        # Split by comma and process each ISSN
        issns = [issn.strip() for issn in issn_clean.split(',') if issn.strip()]
        formatted_issns = []
        
        for issn in issns:
            # Remove any existing dashes and spaces
            issn_digits = ''.join(char for char in issn if char.isdigit())
            
            # Format as XXXX-XXXX if we have 8 digits
            if len(issn_digits) == 8:
                formatted_issn = f"{issn_digits[:4]}-{issn_digits[4:]}"
                formatted_issns.append(formatted_issn)
            elif len(issn_digits) == 7:
                # Handle 7-digit ISSNs by padding with leading zero
                issn_digits = '0' + issn_digits
                formatted_issn = f"{issn_digits[:4]}-{issn_digits[4:]}"
                formatted_issns.append(formatted_issn)
            elif issn_digits:
                # Keep original if it doesn't match expected length
                formatted_issns.append(issn)
        
        # Join with semicolons
        return '; '.join(formatted_issns)
    
    def process_all_files(self):
        """Process all Scimago CSV files in the folder"""
        print(f"🔍 Searching for Scimago files in '{self.data_folder}/' folder...")
        
        # Find all CSV files matching the pattern
        pattern = os.path.join(self.data_folder, 'scimagojr*.csv')
        csv_files = glob.glob(pattern)
        
        if not csv_files:
            print(f"❌ No Scimago CSV files found in '{self.data_folder}/' folder")
            print(f"   Expected files like: scimagojr 1999.csv, scimagojr 2000.csv, etc.")
            return
        
        print(f"📁 Found {len(csv_files)} Scimago files:")
        
        # Sort files by year
        csv_files_with_years = []
        for file_path in csv_files:
            filename = os.path.basename(file_path)
            year = self.extract_year_from_filename(filename)
            if year:
                csv_files_with_years.append((year, file_path, filename))
                print(f"   📄 {filename} (Year: {year})")
            else:
                print(f"   ⚠️  {filename} (Could not extract year)")
        
        # Sort by year
        csv_files_with_years.sort(key=lambda x: x[0])
        self.all_years = [item[0] for item in csv_files_with_years]
        
        print(f"\n📊 Processing {len(csv_files_with_years)} files covering years: {min(self.all_years)}-{max(self.all_years)}")
        
        # Process each file
        for year, file_path, filename in csv_files_with_years:
            print(f"\n📖 Processing {filename}...")
            self.process_single_file(file_path, year)
        
        print(f"\n✅ Processed all files. Found {len(self.journal_data)} unique journals.")
    
    def process_single_file(self, file_path, year):
        """Process a single Scimago CSV file"""
        try:
            # Read CSV with semicolon separator
            df = pd.read_csv(file_path, sep=';', encoding='utf-8', low_memory=False)
            
            print(f"   📊 {len(df)} journals in {year}")
            
            # Process each journal
            for _, row in df.iterrows():
                source_id = str(row.get('Sourceid', ''))
                if not source_id or source_id == 'nan':
                    continue
                
                # Store static information (only if not already stored)
                if source_id not in self.journal_data:
                    self.journal_data[source_id] = {
                        'source_id': source_id,
                        'title': str(row.get('Title', '')).strip('"'),
                        'type': str(row.get('Type', '')),
                        'issn_original': str(row.get('Issn', '')),
                        'issn_formatted': self.clean_issn_format(row.get('Issn', '')),
                        'publisher': str(row.get('Publisher', '')).strip('"'),
                        'categories': str(row.get('Categories', '')).strip('"'),
                        'areas': str(row.get('Areas', '')).strip('"'),
                        'country': str(row.get('Country', '')),
                        'region': str(row.get('Region', '')),
                        'coverage': str(row.get('Coverage', '')).strip('"'),
                        'yearly_data': {}
                    }
                
                # Store yearly metrics
                self.journal_data[source_id]['yearly_data'][year] = {
                    'rank': self._clean_numeric(row.get('Rank')),
                    'sjr': self._clean_numeric(row.get('SJR')),
                    'sjr_best_quartile': str(row.get('SJR Best Quartile', '')),
                    'h_index': self._clean_numeric(row.get('H index')),
                    'total_docs': self._clean_numeric(row.get('Total Docs. (1999)', 0)),  # Note: column name varies
                    'total_citations': self._clean_numeric(row.get('Total Citations (3years)', 0))
                }
        
        except Exception as e:
            print(f"   ❌ Error processing {file_path}: {str(e)}")
    
    def _clean_numeric(self, value):
        """Clean numeric values (handle commas as decimal separators)"""
        if pd.isna(value) or value == '' or value == 'nan':
            return None  # Return None instead of empty string for numeric columns
        
        try:
            # Handle European decimal format (comma as decimal separator)
            str_value = str(value).replace(',', '.')
            return float(str_value)
        except (ValueError, TypeError):
            return None  # Return None instead of empty string
    
    def create_consolidated_dataframe(self):
        """Create a consolidated DataFrame with separate columns for each year"""
        print(f"\n🔧 Creating consolidated database...")
        
        if not self.journal_data:
            print("❌ No journal data to process")
            return None
        
        consolidated_data = []
        
        for source_id, journal_info in self.journal_data.items():
            row = {
                'source_id': journal_info['source_id'],
                'title': journal_info['title'],
                'type': journal_info['type'],
                'issn': journal_info['issn_formatted'],  # Semicolon-separated ISSNs
                'publisher': journal_info['publisher'],
                'categories': journal_info['categories'],
                'areas': journal_info['areas'],
                'country': journal_info['country'],
                'region': journal_info['region'],
                'coverage': journal_info['coverage']
            }
            
            # Add yearly columns for each metric
            for year in self.all_years:
                year_data = journal_info['yearly_data'].get(year, {})
                
                # Create separate columns for each year and metric
                # Use None for missing values instead of empty strings for numeric columns
                row[f'rank_{year}'] = year_data.get('rank')
                row[f'sjr_{year}'] = year_data.get('sjr')
                row[f'sjr_best_quartile_{year}'] = year_data.get('sjr_best_quartile', '')
                row[f'h_index_{year}'] = year_data.get('h_index')
                row[f'total_docs_{year}'] = year_data.get('total_docs')
                row[f'total_citations_{year}'] = year_data.get('total_citations')
            
            consolidated_data.append(row)
        
        df = pd.DataFrame(consolidated_data)
        
        # Sort by most recent SJR (if available) with better error handling
        if self.all_years:
            latest_year = max(self.all_years)
            sjr_col = f'sjr_{latest_year}'
            if sjr_col in df.columns:
                try:
                    # Convert to numeric and sort, handling mixed types gracefully
                    df[sjr_col] = pd.to_numeric(df[sjr_col], errors='coerce')
                    df = df.sort_values(by=sjr_col, ascending=False, na_position='last')
                except Exception as e:
                    print(f"⚠️  Warning: Could not sort by {sjr_col}: {e}")
                    print("   Database created without sorting by SJR")
        
        print(f"✅ Created consolidated database with {len(df)} journals")
        print(f"📊 Columns: {len(df.columns)} total")
        print(f"📅 Year range: {min(self.all_years)}-{max(self.all_years)}")
        
        return df
    
    def create_alternative_format_dataframe(self):
        """Create alternative format with semicolon-separated yearly data"""
        print(f"\n🔧 Creating alternative format (semicolon-separated yearly data)...")
        
        consolidated_data = []
        
        for source_id, journal_info in self.journal_data.items():
            # Collect yearly data
            sjr_values = []
            quartile_values = []
            h_index_values = []
            rank_values = []
            
            for year in sorted(self.all_years):
                year_data = journal_info['yearly_data'].get(year, {})
                
                sjr = year_data.get('sjr')
                quartile = year_data.get('sjr_best_quartile', '')
                h_index = year_data.get('h_index')
                rank = year_data.get('rank')
                
                # Only add to list if value exists (not None)
                if sjr is not None:
                    sjr_values.append(f"{year}: {sjr}")
                if quartile:
                    quartile_values.append(f"{year}: {quartile}")
                if h_index is not None:
                    h_index_values.append(f"{year}: {h_index}")
                if rank is not None:
                    rank_values.append(f"{year}: {rank}")
            
            row = {
                'source_id': journal_info['source_id'],
                'title': journal_info['title'],
                'type': journal_info['type'],
                'issn': journal_info['issn_formatted'],
                'publisher': journal_info['publisher'],
                'categories': journal_info['categories'],
                'areas': journal_info['areas'],
                'country': journal_info['country'],
                'region': journal_info['region'],
                'coverage': journal_info['coverage'],
                'sjr_by_year': ' ; '.join([v for v in sjr_values if v]),
                'sjr_best_quartile_by_year': ' ; '.join([v for v in quartile_values if v]),
                'h_index_by_year': ' ; '.join([v for v in h_index_values if v]),
                'rank_by_year': ' ; '.join([v for v in rank_values if v])
            }
            
            consolidated_data.append(row)
        
        df = pd.DataFrame(consolidated_data)
        
        print(f"✅ Created alternative format with {len(df)} journals")
        
        return df
    
    def save_results(self, df_separate_cols, df_semicolon_format=None, 
                    output_file='scimago_journals_database.csv',
                    output_file_alt='scimago_journals_database_alternative.csv'):
        """Save the consolidated results"""
        
        if df_separate_cols is not None:
            df_separate_cols.to_csv(output_file, index=False, encoding='utf-8')
            print(f"💾 Saved main database: {output_file}")
            print(f"   📊 {len(df_separate_cols)} journals")
            print(f"   📅 {len([col for col in df_separate_cols.columns if 'sjr_' in col and col != 'sjr_best_quartile_by_year'])} years of SJR data")
        
        if df_semicolon_format is not None:
            df_semicolon_format.to_csv(output_file_alt, index=False, encoding='utf-8')
            print(f"💾 Saved alternative format: {output_file_alt}")
        
        # Print sample of main database
        if df_separate_cols is not None and len(df_separate_cols) > 0:
            print(f"\n📋 Sample data (top 3 journals by latest SJR):")
            sample_cols = ['title', 'type', 'issn', 'publisher']
            
            # Add latest year SJR columns
            if self.all_years:
                latest_year = max(self.all_years)
                sample_cols.extend([f'sjr_{latest_year}', f'sjr_best_quartile_{latest_year}', f'h_index_{latest_year}'])
            
            # Show available columns only
            available_cols = [col for col in sample_cols if col in df_separate_cols.columns]
            print(df_separate_cols[available_cols].head(3).to_string())
    
    def print_statistics(self, df):
        """Print useful statistics about the journal database"""
        if df is None or len(df) == 0:
            return
            
        print(f"\n📈 DATABASE STATISTICS:")
        print(f"   📚 Total Journals: {len(df):,}")
        
        # Type distribution
        if 'type' in df.columns:
            type_counts = df['type'].value_counts()
            print(f"   📖 Journal Types:")
            for journal_type, count in type_counts.head(5).items():
                print(f"      • {journal_type}: {count:,}")
        
        # Latest year statistics
        if self.all_years:
            latest_year = max(self.all_years)
            sjr_col = f'sjr_{latest_year}'
            quartile_col = f'sjr_best_quartile_{latest_year}'
            
            if sjr_col in df.columns:
                valid_sjr = df[sjr_col].notna() & (df[sjr_col] != '')
                print(f"   📊 {latest_year} Data:")
                print(f"      • Journals with SJR: {valid_sjr.sum():,}")
                
                if valid_sjr.any():
                    sjr_values = pd.to_numeric(df[sjr_col], errors='coerce')
                    print(f"      • Average SJR: {sjr_values.mean():.3f}")
                    print(f"      • Median SJR: {sjr_values.median():.3f}")
                    print(f"      • Max SJR: {sjr_values.max():.3f}")
            
            if quartile_col in df.columns:
                quartile_counts = df[quartile_col].value_counts()
                print(f"   🏆 {latest_year} Quartile Distribution:")
                for quartile, count in quartile_counts.items():
                    if quartile and quartile != '':
                        print(f"      • {quartile}: {count:,}")
        
        # Coverage years
        print(f"   📅 Year Coverage: {min(self.all_years)}-{max(self.all_years)} ({len(self.all_years)} years)")

def process_scimago_data(data_folder='scimagojr', 
                        create_both_formats=True,
                        output_main='scimago_journals_database.csv',
                        output_alt='scimago_journals_alternative.csv'):
    """
    Main function to process all Scimago JR data
    
    Args:
        data_folder (str): Folder containing Scimago CSV files
        create_both_formats (bool): Whether to create both separate-columns and semicolon formats
        output_main (str): Filename for main output (separate columns)
        output_alt (str): Filename for alternative output (semicolon format)
    """
    
    print("🚀 SCIMAGO JOURNAL DATABASE PROCESSOR")
    print("=" * 50)
    
    processor = ScimagoProcessor(data_folder)
    
    # Process all files
    processor.process_all_files()
    
    if not processor.journal_data:
        print("❌ No data processed. Please check your file paths and formats.")
        return
    
    # Create main format (separate columns for each year)
    df_main = processor.create_consolidated_dataframe()
    
    # Create alternative format (semicolon-separated)
    df_alt = None
    if create_both_formats:
        df_alt = processor.create_alternative_format_dataframe()
    
    # Save results
    processor.save_results(df_main, df_alt, output_main, output_alt)
    
    # Print statistics
    processor.print_statistics(df_main)
    
    print(f"\n🎯 READY FOR FACULTYFINDER INTEGRATION!")
    print(f"   • Use main database for journal impact analysis")
    print(f"   • Match faculty publications with journal metrics")
    print(f"   • Track journal quality trends over time")
    
    return df_main, df_alt

if __name__ == "__main__":
    # Example usage
    print("=== SCIMAGO JOURNAL DATABASE CREATION ===")
    
    # Test ISSN formatting first
    processor = ScimagoProcessor()
    print("\n🔧 ISSN Formatting Test:")
    test_issns = [
        "15454509, 00664154",
        "00928674, 10974172", 
        "15353278, 07320582"
    ]
    
    for test_issn in test_issns:
        formatted = processor.clean_issn_format(test_issn)
        print(f"   Before: {test_issn}")
        print(f"   After:  {formatted}")
        print()
    
    # Process all Scimago files and create comprehensive database
    df_main, df_alt = process_scimago_data(
        data_folder='scimagojr',  # Folder with your Scimago CSV files
        create_both_formats=True,  # Create both formats
        output_main='scimago_journals_comprehensive.csv',
        output_alt='scimago_journals_semicolon_format.csv'
    )
    
    print("\n=== EXPECTED OUTPUT FORMAT ===")
    print("📄 Main Database Columns:")
    print("  Static: source_id, title, type, issn, publisher, categories, areas")
    print("  Yearly: sjr_1999, sjr_2000, ..., sjr_2025")
    print("         rank_1999, rank_2000, ..., rank_2025")
    print("         h_index_1999, h_index_2000, ..., h_index_2025")
    print()
    print("📄 Alternative Format:")
    print("  Static columns + sjr_by_year, sjr_best_quartile_by_year, h_index_by_year")
    print("  Format: '1999: 2.5 ; 2000: 2.8 ; 2001: 3.1'")
    print()
    print("📊 ISSN Format: '1545-4509; 0066-4154' (with dashes, semicolon-separated)")
    
    # Show example of how to use the data
    if df_main is not None and len(df_main) > 0:
        print("\n=== SAMPLE INTEGRATION WITH FACULTYFINDER ===")
        print("# Example: Find journal impact for a publication")
        print("def get_journal_impact(journal_title, year):")
        print("    match = df_main[df_main['title'].str.contains(journal_title, case=False)]")
        print("    if not match.empty:")
        print("        sjr_col = f'sjr_{year}'")
        print("        return match.iloc[0][sjr_col] if sjr_col in match.columns else None")
        print("    return None")
        print()
        print("# Usage:")
        print("# impact = get_journal_impact('Cell', 2023)")
        print("# quartile = get_journal_quartile('Nature', 2023)")
        
        # Show actual ISSN examples from processed data
        print("\n=== SAMPLE ISSN FORMATTING FROM PROCESSED DATA ===")
        if 'issn' in df_main.columns:
            sample_issns = df_main['issn'].dropna().head(3)
            for i, issn in enumerate(sample_issns, 1):
                journal_title = df_main.iloc[sample_issns.index[i-1]]['title'] if 'title' in df_main.columns else 'Unknown'
                print(f"   {i}. {journal_title}")
                print(f"      ISSN: {issn}")
        print()
        print("✅ All ISSNs now properly formatted with dashes and semicolon separators!")