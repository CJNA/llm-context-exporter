"""
Secure file deletion utilities.

This module provides secure deletion of sensitive files to prevent recovery.
"""

import os
import secrets
from typing import Optional


class SecureFileDeleter:
    """
    Provides secure deletion of files to prevent data recovery.
    
    Uses multiple-pass overwriting before deletion to ensure
    sensitive data cannot be recovered from disk.
    """
    
    def __init__(self, passes: int = 3):
        """
        Initialize the secure deleter.
        
        Args:
            passes: Number of overwrite passes (default: 3)
        """
        self.passes = passes
    
    def secure_delete(self, file_path: str) -> bool:
        """
        Securely delete a file by overwriting it multiple times.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                return True  # File doesn't exist, consider it deleted
            
            file_size = os.path.getsize(file_path)
            
            # Overwrite the file multiple times
            with open(file_path, 'r+b') as f:
                for pass_num in range(self.passes):
                    # Seek to beginning
                    f.seek(0)
                    
                    # Overwrite with random data
                    if pass_num == 0:
                        # First pass: all zeros
                        f.write(b'\x00' * file_size)
                    elif pass_num == 1:
                        # Second pass: all ones
                        f.write(b'\xFF' * file_size)
                    else:
                        # Subsequent passes: random data
                        f.write(secrets.token_bytes(file_size))
                    
                    # Ensure data is written to disk
                    f.flush()
                    os.fsync(f.fileno())
            
            # Finally, delete the file
            os.unlink(file_path)
            return True
            
        except Exception as e:
            print(f"Warning: Secure deletion failed for {file_path}: {e}")
            # Fall back to regular deletion
            try:
                os.unlink(file_path)
                return True
            except:
                return False
    
    def secure_delete_directory(self, dir_path: str, recursive: bool = True) -> bool:
        """
        Securely delete all files in a directory.
        
        Args:
            dir_path: Path to the directory
            recursive: Whether to delete subdirectories recursively
            
        Returns:
            True if all deletions were successful
        """
        if not os.path.exists(dir_path):
            return True
        
        success = True
        
        try:
            for root, dirs, files in os.walk(dir_path, topdown=False):
                # Delete files
                for file in files:
                    file_path = os.path.join(root, file)
                    if not self.secure_delete(file_path):
                        success = False
                
                # Delete directories (only if recursive)
                if recursive:
                    for dir_name in dirs:
                        dir_full_path = os.path.join(root, dir_name)
                        try:
                            os.rmdir(dir_full_path)
                        except:
                            success = False
            
            # Delete the root directory
            try:
                os.rmdir(dir_path)
            except:
                success = False
                
        except Exception as e:
            print(f"Warning: Directory deletion failed for {dir_path}: {e}")
            success = False
        
        return success
    
    def wipe_free_space(self, directory: str, size_mb: Optional[int] = None):
        """
        Wipe free space in a directory to prevent recovery of deleted files.
        
        Args:
            directory: Directory to wipe free space in
            size_mb: Maximum size in MB to write (None for available space)
        """
        import shutil
        
        if not os.path.exists(directory):
            return
        
        try:
            # Get available space
            total, used, free = shutil.disk_usage(directory)
            
            # Determine how much to wipe
            if size_mb is None:
                # Use 90% of free space to avoid filling disk completely
                wipe_bytes = int(free * 0.9)
            else:
                wipe_bytes = min(size_mb * 1024 * 1024, int(free * 0.9))
            
            if wipe_bytes <= 0:
                return
            
            # Create temporary file for wiping
            wipe_file = os.path.join(directory, f".wipe_temp_{secrets.token_hex(8)}")
            
            try:
                with open(wipe_file, 'wb') as f:
                    # Write in chunks to avoid memory issues
                    chunk_size = 1024 * 1024  # 1MB chunks
                    written = 0
                    
                    while written < wipe_bytes:
                        remaining = min(chunk_size, wipe_bytes - written)
                        chunk = secrets.token_bytes(remaining)
                        f.write(chunk)
                        written += remaining
                        
                        # Flush to disk
                        f.flush()
                        os.fsync(f.fileno())
                
                # Securely delete the wipe file
                self.secure_delete(wipe_file)
                
            except Exception:
                # Clean up wipe file if it exists
                if os.path.exists(wipe_file):
                    try:
                        os.unlink(wipe_file)
                    except:
                        pass
                raise
                
        except Exception as e:
            print(f"Warning: Free space wiping failed for {directory}: {e}")
    
    def secure_delete_with_verification(self, file_path: str) -> bool:
        """
        Securely delete a file and verify it's gone.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if deletion was successful and verified
        """
        if not os.path.exists(file_path):
            return True
        
        # Get file info before deletion
        original_size = os.path.getsize(file_path)
        
        # Perform secure deletion
        success = self.secure_delete(file_path)
        
        if not success:
            return False
        
        # Verify file is gone
        if os.path.exists(file_path):
            return False
        
        # Try to wipe some free space where the file was
        try:
            directory = os.path.dirname(file_path)
            self.wipe_free_space(directory, max(1, original_size // (1024 * 1024)))
        except:
            pass  # Free space wiping is best-effort
        
        return True