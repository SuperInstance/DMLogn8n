#!/usr/bin/env python3
"""
Format Transformer
Handles data format conversion between different serialization formats
"""

import asyncio
import json
import logging
import pickle
import gzip
import zipfile
import tarfile
from typing import Dict, List, Optional, Any, Union, BinaryIO, TextIO
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import io
import csv
import xml.etree.ElementTree as ET
from xml.dom import minidom
import yaml
import toml
from datetime import datetime, date
import uuid

logger = logging.getLogger("format_transformer")

class DataFormat(Enum):
    """Supported data formats"""
    JSON = "json"
    JSONL = "jsonl"
    CSV = "csv"
    XML = "xml"
    YAML = "yaml"
    TOML = "toml"
    PICKLE = "pickle"
    PARQUET = "parquet"
    AVRO = "avro"
    PROTOBUF = "protobuf"
    EXCEL = "excel"
    SQLITE = "sqlite"

class CompressionType(Enum):
    """Supported compression types"""
    NONE = "none"
    GZIP = "gzip"
    ZIP = "zip"
    TAR = "tar"
    BZIP2 = "bzip2"

@dataclass
class FormatTransformation:
    """Format transformation configuration"""
    source_format: DataFormat
    target_format: DataFormat
    compression: CompressionType = CompressionType.NONE
    encoding: str = "utf-8"
    batch_size: int = 1000
    options: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FormatValidator:
    """Format validation configuration"""
    format: DataFormat
    schema: Optional[Dict[str, Any]] = None
    required_fields: List[str] = field(default_factory=list)
    field_types: Dict[str, str] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)

