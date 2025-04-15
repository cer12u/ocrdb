import os
from typing import Optional, BinaryIO, Dict, Any, List
import io
from enum import Enum
import tempfile
import shutil
from pathlib import Path

from PIL import Image
import pytesseract
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False


class OCREngine(str, Enum):
    """Available OCR engines."""
    TESSERACT = "tesseract"
    EASYOCR = "easyocr"
    PADDLEOCR = "paddleocr"


class OCRError(Exception):
    """Exception raised for OCR-related errors."""
    pass


class OCRProcessor:
    """Base class for OCR processors."""
    
    def __init__(self):
        """Initialize OCR processor."""
        self.name = "base"
        self.version = "0.0.0"
    
    async def process_image(self, image: BinaryIO) -> str:
        """
        Process an image and extract text.
        
        Args:
            image: File-like object containing the image data
            
        Returns:
            str: Extracted text
        """
        raise NotImplementedError
    
    async def process_pdf(self, pdf: BinaryIO) -> List[str]:
        """
        Process a PDF and extract text from each page.
        
        Args:
            pdf: File-like object containing the PDF data
            
        Returns:
            List[str]: List of extracted text for each page
        """
        raise NotImplementedError
    
    def get_info(self) -> Dict[str, str]:
        """
        Get information about the OCR engine.
        
        Returns:
            Dict[str, str]: Engine name and version
        """
        return {
            "name": self.name,
            "version": self.version
        }


class TesseractOCR(OCRProcessor):
    """Tesseract OCR processor."""
    
    def __init__(self):
        """Initialize Tesseract OCR processor."""
        super().__init__()
        self.name = "tesseract"
        try:
            self.version = pytesseract.get_tesseract_version().version_str
        except:
            self.version = "unknown"
    
    async def process_image(self, image: BinaryIO) -> str:
        """Process an image with Tesseract OCR."""
        try:
            img = Image.open(image)
            
            text = pytesseract.image_to_string(img)
            
            return text
        except Exception as e:
            raise OCRError(f"Tesseract OCR error: {e}")
    
    async def process_pdf(self, pdf: BinaryIO) -> List[str]:
        """
        Process a PDF with Tesseract OCR.
        
        Note: This is a simple implementation that uses pdf2image to convert
        PDF pages to images and then processes each image with Tesseract.
        For a production environment, consider using a more robust solution.
        """
        try:
            try:
                from pdf2image import convert_from_bytes
            except ImportError:
                raise OCRError("pdf2image is required for PDF processing")
            
            pdf_data = pdf.read()
            images = convert_from_bytes(pdf_data)
            
            results = []
            for img in images:
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                
                text = await self.process_image(img_byte_arr)
                results.append(text)
            
            return results
        except OCRError:
            raise
        except Exception as e:
            raise OCRError(f"PDF processing error: {e}")


class EasyOCR(OCRProcessor):
    """EasyOCR processor."""
    
    def __init__(self):
        """Initialize EasyOCR processor."""
        super().__init__()
        self.name = "easyocr"
        self.version = "unknown"  # EasyOCR doesn't provide version info easily
        
        if not EASYOCR_AVAILABLE:
            raise OCRError("EasyOCR is not installed")
            
        self.reader = easyocr.Reader(['en', 'ja'])  # English and Japanese
    
    async def process_image(self, image: BinaryIO) -> str:
        """Process an image with EasyOCR."""
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                shutil.copyfileobj(image, temp)
                temp_path = temp.name
            
            try:
                results = self.reader.readtext(temp_path)
                
                text = " ".join([result[1] for result in results])
                
                return text
            finally:
                os.unlink(temp_path)
        except Exception as e:
            raise OCRError(f"EasyOCR error: {e}")
    
    async def process_pdf(self, pdf: BinaryIO) -> List[str]:
        """Process a PDF with EasyOCR."""
        try:
            try:
                from pdf2image import convert_from_bytes
            except ImportError:
                raise OCRError("pdf2image is required for PDF processing")
            
            pdf_data = pdf.read()
            images = convert_from_bytes(pdf_data)
            
            results = []
            for img in images:
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                
                text = await self.process_image(img_byte_arr)
                results.append(text)
            
            return results
        except OCRError:
            raise
        except Exception as e:
            raise OCRError(f"PDF processing error: {e}")


