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

This demonstration uses SQL on FHIR ViewDefinitions to identify and analyze laboratory results that were issued after patient discharge, providing actionable intelligence for quality improvement initiatives.

### Analytics Approach

We'll use two complementary ViewDefinitions:

1. **LabObservationView**: Extracts laboratory observations with timing and encounter references
2. **EncounterView**: Extracts encounter timing information for discharge analysis

By joining these views, we can identify labs that were issued after discharge time - representing tests that were pending when the patient left.

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

## Demo Walkthrough

### Step 1: Generate Test Data with Synthea

#### 1.1 Clone Synthea

```bash
# Clone Synthea
git clone https://github.com/synthetichealth/synthea.git
cd synthea
```

#### 1.2 Install the TPD Custom Module

Copy the `tpd.json` module from this repository into Synthea's modules directory:

**macOS/Linux:**
```bash
# From the synthea directory
cp ../tpd.json src/main/resources/modules/
```

**Windows:**
```powershell
copy ..\tpd.json src\main\resources\modules\
```

#### 1.3 Generate Synthetic Patients

Generate 10000 patients with the TPD module:

**macOS/Linux:**
```bash
./run_synthea -m tpd -p 10000 --exporter.fhir.bulk_data=true
```

**Windows:**
```powershell
.\run_synthea.bat -m tpd -p 10000 --exporter.fhir.bulk_data=true
```

This creates FHIR R4 resources in NDJSON format in `output/fhir/` with:
- Encounter resources (visits with varied lengths of stay)
- Observation resources (laboratory results with timing information)

The NDJSON format provides one FHIR resource per line, ideal for streaming and bulk processing.

### Step 2: Download Helios Software Binaries

Change directory back to the root of the project.
```bash
cd ..
```

