import os
import json
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from pdf_processor import PDFProcessor

class BatchPDFProcessor:
    def __init__(self, max_workers: int = 4):
        self.processor = PDFProcessor()
        self.max_workers = max_workers
        
    def _normalize_raster_results(self, results: Dict) -> Dict[str, Any]:
        """Normalize raster processing results to a standard format"""
        return {
            "type": "raster",
            "total_pages": results["total_pages"],
            "processed_files": [
                {
                    "page_number": i + 1,
                    "file_path": path,
                    "file_type": "image"
                }
                for i, path in enumerate(results["processed_images"])
            ]
        }
    
    def _normalize_vector_results(self, results: Dict) -> Dict[str, Any]:
        """Normalize vector processing results to a standard format"""
        return {
            "type": "vector",
            "total_pages": results["total_pages"],
            "processed_files": [
                {
                    "page_number": i + 1,
                    "file_path": f"page_{i+1}_text.txt",
                    "file_type": "text",
                    "content_length": len(text)
                }
                for i, text in enumerate(results["text_content"])
            ],
            "metadata": results["metadata"] if results["metadata"] else {}
        }
    
    def process_single_pdf(self, pdf_path: str, output_dir: str) -> Dict[str, Any]:
        """Process a single PDF and return normalized results"""
        try:
            # Create a subdirectory for this PDF
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            pdf_output_dir = os.path.join(output_dir, pdf_name)
            os.makedirs(pdf_output_dir, exist_ok=True)
            
            # Process the PDF
            pdf_type, results = self.processor.process_pdf(pdf_path, pdf_output_dir)
            
            # Normalize results
            if pdf_type == "raster":
                normalized_results = self._normalize_raster_results(results)
            else:
                normalized_results = self._normalize_vector_results(results)
            
            # Add PDF information
            normalized_results["pdf_name"] = pdf_name
            normalized_results["pdf_path"] = pdf_path
            
            return normalized_results
            
        except Exception as e:
            return {
                "pdf_name": os.path.basename(pdf_path),
                "pdf_path": pdf_path,
                "error": str(e)
            }
    
    def process_directory(self, input_dir: str, output_dir: str) -> Dict[str, Any]:
        """Process all PDFs in a directory and return combined results"""
        # Find all PDF files
        pdf_files = [
            os.path.join(input_dir, f)
            for f in os.listdir(input_dir)
            if f.lower().endswith('.pdf')
        ]
        
        if not pdf_files:
            return {"error": "No PDF files found in the input directory"}
        
        # Process PDFs in parallel
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_pdf = {
                executor.submit(self.process_single_pdf, pdf_path, output_dir): pdf_path
                for pdf_path in pdf_files
            }
            
            for future in as_completed(future_to_pdf):
                pdf_path = future_to_pdf[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        "pdf_name": os.path.basename(pdf_path),
                        "pdf_path": pdf_path,
                        "error": str(e)
                    })
        
        # Create summary
        summary = {
            "total_pdfs": len(pdf_files),
            "successful_processing": len([r for r in results if "error" not in r]),
            "failed_processing": len([r for r in results if "error" in r]),
            "results": results
        }
        
        # Save results to JSON file
        output_file = os.path.join(output_dir, "processing_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        return summary 