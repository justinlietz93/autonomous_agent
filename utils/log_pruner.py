#!/usr/bin/env python3
"""
Log pruning utility to maintain a maximum number of log files in a directory.
Identifies datetime patterns in filenames and removes oldest files.
"""

import os
from pathlib import Path
from datetime import datetime
import re
from typing import List, Optional, Tuple
import logging

class LogPruner:
    """Manages log file pruning based on datetime in filenames."""
    
    def __init__(self, datetime_pattern: str = r"\d{8}"):
        """
        Initialize the log pruner.
        
        Args:
            datetime_pattern: Regex pattern to match datetime in filenames.
                            Default matches format: YYYYMMDD
        """
        self.datetime_pattern = datetime_pattern
        self.logger = logging.getLogger(__name__)
    
    def extract_datetime(self, filename: str) -> Optional[Tuple[str, datetime]]:
        """
        Extract datetime from filename using the pattern.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            Tuple of (datetime_str, datetime_obj) if found, None if no match
        """
        match = re.search(self.datetime_pattern, filename)
        if not match:
            return None
            
        datetime_str = match.group(0)
        try:
            dt = datetime.strptime(datetime_str, "%Y%m%d")
            return (datetime_str, dt)
        except ValueError:
            return None
    
    def get_files_by_age(self, directory: Path) -> List[Tuple[Path, datetime]]:
        """
        Get list of files with valid datetime in name, sorted by age (oldest first).
        
        Args:
            directory: Path to directory containing log files
            
        Returns:
            List of (file_path, datetime) tuples, sorted by datetime
        """
        dated_files = []
        
        for file_path in directory.iterdir():
            if not file_path.is_file():
                continue
                
            datetime_info = self.extract_datetime(file_path.name)
            if datetime_info:
                dated_files.append((file_path, datetime_info[1]))
        
        return sorted(dated_files, key=lambda x: x[1])
    
    def prune_logs(self, directory: str | Path, max_files: int) -> List[Path]:
        """
        Prune oldest log files to maintain maximum number of files.
        
        Args:
            directory: Path to log directory
            max_files: Maximum number of files to keep
            
        Returns:
            List of paths that were deleted
        
        Raises:
            ValueError: If max_files is less than 1
            FileNotFoundError: If directory doesn't exist
        """
        if max_files < 1:
            raise ValueError("max_files must be at least 1")
        
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        # Get sorted list of files with dates
        dated_files = self.get_files_by_age(directory)
        
        # Calculate how many files to remove
        files_to_remove = len(dated_files) - max_files
        if files_to_remove <= 0:
            return []
        
        # Remove oldest files
        removed_files = []
        for file_path, _ in dated_files[:files_to_remove]:
            try:
                file_path.unlink()
                removed_files.append(file_path)
                self.logger.info(f"Removed old log file: {file_path}")
            except Exception as e:
                self.logger.error(f"Error removing {file_path}: {e}")
        
        return removed_files

def prune_logs(directory: str | Path, max_files: int) -> List[Path]:
    """
    Convenience function to prune logs without instantiating LogPruner.
    
    Args:
        directory: Path to log directory
        max_files: Maximum number of files to keep
        
    Returns:
        List of paths that were deleted
    """
    pruner = LogPruner()
    return pruner.prune_logs(directory, max_files)

# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Prune old log files from a directory')
    parser.add_argument('directory', help='Directory containing log files')
    parser.add_argument('--max-files', type=int, default=10,
                       help='Maximum number of files to keep (default: 10)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without actually deleting')
    
    args = parser.parse_args()
    
    try:
        pruner = LogPruner()
        if args.dry_run:
            files = pruner.get_files_by_age(Path(args.directory))
            to_delete = files[:-args.max_files] if len(files) > args.max_files else []
            print(f"\nWould delete {len(to_delete)} files:")
            for file_path, dt in to_delete:
                print(f"  {file_path} ({dt})")
        else:
            removed = pruner.prune_logs(args.directory, args.max_files)
            print(f"\nRemoved {len(removed)} files:")
            for file_path in removed:
                print(f"  {file_path}")
    except Exception as e:
        print(f"Error: {e}")
