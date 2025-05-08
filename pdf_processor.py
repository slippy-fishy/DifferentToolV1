import os
from typing import Tuple, Dict, List, Optional
import cv2
import numpy as np
from PyPDF2 import PdfReader
from PIL import Image
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from tqdm import tqdm

class PDFProcessor:
    def __init__(self, max_workers: int = 4, max_pages: Optional[int] = None):
        self.raster_threshold = 0.95  # Threshold for determining if a PDF is raster-based
        self.max_workers = max_workers
        self.max_pages = max_pages  # Maximum number of pages to process (None for all pages)
        
    def detect_pdf_type(self, pdf_path: str) -> str:
        """
        Detect if a PDF is primarily raster-based or vector-based.
        Returns: 'raster' or 'vector'
        """
        try:
            # First check if it's vector-based by looking for text
            reader = PdfReader(pdf_path)
            page = reader.pages[0]
            
            # If the page has text content, it's likely vector-based
            if page.extract_text().strip():
                return 'vector'
            
            # If no text found, check if it's raster-based
            # Convert first page to image
            img = self._convert_pdf_page_to_image(pdf_path)
            
            # Convert PIL image to OpenCV format
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # Calculate image statistics
            edges = cv2.Canny(cv_img, 100, 200)
            edge_density = np.count_nonzero(edges) / (edges.shape[0] * edges.shape[1])
            
            # If edge density is high, it's likely raster-based
            if edge_density > self.raster_threshold:
                return 'raster'
            
            return 'vector'
            
        except Exception as e:
            raise Exception(f"Error detecting PDF type: {str(e)}")
    
    def _convert_pdf_page_to_image(self, pdf_path: str, page_num: int = 0) -> Image.Image:
        """Convert a PDF page to an image using PyPDF2 and Pillow"""
        try:
            reader = PdfReader(pdf_path)
            page = reader.pages[page_num]
            
            # Get the page dimensions
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            
            # Create a blank image with white background
            img = Image.new('RGB', (int(width), int(height)), 'white')
            
            # Try to extract images from the page
            for image in page.images:
                try:
                    image_data = image.data
                    image_stream = io.BytesIO(image_data)
                    page_image = Image.open(image_stream)
                    img.paste(page_image, (0, 0))
                except:
                    continue
            
            return img
            
        except Exception as e:
            raise Exception(f"Error converting PDF page to image: {str(e)}")
    
    def _process_single_page(self, pdf_path: str, page_num: int, output_dir: str) -> Dict:
        """Process a single page of the PDF"""
        try:
            # Convert page to image
            img = self._convert_pdf_page_to_image(pdf_path, page_num)
            
            # Convert to OpenCV format
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            
            # Basic image processing
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Save processed image
            output_path = os.path.join(output_dir, f'page_{page_num+1}_processed.png')
            cv2.imwrite(output_path, thresh)
            
            return {
                'page_number': page_num + 1,
                'file_path': output_path
            }
            
        except Exception as e:
            return {
                'page_number': page_num + 1,
                'error': str(e)
            }
    
    def process_raster_pdf(self, pdf_path: str, output_dir: str) -> Dict:
        """
        Process raster-based PDFs using image processing techniques
        """
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            
            # Limit the number of pages to process
            pages_to_process = min(total_pages, self.max_pages) if self.max_pages else total_pages
            
            print(f"\nProcessing {pages_to_process} of {total_pages} pages as raster PDF...")
            start_time = time.time()
            
            results = {
                'total_pages': total_pages,
                'pages_processed': pages_to_process,
                'processed_images': []
            }
            
            # Process pages in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit pages for processing
                future_to_page = {
                    executor.submit(self._process_single_page, pdf_path, i, output_dir): i
                    for i in range(pages_to_process)
                }
                
                # Process results as they complete
                with tqdm(total=pages_to_process, desc="Processing pages") as pbar:
                    for future in as_completed(future_to_page):
                        result = future.result()
                        if 'error' not in result:
                            results['processed_images'].append(result['file_path'])
                        pbar.update(1)
            
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"\nProcessing completed in {processing_time:.2f} seconds")
            print(f"Average time per page: {processing_time/pages_to_process:.2f} seconds")
            
            return results
            
        except Exception as e:
            raise Exception(f"Error processing raster PDF: {str(e)}")
    
    def _process_vector_page(self, page, page_num: int, output_dir: str) -> Dict:
        """Process a single vector page"""
        try:
            # Extract text with error handling
            try:
                text = page.extract_text()
                if text is None:
                    text = ""
            except Exception as e:
                print(f"Warning: Error extracting text from page {page_num + 1}: {str(e)}")
                text = ""
            
            # Only save if there's actual text content
            if text.strip():
                try:
                    output_path = os.path.join(output_dir, f'page_{page_num+1}_text.txt')
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                except Exception as e:
                    print(f"Warning: Error saving text for page {page_num + 1}: {str(e)}")
            
            return {
                'page_number': page_num + 1,
                'text': text,
                'text_length': len(text)
            }
            
        except Exception as e:
            print(f"Warning: Error processing page {page_num + 1}: {str(e)}")
            return {
                'page_number': page_num + 1,
                'text': "",
                'text_length': 0,
                'error': str(e)
            }
    
    def process_vector_pdf(self, pdf_path: str, output_dir: str) -> Dict:
        """
        Process vector-based PDFs using PDF-specific techniques
        """
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            
            print(f"\nExtracting text from {total_pages} pages...")
            start_time = time.time()
            
            results = {
                'total_pages': total_pages,
                'pages_processed': total_pages,
                'text_content': [],
                'metadata': reader.metadata,
                'pages_with_text': 0,
                'total_text_length': 0
            }
            
            # Process pages in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit pages for processing
                future_to_page = {
                    executor.submit(self._process_vector_page, reader.pages[i], i, output_dir): i
                    for i in range(total_pages)
                }
                
                # Process results as they complete
                with tqdm(total=total_pages, desc="Extracting text") as pbar:
                    for future in as_completed(future_to_page):
                        result = future.result()
                        results['text_content'].append(result['text'])
                        if result['text'].strip():
                            results['pages_with_text'] += 1
                            results['total_text_length'] += result['text_length']
                        pbar.update(1)
            
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"\nText extraction completed in {processing_time:.2f} seconds")
            print(f"Pages with text: {results['pages_with_text']} of {total_pages}")
            print(f"Total text extracted: {results['total_text_length']} characters")
            print(f"Average time per page: {processing_time/total_pages:.2f} seconds")
            
            return results
            
        except Exception as e:
            raise Exception(f"Error processing vector PDF: {str(e)}")
    
    def process_pdf(self, pdf_path: str, output_dir: str) -> Tuple[str, Dict]:
        """
        Main processing function that detects PDF type and routes to appropriate pipeline
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        print("Detecting PDF type...")
        # Detect PDF type
        pdf_type = self.detect_pdf_type(pdf_path)
        print(f"PDF type detected: {pdf_type}")
        
        # Process based on type
        if pdf_type == 'raster':
            results = self.process_raster_pdf(pdf_path, output_dir)
        else:
            results = self.process_vector_pdf(pdf_path, output_dir)
        
        return pdf_type, results 