#!/usr/bin/env python3
"""
Import/Export Capabilities for DMlogn8n Data Tables

This script provides comprehensive data import/export functionality
including backup, restore, migration, and data transformation capabilities.
"""

import json
import csv
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import os
import zipfile
import io
from pathlib import Path
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ExportMetadata:
    """Metadata for export files"""
    export_version: str = "1.0"
    export_timestamp: str = ""
    data_types: List[str] = None
    total_records: int = 0
    campaign_id: str = ""
    export_format: str = "json"
    compression: str = "none"
    checksum: str = ""

    def __post_init__(self):
        if self.export_timestamp == "":
            self.export_timestamp = datetime.now().isoformat()
        if self.data_types is None:
            self.data_types = []

class DataImportExportManager:
    """Comprehensive data import/export manager"""

    def __init__(self, export_dir: str = "/home/activeloguser/DMLogn8n/exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
        self.supported_formats = ["json", "csv", "xml", "yaml", "sqlite"]
        self.compression_formats = ["none", "zip", "gzip"]

    def export_campaign_data(self, campaign_id: str, data: Dict[str, Any],
                           format_type: str = "json", compression: str = "none",
                           include_metadata: bool = True) -> Dict[str, Any]:
        """Export campaign data in specified format"""
        try:
            if format_type not in self.supported_formats:
                raise ValueError(f"Unsupported format: {format_type}")

            if compression not in self.compression_formats:
                raise ValueError(f"Unsupported compression: {compression}")

            # Prepare export data
            export_data = {
                "campaign_id": campaign_id,
                "export_timestamp": datetime.now().isoformat(),
                "data": data
            }

            if include_metadata:
                metadata = ExportMetadata(
                    campaign_id=campaign_id,
                    data_types=list(data.keys()),
                    total_records=sum(len(records) if isinstance(records, list) else 1
                                    for records in data.values()),
                    export_format=format_type,
                    compression=compression
                )
                export_data["metadata"] = asdict(metadata)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"campaign_{campaign_id}_export_{timestamp}"

            # Export based on format
            if format_type == "json":
                file_content = self._export_to_json(export_data)
                filename = f"{base_filename}.json"
            elif format_type == "csv":
                file_content = self._export_to_csv(export_data)
                filename = f"{base_filename}.csv"
            elif format_type == "xml":
                file_content = self._export_to_xml(export_data)
                filename = f"{base_filename}.xml"
            elif format_type == "yaml":
                file_content = self._export_to_yaml(export_data)
                filename = f"{base_filename}.yaml"
            else:
                raise ValueError(f"Format {format_type} not yet implemented")

            # Apply compression if requested
            if compression == "zip":
                filename = self._compress_to_zip(file_content, base_filename, filename)
            elif compression == "gzip":
                filename = self._compress_to_gzip(file_content, filename)

            logger.info(f"Successfully exported campaign {campaign_id} to {filename}")
            return {
                "success": True,
                "filename": filename,
                "file_path": str(self.export_dir / filename),
                "format": format_type,
                "compression": compression,
                "size_bytes": len(file_content) if isinstance(file_content, bytes) else len(file_content.encode()),
                "record_count": metadata.total_records if include_metadata else "unknown"
            }

        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "campaign_id": campaign_id
            }

    def _export_to_json(self, data: Dict) -> str:
        """Export data to JSON format"""
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)

    def _export_to_csv(self, data: Dict) -> str:
        """Export data to CSV format (flattened structure)"""
        output = io.StringIO()

        # Export metadata first
        if "metadata" in data:
            writer = csv.writer(output)
            writer.writerow(["Metadata"])
            for key, value in data["metadata"].items():
                writer.writerow([key, value])
            writer.writerow([])  # Empty row separator

        # Export each data type
        writer = csv.writer(output)
        for data_type, records in data.get("data", {}).items():
            if not records:
                continue

            writer.writerow([f"Data Type: {data_type}"])

            if isinstance(records, list) and records:
                # Write headers
                headers = list(records[0].keys())
                writer.writerow(headers)

                # Write data rows
                for record in records:
                    row = []
                    for header in headers:
                        value = record.get(header, "")
                        # Convert complex objects to JSON string
                        if isinstance(value, (dict, list)):
                            value = json.dumps(value)
                        row.append(str(value))
                    writer.writerow(row)
            else:
                # Single record
                if isinstance(records, dict):
                    headers = list(records.keys())
                    writer.writerow(headers)
                    row = []
                    for header in headers:
                        value = records.get(header, "")
                        if isinstance(value, (dict, list)):
                            value = json.dumps(value)
                        row.append(str(value))
                    writer.writerow(row)

            writer.writerow([])  # Empty row separator

        return output.getvalue()

    def _export_to_xml(self, data: Dict) -> str:
        """Export data to XML format"""
        root = ET.Element("campaign_export")

        # Add metadata
        if "metadata" in data:
            metadata_elem = ET.SubElement(root, "metadata")
            for key, value in data["metadata"].items():
                elem = ET.SubElement(metadata_elem, key)
                elem.text = str(value)

        # Add data
        data_elem = ET.SubElement(root, "data")
        for data_type, records in data.get("data", {}).items():
            type_elem = ET.SubElement(data_elem, data_type)

            if isinstance(records, list):
                for i, record in enumerate(records):
                    record_elem = ET.SubElement(type_elem, "record", id=str(i))
                    self._dict_to_xml(record, record_elem)
            else:
                record_elem = ET.SubElement(type_elem, "record")
                self._dict_to_xml(records, record_elem)

        return ET.tostring(root, encoding='unicode', pretty_print=True)

    def _dict_to_xml(self, data: Dict, parent_elem):
        """Convert dictionary to XML elements"""
        for key, value in data.items():
            # Clean key name for XML
            clean_key = key.replace(" ", "_").replace("-", "_")

            if isinstance(value, dict):
                child_elem = ET.SubElement(parent_elem, clean_key)
                self._dict_to_xml(value, child_elem)
            elif isinstance(value, list):
                for item in value:
                    child_elem = ET.SubElement(parent_elem, clean_key)
                    if isinstance(item, dict):
                        self._dict_to_xml(item, child_elem)
                    else:
                        child_elem.text = str(item)
            else:
                child_elem = ET.SubElement(parent_elem, clean_key)
                child_elem.text = str(value)

    def _export_to_yaml(self, data: Dict) -> str:
        """Export data to YAML format"""
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)

    def _compress_to_zip(self, content: str, base_filename: str, original_filename: str) -> str:
        """Compress content to ZIP format"""
        zip_filename = f"{base_filename}.zip"
        zip_path = self.export_dir / zip_filename

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(original_filename, content)

        return zip_filename

    def _compress_to_gzip(self, content: str, filename: str) -> str:
        """Compress content to GZIP format"""
        import gzip

        gzip_filename = f"{filename}.gz"
        gzip_path = self.export_dir / gzip_filename

        with gzip.open(gzip_path, 'wt', encoding='utf-8') as gz_file:
            gz_file.write(content)

        return gzip_filename

    def import_campaign_data(self, file_path: str, format_type: str = None,
                           validate_data: bool = True) -> Dict[str, Any]:
        """Import campaign data from file"""
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Auto-detect format if not specified
            if format_type is None:
                format_type = self._detect_file_format(file_path)

            # Handle compressed files
            if file_path.suffix == '.zip':
                return self._import_from_zip(file_path, validate_data)
            elif file_path.suffix == '.gz':
                return self._import_from_gzip(file_path, format_type, validate_data)

            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse based on format
            if format_type == "json":
                data = json.loads(content)
            elif format_type == "csv":
                data = self._import_from_csv(content)
            elif format_type == "xml":
                data = self._import_from_xml(content)
            elif format_type == "yaml":
                data = yaml.safe_load(content)
            else:
                raise ValueError(f"Unsupported format: {format_type}")

            # Validate imported data
            if validate_data:
                validation_result = self._validate_imported_data(data)
                if not validation_result["valid"]:
                    return {
                        "success": False,
                        "error": "Data validation failed",
                        "validation_errors": validation_result["errors"],
                        "data": data
                    }

            logger.info(f"Successfully imported campaign data from {file_path}")
            return {
                "success": True,
                "data": data,
                "format": format_type,
                "file_path": str(file_path),
                "validation": validation_result if validate_data else None
            }

        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file_path": str(file_path)
            }

    def _detect_file_format(self, file_path: Path) -> str:
        """Auto-detect file format from extension"""
        suffix = file_path.suffix.lower()

        if suffix == '.json':
            return "json"
        elif suffix == '.csv':
            return "csv"
        elif suffix == '.xml':
            return "xml"
        elif suffix in ['.yaml', '.yml']:
            return "yaml"
        else:
            # Try to read first few lines to detect format
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()

                if first_line.startswith('{') or first_line.startswith('['):
                    return "json"
                elif first_line.startswith('<?xml'):
                    return "xml"
                elif ',' in first_line:
                    return "csv"
                else:
                    return "yaml"  # Default assumption
            except:
                return "json"  # Safest default

    def _import_from_csv(self, content: str) -> Dict[str, Any]:
        """Import data from CSV format"""
        reader = csv.DictReader(io.StringIO(content))
        data = {"data": {}}

        current_data_type = None
        records = []

        for row in reader:
            # Check if this is a data type marker
            if len(row) == 1 and list(row.values())[0].startswith("Data Type: "):
                # Save previous data type if exists
                if current_data_type and records:
                    data["data"][current_data_type] = records

                # Start new data type
                current_data_type = list(row.values())[0].replace("Data Type: ", "")
                records = []
                continue

            # Skip empty rows and metadata rows
            if not any(row.values()) or len(row) == 2:
                continue

            # Process data row
            processed_row = {}
            for key, value in row.items():
                if value:
                    # Try to parse as JSON for complex values
                    try:
                        processed_row[key] = json.loads(value)
                    except:
                        processed_row[key] = value

            records.append(processed_row)

        # Save last data type
        if current_data_type and records:
            data["data"][current_data_type] = records

        return data

    def _import_from_xml(self, content: str) -> Dict[str, Any]:
        """Import data from XML format"""
        root = ET.fromstring(content)
        data = {"data": {}}

        # Parse metadata
        metadata_elem = root.find("metadata")
        if metadata_elem is not None:
            data["metadata"] = self._xml_to_dict(metadata_elem)

        # Parse data
        data_elem = root.find("data")
        if data_elem is not None:
            for child in data_elem:
                records = []
                for record in child.findall("record"):
                    records.append(self._xml_to_dict(record))
                data["data"][child.tag] = records

        return data

    def _xml_to_dict(self, elem) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}

        for child in elem:
            if len(child) > 0:
                # Has children
                if child.tag in result:
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(self._xml_to_dict(child))
                else:
                    result[child.tag] = self._xml_to_dict(child)
            else:
                # Leaf node
                result[child.tag] = child.text or ""

        return result

    def _import_from_zip(self, file_path: Path, validate_data: bool) -> Dict[str, Any]:
        """Import data from ZIP file"""
        with zipfile.ZipFile(file_path, 'r') as zipf:
            # Find the first data file in the zip
            data_files = [f for f in zipf.namelist() if not f.startswith('__MACOSX/')]

            if not data_files:
                raise ValueError("No data files found in ZIP archive")

            # Import the first data file found
            with zipf.open(data_files[0]) as f:
                content = f.read().decode('utf-8')

            # Detect format and import
            format_type = self._detect_file_format(Path(data_files[0]))

            if format_type == "json":
                data = json.loads(content)
            elif format_type == "yaml":
                data = yaml.safe_load(content)
            elif format_type == "xml":
                data = self._import_from_xml(content)
            else:
                raise ValueError(f"Unsupported format in ZIP: {format_type}")

            if validate_data:
                validation_result = self._validate_imported_data(data)
                if not validation_result["valid"]:
                    return {
                        "success": False,
                        "error": "Data validation failed",
                        "validation_errors": validation_result["errors"],
                        "data": data
                    }

            return {
                "success": True,
                "data": data,
                "format": format_type,
                "source_files": data_files,
                "validation": validation_result
            }

    def _import_from_gzip(self, file_path: Path, format_type: str, validate_data: bool) -> Dict[str, Any]:
        """Import data from GZIP file"""
        import gzip

        with gzip.open(file_path, 'rt', encoding='utf-8') as gz_file:
            content = gz_file.read()

        # Parse based on format
        if format_type == "json":
            data = json.loads(content)
        elif format_type == "yaml":
            data = yaml.safe_load(content)
        else:
            raise ValueError(f"Unsupported GZIP format: {format_type}")

        if validate_data:
            validation_result = self._validate_imported_data(data)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Data validation failed",
                    "validation_errors": validation_result["errors"],
                    "data": data
                }

        return {
            "success": True,
            "data": data,
            "format": format_type,
            "validation": validation_result
        }

    def _validate_imported_data(self, data: Dict) -> Dict[str, Any]:
        """Validate imported data structure"""
        errors = []
        warnings = []

        # Check basic structure
        if "data" not in data:
            errors.append("Missing 'data' section in imported file")

        if "campaign_id" not in data and "campaignId" not in data.get("metadata", {}):
            warnings.append("No campaign ID found in imported data")

        # Validate data types
        if "data" in data:
            expected_types = ["characters", "scenes", "world", "relationships", "sync_history"]
            found_types = list(data["data"].keys())

            for data_type in found_types:
                if data_type not in expected_types:
                    warnings.append(f"Unexpected data type: {data_type}")

                records = data["data"][data_type]
                if isinstance(records, list) and len(records) > 0:
                    # Check first record structure
                    sample_record = records[0]
                    if not isinstance(sample_record, dict):
                        errors.append(f"Invalid record structure in {data_type}: expected dict, got {type(sample_record)}")
                elif isinstance(records, dict):
                    # Single record
                    if not isinstance(records, dict):
                        errors.append(f"Invalid record structure in {data_type}: expected dict, got {type(records)}")

        # Check metadata if present
        if "metadata" in data:
            metadata = data["metadata"]
            required_metadata = ["export_timestamp", "export_format"]
            for field in required_metadata:
                if field not in metadata:
                    warnings.append(f"Missing metadata field: {field}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "data_types": list(data.get("data", {}).keys()),
            "total_records": sum(
                len(records) if isinstance(records, list) else 1
                for records in data.get("data", {}).values()
            )
        }

    def create_backup(self, campaign_id: str, data: Dict[str, Any],
                     backup_type: str = "full") -> Dict[str, Any]:
        """Create backup of campaign data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            backup_data = {
                "backup_info": {
                    "campaign_id": campaign_id,
                    "backup_timestamp": datetime.now().isoformat(),
                    "backup_type": backup_type,
                    "backup_version": "1.0"
                },
                "data": data
            }

            # Create backup file
            backup_filename = f"backup_{campaign_id}_{backup_type}_{timestamp}.json"
            backup_path = self.export_dir / "backups"
            backup_path.mkdir(exist_ok=True)

            backup_file_path = backup_path / backup_filename

            with open(backup_file_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)

            # Create compressed backup as well
            compressed_backup = backup_path / f"{backup_filename}.zip"
            with zipfile.ZipFile(compressed_backup, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr(backup_filename, json.dumps(backup_data, indent=2, ensure_ascii=False, default=str))

            logger.info(f"Backup created: {backup_filename}")

            return {
                "success": True,
                "backup_file": str(backup_file_path),
                "compressed_backup": str(compressed_backup),
                "backup_type": backup_type,
                "timestamp": timestamp,
                "size_bytes": backup_file_path.stat().st_size
            }

        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "campaign_id": campaign_id
            }

    def restore_backup(self, backup_file_path: str) -> Dict[str, Any]:
        """Restore campaign data from backup"""
        try:
            backup_file_path = Path(backup_file_path)

            if not backup_file_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_file_path}")

            # Handle compressed backups
            if backup_file_path.suffix == '.zip':
                return self._restore_from_compressed_backup(backup_file_path)

            # Load backup file
            with open(backup_file_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            # Validate backup structure
            if "backup_info" not in backup_data or "data" not in backup_data:
                raise ValueError("Invalid backup file structure")

            backup_info = backup_data["backup_info"]

            logger.info(f"Restoring backup for campaign {backup_info['campaign_id']} from {backup_info['backup_timestamp']}")

            return {
                "success": True,
                "campaign_id": backup_info["campaign_id"],
                "backup_timestamp": backup_info["backup_timestamp"],
                "backup_type": backup_info.get("backup_type", "unknown"),
                "data": backup_data["data"],
                "restored_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Backup restoration failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "backup_file": str(backup_file_path)
            }

    def _restore_from_compressed_backup(self, backup_file_path: Path) -> Dict[str, Any]:
        """Restore from compressed backup file"""
        with zipfile.ZipFile(backup_file_path, 'r') as zipf:
            # Find the backup JSON file
            backup_files = [f for f in zipf.namelist() if f.endswith('.json')]

            if not backup_files:
                raise ValueError("No backup JSON file found in compressed backup")

            with zipf.open(backup_files[0]) as f:
                backup_data = json.load(f)

            if "backup_info" not in backup_data or "data" not in backup_data:
                raise ValueError("Invalid backup file structure")

            backup_info = backup_data["backup_info"]

            return {
                "success": True,
                "campaign_id": backup_info["campaign_id"],
                "backup_timestamp": backup_info["backup_timestamp"],
                "backup_type": backup_info.get("backup_type", "unknown"),
                "data": backup_data["data"],
                "restored_at": datetime.now().isoformat(),
                "source_files": backup_files
            }

    def list_exports(self, campaign_id: str = None) -> Dict[str, Any]:
        """List available export files"""
        try:
            exports = []

            for file_path in self.export_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix in ['.json', '.csv', '.xml', '.yaml', '.zip', '.gz']:
                    # Extract file info
                    stat = file_path.stat()

                    file_info = {
                        "filename": file_path.name,
                        "path": str(file_path),
                        "size_bytes": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "format": file_path.suffix[1:] if file_path.suffix else "unknown",
                        "compressed": file_path.suffix in ['.zip', '.gz']
                    }

                    # Try to extract campaign ID from filename
                    if "campaign_" in file_path.name:
                        parts = file_path.name.split("_")
                        if len(parts) >= 2:
                            file_info["campaign_id"] = parts[1]

                    exports.append(file_info)

            # Filter by campaign ID if specified
            if campaign_id:
                exports = [exp for exp in exports if exp.get("campaign_id") == campaign_id]

            # Sort by modification date (newest first)
            exports.sort(key=lambda x: x["modified"], reverse=True)

            return {
                "success": True,
                "exports": exports,
                "total_count": len(exports),
                "total_size_bytes": sum(exp["size_bytes"] for exp in exports)
            }

        except Exception as e:
            logger.error(f"Failed to list exports: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Example usage and testing functions
def test_import_export():
    """Test import/export functionality"""
    manager = DataImportExportManager()

    # Sample data
    campaign_data = {
        "characters": [
            {
                "characterId": "char_001",
                "name": "Test Character",
                "level": 5,
                "hpCurrent": 45,
                "hpMax": 50
            }
        ],
        "scenes": [
            {
                "sceneId": "scene_001",
                "name": "Test Scene",
                "lighting": "normal",
                "weather": "clear"
            }
        ]
    }

    # Test export
    export_result = manager.export_campaign_data("test_campaign", campaign_data, "json", "zip")
    print("Export result:", export_result)

    if export_result["success"]:
        # Test import
        import_result = manager.import_campaign_data(export_result["file_path"])
        print("Import result:", import_result)

        # Test backup
        backup_result = manager.create_backup("test_campaign", campaign_data)
        print("Backup result:", backup_result)

if __name__ == "__main__":
    test_import_export()