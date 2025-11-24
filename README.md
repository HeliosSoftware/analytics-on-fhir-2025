# Helios Software: High-performance Clinical Analytics with SQL on FHIR using Rust

**Analytics on FHIR 2025 Conference Presentation**

This repository contains materials for the session demonstrating Helios Software, an open-source Rust implementation of SQL on FHIR. The presentation showcases real-world laboratory analytics using three deployment patterns: batch processing (CLI), microservices (HTTP server), and data science workflows (Python bindings).

## Session Description

Helios Software is an open source Rust implementation of SQL on FHIR that includes a simple CLI for batch transformations, a HTTP server ideal for microservices, and Python bindings for using SQL on FHIR directly in your data science and analytics projects.

In this session, Steve will demonstrate a real-world laboratory analytics challenge across different workflows, illustrating concrete patterns for integrating SQL on FHIR into pipelines for batch, microservice, and data science workloads.

## Use Case: Tests Pending at Discharge (TPD)

### Clinical Scenario

Tests Pending at Discharge represents a significant quality and safety concern in healthcare. When laboratory tests are ordered during an inpatient stay but results are not available at discharge, several risks emerge:

- **Patient Safety**: Critical abnormal results may go unnoticed
- **Readmissions**: Unresolved issues can lead to hospital readmissions
- **Continuity of Care**: Outpatient providers may lack essential diagnostic information
- **Resource Utilization**: Follow-up testing may be duplicated unnecessarily

This demonstration uses SQL on FHIR ViewDefinitions to identify and analyze pending laboratory results at patient discharge, providing actionable intelligence for quality improvement initiatives.

### Analytics Approach

We'll use two complementary ViewDefinitions:

1. **DiagnosticReportAtDischargeView**: Identifies individual lab reports that were not finalized by discharge time
2. **EncounterPendingLabCountView**: Aggregates pending lab counts per encounter for population-level analysis

## Prerequisites

### System Requirements

- **Java 11+** (for Synthea)
- **Python 3.8+** (for pysof)
- **curl** (for downloading binaries)

### Installation

#### Java (Required for Synthea)

**macOS:**
```bash
brew install openjdk@11
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install openjdk-11-jdk
```

