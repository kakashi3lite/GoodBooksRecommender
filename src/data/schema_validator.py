"""
Production-Grade Data Schema Validation Module
Following Bookworm AI Coding Standards for comprehensive data validation.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from abc import ABC, abstractmethod

try:
    from src.core.logging import get_logger
    from src.core.exceptions import DataLoadError, ValidationError
    logger = get_logger(__name__)
except ImportError:
    # Fallback for standalone usage
    logger = logging.getLogger(__name__)


class DataType(Enum):
    """Enumeration of supported data types for validation."""
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    DATE = "date"
    BOOLEAN = "boolean"


@dataclass
class ColumnSchema:
    """Schema definition for a single column."""
    name: str
    data_type: DataType
    nullable: bool = True
    unique: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    foreign_key: Optional[Tuple[str, str]] = None  # (table, column)


@dataclass
class TableSchema:
    """Schema definition for a complete table."""
    name: str
    columns: List[ColumnSchema]
    primary_key: Optional[List[str]] = None
    required_columns: Optional[List[str]] = None


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    table_name: str
    errors: List[str]
    warnings: List[str]
    row_count: int
    column_count: int
    summary: Dict[str, Any]


class DataValidator(ABC):
    """Abstract base class for data validators."""
    
    @abstractmethod
    def validate_schema(self, df: pd.DataFrame, schema: TableSchema) -> ValidationResult:
        """Validate DataFrame against schema."""
        pass
    
    @abstractmethod
    def validate_referential_integrity(self, datasets: Dict[str, pd.DataFrame]) -> List[str]:
        """Validate foreign key relationships between datasets."""
        pass


class CSVDataValidator(DataValidator):
    """Production-grade CSV data validator with comprehensive checks."""
    
    def __init__(self):
        self.schemas = self._define_schemas()
    
    def _define_schemas(self) -> Dict[str, TableSchema]:
        """Define expected schemas for all data files."""
        return {
            "books": TableSchema(
                name="books",
                columns=[
                    ColumnSchema("book_id", DataType.INTEGER, nullable=False, unique=True, min_value=1),
                    ColumnSchema("goodreads_book_id", DataType.INTEGER, nullable=False, unique=True, min_value=1),
                    ColumnSchema("title", DataType.STRING, nullable=False, min_length=1, max_length=500),
                    ColumnSchema("authors", DataType.STRING, nullable=False, min_length=1, max_length=500),
                    ColumnSchema("average_rating", DataType.FLOAT, nullable=False, min_value=0.0, max_value=5.0),
                    ColumnSchema("isbn", DataType.STRING, nullable=True, min_length=10, max_length=13),
                    ColumnSchema("isbn13", DataType.STRING, nullable=True, min_length=13, max_length=13),
                    ColumnSchema("language_code", DataType.STRING, nullable=True, min_length=2, max_length=3),
                    ColumnSchema("num_pages", DataType.INTEGER, nullable=True, min_value=1, max_value=10000),
                    ColumnSchema("ratings_count", DataType.INTEGER, nullable=True, min_value=0),
                    ColumnSchema("text_reviews_count", DataType.INTEGER, nullable=True, min_value=0),
                    ColumnSchema("publication_date", DataType.INTEGER, nullable=True, min_value=1000, max_value=2030),
                    ColumnSchema("publisher", DataType.STRING, nullable=True, max_length=200),
                    ColumnSchema("genres", DataType.STRING, nullable=True, max_length=500),
                ],
                primary_key=["book_id"],
                required_columns=["book_id", "goodreads_book_id", "title", "authors", "average_rating"]
            ),
            
            "ratings": TableSchema(
                name="ratings",
                columns=[
                    ColumnSchema("user_id", DataType.INTEGER, nullable=False, min_value=1),
                    ColumnSchema("book_id", DataType.INTEGER, nullable=False, min_value=1),
                    ColumnSchema("rating", DataType.INTEGER, nullable=False, min_value=1, max_value=5),
                ],
                primary_key=["user_id", "book_id"],
                required_columns=["user_id", "book_id", "rating"]
            ),
            
            "tags": TableSchema(
                name="tags",
                columns=[
                    ColumnSchema("tag_id", DataType.INTEGER, nullable=False, unique=True, min_value=1),
                    ColumnSchema("tag_name", DataType.STRING, nullable=False, min_length=1, max_length=100),
                ],
                primary_key=["tag_id"],
                required_columns=["tag_id", "tag_name"]
            ),
            
            "book_tags": TableSchema(
                name="book_tags",
                columns=[
                    ColumnSchema("goodreads_book_id", DataType.INTEGER, nullable=False, min_value=1),
                    ColumnSchema("tag_id", DataType.INTEGER, nullable=False, min_value=1),
                    ColumnSchema("count", DataType.INTEGER, nullable=False, min_value=0),
                ],
                primary_key=["goodreads_book_id", "tag_id"],
                required_columns=["goodreads_book_id", "tag_id", "count"]
            )
        }
    
    def validate_column(self, df: pd.DataFrame, column: ColumnSchema) -> List[str]:
        """Validate a single column against its schema."""
        errors = []
        
        # Check if column exists
        if column.name not in df.columns:
            if not column.nullable:
                errors.append(f"Required column '{column.name}' is missing")
            return errors
        
        series = df[column.name]
        
        # Check for null values
        if not column.nullable and series.isnull().any():
            null_count = series.isnull().sum()
            errors.append(f"Column '{column.name}' has {null_count} null values but should not be nullable")
        
        # Skip validation for all-null columns
        if series.isnull().all():
            return errors
        
        # Data type validation
        try:
            if column.data_type == DataType.INTEGER:
                # Check if can be converted to integer
                non_null_series = series.dropna()
                if not non_null_series.empty:
                    pd.to_numeric(non_null_series, errors='raise', downcast='integer')
            elif column.data_type == DataType.FLOAT:
                non_null_series = series.dropna()
                if not non_null_series.empty:
                    pd.to_numeric(non_null_series, errors='raise')
            elif column.data_type == DataType.STRING:
                # Check if values are string-like
                non_null_series = series.dropna()
                if not non_null_series.empty and not all(isinstance(x, (str, int, float)) for x in non_null_series):
                    errors.append(f"Column '{column.name}' contains non-string values")
        except (ValueError, TypeError) as e:
            errors.append(f"Column '{column.name}' data type validation failed: {str(e)}")
        
        # Value range validation
        if column.data_type in [DataType.INTEGER, DataType.FLOAT]:
            numeric_series = pd.to_numeric(series, errors='coerce').dropna()
            if not numeric_series.empty:
                if column.min_value is not None and (numeric_series < column.min_value).any():
                    errors.append(f"Column '{column.name}' has values below minimum {column.min_value}")
                if column.max_value is not None and (numeric_series > column.max_value).any():
                    errors.append(f"Column '{column.name}' has values above maximum {column.max_value}")
        
        # String length validation
        if column.data_type == DataType.STRING:
            string_series = series.dropna().astype(str)
            if not string_series.empty:
                if column.min_length is not None and (string_series.str.len() < column.min_length).any():
                    errors.append(f"Column '{column.name}' has values shorter than minimum length {column.min_length}")
                if column.max_length is not None and (string_series.str.len() > column.max_length).any():
                    errors.append(f"Column '{column.name}' has values longer than maximum length {column.max_length}")
        
        # Uniqueness validation
        if column.unique and series.duplicated().any():
            dup_count = series.duplicated().sum()
            errors.append(f"Column '{column.name}' should be unique but has {dup_count} duplicates")
        
        # Allowed values validation
        if column.allowed_values is not None:
            invalid_values = series.dropna()[~series.dropna().isin(column.allowed_values)]
            if not invalid_values.empty:
                errors.append(f"Column '{column.name}' has invalid values: {invalid_values.unique().tolist()}")
        
        return errors
    
    def validate_schema(self, df: pd.DataFrame, schema: TableSchema) -> ValidationResult:
        """Validate DataFrame against table schema."""
        errors = []
        warnings = []
        
        logger.info(f"Validating schema for table: {schema.name}")
        
        # Check required columns
        if schema.required_columns:
            missing_required = set(schema.required_columns) - set(df.columns)
            if missing_required:
                errors.extend([f"Missing required column: {col}" for col in missing_required])
        
        # Check for extra columns
        expected_columns = {col.name for col in schema.columns}
        extra_columns = set(df.columns) - expected_columns
        if extra_columns:
            warnings.extend([f"Unexpected column found: {col}" for col in extra_columns])
        
        # Validate each column
        for column in schema.columns:
            column_errors = self.validate_column(df, column)
            errors.extend(column_errors)
        
        # Primary key validation
        if schema.primary_key:
            try:
                pk_df = df[schema.primary_key].dropna()
                if not pk_df.empty and pk_df.duplicated().any():
                    errors.append(f"Primary key {schema.primary_key} has duplicate values")
            except KeyError as e:
                errors.append(f"Primary key column missing: {str(e)}")
        
        # Generate summary statistics
        summary = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "null_counts": df.isnull().sum().to_dict(),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
        }
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            table_name=schema.name,
            errors=errors,
            warnings=warnings,
            row_count=len(df),
            column_count=len(df.columns),
            summary=summary
        )
    
    def validate_referential_integrity(self, datasets: Dict[str, pd.DataFrame]) -> List[str]:
        """Validate foreign key relationships between datasets."""
        errors = []
        
        # Check book_id references between ratings and books
        if "ratings" in datasets and "books" in datasets:
            ratings_book_ids = set(datasets["ratings"]["book_id"].dropna())
            books_book_ids = set(datasets["books"]["book_id"].dropna())
            
            missing_books = ratings_book_ids - books_book_ids
            if missing_books:
                errors.append(f"Ratings table references non-existent book_ids: {list(missing_books)[:10]}...")
        
        # Check goodreads_book_id references between book_tags and books
        if "book_tags" in datasets and "books" in datasets:
            book_tags_book_ids = set(datasets["book_tags"]["goodreads_book_id"].dropna())
            books_goodreads_ids = set(datasets["books"]["goodreads_book_id"].dropna())
            
            missing_books = book_tags_book_ids - books_goodreads_ids
            if missing_books:
                errors.append(f"Book_tags table references non-existent goodreads_book_ids: {list(missing_books)[:10]}...")
        
        # Check tag_id references between book_tags and tags
        if "book_tags" in datasets and "tags" in datasets:
            book_tags_tag_ids = set(datasets["book_tags"]["tag_id"].dropna())
            tags_tag_ids = set(datasets["tags"]["tag_id"].dropna())
            
            missing_tags = book_tags_tag_ids - tags_tag_ids
            if missing_tags:
                errors.append(f"Book_tags table references non-existent tag_ids: {list(missing_tags)[:10]}...")
        
        return errors
    
    def validate_all_datasets(self, data_dir: Path) -> Dict[str, ValidationResult]:
        """Validate all datasets in the data directory."""
        results = {}
        datasets = {}
        
        # Load all datasets
        for schema_name, schema in self.schemas.items():
            file_path = data_dir / f"{schema_name}.csv"
            
            if not file_path.exists():
                results[schema_name] = ValidationResult(
                    is_valid=False,
                    table_name=schema_name,
                    errors=[f"File {file_path} not found"],
                    warnings=[],
                    row_count=0,
                    column_count=0,
                    summary={}
                )
                continue
            
            try:
                df = pd.read_csv(file_path)
                datasets[schema_name] = df
                
                # Validate schema
                result = self.validate_schema(df, schema)
                results[schema_name] = result
                
                logger.info(f"Validated {schema_name}: {len(result.errors)} errors, {len(result.warnings)} warnings")
                
            except Exception as e:
                results[schema_name] = ValidationResult(
                    is_valid=False,
                    table_name=schema_name,
                    errors=[f"Failed to load file: {str(e)}"],
                    warnings=[],
                    row_count=0,
                    column_count=0,
                    summary={}
                )
        
        # Validate referential integrity
        if datasets:
            integrity_errors = self.validate_referential_integrity(datasets)
            if integrity_errors:
                # Add integrity errors to a summary result
                results["referential_integrity"] = ValidationResult(
                    is_valid=len(integrity_errors) == 0,
                    table_name="referential_integrity",
                    errors=integrity_errors,
                    warnings=[],
                    row_count=0,
                    column_count=0,
                    summary={}
                )
        
        return results
    
    def generate_validation_report(self, results: Dict[str, ValidationResult]) -> str:
        """Generate a comprehensive validation report."""
        report = ["=" * 80]
        report.append("DATA VALIDATION REPORT")
        report.append("=" * 80)
        
        total_errors = sum(len(result.errors) for result in results.values())
        total_warnings = sum(len(result.warnings) for result in results.values())
        
        report.append(f"Overall Status: {'PASSED' if total_errors == 0 else 'FAILED'}")
        report.append(f"Total Errors: {total_errors}")
        report.append(f"Total Warnings: {total_warnings}")
        report.append("")
        
        for table_name, result in results.items():
            report.append(f"Table: {table_name}")
            report.append("-" * 40)
            report.append(f"Status: {'VALID' if result.is_valid else 'INVALID'}")
            report.append(f"Rows: {result.row_count}")
            report.append(f"Columns: {result.column_count}")
            
            if result.errors:
                report.append("Errors:")
                for error in result.errors:
                    report.append(f"  - {error}")
            
            if result.warnings:
                report.append("Warnings:")
                for warning in result.warnings:
                    report.append(f"  - {warning}")
            
            if result.summary:
                report.append("Summary:")
                for key, value in result.summary.items():
                    if key != "null_counts":
                        report.append(f"  {key}: {value}")
            
            report.append("")
        
        return "\n".join(report)


def validate_data_directory(data_dir: str) -> Dict[str, ValidationResult]:
    """
    Main entry point for data validation.
    
    Args:
        data_dir: Path to directory containing CSV files
        
    Returns:
        Dictionary of validation results for each table
    """
    validator = CSVDataValidator()
    return validator.validate_all_datasets(Path(data_dir))


if __name__ == "__main__":
    # Example usage
    results = validate_data_directory("data")
    validator = CSVDataValidator()
    report = validator.generate_validation_report(results)
    print(report)
    validator.print_report(report)
    
    # Exit with error code if validation failed
    if not report['summary']['validation_passed']:
        sys.exit(1)

if __name__ == "__main__":
    main()