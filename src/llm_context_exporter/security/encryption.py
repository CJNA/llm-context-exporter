"""
File encryption utilities.

This module provides AES-256-GCM encryption for protecting context files at rest.
"""

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets


class FileEncryption:
    """
    Handles encryption and decryption of context files.
    
    Uses AES-256-GCM with PBKDF2 key derivation for secure file storage.
    """
    
    def __init__(self):
        """Initialize the encryption handler."""
        self.key_length = 32  # 256 bits
        self.salt_length = 16
        self.nonce_length = 12
        self.iterations = 100000  # PBKDF2 iterations
    
    def encrypt_file(self, file_path: str, password: str) -> str:
        """
        Encrypt a file with the given password.
        
        Args:
            file_path: Path to the file to encrypt
            password: Password for encryption
            
        Returns:
            Path to the encrypted file (.enc extension)
            
        Raises:
            FileNotFoundError: If the input file doesn't exist
            PermissionError: If unable to read input or write output file
            ValueError: If password is empty
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        encrypted_path = file_path + ".enc"
        
        try:
            # Read original file
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Generate salt and derive key
            salt = secrets.token_bytes(self.salt_length)
            key = self._derive_key(password, salt)
            
            # Encrypt data
            aesgcm = AESGCM(key)
            nonce = secrets.token_bytes(self.nonce_length)
            ciphertext = aesgcm.encrypt(nonce, data, None)
            
            # Create header with version and metadata
            header = b'LLMCTX01'  # 8-byte header: format identifier + version
            
            # Write encrypted file (header + salt + nonce + ciphertext)
            with open(encrypted_path, 'wb') as f:
                f.write(header + salt + nonce + ciphertext)
            
            return encrypted_path
            
        except PermissionError as e:
            raise PermissionError(f"Permission denied accessing files: {e}")
        except Exception as e:
            # Clean up partial file if it exists
            if os.path.exists(encrypted_path):
                try:
                    os.unlink(encrypted_path)
                except:
                    pass
            raise RuntimeError(f"Encryption failed: {e}")
    
    def decrypt_file(self, encrypted_file_path: str, password: str, output_path: str = None) -> str:
        """
        Decrypt a file with the given password.
        
        Args:
            encrypted_file_path: Path to the encrypted file
            password: Password for decryption
            output_path: Optional output path (defaults to removing .enc extension)
            
        Returns:
            Path to the decrypted file
            
        Raises:
            FileNotFoundError: If the encrypted file doesn't exist
            ValueError: If password is incorrect or file is corrupted
            PermissionError: If unable to read or write files
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        if not os.path.exists(encrypted_file_path):
            raise FileNotFoundError(f"Encrypted file not found: {encrypted_file_path}")
        
        if output_path is None:
            output_path = encrypted_file_path.replace('.enc', '')
        
        try:
            # Read encrypted file
            with open(encrypted_file_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Check minimum file size
            min_size = 8 + self.salt_length + self.nonce_length  # header + salt + nonce
            if len(encrypted_data) < min_size:
                raise ValueError("File too small to be a valid encrypted file")
            
            # Check header
            header = encrypted_data[:8]
            if header != b'LLMCTX01':
                raise ValueError("Invalid file format - not a valid encrypted context file")
            
            # Extract salt, nonce, and ciphertext
            data_start = 8  # After header
            salt = encrypted_data[data_start:data_start + self.salt_length]
            nonce = encrypted_data[data_start + self.salt_length:data_start + self.salt_length + self.nonce_length]
            ciphertext = encrypted_data[data_start + self.salt_length + self.nonce_length:]
            
            # Derive key and decrypt
            key = self._derive_key(password, salt)
            aesgcm = AESGCM(key)
            
            try:
                plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            except Exception as e:
                raise ValueError("Decryption failed - incorrect password or corrupted file") from e
            
            # Write decrypted file
            with open(output_path, 'wb') as f:
                f.write(plaintext)
            
            return output_path
            
        except PermissionError as e:
            raise PermissionError(f"Permission denied accessing files: {e}")
        except ValueError:
            raise  # Re-raise ValueError as-is
        except Exception as e:
            raise RuntimeError(f"Decryption failed: {e}")
    
    def encrypt_data(self, data: bytes, password: str) -> bytes:
        """
        Encrypt raw data with the given password.
        
        Args:
            data: Raw data to encrypt
            password: Password for encryption
            
        Returns:
            Encrypted data with header, salt, nonce, and ciphertext
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Generate salt and derive key
        salt = secrets.token_bytes(self.salt_length)
        key = self._derive_key(password, salt)
        
        # Encrypt data
        aesgcm = AESGCM(key)
        nonce = secrets.token_bytes(self.nonce_length)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        
        # Create header with version and metadata
        header = b'LLMCTX01'  # 8-byte header: format identifier + version
        
        return header + salt + nonce + ciphertext
    
    def decrypt_data(self, encrypted_data: bytes, password: str) -> bytes:
        """
        Decrypt raw encrypted data with the given password.
        
        Args:
            encrypted_data: Encrypted data with header
            password: Password for decryption
            
        Returns:
            Decrypted raw data
        """
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Check minimum size
        min_size = 8 + self.salt_length + self.nonce_length
        if len(encrypted_data) < min_size:
            raise ValueError("Data too small to be valid encrypted data")
        
        # Check header
        header = encrypted_data[:8]
        if header != b'LLMCTX01':
            raise ValueError("Invalid data format - not valid encrypted context data")
        
        # Extract components
        data_start = 8
        salt = encrypted_data[data_start:data_start + self.salt_length]
        nonce = encrypted_data[data_start + self.salt_length:data_start + self.salt_length + self.nonce_length]
        ciphertext = encrypted_data[data_start + self.salt_length + self.nonce_length:]
        
        # Derive key and decrypt
        key = self._derive_key(password, salt)
        aesgcm = AESGCM(key)
        
        try:
            return aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as e:
            raise ValueError("Decryption failed - incorrect password or corrupted data") from e
    
    def is_encrypted_file(self, file_path: str) -> bool:
        """
        Check if a file is encrypted with this system.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file appears to be encrypted
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
                return header == b'LLMCTX01'
        except:
            return False
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_length,
            salt=salt,
            iterations=self.iterations,
        )
        return kdf.derive(password.encode('utf-8'))