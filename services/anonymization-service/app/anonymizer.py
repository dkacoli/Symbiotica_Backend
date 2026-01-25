import pandas as pd
import hashlib
import random
import string
from faker import Faker
from typing import List, Dict, Tuple
import io
import json

class AnonymizationEngine:
    """Handles dataset anonymization with multiple strategies"""
    
    def __init__(self):
        self.fake = Faker()
    
    def anonymize_by_hashing(self, value: str) -> str:
        """Anonymize using SHA256 hashing"""
        return hashlib.sha256(value.encode()).hexdigest()[:16]
    
    def anonymize_by_tokenization(self, value: str) -> str:
        """Anonymize using tokenization (random token mapping)"""
        return f"TOKEN_{random.randint(100000, 999999)}"
    
    def anonymize_by_removal(self, value: str) -> str:
        """Remove data by returning NULL"""
        return None
    
    def anonymize_by_masking(self, value: str, pattern: str = "***") -> str:
        """Anonymize by masking (e.g., email -> ***@***.com)"""
        if "@" in str(value):  # Email
            return "***@***.com"
        return pattern
    
    def anonymize_by_generalization(self, value: str, category: str = "general") -> str:
        """Anonymize by generalizing data"""
        if category == "age":
            age = int(value) if value else 0
            if age < 20:
                return "<20"
            elif age < 30:
                return "20-30"
            elif age < 40:
                return "30-40"
            elif age < 50:
                return "40-50"
            else:
                return "50+"
        elif category == "location":
            return "UNKNOWN_LOCATION"
        return str(value)
    
    def anonymize_by_synthetic_data(self, value: str, data_type: str) -> str:
        """Replace with synthetic data"""
        if data_type == "name":
            return self.fake.name()
        elif data_type == "email":
            return self.fake.email()
        elif data_type == "phone":
            return self.fake.phone_number()
        elif data_type == "address":
            return self.fake.address()
        return self.fake.word()
    
    def anonymize_dataset(
        self,
        file_data: bytes,
        file_format: str,
        fields_to_anonymize: List[str],
        method: str,
    ) -> bytes:
        """Anonymize a complete dataset"""
        
        # Load dataset based on format
        if file_format.upper() == "CSV":
            df = pd.read_csv(io.BytesIO(file_data))
        elif file_format.upper() == "JSON":
            df = pd.read_json(io.BytesIO(file_data))
        elif file_format.upper() == "PARQUET":
            df = pd.read_parquet(io.BytesIO(file_data))
        else:
            raise ValueError(f"Unsupported format: {file_format}")
        
        # Validate fields exist
        for field in fields_to_anonymize:
            if field not in df.columns:
                raise ValueError(f"Field '{field}' not found in dataset")
        
        # Apply anonymization method
        for field in fields_to_anonymize:
            if method == "hashing":
                df[field] = df[field].astype(str).apply(self.anonymize_by_hashing)
            elif method == "tokenization":
                df[field] = df[field].astype(str).apply(self.anonymize_by_tokenization)
            elif method == "removal":
                df[field] = None
            elif method == "masking":
                df[field] = df[field].astype(str).apply(self.anonymize_by_masking)
            elif method == "generalization":
                df[field] = df[field].astype(str).apply(
                    lambda x: self.anonymize_by_generalization(x, field)
                )
            elif method == "synthetic":
                df[field] = df[field].astype(str).apply(
                    lambda x: self.anonymize_by_synthetic_data(x, field)
                )
        
        # Export anonymized dataset
        output = io.BytesIO()
        if file_format.upper() == "CSV":
            df.to_csv(output, index=False)
        elif file_format.upper() == "JSON":
            df.to_json(output, orient="records")
        elif file_format.upper() == "PARQUET":
            df.to_parquet(output, index=False)
        
        return output.getvalue()
    
    def get_anonymization_report(
        self,
        original_file: bytes,
        anonymized_file: bytes,
        file_format: str,
        anonymized_fields: List[str],
    ) -> Dict:
        """Generate report on anonymization results"""
        
        df_original = pd.read_csv(io.BytesIO(original_file)) if file_format.upper() == "CSV" else None
        df_anonymized = pd.read_csv(io.BytesIO(anonymized_file)) if file_format.upper() == "CSV" else None
        
        if df_original is None or df_anonymized is None:
            return {"status": "report_generation_skipped"}
        
        return {
            "total_rows": len(df_original),
            "total_columns": len(df_original.columns),
            "anonymized_fields": anonymized_fields,
            "fields_remaining": len(df_original.columns) - len(anonymized_fields),
            "file_size_original": len(original_file),
            "file_size_anonymized": len(anonymized_file),
            "compression_ratio": len(anonymized_file) / len(original_file),
        }