**Windows:**
Download and install from [Adoptium](https://adoptium.net/) or use:
```powershell
winget install EclipseAdoptium.Temurin.11.JDK
```

#### Python and Dependencies

**macOS/Linux:**
```bash
python3 -m pip install --upgrade pip
pip install pandas plotly pysof
```

**Windows:**
```powershell
python -m pip install --upgrade pip
pip install pandas plotly pysof
```

## Demo Walkthrough

### Step 1: Generate Test Data with Synthea

#### 1.1 Clone and Build Synthea

```bash
# Clone Synthea
git clone https://github.com/synthetichealth/synthea.git
cd synthea

# Build (this may take a few minutes)
./gradlew build check test
```

**Windows:**
```powershell
git clone https://github.com/synthetichealth/synthea.git
cd synthea
.\gradlew.bat build check test
```

#### 1.2 Install the TPD Custom Module

Copy the `tpd.json` module from this repository into Synthea's modules directory:

**macOS/Linux:**
```bash
# From the synthea directory
cp ../analytics-on-fhir-2025/tpd.json src/main/resources/modules/
```

**Windows:**
```powershell
copy ..\analytics-on-fhir-2025\tpd.json src\main\resources\modules\
```

#### 1.3 Configure NDJSON Export

Configure Synthea to export FHIR data in NDJSON format by editing the `src/main/resources/synthea.properties` file:

**macOS/Linux:**
```bash
# Open synthea.properties in your editor
nano src/main/resources/synthea.properties
```

**Windows:**
```powershell
notepad src\main\resources\synthea.properties
```

Find and modify these settings:

```properties
# Disable bundle export
exporter.fhir.export = false

# Enable NDJSON export
exporter.fhir.bulk_data = true
```

Save the file and exit.

#### 1.4 Generate Synthetic Patients

Generate 100 patients with the TPD module:

**macOS/Linux:**
```bash
./run_synthea -m tpd -p 100 Massachusetts
```

**Windows:**
```powershell
.\run_synthea.bat -m tpd -p 100 Massachusetts
```

This creates FHIR R4 resources in NDJSON format in `output/fhir/` with:
- Encounter resources (inpatient stays with varied lengths of stay)
- DiagnosticReport resources (with realistic pending statuses)
- Observation resources (laboratory results organized into Blue/Orange/Red categories)

The NDJSON format provides one FHIR resource per line, ideal for streaming and bulk processing.

#### 1.5 Copy Generated Data

Create a test data directory in this repository:

**macOS/Linux:**
```bash
cd ../analytics-on-fhir-2025
mkdir -p test-data
cp ../synthea/output/fhir/*.ndjson test-data/
```

**Windows:**
```powershell
cd ..\analytics-on-fhir-2025
mkdir test-data
copy ..\synthea\output\fhir\*.ndjson test-data\
```

### Step 2: Download Helios Software Binaries

Download the appropriate binaries for your platform from [hfs v0.1.30 release](https://github.com/HeliosSoftware/hfs/releases/tag/v0.1.30):

#### macOS

```bash
# Download sof-cli
curl -L https://github.com/HeliosSoftware/hfs/releases/download/v0.1.30/sof-cli-macos-x64 -o sof-cli
chmod +x sof-cli

# Download sof-server
curl -L https://github.com/HeliosSoftware/hfs/releases/download/v0.1.30/sof-server-macos-x64 -o sof-server
chmod +x sof-server

# Verify installation
./sof-cli --version
./sof-server --version
```

#### Linux

```bash
# Download sof-cli
curl -L https://github.com/HeliosSoftware/hfs/releases/download/v0.1.30/sof-cli-linux-x64 -o sof-cli
chmod +x sof-cli

# Download sof-server
curl -L https://github.com/HeliosSoftware/hfs/releases/download/v0.1.30/sof-server-linux-x64 -o sof-server
chmod +x sof-server

# Verify installation
./sof-cli --version
./sof-server --version
```

#### Windows (PowerShell)

```powershell
# Download sof-cli
Invoke-WebRequest -Uri "https://github.com/HeliosSoftware/hfs/releases/download/v0.1.30/sof-cli-windows-x64.exe" -OutFile "sof-cli.exe"

# Download sof-server
Invoke-WebRequest -Uri "https://github.com/HeliosSoftware/hfs/releases/download/v0.1.30/sof-server-windows-x64.exe" -OutFile "sof-server.exe"

# Verify installation
.\sof-cli.exe --version
.\sof-server.exe --version
```

### Step 3: Batch Processing with sof-cli

The `sof-cli` tool is ideal for batch transformations, ETL pipelines, and scheduled analytics jobs.

#### 3.1 Run DiagnosticReportAtDischargeView

This ViewDefinition identifies individual lab reports pending at discharge:

**macOS/Linux:**
```bash
./sof-cli run \
  --view-definition DiagnosticReportAtDischargeView.json \
  --fhir-data test-data/ \
  --output diagnostic_reports_pending.csv \
  --format csv
```

**Windows:**
```powershell
.\sof-cli.exe run `
  --view-definition DiagnosticReportAtDischargeView.json `
  --fhir-data test-data\ `
  --output diagnostic_reports_pending.csv `
  --format csv
```

**Output columns:**
- `report_id`: Unique DiagnosticReport identifier
- `hospital_discharge_time`: When the patient was discharged
- `report_status`: Status of the report (registered, partial, preliminary)
- `encounter_id`: Reference to the associated encounter

#### 3.2 Run EncounterPendingLabCountView

This ViewDefinition provides encounter-level aggregation:

**macOS/Linux:**
```bash
./sof-cli run \
  --view-definition EncounterPendingLabCountView.json \
  --fhir-data test-data/ \
  --output encounter_summary.csv \
  --format csv
```

**Windows:**
```powershell
.\sof-cli.exe run `
  --view-definition EncounterPendingLabCountView.json `
  --fhir-data test-data\ `
  --output encounter_summary.csv `
  --format csv
```

**Output columns:**
- `encounter_id`: Unique encounter identifier
- `hospital_discharge_time`: Discharge timestamp
- `pending_lab_count`: Number of labs still pending at discharge

#### 3.3 Inspect Results

**macOS/Linux:**
```bash
# View first 10 rows
head -10 diagnostic_reports_pending.csv
head -10 encounter_summary.csv

# Count total pending reports
wc -l diagnostic_reports_pending.csv

# Find encounters with most pending labs
sort -t, -k3 -nr encounter_summary.csv | head -10
```

**Windows (PowerShell):**
```powershell
# View first 10 rows
Get-Content diagnostic_reports_pending.csv | Select-Object -First 10
Get-Content encounter_summary.csv | Select-Object -First 10

# Count total pending reports
(Get-Content diagnostic_reports_pending.csv | Measure-Object -Line).Lines

# Import and analyze
Import-Csv encounter_summary.csv | Sort-Object pending_lab_count -Descending | Select-Object -First 10
```

### Step 4: Microservices with sof-server

The `sof-server` provides a REST API for on-demand ViewDefinition execution, ideal for integrating SQL on FHIR into microservice architectures.

#### 4.1 Start the Server

**macOS/Linux:**
```bash
./sof-server --port 8080 --fhir-data test-data/ &
```

**Windows (PowerShell, run in separate window):**
```powershell
.\sof-server.exe --port 8080 --fhir-data test-data\
```

#### 4.2 Execute ViewDefinitions via HTTP

**Execute DiagnosticReportAtDischargeView:**

**macOS/Linux:**
```bash
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d @DiagnosticReportAtDischargeView.json \
  | jq '.'
```

**Windows (PowerShell):**
```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8080/run" `
  -ContentType "application/json" `
  -InFile "DiagnosticReportAtDischargeView.json" | ConvertTo-Json
```

**Execute EncounterPendingLabCountView:**

**macOS/Linux:**
```bash
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d @EncounterPendingLabCountView.json \
  | jq '.rows[] | select(.pending_lab_count > 0)'
```

**Windows (PowerShell):**
```powershell
$result = Invoke-RestMethod -Method POST -Uri "http://localhost:8080/run" `
  -ContentType "application/json" `
  -InFile "EncounterPendingLabCountView.json"
$result.rows | Where-Object { $_.pending_lab_count -gt 0 }
```

### Step 5: Data Science with pysof

The Python bindings enable SQL on FHIR integration into Jupyter notebooks, data pipelines, and ML workflows.

#### 5.1 Create Analysis Script

Create a new file `analyze_tpd.py`:

```python
"""
Tests Pending at Discharge - Analysis and Visualization
Analytics on FHIR 2025 Conference Demo
"""

import json
import glob
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pysof import ViewDefinitionRunner
from datetime import datetime

def load_fhir_data(data_dir='test-data'):
    """Load all FHIR bundles from directory"""
    fhir_bundles = []
    for file_path in glob.glob(f'{data_dir}/*.json'):
        with open(file_path, 'r') as f:
            fhir_bundles.append(json.load(f))
    return fhir_bundles

def load_view_definition(file_path):
    """Load a ViewDefinition from JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def main():
    print("=" * 60)
    print("Tests Pending at Discharge - Analysis")
    print("=" * 60)

    # Load FHIR data
    print("\n1. Loading FHIR test data...")
    fhir_data = load_fhir_data()
    print(f"   Loaded {len(fhir_data)} FHIR bundles")

    # Load ViewDefinitions
    print("\n2. Loading ViewDefinitions...")
    dr_view = load_view_definition('DiagnosticReportAtDischargeView.json')
    enc_view = load_view_definition('EncounterPendingLabCountView.json')
    print("   ✓ DiagnosticReportAtDischargeView")
    print("   ✓ EncounterPendingLabCountView")

    # Execute ViewDefinitions
    print("\n3. Running SQL on FHIR transformations...")
    runner = ViewDefinitionRunner()

    dr_results = runner.run(dr_view, fhir_data)
    dr_df = pd.DataFrame(dr_results)
    print(f"   ✓ Found {len(dr_df)} pending diagnostic reports")

    enc_results = runner.run(enc_view, fhir_data)
    enc_df = pd.DataFrame(enc_results)
    print(f"   ✓ Analyzed {len(enc_df)} encounters")

    # Calculate summary statistics
    print("\n4. Summary Statistics")
    print("   " + "-" * 50)

    encounters_with_pending = len(enc_df[enc_df['pending_lab_count'] > 0])
    pending_rate = (encounters_with_pending / len(enc_df) * 100) if len(enc_df) > 0 else 0

    print(f"   Total encounters: {len(enc_df)}")
    print(f"   Encounters with pending labs: {encounters_with_pending}")
    print(f"   Pending lab rate: {pending_rate:.1f}%")
    print(f"   Total pending lab reports: {len(dr_df)}")

    if len(dr_df) > 0:
        print(f"\n   Report Status Breakdown:")
        status_counts = dr_df['report_status'].value_counts()
        for status, count in status_counts.items():
            print(f"     - {status}: {count}")

    if len(enc_df) > 0 and 'pending_lab_count' in enc_df.columns:
        avg_pending = enc_df['pending_lab_count'].mean()
        max_pending = enc_df['pending_lab_count'].max()
        print(f"\n   Average pending labs per encounter: {avg_pending:.2f}")
        print(f"   Maximum pending labs (single encounter): {max_pending}")

    # Create visualizations
    print("\n5. Generating visualizations...")

    # Visualization 1: Pending Lab Status Distribution
    if len(dr_df) > 0:
        fig1 = px.bar(
            dr_df['report_status'].value_counts().reset_index(),
            x='report_status',
            y='count',
            title='Pending Lab Reports by Status',
            labels={'report_status': 'Report Status', 'count': 'Number of Reports'},
            color='report_status',
            color_discrete_map={
                'registered': '#ff7f0e',
                'partial': '#2ca02c',
                'preliminary': '#1f77b4'
            }
        )
        fig1.update_layout(showlegend=False, height=500)
        fig1.write_html('viz_1_status_distribution.html')
        print("   ✓ Created viz_1_status_distribution.html")

    # Visualization 2: Pending Lab Count Distribution
    if len(enc_df) > 0 and 'pending_lab_count' in enc_df.columns:
        fig2 = px.histogram(
            enc_df,
            x='pending_lab_count',
            nbins=20,
            title='Distribution of Pending Lab Counts per Encounter',
            labels={'pending_lab_count': 'Number of Pending Labs', 'count': 'Number of Encounters'},
            color_discrete_sequence=['#1f77b4']
        )
        fig2.update_layout(height=500, showlegend=False)
        fig2.write_html('viz_2_count_distribution.html')
        print("   ✓ Created viz_2_count_distribution.html")

    # Visualization 3: Time Series Analysis
    if len(dr_df) > 0 and 'hospital_discharge_time' in dr_df.columns:
        dr_df['hospital_discharge_time'] = pd.to_datetime(dr_df['hospital_discharge_time'])
        dr_df['discharge_date'] = dr_df['hospital_discharge_time'].dt.date

        daily_counts = dr_df.groupby('discharge_date').size().reset_index(name='count')
        daily_counts['discharge_date'] = pd.to_datetime(daily_counts['discharge_date'])

        fig3 = px.line(
            daily_counts,
            x='discharge_date',
            y='count',
            title='Pending Labs at Discharge - Daily Trend',
            labels={'discharge_date': 'Discharge Date', 'count': 'Number of Pending Labs'},
            markers=True
        )
        fig3.update_traces(line_color='#d62728', marker=dict(size=8))
        fig3.update_layout(height=500)
        fig3.write_html('viz_3_daily_trend.html')
        print("   ✓ Created viz_3_daily_trend.html")

    # Visualization 4: Combined Dashboard
    if len(dr_df) > 0 and len(enc_df) > 0:
        fig4 = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Status Distribution',
                'Pending Count per Encounter',
                'Key Metrics',
                'Top Encounters by Pending Labs'
            ),
            specs=[
                [{"type": "bar"}, {"type": "histogram"}],
                [{"type": "indicator"}, {"type": "bar"}]
            ]
        )

        # Status distribution
        status_counts = dr_df['report_status'].value_counts()
        fig4.add_trace(
            go.Bar(x=status_counts.index, y=status_counts.values, name='Status'),
            row=1, col=1
        )

        # Pending count histogram
        fig4.add_trace(
            go.Histogram(x=enc_df['pending_lab_count'], name='Count Distribution'),
            row=1, col=2
        )

        # Key metric indicator
        fig4.add_trace(
            go.Indicator(
                mode="number+delta",
                value=pending_rate,
                title={'text': "Encounters with<br>Pending Labs (%)"},
                delta={'reference': 20, 'relative': False},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=2, col=1
        )

        # Top encounters
        top_encounters = enc_df.nlargest(10, 'pending_lab_count')
        fig4.add_trace(
            go.Bar(
                x=top_encounters['encounter_id'],
                y=top_encounters['pending_lab_count'],
                name='Top Encounters'
            ),
            row=2, col=2
        )

        fig4.update_layout(
            height=800,
            showlegend=False,
            title_text="Tests Pending at Discharge - Executive Dashboard"
        )
        fig4.write_html('viz_4_dashboard.html')
        print("   ✓ Created viz_4_dashboard.html")

    # Export data
    print("\n6. Exporting data files...")
    dr_df.to_csv('analysis_diagnostic_reports.csv', index=False)
    enc_df.to_csv('analysis_encounters.csv', index=False)
    print("   ✓ analysis_diagnostic_reports.csv")
    print("   ✓ analysis_encounters.csv")

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)
    print("\nOpen the HTML files in your browser to view visualizations:")
    print("  - viz_1_status_distribution.html")
    print("  - viz_2_count_distribution.html")
    print("  - viz_3_daily_trend.html")
    print("  - viz_4_dashboard.html")

if __name__ == '__main__':
    main()
```

#### 5.2 Run the Analysis

**macOS/Linux:**
```bash
python3 analyze_tpd.py
```

**Windows:**
```powershell
python analyze_tpd.py
```

#### 5.3 View Results

The script generates:
- **4 interactive HTML visualizations** (open in any web browser)
- **2 CSV files** with detailed results for further analysis

Open the visualizations:

**macOS:**
```bash
open viz_4_dashboard.html
```

**Linux:**
```bash
xdg-open viz_4_dashboard.html
```

**Windows:**
```powershell
Start-Process viz_4_dashboard.html
```

## Understanding the ViewDefinitions

### DiagnosticReportAtDischargeView.json

This ViewDefinition identifies individual lab reports that were not finalized by patient discharge.

**Key Logic:**

```json
{
  "where": [
    {
      "path": "category.coding.where(system='http://terminology.hl7.org/CodeSystem/v2-0074' and code='LAB').exists()",
      "description": "Filter for Laboratory reports only."
    },
    {
      "path": "status in ('registered', 'partial', 'preliminary')",
      "description": "Filter for reports that are not yet final/complete."
    },
    {
      "path": "encounter.resolve().period.end.exists()",
      "description": "Ensure the encounter has a discharge time."
    },
    {
      "path": "issued > encounter.resolve().period.end",
      "description": "The report was not 'issued' (or finalized) before or at the encounter end time (discharge)."
    }
  ]
}
```

**FHIRPath Techniques:**
- `.where()` - Filters collections
- `.resolve()` - Follows references (DiagnosticReport → Encounter)
- `.exists()` - Checks for presence of values
- Comparison operators - `>` compares dates/times

### EncounterPendingLabCountView.json

This ViewDefinition provides encounter-level aggregation for population analysis.

**Key Logic:**

```json
{
  "select": [
    {
      "column": [
        {
          "name": "pending_lab_count",
          "path": "DiagnosticReport.where(encounter.reference=id and status in ('registered', 'partial', 'preliminary') and issued > %resource.period.end).count()",
          "description": "Count of lab reports not issued by discharge time."
        }
      ]
    }
  ]
}
```

**Advanced Techniques:**
- `DiagnosticReport.where()` - Queries across resource types
- `%resource` - References the current Encounter being processed
- `.count()` - Aggregates results
- Complex boolean logic - Multiple conditions in single path

## Expected Results

### Typical Findings

From a dataset of 100 synthetic patients, you should expect:

- **20-30 encounters** with at least one pending lab
- **40-60 total pending lab reports**
- **Status distribution**: Approximately 40% preliminary, 35% registered, 25% partial
- **Average pending labs**: 1-3 per affected encounter
- **Peak pending labs**: 5-8 for outlier encounters

### Clinical Interpretation

High rates of pending labs suggest:
- Need for improved discharge coordination
- Potential for clinical decision support at discharge
- Opportunity for automated follow-up workflows
- Risk stratification for post-discharge monitoring

## Repository Contents

```
analytics-on-fhir-2025/
├── README.md                              # This file
├── DiagnosticReportAtDischargeView.json   # ViewDefinition for individual reports
├── EncounterPendingLabCountView.json      # ViewDefinition for encounter aggregation
├── tpd.json                               # Synthea module for test data generation
├── analyze_tpd.py                         # Python analysis script
├── test-data/                             # Generated FHIR bundles (created in Step 1)
├── *.csv                                  # Analysis results (created in Steps 3 & 5)
└── viz_*.html                             # Interactive visualizations (created in Step 5)
```

## Additional Resources

### SQL on FHIR
- [SQL on FHIR v2 Specification](https://build.fhir.org/ig/FHIR/sql-on-fhir-v2/)
- [ViewDefinition Resource](https://build.fhir.org/ig/FHIR/sql-on-fhir-v2/StructureDefinition-ViewDefinition.html)
- [FHIRPath Specification](http://hl7.org/fhirpath/)

### Helios Software
- [GitHub Repository](https://github.com/HeliosSoftware/hfs)
- [Release v0.1.30](https://github.com/HeliosSoftware/hfs/releases/tag/v0.1.30)

### Synthea
- [Synthea GitHub](https://github.com/synthetichealth/synthea)
- [Module Builder Guide](https://github.com/synthetichealth/synthea/wiki/Module-Builder)
- [Generic Module Framework](https://github.com/synthetichealth/synthea/wiki/Generic-Module-Framework)

### FHIR Resources
- [DiagnosticReport](https://www.hl7.org/fhir/diagnosticreport.html)
- [Encounter](https://www.hl7.org/fhir/encounter.html)
- [Observation](https://www.hl7.org/fhir/observation.html)

## Questions or Feedback

For questions about:
- ** The instructions in this README: Open an issua at [analytics-on-fhir-2025 GitHub](https://github.com/HeliosSoftware/analytics-on-fhir-2025/issues)
- **Helios Software**: Open an issue at [hfs GitHub](https://github.com/HeliosSoftware/hfs/issues)
- **SQL on FHIR**: Visit the [FHIR Chat](https://chat.fhir.org/) #sql-on-fhir channel

## License

The materials in this repository are provided for educational purposes as part of the Analytics on FHIR 2025 conference under the open source MIT license.

---

**Analytics on FHIR 2025** | Presented by Steve Munini | Helios Software