Download and extract the appropriate binaries for your platform from the [latest hfs release](https://github.com/HeliosSoftware/hfs/releases/latest):

#### macOS (Apple Silicon)

```bash
# Download and extract the tar.gz archive
curl -L https://github.com/HeliosSoftware/hfs/releases/download/v0.1.32/hfs-0.1.32-aarch64-apple-darwin.tar.gz -o hfs.tar.gz
tar -xzf hfs.tar.gz

# Make binaries executable
chmod +x sof-cli sof-server

# Verify installation
./sof-cli --help
./sof-server --help
```

#### Linux (x86_64)

```bash
# Download and extract the tar.gz archive
curl -L https://github.com/HeliosSoftware/hfs/releases/download/v0.1.32/hfs-0.1.32-x86_64-unknown-linux-gnu.tar.gz -o hfs.tar.gz
tar -xzf hfs.tar.gz

# Make binaries executable
chmod +x sof-cli sof-server

# Verify installation
./sof-cli --help
./sof-server --help
```

#### Windows (x86_64)

```powershell
# Download and extract the zip archive
Invoke-WebRequest -Uri "https://github.com/HeliosSoftware/hfs/releases/download/v0.1.32/hfs-0.1.32-x86_64-pc-windows-msvc.zip" -OutFile "hfs.zip"
Expand-Archive -Path "hfs.zip" -DestinationPath "."

# Verify installation
.\sof-cli.exe --help
.\sof-server.exe --help
```

### Step 3: Batch Processing with sof-cli

The `sof-cli` tool is ideal for batch transformations, ETL pipelines, and scheduled analytics jobs.

#### 3.1 Run LabObservationView

This ViewDefinition extracts laboratory observations with timing information:

**macOS/Linux:**
```bash
./sof-cli \
  --view LabObservationView.json \
  --source ./synthea/output/fhir/Observation.ndjson \
  --output lab_observations.csv \
  --format csv
```

**Windows:**
```powershell
.\sof-cli.exe `
  --view LabObservationView.json `
  --source .\synthea\output\fhir\Observation.ndjson `
  --output lab_observations.csv `
  --format csv
```

**Output columns:**
- `observation_id`: Unique Observation identifier
- `lab_code`: LOINC code for the lab test
- `lab_display`: Display name of the lab test
- `status`: Status of the observation
- `effective_time`: When the observation was made
- `issued_time`: When the result was issued/available
- `encounter_id`: Reference to the associated encounter
- `patient_id`: Reference to the patient

#### 3.2 Run EncounterView

This ViewDefinition extracts encounter timing for discharge analysis:

**macOS/Linux:**
```bash
./sof-cli \
  --view EncounterView.json \
  --source ./synthea/output/fhir/Encounter.ndjson \
  --output encounters.csv \
  --format csv
```

**Windows:**
```powershell
.\sof-cli.exe `
  --view EncounterView.json `
  --source .\synthea\output\fhir\Encounter.ndjson `
  --output encounters.csv `
  --format csv
```

**Output columns:**
- `encounter_id`: Unique encounter identifier
- `encounter_class`: Class of encounter (AMB, IMP, etc.)
- `encounter_type`: Type of encounter
- `start_time`: When the encounter started
- `end_time`: Discharge timestamp
- `patient_id`: Reference to the patient

#### 3.3 Inspect Results

**macOS/Linux:**
```bash
# View first 10 rows
head -10 lab_observations.csv
head -10 encounters.csv

# Count total lab observations
wc -l lab_observations.csv

# Count encounters
wc -l encounters.csv
```

**Windows (PowerShell):**
```powershell
# View first 10 rows
Get-Content lab_observations.csv | Select-Object -First 10
Get-Content encounters.csv | Select-Object -First 10

# Count total lab observations
(Get-Content lab_observations.csv | Measure-Object -Line).Lines

# Count encounters
(Get-Content encounters.csv | Measure-Object -Line).Lines
```

### Step 4: Microservices with sof-server

The `sof-server` provides a REST API for on-demand ViewDefinition execution, ideal for integrating SQL on FHIR into microservice architectures.

#### 4.1 Start the Server

**macOS/Linux:**
```bash
./sof-server --port 8080 &
```

**Windows (PowerShell, run in separate window):**
```powershell
.\sof-server.exe --port 8080
```

#### 4.2 Execute ViewDefinitions via HTTP

The server is stateless - each request must include both the ViewDefinition and the FHIR data source.  Note - the `source` parameter will need an absolute path in this example.

**Execute LabObservationView:**

**macOS/Linux:**
```bash
curl -X POST "http://localhost:8080/ViewDefinition/\$viewdefinition-run?source=file://\$(pwd)/synthea/output/fhir/Observation.ndjson" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d @LabObservationViewAsParameters.json \
  | jq '.'
```

**Windows (PowerShell):**
```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8080/ViewDefinition/`$viewdefinition-run?source=file:///$((Get-Location).Path -replace '\\','/')/synthea/output/fhir/Observation.ndjson" `
  -ContentType "application/json" `
  -Headers @{Accept="application/json"} `
  -InFile "LabObservationViewAsParameters.json" | ConvertTo-Json
```

### Step 5: Data Science with pysof

The Python bindings enable SQL on FHIR integration into Jupyter notebooks, data pipelines, and ML workflows.

#### 5.1 Set Up Python Environment

It is recommended to use a virtual environment to avoid conflicts with system packages.

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install pandas plotly pysof
```

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install pandas plotly pysof
```

#### 5.2 Review the Analysis Script

The repository includes `analyze_tpd.py`, a Python script that demonstrates the Tests Pending at Discharge analysis. This script:

- Loads the CSV files generated by sof-cli
- Joins lab observations with encounters on encounter references
- Identifies labs where `issued_time > end_time` (issued after discharge)
- Calculates summary statistics (pending rate, distribution by lab code)
- Generates an interactive Plotly visualizations
- Exports detailed analysis files for further investigation

#### 5.3 Run the Analysis

First, generate the CSV files using sof-cli (if not already done):

**macOS/Linux:**
```bash
./sof-cli --view LabObservationView.json --source ./synthea/output/fhir/Observation.ndjson --output lab_observations.csv --format csv
./sof-cli --view EncounterView.json --source ./synthea/output/fhir/Encounter.ndjson --output encounters.csv --format csv
```

**Windows:**
```powershell
.\sof-cli.exe --view LabObservationView.json --source .\synthea\output\fhir\Observation.ndjson --output lab_observations.csv --format csv
.\sof-cli.exe --view EncounterView.json --source .\synthea\output\fhir\Encounter.ndjson --output encounters.csv --format csv
```

Then run the analysis:

**macOS/Linux:**
```bash
python3 analyze_tpd.py
```

**Windows:**
```powershell
python analyze_tpd.py
```

#### 5.4 View Results

The script generates:
- **HTML visualization** (open in any web browser)
- **2 CSV files** with detailed results for further analysis

Open the visualizations:

**macOS:**
```bash
open tests_pending_by_day.html
```

**Linux:**
```bash
xdg-open tests_pending_by_day.html
```

**Windows:**
```powershell
Start-Process tests_pending_by_day.html
```

## Understanding the ViewDefinitions

### LabObservationView.json

This ViewDefinition extracts laboratory observations with their timing and encounter information.

**Key Logic:**

```json
{
  "where": [
    {
      "path": "category.coding.where(system='http://terminology.hl7.org/CodeSystem/observation-category' and code='laboratory').exists()",
      "description": "Filter for Laboratory observations only."
    },
    {
      "path": "encounter.exists()",
      "description": "Ensure the observation has an associated encounter."
    }
  ]
}
```

**FHIRPath Techniques:**
- `.where()` - Filters collections based on conditions
- `.exists()` - Checks for presence of values
- Compound conditions with `and`

### EncounterView.json

This ViewDefinition extracts encounter timing for discharge analysis.

**Key Logic:**

```json
{
  "where": [
    {
      "path": "period.end.exists()",
      "description": "Only include encounters that have ended (patient discharged)."
    }
  ]
}
```

**Key Fields:**
- `period.start` - When the encounter began
- `period.end` - When the patient was discharged
- `class.code` - Type of encounter (AMB, IMP, etc.)

### Analytics Join Pattern

The analysis script demonstrates a common pattern for SQL on FHIR analytics:

1. **Extract** data from different resource types using ViewDefinitions
2. **Transform** timestamps and references
3. **Join** the datasets on common keys (encounter references)
4. **Analyze** the combined data to identify patterns

This pattern enables complex analytics that span multiple FHIR resource types while keeping each ViewDefinition simple and focused.

## Expected Results

### Typical Findings

From a dataset of 10,000 synthetic patients, you should expect:

- **Lab observations with encounter references**
- **Encounters with timing information**
- **Labs issued after discharge** (based on timing comparison)

### Clinical Interpretation

Labs issued after discharge suggest:
- Need for improved discharge coordination
- Potential for clinical decision support at discharge
- Opportunity for automated follow-up workflows
- Risk stratification for post-discharge monitoring

## Repository Contents

```
analytics-on-fhir-2025/
├── README.md                    # This file
├── LabObservationView.json      # ViewDefinition for lab observations
├── EncounterView.json           # ViewDefinition for encounter timing
├── tpd.json                     # Synthea module for test data generation
├── analyze_tpd.py               # Python analysis script
├── synthea/output/fhir/         # Generated FHIR data (created in Step 1)
├── *.csv                        # Analysis results (created in Steps 3 & 5)
└── viz_*.html                   # Interactive visualizations (created in Step 5)
```

## Additional Resources

### SQL on FHIR
- [SQL on FHIR v2 Specification](https://build.fhir.org/ig/FHIR/sql-on-fhir-v2/)
- [ViewDefinition Resource](https://build.fhir.org/ig/FHIR/sql-on-fhir-v2/StructureDefinition-ViewDefinition.html)
- [FHIRPath Specification](http://hl7.org/fhirpath/)

### Helios Software
- [GitHub Repository](https://github.com/HeliosSoftware/hfs)
- [Release v0.1.32](https://github.com/HeliosSoftware/hfs/releases/tag/v0.1.32)

### Synthea
- [Synthea GitHub](https://github.com/synthetichealth/synthea)
- [Module Builder Guide](https://github.com/synthetichealth/synthea/wiki/Module-Builder)
- [Generic Module Framework](https://github.com/synthetichealth/synthea/wiki/Generic-Module-Framework)

### FHIR Resources
- [Observation](https://www.hl7.org/fhir/observation.html)
- [Encounter](https://www.hl7.org/fhir/encounter.html)

## Questions or Feedback

For questions about:
- **The instructions in this README**: Open an issue at [analytics-on-fhir-2025 GitHub](https://github.com/HeliosSoftware/analytics-on-fhir-2025/issues)
- **Helios Software**: Open an issue at [hfs GitHub](https://github.com/HeliosSoftware/hfs/issues)
- **SQL on FHIR**: Visit the [FHIR Chat](https://chat.fhir.org/) #sql-on-fhir channel

## License

The materials in this repository are provided for educational purposes as part of the Analytics on FHIR 2025 conference under the open source MIT license.

---

**Analytics on FHIR 2025** | Presented by Steve Munini | Helios Software
