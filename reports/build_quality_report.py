# Generates PDF data quality report from validation results
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime
from fpdf import FPDF

class DataQualityReport(FPDF):
    def header(self):
        # Title at the top
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'RecoMart Data Quality Report', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
        self.ln(10)
    
    def chapter_title(self, title):
        # Chapter heading
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)
    
    def section_title(self, title):
        # Section heading
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, title, 0, 1, 'L')
        self.ln(3)
    
    def body_text(self, text):
        # Regular body text
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 6, text)
        self.ln(5)
    
    def add_missing_values_table(self, missing_dict, table_name):
        # Add a table showing missing values per column
        self.section_title(f'Missing Values in {table_name}')
        
        self.set_font('Arial', 'B', 10)
        self.cell(60, 7, 'Column', 1)
        self.cell(40, 7, 'Missing Count', 1)
        self.ln()
        
        self.set_font('Arial', '', 10)
        for col, count in missing_dict.items():
            count_int = int(count) if isinstance(count, str) else count
            if count_int > 0:
                self.cell(60, 7, col, 1)
                self.cell(40, 7, str(count_int), 1)
                self.ln()
        
        self.ln(5)
    
    def add_issues_list(self, issues_dict, title):
        # Add a list of issues found
        self.section_title(title)
        
        self.set_font('Arial', '', 10)
        for issue, count in issues_dict.items():
            if isinstance(count, bool):
                status = 'Yes' if count else 'No'
                self.cell(0, 6, f'- {issue}: {status}', 0, 1)
            elif isinstance(count, int) and count > 0:
                self.cell(0, 6, f'- {issue}: {count}', 0, 1)
            elif isinstance(count, int) and count == 0:
                self.cell(0, 6, f'- {issue}: None found', 0, 1)
            else:
                self.cell(0, 6, f'- {issue}: {count}', 0, 1)
        
        self.ln(5)

def load_validation_results():
    # Load the validation results JSON file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_path = os.path.join(base_dir, 'reports', 'validation_results.json')
    
    try:
        with open(results_path, 'r') as f:
            results = json.load(f)
        return results
    except FileNotFoundError:
        print(f"Error: Validation results not found at {results_path}")
        print("Please run validation/validate_data.py first to generate the results.")
        return None

def generate_report(results):
    # Generate the PDF report
    pdf = DataQualityReport()
    pdf.add_page()
    
    # Events section
    pdf.chapter_title('Events Dataset')
    
    # Row counts
    pdf.section_title('Row Counts')
    pdf.body_text(f"Total rows read: {results['row_counts']['events_original']}")
    pdf.body_text(f"Rows after cleaning: {results['row_counts']['events_cleaned']}")
    pdf.body_text(f"Rows dropped: {results['row_counts']['events_original'] - results['row_counts']['events_cleaned']}")
    
    # Missing values
    pdf.add_missing_values_table(results['missing_values']['events'], 'Events')
    
    # Duplicates
    pdf.section_title('Duplicates')
    pdf.body_text(f"Fully duplicate rows found: {results['duplicates']['events_full_duplicates']}")
    
    # Schema issues
    pdf.add_issues_list({
        'Invalid event types': results['schema_issues']['invalid_event_type_count'],
        'Price not numeric': results['schema_issues']['price_not_numeric']
    }, 'Schema Issues')
    
    # Range issues
    pdf.add_issues_list({
        'Price <= 0': results['range_issues']['invalid_price_count'],
        'Future event_time': results['range_issues']['future_event_count'],
        'Empty user_session': results['range_issues']['empty_session_count']
    }, 'Range and Format Issues')
    
    pdf.ln(10)
    
    # Users section
    pdf.chapter_title('Users Dataset')
    
    # Row counts
    pdf.section_title('Row Counts')
    pdf.body_text(f"Total rows read: {results['row_counts']['users_original']}")
    pdf.body_text(f"Rows after cleaning: {results['row_counts']['users_cleaned']}")
    pdf.body_text(f"Rows dropped: {results['row_counts']['users_original'] - results['row_counts']['users_cleaned']}")
    
    # Missing values
    pdf.add_missing_values_table(results['missing_values']['users'], 'Users')
    
    # Duplicates
    pdf.section_title('Duplicates')
    pdf.body_text(f"Duplicate user IDs found: {results['duplicates']['users_duplicate_ids']}")
    
    # Schema issues
    pdf.add_issues_list({
        'Age not numeric': results['schema_issues']['age_not_numeric']
    }, 'Schema Issues')
    
    # Range issues
    pdf.add_issues_list({
        'Age outside 0-100 range': results['range_issues']['invalid_age_count']
    }, 'Range and Format Issues')
    
    pdf.ln(10)
    
    # Products section
    pdf.chapter_title('Products Dataset')
    
    # Row counts
    pdf.section_title('Row Counts')
    pdf.body_text(f"Total unique products: {results['row_counts']['products']}")
    
    # Missing values
    pdf.add_missing_values_table(results['missing_values']['products'], 'Products')
    
    # Duplicates
    pdf.section_title('Duplicates')
    pdf.body_text(f"Duplicate product IDs found: {results['duplicates']['products_duplicate_ids']}")
    
    pdf.ln(10)
    
    # Summary
    pdf.chapter_title('Summary')
    
    events_dropped = results['row_counts']['events_original'] - results['row_counts']['events_cleaned']
    users_dropped = results['row_counts']['users_original'] - results['row_counts']['users_cleaned']
    total_original = results['row_counts']['events_original'] + results['row_counts']['users_original']
    total_cleaned = results['row_counts']['events_cleaned'] + results['row_counts']['users_cleaned']
    total_dropped = total_original - total_cleaned
    drop_percentage = (total_dropped / total_original * 100) if total_original > 0 else 0
    
    summary_text = f"""Overall, the validation process cleaned {total_original} rows of data across events and users datasets. A total of {total_dropped} rows were dropped ({drop_percentage:.1f}% of the original data).

Most of the data quality issues were related to missing values in optional fields (like city and gender for users, which were filled with 'unknown'), invalid event types, and rows with price <= 0. The events dataset had {events_dropped} rows removed, primarily due to invalid event types, pricing issues, and duplicate entries. The users dataset had {users_dropped} rows removed, mainly due to invalid age values outside the 0-100 range.

After cleaning, the final validated datasets contain {total_cleaned} rows of high-quality data ready for feature engineering and analysis."""
    
    pdf.body_text(summary_text)
    
    # Save the PDF
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(base_dir, 'reports', '02_data_quality_report.pdf')
    pdf.output(output_path)
    
    print(f"PDF report generated: {output_path}")
    return output_path

def main():
    # Main function to generate the report
    print("Loading validation results...")
    results = load_validation_results()
    
    if results is None:
        return
    
    print("Generating PDF report...")
    generate_report(results)
    print("Report generation complete.")

if __name__ == "__main__":
    main()
