# PDF Type Detector and Processor

This tool detects whether a PDF is primarily raster-based or vector-based and processes it accordingly using specialized pipelines for each type. It supports both single PDF processing and batch processing of multiple PDFs.

## Features

- Automatic PDF type detection (Raster vs Vector)
- Dual processing pipelines:
  - Raster PDFs: Image processing pipeline with edge detection and thresholding
  - Vector PDFs: Text extraction and metadata processing
- Batch processing support for multiple PDFs
- Parallel processing with configurable number of workers
- Normalized JSON output format
- Output generation for both types

## Requirements

- Python 3.7+
- Poppler (for PDF to image conversion)

## Installation

1. Install the required Python packages:
```bash
pip install -r requirements.txt
```

2. Install Poppler:
- Windows: Download and install from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases/)
- Linux: `sudo apt-get install poppler-utils`
- macOS: `brew install poppler`

## Usage

### Single PDF Processing

1. Place your PDF file in the project directory
2. Run the example script and choose option 1:
```bash
python example.py
```

### Batch Processing

1. Create a directory named `pdfs` in the project directory
2. Place all your PDF files in the `pdfs` directory
3. Run the example script and choose option 2:
```bash
python example.py
```

## Output

### Single PDF Processing
The tool will create an `output/single` directory containing:
- For raster PDFs: Processed images of each page
- For vector PDFs: Text files containing extracted content and metadata

### Batch Processing
The tool will create an `output/batch` directory containing:
- A subdirectory for each processed PDF
- A `processing_results.json` file with the following structure:
```json
{
  "total_pdfs": 10,
  "successful_processing": 8,
  "failed_processing": 2,
  "results": [
    {
      "pdf_name": "example1",
      "pdf_path": "pdfs/example1.pdf",
      "type": "raster",
      "total_pages": 5,
      "processed_files": [
        {
          "page_number": 1,
          "file_path": "page_1_processed.png",
          "file_type": "image"
        }
      ]
    },
    {
      "pdf_name": "example2",
      "pdf_path": "pdfs/example2.pdf",
      "type": "vector",
      "total_pages": 3,
      "processed_files": [
        {
          "page_number": 1,
          "file_path": "page_1_text.txt",
          "file_type": "text",
          "content_length": 1500
        }
      ],
      "metadata": {
        "Author": "John Doe",
        "Title": "Example Document"
      }
    }
  ]
}
```

## How it Works

The tool uses a combination of techniques to detect PDF type:
1. Edge detection and density analysis
2. Text content extraction
3. PDF metadata analysis

Based on the detection results, it routes the PDF through the appropriate processing pipeline:
- Raster pipeline: Image processing with OpenCV
- Vector pipeline: Text extraction and metadata processing

For batch processing, the tool:
1. Processes multiple PDFs in parallel using ThreadPoolExecutor
2. Creates separate output directories for each PDF
3. Normalizes all results to a consistent JSON format
4. Generates a summary of the processing results