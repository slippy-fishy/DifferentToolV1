from pdf_processor import PDFProcessor
from batch_processor import BatchPDFProcessor
import os
import json

def process_single_pdf():
    """Example of processing a single PDF"""
    # Initialize processor (page limit only applies to raster PDFs)
    processor = PDFProcessor(max_workers=4, max_pages=10)
    
    # Get the first PDF file from the pdfs directory
    pdf_dir = "pdfs"
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in the 'pdfs' directory!")
        return
    
    pdf_path = os.path.join(pdf_dir, pdf_files[0])
    output_dir = "output/single"
    
    try:
        print(f"Processing PDF: {pdf_files[0]}")
        # Process the PDF
        pdf_type, results = processor.process_pdf(pdf_path, output_dir)
        
        print(f"PDF Type: {pdf_type}")
        print(f"Total Pages in PDF: {results['total_pages']}")
        print(f"Pages Processed: {results['pages_processed']}")
        
        if pdf_type == 'raster':
            print("\nProcessed Images:")
            for img_path in results['processed_images']:
                print(f"- {img_path}")
        else:
            print("\nExtracted Text Files:")
            for i, text in enumerate(results['text_content']):
                if text.strip():  # Only show non-empty text content
                    print(f"- Page {i+1}: {len(text)} characters")
            
            print("\nPDF Metadata:")
            for key, value in results['metadata'].items():
                print(f"- {key}: {value}")
                
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")

def process_multiple_pdfs():
    """Example of processing multiple PDFs in a directory"""
    # Initialize batch processor (page limit only applies to raster PDFs)
    batch_processor = BatchPDFProcessor(max_workers=4)
    
    input_dir = "pdfs"  # Directory containing PDF files
    output_dir = "output/batch"
    
    try:
        # Create input directory if it doesn't exist
        os.makedirs(input_dir, exist_ok=True)
        
        # Process all PDFs in the directory
        summary = batch_processor.process_directory(input_dir, output_dir)
        
        # Print summary
        print("\nProcessing Summary:")
        print(f"Total PDFs: {summary['total_pdfs']}")
        print(f"Successfully processed: {summary['successful_processing']}")
        print(f"Failed to process: {summary['failed_processing']}")
        
        # Print results for each PDF
        print("\nDetailed Results:")
        for result in summary['results']:
            print(f"\nPDF: {result['pdf_name']}")
            if 'error' in result:
                print(f"Error: {result['error']}")
            else:
                print(f"Type: {result['type']}")
                print(f"Total Pages: {result['total_pages']}")
                print(f"Pages Processed: {result['pages_processed']}")
                print("Processed Files:")
                for file_info in result['processed_files']:
                    print(f"- Page {file_info['page_number']}: {file_info['file_path']}")
        
        print(f"\nComplete results saved to: {os.path.join(output_dir, 'processing_results.json')}")
        
    except Exception as e:
        print(f"Error in batch processing: {str(e)}")

if __name__ == "__main__":
    print("1. Process single PDF")
    print("2. Process multiple PDFs")
    choice = input("Enter your choice (1 or 2): ")
    
    if choice == "1":
        process_single_pdf()
    elif choice == "2":
        process_multiple_pdfs()
    else:
        print("Invalid choice!") 