class FormatTransformer:
    """Advanced data format transformation engine"""

    def __init__(self):
        self.format_handlers = self._initialize_format_handlers()
        self.compression_handlers = self._initialize_compression_handlers()
        self.schema_validators = self._initialize_schema_validators()

    def _initialize_format_handlers(self) -> Dict[DataFormat, callable]:
        """Initialize format-specific handlers"""
        return {
            DataFormat.JSON: self._handle_json,
            DataFormat.JSONL: self._handle_jsonl,
            DataFormat.CSV: self._handle_csv,
            DataFormat.XML: self._handle_xml,
            DataFormat.YAML: self._handle_yaml,
            DataFormat.TOML: self._handle_toml,
            DataFormat.PICKLE: self._handle_pickle,
            DataFormat.EXCEL: self._handle_excel,
        }

    def _initialize_compression_handlers(self) -> Dict[CompressionType, callable]:
        """Initialize compression handlers"""
        return {
            CompressionType.NONE: self._handle_no_compression,
            CompressionType.GZIP: self._handle_gzip,
            CompressionType.ZIP: self._handle_zip,
            CompressionType.TAR: self._handle_tar,
        }

    def _initialize_schema_validators(self) -> Dict[DataFormat, callable]:
        """Initialize schema validators for different formats"""
        return {
            DataFormat.JSON: self._validate_json_schema,
            DataFormat.CSV: self._validate_csv_schema,
            DataFormat.XML: self._validate_xml_schema,
            DataFormat.YAML: self._validate_yaml_schema,
        }

    async def transform_format(self, data: Union[str, bytes, List[Dict]],
                             transformation: FormatTransformation) -> Union[str, bytes]:
        """Transform data from source format to target format"""
        logger.info(f"Transforming from {transformation.source_format} to {transformation.target_format}")

        try:
            # Parse source format
            parsed_data = await self._parse_source_format(data, transformation)

            # Convert to target format
            target_data = await self._convert_to_target_format(parsed_data, transformation)

            # Apply compression if needed
            if transformation.compression != CompressionType.NONE:
                target_data = await self._apply_compression(target_data, transformation)

            return target_data

        except Exception as e:
            logger.error(f"Format transformation failed: {e}")
            raise

    async def transform_file(self, input_path: Path, output_path: Path,
                           transformation: FormatTransformation) -> bool:
        """Transform file from source format to target format"""
        logger.info(f"Transforming file {input_path} to {output_path}")

        try:
            # Read input file
            input_data = await self._read_file(input_path, transformation)

            # Transform format
            output_data = await self.transform_format(input_data, transformation)

            # Write output file
            await self._write_file(output_path, output_data, transformation)

            logger.info(f"File transformation completed: {output_path}")
            return True

        except Exception as e:
            logger.error(f"File transformation failed: {e}")
            return False

    async def transform_batch_files(self, input_files: List[Path], output_dir: Path,
                                  transformation: FormatTransformation) -> Dict[str, bool]:
        """Transform multiple files in batch"""
        results = {}

        for input_file in input_files:
            try:
                # Generate output filename
                output_filename = self._generate_output_filename(input_file, transformation)
                output_path = output_dir / output_filename

                # Transform file
                success = await self.transform_file(input_file, output_path, transformation)
                results[str(input_file)] = success

            except Exception as e:
                logger.error(f"Failed to transform {input_file}: {e}")
                results[str(input_file)] = False

        return results

    async def _parse_source_format(self, data: Union[str, bytes, List[Dict]],
                                 transformation: FormatTransformation) -> List[Dict]:
        """Parse data from source format"""
        source_format = transformation.source_format
        handler = self.format_handlers.get(source_format)

        if not handler:
            raise ValueError(f"Unsupported source format: {source_format}")

        return await handler("parse", data, transformation)

    async def _convert_to_target_format(self, parsed_data: List[Dict],
                                      transformation: FormatTransformation) -> Union[str, bytes]:
        """Convert parsed data to target format"""
        target_format = transformation.target_format
        handler = self.format_handlers.get(target_format)

        if not handler:
            raise ValueError(f"Unsupported target format: {target_format}")

        return await handler("serialize", parsed_data, transformation)

    async def _apply_compression(self, data: Union[str, bytes],
                              transformation: FormatTransformation) -> bytes:
        """Apply compression to data"""
        compression_type = transformation.compression
        handler = self.compression_handlers.get(compression_type)

        if not handler:
            raise ValueError(f"Unsupported compression type: {compression_type}")

        return await handler("compress", data, transformation)

    async def _read_file(self, file_path: Path, transformation: FormatTransformation) -> Union[str, bytes]:
        """Read file data with appropriate encoding"""
        read_mode = "rb" if transformation.source_format in [DataFormat.PICKLE, DataFormat.PARQUET] else "r"
        encoding = transformation.encoding if read_mode == "r" else None

        with open(file_path, read_mode, encoding=encoding) as f:
            data = f.read()

        # Handle compression if input file is compressed
        if file_path.suffix.lower() == '.gz':
            data = await self._handle_gzip("decompress", data, transformation)
        elif file_path.suffix.lower() in ['.zip']:
            data = await self._handle_zip("extract", data, transformation)

        return data

    async def _write_file(self, file_path: Path, data: Union[str, bytes],
                        transformation: FormatTransformation):
        """Write data to file with appropriate encoding"""
        # Create output directory if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        write_mode = "wb" if isinstance(data, bytes) else "w"
        encoding = transformation.encoding if write_mode == "w" else None

        with open(file_path, write_mode, encoding=encoding) as f:
            f.write(data)

    def _generate_output_filename(self, input_path: Path, transformation: FormatTransformation) -> str:
        """Generate output filename based on transformation"""
        stem = input_path.stem

        # Add compression suffix
        compression_suffix = self._get_compression_suffix(transformation.compression)

        # Change extension based on target format
        target_extension = self._get_format_extension(transformation.target_format)

        return f"{stem}{target_extension}{compression_suffix}"

    def _get_compression_suffix(self, compression_type: CompressionType) -> str:
        """Get file extension for compression type"""
        suffixes = {
            CompressionType.NONE: "",
            CompressionType.GZIP: ".gz",
            CompressionType.ZIP: ".zip",
            CompressionType.TAR: ".tar",
        }
        return suffixes.get(compression_type, "")

    def _get_format_extension(self, format_type: DataFormat) -> str:
        """Get file extension for format type"""
        extensions = {
            DataFormat.JSON: ".json",
            DataFormat.JSONL: ".jsonl",
            DataFormat.CSV: ".csv",
            DataFormat.XML: ".xml",
            DataFormat.YAML: ".yaml",
            DataFormat.TOML: ".toml",
            DataFormat.PICKLE: ".pkl",
            DataFormat.PARQUET: ".parquet",
            DataFormat.AVRO: ".avro",
            DataFormat.EXCEL: ".xlsx",
        }
        return extensions.get(format_type, ".txt")

    # Format handlers
    async def _handle_json(self, operation: str, data: Union[str, List[Dict]],
                         transformation: FormatTransformation) -> Union[List[Dict], str]:
        """Handle JSON format operations"""
        if operation == "parse":
            if isinstance(data, str):
                parsed = json.loads(data)
            else:
                parsed = data

            # Ensure we have a list of records
            if isinstance(parsed, dict):
                return [parsed]
            elif isinstance(parsed, list):
                return parsed
            else:
                raise ValueError("Invalid JSON structure")

        elif operation == "serialize":
            options = transformation.options
            indent = options.get("indent", 2)
            sort_keys = options.get("sort_keys", True)

            return json.dumps(data, indent=indent, sort_keys=sort_keys,
                           ensure_ascii=False, default=self._json_serializer)

    async def _handle_jsonl(self, operation: str, data: Union[str, List[Dict]],
                           transformation: FormatTransformation) -> Union[List[Dict], str]:
        """Handle JSONL format operations"""
        if operation == "parse":
            if isinstance(data, str):
                lines = data.strip().split('\n')
                parsed = [json.loads(line) for line in lines if line.strip()]
                return parsed
            else:
                return data

        elif operation == "serialize":
            lines = [json.dumps(record, default=self._json_serializer) for record in data]
            return '\n'.join(lines)

    async def _handle_csv(self, operation: str, data: Union[str, bytes, List[Dict]],
                        transformation: FormatTransformation) -> Union[List[Dict], str]:
        """Handle CSV format operations"""
        if operation == "parse":
            if isinstance(data, str):
                # Parse CSV string
                reader = csv.DictReader(io.StringIO(data))
                return list(reader)
            elif isinstance(data, bytes):
                # Parse CSV bytes
                reader = csv.DictReader(io.StringIO(data.decode(transformation.encoding)))
                return list(reader)
            else:
                # data is already parsed
                return data

        elif operation == "serialize":
            options = transformation.options
            delimiter = options.get("delimiter", ",")
            quotechar = options.get("quotechar", '"')
            fieldnames = options.get("fieldnames")

            if not fieldnames and data:
                # Extract fieldnames from first record
                fieldnames = list(data[0].keys())

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames,
                                  delimiter=delimiter, quotechar=quotechar)
            writer.writeheader()

            for record in data:
                writer.writerow(record)

            return output.getvalue()

    async def _handle_xml(self, operation: str, data: Union[str, List[Dict]],
                         transformation: FormatTransformation) -> Union[List[Dict], str]:
        """Handle XML format operations"""
        if operation == "parse":
            if isinstance(data, str):
                root = ET.fromstring(data)
                return self._xml_to_dict(root)
            else:
                return data

        elif operation == "serialize":
            options = transformation.options
            root_element = options.get("root_element", "data")
            record_element = options.get("record_element", "record")

            root = ET.Element(root_element)

            for record in data:
                record_elem = ET.SubElement(root, record_element)
                for key, value in record.items():
                    if value is not None:
                        child = ET.SubElement(record_elem, key)
                        child.text = str(value)

            # Pretty print XML
            rough_string = ET.tostring(root, encoding='unicode')
            reparsed = minidom.parseString(rough_string)
            return reparsed.toprettyxml(indent="  ")

    async def _handle_yaml(self, operation: str, data: Union[str, List[Dict]],
                          transformation: FormatTransformation) -> Union[List[Dict], str]:
        """Handle YAML format operations"""
        if operation == "parse":
            if isinstance(data, str):
                parsed = yaml.safe_load(data)
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, dict):
                    return [parsed]
                else:
                    raise ValueError("Invalid YAML structure")
            else:
                return data

        elif operation == "serialize":
            options = transformation.options
            default_flow_style = options.get("default_flow_style", False)
            sort_keys = options.get("sort_keys", False)

            return yaml.dump(data, default_flow_style=default_flow_style,
                           sort_keys=sort_keys, allow_unicode=True)

    async def _handle_toml(self, operation: str, data: Union[str, List[Dict]],
                          transformation: FormatTransformation) -> Union[List[Dict], str]:
        """Handle TOML format operations"""
        if operation == "parse":
            if isinstance(data, str):
                parsed = toml.loads(data)
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, dict):
                    return [parsed]
                else:
                    raise ValueError("Invalid TOML structure")
            else:
                return data

        elif operation == "serialize":
            # TOML typically represents a single document, so we'll use the first record
            if data:
                return toml.dumps(data[0])
            else:
                return ""

    async def _handle_pickle(self, operation: str, data: Union[bytes, List[Dict]],
                           transformation: FormatTransformation) -> Union[List[Dict], bytes]:
        """Handle Pickle format operations"""
        if operation == "parse":
            if isinstance(data, bytes):
                return pickle.loads(data)
            else:
                return data

        elif operation == "serialize":
            return pickle.dumps(data)

    async def _handle_excel(self, operation: str, data: Union[bytes, List[Dict]],
                           transformation: FormatTransformation) -> Union[List[Dict], bytes]:
        """Handle Excel format operations"""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for Excel format support")

        if operation == "parse":
            if isinstance(data, bytes):
                # Read Excel file from bytes
                df = pd.read_excel(io.BytesIO(data))
                return df.to_dict('records')
            else:
                return data

        elif operation == "serialize":
            options = transformation.options
            sheet_name = options.get("sheet_name", "Sheet1")
            index = options.get("index", False)

            df = pd.DataFrame(data)
            output = io.BytesIO()
            df.to_excel(output, sheet_name=sheet_name, index=index)
            return output.getvalue()

    # Compression handlers
    async def _handle_no_compression(self, operation: str, data: Union[str, bytes],
                                   transformation: FormatTransformation) -> bytes:
        """Handle no compression"""
        if isinstance(data, str):
            return data.encode(transformation.encoding)
        return data

    async def _handle_gzip(self, operation: str, data: Union[str, bytes],
                         transformation: FormatTransformation) -> bytes:
        """Handle gzip compression/decompression"""
        if operation == "compress":
            if isinstance(data, str):
                data = data.encode(transformation.encoding)
            return gzip.compress(data)

        elif operation == "decompress":
            decompressed = gzip.decompress(data)
            # Try to decode as string, return bytes if fails
            try:
                return decompressed.decode(transformation.encoding)
            except UnicodeDecodeError:
                return decompressed

    async def _handle_zip(self, operation: str, data: Union[str, bytes],
                        transformation: FormatTransformation) -> bytes:
        """Handle zip compression/decompression"""
        if operation == "compress":
            if isinstance(data, str):
                data = data.encode(transformation.encoding)

            # Create in-memory zip file
            output = io.BytesIO()
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr("data", data)
            return output.getvalue()

        elif operation == "extract":
            # Extract from zip file
            with zipfile.ZipFile(io.BytesIO(data)) as zip_file:
                # Find the first file in the archive
                file_list = zip_file.namelist()
                if file_list:
                    extracted = zip_file.read(file_list[0])
                    try:
                        return extracted.decode(transformation.encoding)
                    except UnicodeDecodeError:
                        return extracted
                else:
                    raise ValueError("Empty zip archive")

    async def _handle_tar(self, operation: str, data: Union[str, bytes],
                         transformation: FormatTransformation) -> bytes:
        """Handle tar compression/decompression"""
        if operation == "compress":
            if isinstance(data, str):
                data = data.encode(transformation.encoding)

            # Create in-memory tar file
            output = io.BytesIO()
            with tarfile.open(fileobj=output, mode='w:gz') as tar_file:
                # Create a tarinfo object
                tarinfo = tarfile.TarInfo(name="data")
                tarinfo.size = len(data)
                tar_file.addfile(tarinfo, io.BytesIO(data))
            return output.getvalue()

        elif operation == "extract":
            # Extract from tar file
            with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tar_file:
                members = tar_file.getmembers()
                if members:
                    extracted = tar_file.extractfile(members[0])
                    if extracted:
                        content = extracted.read()
                        try:
                            return content.decode(transformation.encoding)
                        except UnicodeDecodeError:
                            return content
                else:
                    raise ValueError("Empty tar archive")

    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}

        # Add attributes
        if element.attrib:
            result['@attributes'] = element.attrib

        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            else:
                result['#text'] = element.text.strip()

        # Add child elements
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data

        return result

    def _json_serializer(self, obj):
        """Custom JSON serializer for special types"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)

    async def validate_format(self, data: Union[str, bytes], validator: FormatValidator) -> bool:
        """Validate data against format and schema"""
        try:
            validation_handler = self.schema_validators.get(validator.format)
            if validation_handler:
                return await validation_handler(data, validator)
            else:
                logger.warning(f"No validator available for format: {validator.format}")
                return True
        except Exception as e:
            logger.error(f"Format validation failed: {e}")
            return False

    async def _validate_json_schema(self, data: Union[str, bytes], validator: FormatValidator) -> bool:
        """Validate JSON data against schema"""
        try:
            parsed = json.loads(data) if isinstance(data, str) else json.loads(data.decode())

            # Check required fields
            if isinstance(parsed, dict):
                for field in validator.required_fields:
                    if field not in parsed:
                        return False

            # Validate field types
            if isinstance(parsed, dict) and validator.field_types:
                for field, expected_type in validator.field_types.items():
                    if field in parsed:
                        actual_type = type(parsed[field]).__name__
                        if actual_type != expected_type:
                            return False

            return True

        except Exception as e:
            logger.error(f"JSON validation failed: {e}")
            return False

    async def _validate_csv_schema(self, data: Union[str, bytes], validator: FormatValidator) -> bool:
        """Validate CSV data against schema"""
        try:
            csv_data = data.decode() if isinstance(data, bytes) else data
            reader = csv.DictReader(io.StringIO(csv_data))

            # Check required fields
            if validator.required_fields:
                fieldnames = reader.fieldnames or []
                for field in validator.required_fields:
                    if field not in fieldnames:
                        return False

            # Validate data types (simplified)
            if validator.field_types:
                for row in reader:
                    for field, expected_type in validator.field_types.items():
                        if field in row and row[field]:
                            try:
                                if expected_type == "int":
                                    int(row[field])
                                elif expected_type == "float":
                                    float(row[field])
                            except ValueError:
                                return False

            return True

        except Exception as e:
            logger.error(f"CSV validation failed: {e}")
            return False

    async def _validate_xml_schema(self, data: Union[str, bytes], validator: FormatValidator) -> bool:
        """Validate XML data against schema"""
        try:
            xml_data = data.decode() if isinstance(data, bytes) else data
            root = ET.fromstring(xml_data)

            # Check required elements
            for field in validator.required_fields:
                if root.find(field) is None:
                    return False

            return True

        except Exception as e:
            logger.error(f"XML validation failed: {e}")
            return False

    async def _validate_yaml_schema(self, data: Union[str, bytes], validator: FormatValidator) -> bool:
        """Validate YAML data against schema"""
        try:
            yaml_data = data.decode() if isinstance(data, bytes) else data
            parsed = yaml.safe_load(yaml_data)

            # Check required fields
            if isinstance(parsed, dict):
                for field in validator.required_fields:
                    if field not in parsed:
                        return False

            # Validate field types
            if isinstance(parsed, dict) and validator.field_types:
                for field, expected_type in validator.field_types.items():
                    if field in parsed:
                        actual_type = type(parsed[field]).__name__
                        if actual_type != expected_type:
                            return False

            return True

        except Exception as e:
            logger.error(f"YAML validation failed: {e}")
            return False

    async def estimate_transformation_time(self, data_size_bytes: int,
                                         transformation: FormatTransformation) -> float:
        """Estimate transformation time in seconds"""
        # Base processing rates (bytes per second)
        processing_rates = {
            DataFormat.JSON: 1000000,      # 1MB/s
            DataFormat.JSONL: 1200000,     # 1.2MB/s
            DataFormat.CSV: 2000000,       # 2MB/s
            DataFormat.XML: 800000,        # 0.8MB/s
            DataFormat.YAML: 900000,       # 0.9MB/s
            DataFormat.PICKLE: 5000000,    # 5MB/s
            DataFormat.EXCEL: 500000,      # 0.5MB/s
        }

        source_rate = processing_rates.get(transformation.source_format, 1000000)
        target_rate = processing_rates.get(transformation.target_format, 1000000)

        # Compression overhead
        compression_overhead = {
            CompressionType.NONE: 1.0,
            CompressionType.GZIP: 1.3,
            CompressionType.ZIP: 1.5,
            CompressionType.TAR: 1.4,
        }

        overhead = compression_overhead.get(transformation.compression, 1.0)

        # Calculate estimated time
        parse_time = data_size_bytes / source_rate
        serialize_time = data_size_bytes / target_rate
        total_time = (parse_time + serialize_time) * overhead

        return total_time

    async def get_format_info(self, data: Union[str, bytes]) -> Dict[str, Any]:
        """Get information about data format"""
        info = {
            "size_bytes": len(data) if isinstance(data, (str, bytes)) else 0,
            "format": None,
            "encoding": None,
            "is_compressed": False,
            "compression_type": None
        }

        if isinstance(data, bytes):
            # Try to detect encoding
            try:
                decoded = data.decode('utf-8')
                info["encoding"] = "utf-8"
                data = decoded
            except UnicodeDecodeError:
                try:
                    decoded = data.decode('latin-1')
                    info["encoding"] = "latin-1"
                    data = decoded
                except UnicodeDecodeError:
                    info["encoding"] = "binary"
                    return info

        # Detect format
        if isinstance(data, str):
            stripped = data.strip()

            if stripped.startswith('{') and stripped.endswith('}'):
                info["format"] = DataFormat.JSON
            elif stripped.startswith('[') and stripped.endswith(']'):
                info["format"] = DataFormat.JSON if '\n' not in stripped[:100] else DataFormat.JSONL
            elif stripped.startswith('<') and stripped.endswith('>'):
                info["format"] = DataFormat.XML
            elif stripped.startswith('---') or '\n:' in stripped[:50]:
                info["format"] = DataFormat.YAML
            elif ',' in stripped[:100] and '\n' in stripped:
                info["format"] = DataFormat.CSV
            else:
                info["format"] = DataFormat.JSON  # Default assumption

        # Detect compression
        if isinstance(data, bytes) and len(data) > 2:
            if data[:2] == b'\x1f\x8b':
                info["is_compressed"] = True
                info["compression_type"] = CompressionType.GZIP
            elif data[:4] == b'PK\x03\x04':
                info["is_compressed"] = True
                info["compression_type"] = CompressionType.ZIP

        return info

# Example usage and testing
async def test_format_transformer():
    """Test format transformation"""
    transformer = FormatTransformer()

    # Sample data
    sample_data = [
        {"id": 1, "name": "John", "age": 30, "email": "john@example.com"},
        {"id": 2, "name": "Jane", "age": 25, "email": "jane@example.com"},
        {"id": 3, "name": "Bob", "age": 35, "email": "bob@example.com"}
    ]

    # Test transformations
    transformations = [
        FormatTransformation(
            source_format=DataFormat.JSON,
            target_format=DataFormat.CSV,
            compression=CompressionType.NONE
        ),
        FormatTransformation(
            source_format=DataFormat.CSV,
            target_format=DataFormat.JSONL,
            compression=CompressionType.GZIP
        ),
        FormatTransformation(
            source_format=DataFormat.JSON,
            target_format=DataFormat.XML,
            compression=CompressionType.NONE,
            options={
                "root_element": "users",
                "record_element": "user"
            }
        )
    ]

    try:
        for i, transformation in enumerate(transformations):
            print(f"\n--- Transformation {i+1}: {transformation.source_format} -> {transformation.target_format} ---")

            # Convert to source format first
            source_data = await transformer._convert_to_target_format(sample_data,
                FormatTransformation(DataFormat.JSON, transformation.source_format))

            # Transform
            result = await transformer.transform_format(source_data, transformation)

            # Print result (first 200 chars)
            result_preview = result[:200] if isinstance(result, str) else result[:200].decode('utf-8', errors='ignore')
            print(f"Result preview: {result_preview}...")

            # Get format info
            format_info = await transformer.get_format_info(result)
            print(f"Format info: {format_info}")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_format_transformer())