class PaddleOCRProcessor(OCRProcessor):
    """PaddleOCR processor."""
    
    def __init__(self):
        """Initialize PaddleOCR processor."""
        super().__init__()
        self.name = "paddleocr"
        self.version = "unknown"  # PaddleOCR doesn't provide version info easily
        
        if not PADDLEOCR_AVAILABLE:
            raise OCRError("PaddleOCR is not installed")
            
        self.ocr = PaddleOCR(use_angle_cls=True, lang="en")
    
    async def process_image(self, image: BinaryIO) -> str:
        """Process an image with PaddleOCR."""
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                shutil.copyfileobj(image, temp)
                temp_path = temp.name
            
            try:
                results = self.ocr.ocr(temp_path, cls=True)
                
                text = ""
                for idx in range(len(results)):
                    res = results[idx]
                    for line in res:
                        text += line[1][0] + " "
                
                return text.strip()
            finally:
                os.unlink(temp_path)
        except Exception as e:
            raise OCRError(f"PaddleOCR error: {e}")
    
    async def process_pdf(self, pdf: BinaryIO) -> List[str]:
        """Process a PDF with PaddleOCR."""
        try:
            try:
                from pdf2image import convert_from_bytes
            except ImportError:
                raise OCRError("pdf2image is required for PDF processing")
            
            pdf_data = pdf.read()
            images = convert_from_bytes(pdf_data)
            
            results = []
            for img in images:
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                
                text = await self.process_image(img_byte_arr)
                results.append(text)
            
            return results
        except OCRError:
            raise
        except Exception as e:
            raise OCRError(f"PDF processing error: {e}")


async def get_ocr_processor(engine: str = "tesseract") -> OCRProcessor:
    """
    Factory function to get the appropriate OCR processor.
    
    Args:
        engine: OCR engine to use
        
    Returns:
        OCRProcessor: OCR processor implementation
        
    Raises:
        OCRError: If the requested engine is not available
    """
    if engine == OCREngine.TESSERACT:
        return TesseractOCR()
    elif engine == OCREngine.EASYOCR:
        if not EASYOCR_AVAILABLE:
            raise OCRError("EasyOCR is not installed")
        return EasyOCR()
    elif engine == OCREngine.PADDLEOCR:
        if not PADDLEOCR_AVAILABLE:
            raise OCRError("PaddleOCR is not installed")
        return PaddleOCRProcessor()
    else:
        raise OCRError(f"Unknown OCR engine: {engine}")


async def get_available_ocr_engines() -> List[Dict[str, Any]]:
    """
    Get a list of available OCR engines.
    
    Returns:
        List[Dict[str, Any]]: List of available OCR engines with their info
    """
    engines = []
    
    try:
        processor = TesseractOCR()
        engines.append({
            "id": OCREngine.TESSERACT,
            "name": "Tesseract OCR",
            "version": processor.version,
            "available": True
        })
    except Exception:
        engines.append({
            "id": OCREngine.TESSERACT,
            "name": "Tesseract OCR",
            "version": "unknown",
            "available": False
        })
    
    engines.append({
        "id": OCREngine.EASYOCR,
        "name": "EasyOCR",
        "version": "unknown",
        "available": EASYOCR_AVAILABLE
    })
    
    engines.append({
        "id": OCREngine.PADDLEOCR,
        "name": "PaddleOCR",
        "version": "unknown",
        "available": PADDLEOCR_AVAILABLE
    })
    
    return engines
