#!/usr/bin/env python3
"""
Advanced Compression Engine for API Performance
Intelligent request/response compression with multiple algorithms
"""

import asyncio
import time
import gzip
import lzma
import zlib
import bz2
import brotli
import zstandard as zstd
import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import io
import hashlib
from fastapi import Request, Response
from fastapi.middleware.gzip import GZipMiddleware
import orjson

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class CompressionAlgorithm(Enum):
    """Compression algorithms supported"""
    NONE = "none"
    GZIP = "gzip"
    DEFLATE = "deflate"
    BROTLI = "br"
    ZSTD = "zstd"
    LZMA = "lzma"
    BZIP2 = "bzip2"

class CompressionLevel(Enum):
    """Compression levels"""
    FASTEST = 1
    FAST = 3
    BALANCED = 6
    BEST = 9
    ULTRA = 12

@dataclass
class CompressionConfig:
    """Configuration for compression engine"""
    # Default settings
    default_algorithm: CompressionAlgorithm = CompressionAlgorithm.GZIP
    default_level: CompressionLevel = CompressionLevel.BALANCED

    # Thresholds
    compression_threshold: int = 1024  # 1KB minimum size
    max_compression_size: int = 100 * 1024 * 1024  # 100MB max

    # Performance settings
    enable_adaptive_compression: bool = True
    enable_streaming_compression: bool = True
    enable_parallel_compression: bool = True
    max_parallel_workers: int = 4

    # Content type settings
    compressible_types: List[str] = None
    excluded_types: List[str] = None

    # Adaptive settings
    adaptive_learning_rate: float = 0.1
    performance_threshold_ms: float = 10.0  # Max compression time

    def __post_init__(self):
        if self.compressible_types is None:
            self.compressible_types = [
                "application/json",
                "text/html",
                "text/css",
                "text/javascript",
                "application/javascript",
                "text/xml",
                "application/xml",
                "text/plain"
            ]

        if self.excluded_types is None:
            self.excluded_types = [
                "image/jpeg",
                "image/png",
                "image/gif",
                "video/mp4",
                "audio/mpeg",
                "application/zip",
                "application/gzip"
            ]

@dataclass
class CompressionResult:
    """Result of compression operation"""
    original_size: int
    compressed_size: int
    algorithm: CompressionAlgorithm
    level: CompressionLevel
    compression_time: float
    compression_ratio: float
    success: bool
    error: Optional[str] = None

@dataclass
class CompressionStats:
    """Compression statistics"""
    total_compressions: int = 0
    total_decompressions: int = 0
    bytes_saved: int = 0
    total_time_saved: float = 0.0
    algorithm_usage: Dict[str, int] = None
    average_compression_time: float = 0.0
    average_compression_ratio: float = 0.0

    def __post_init__(self):
        if self.algorithm_usage is None:
            self.algorithm_usage = {}

class CompressionBenchmark:
    """Benchmark compression algorithms for performance optimization"""

    def __init__(self):
        self.algorithm_performance: Dict[CompressionAlgorithm, Dict[str, float]] = {}

    async def benchmark_algorithms(self, data: bytes, sample_size: int = 1000) -> Dict[CompressionAlgorithm, Dict[str, float]]:
        """Benchmark all compression algorithms with sample data"""
        algorithms = [
            CompressionAlgorithm.GZIP,
            CompressionAlgorithm.DEFLATE,
            CompressionAlgorithm.BROTLI,
            CompressionAlgorithm.ZSTD,
            CompressionAlgorithm.LZMA,
            CompressionAlgorithm.BZIP2
        ]

        results = {}

        for algorithm in algorithms:
            try:
                # Test different compression levels
                level_results = []
                for level in [1, 3, 6, 9]:
                    start_time = time.perf_counter()
                    compressed = await self._compress_with_algorithm(data, algorithm, level)
                    compression_time = time.perf_counter() - start_time

                    if compressed:
                        compression_ratio = len(compressed) / len(data)
                        level_results.append({
                            'level': level,
                            'time': compression_time,
                            'ratio': compression_ratio,
                            'size': len(compressed)
                        })

                # Find optimal level
                if level_results:
                    optimal = min(level_results, key=lambda x: x['time'] * x['ratio'])
                    results[algorithm] = {
                        'optimal_level': optimal['level'],
                        'compression_time': optimal['time'],
                        'compression_ratio': optimal['ratio'],
                        'throughput_mbps': len(data) / (optimal['time'] * 1024 * 1024)
                    }

            except Exception as e:
                logger.error(f"Benchmark error for {algorithm}: {e}")

        self.algorithm_performance = results
        return results

    async def _compress_with_algorithm(self, data: bytes, algorithm: CompressionAlgorithm, level: int) -> Optional[bytes]:
        """Compress data with specific algorithm and level"""
        try:
            if algorithm == CompressionAlgorithm.GZIP:
                return gzip.compress(data, compresslevel=level)
            elif algorithm == CompressionAlgorithm.DEFLATE:
                return zlib.compress(data, level=level)
            elif algorithm == CompressionAlgorithm.BROTLI:
                return brotli.compress(data, quality=level)
            elif algorithm == CompressionAlgorithm.ZSTD:
                compressor = zstd.ZstdCompressor(level=level)
                return compressor.compress(data)
            elif algorithm == CompressionAlgorithm.LZMA:
                return lzma.compress(data, preset=min(level, 9))
            elif algorithm == CompressionAlgorithm.BZIP2:
                return bz2.compress(data, compresslevel=min(level, 9))
        except Exception as e:
            logger.error(f"Compression error: {e}")

        return None

class AdaptiveCompressor:
    """Adaptive compression that learns from performance patterns"""

    def __init__(self, config: CompressionConfig):
        self.config = config
        self.performance_history: Dict[str, List[CompressionResult]] = {}
        self.content_type_performance: Dict[str, CompressionAlgorithm] = {}
        self.benchmark = CompressionBenchmark()

    def should_compress(self, content_type: str, content_length: int) -> bool:
        """Determine if content should be compressed"""
        # Check size thresholds
        if content_length < self.config.compression_threshold:
            return False

        if content_length > self.config.max_compression_size:
            return False

        # Check content type
        if content_type in self.config.excluded_types:
            return False

        if content_type in self.config.compressible_types:
            return True

        # Check if it's a text type
        if content_type.startswith('text/'):
            return True

        return False

    def select_algorithm(self, content_type: str, content_length: int) -> Tuple[CompressionAlgorithm, CompressionLevel]:
        """Select optimal compression algorithm based on content type and size"""
        # Use learned performance if available
        if self.config.enable_adaptive_compression and content_type in self.content_type_performance:
            algorithm = self.content_type_performance[content_type]
            level = self._select_optimal_level(content_length)
            return algorithm, level

        # Use content type heuristics
        if content_type == "application/json":
            if content_length < 10 * 1024:  # < 10KB
                return CompressionAlgorithm.ZSTD, CompressionLevel.FAST
            else:
                return CompressionAlgorithm.BROTLI, CompressionLevel.BALANCED

        elif content_type.startswith('text/'):
            if content_length < 50 * 1024:  # < 50KB
                return CompressionAlgorithm.GZIP, CompressionLevel.FAST
            else:
                return CompressionAlgorithm.BROTLI, CompressionLevel.BALANCED

        else:
            return self.config.default_algorithm, self.config.default_level

    def _select_optimal_level(self, content_length: int) -> CompressionLevel:
        """Select optimal compression level based on content size"""
        if content_length < 1024:  # < 1KB
            return CompressionLevel.FASTEST
        elif content_length < 10 * 1024:  # < 10KB
            return CompressionLevel.FAST
        elif content_length < 100 * 1024:  # < 100KB
            return CompressionLevel.BALANCED
        else:
            return CompressionLevel.BEST

    def update_performance_history(self, content_type: str, result: CompressionResult):
        """Update performance history for learning"""
        if content_type not in self.performance_history:
            self.performance_history[content_type] = []

        self.performance_history[content_type].append(result)

        # Keep only last 100 results
        if len(self.performance_history[content_type]) > 100:
            self.performance_history[content_type] = self.performance_history[content_type][-100:]

        # Update optimal algorithm if adaptive learning is enabled
        if self.config.enable_adaptive_compression:
            self._update_optimal_algorithm(content_type)

    def _update_optimal_algorithm(self, content_type: str):
        """Update optimal algorithm based on performance history"""
        history = self.performance_history.get(content_type, [])
        if not history:
            return

        # Calculate average performance by algorithm
        algorithm_performance = {}
        for result in history:
            if result.success:
                if result.algorithm not in algorithm_performance:
                    algorithm_performance[result.algorithm] = []
                algorithm_performance[result.algorithm].append(result)

        # Find best performing algorithm
        best_algorithm = None
        best_score = float('inf')

        for algorithm, results in algorithm_performance.items():
            if not results:
                continue

            avg_time = sum(r.compression_time for r in results) / len(results)
            avg_ratio = sum(r.compression_ratio for r in results) / len(results)
            score = avg_time * avg_ratio  # Lower is better

            if score < best_score:
                best_score = score
                best_algorithm = algorithm

        if best_algorithm:
            self.content_type_performance[content_type] = best_algorithm

class StreamingCompressor:
    """Streaming compression for large data"""

    def __init__(self, algorithm: CompressionAlgorithm, level: CompressionLevel):
        self.algorithm = algorithm
        self.level = level
        self.compressor = None

    def initialize_compressor(self):
        """Initialize streaming compressor"""
        if self.algorithm == CompressionAlgorithm.GZIP:
            self.compressor = gzip.compress(self.level.value)
        elif self.algorithm == CompressionAlgorithm.ZSTD:
            self.compressor = zstd.ZstdCompressor(level=self.level.value).compressobj()
        elif self.algorithm == CompressionAlgorithm.BROTLI:
            self.compressor = brotli.Compressor(quality=self.level.value)

    async def compress_chunk(self, chunk: bytes) -> bytes:
        """Compress a chunk of data"""
        if not self.compressor:
            self.initialize_compressor()

        if self.algorithm == CompressionAlgorithm.ZSTD:
            return self.compressor.compress(chunk)
        elif self.algorithm == CompressionAlgorithm.BROTLI:
            return self.compressor.process(chunk)
        else:
            # For algorithms that don't support streaming well
            return await self._compress_chunk_fallback(chunk)

    async def finish_compression(self) -> bytes:
        """Finish compression and return any remaining data"""
        if self.algorithm == CompressionAlgorithm.ZSTD:
            return self.compressor.flush()
        elif self.algorithm == CompressionAlgorithm.BROTLI:
            return self.compressor.finish()
        else:
            return b""

    async def _compress_chunk_fallback(self, chunk: bytes) -> bytes:
        """Fallback for non-streaming algorithms"""
        if self.algorithm == CompressionAlgorithm.GZIP:
            return gzip.compress(chunk, compresslevel=self.level.value)
        elif self.algorithm == CompressionAlgorithm.LZMA:
            return lzma.compress(chunk, preset=self.level.value)
        else:
            return chunk

class ParallelCompressor:
    """Parallel compression for large payloads"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = None

    async def compress_parallel(self, data: bytes, algorithm: CompressionAlgorithm,
                              level: CompressionLevel, chunk_size: int = 1024 * 1024) -> bytes:
        """Compress data in parallel chunks"""
        if len(data) <= chunk_size:
            # Use regular compression for small data
            return await self._compress_single(data, algorithm, level)

        # Split data into chunks
        chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]

        # Compress chunks in parallel
        tasks = []
        for chunk in chunks:
            task = asyncio.create_task(self._compress_single(chunk, algorithm, level))
            tasks.append(task)

        compressed_chunks = await asyncio.gather(*tasks)

        # Concatenate compressed chunks
        return b"".join(compressed_chunks)

    async def _compress_single(self, data: bytes, algorithm: CompressionAlgorithm,
                             level: CompressionLevel) -> bytes:
        """Compress single chunk"""
        start_time = time.perf_counter()

        try:
            if algorithm == CompressionAlgorithm.GZIP:
                result = gzip.compress(data, compresslevel=level.value)
            elif algorithm == CompressionAlgorithm.BROTLI:
                result = brotli.compress(data, quality=level.value)
            elif algorithm == CompressionAlgorithm.ZSTD:
                compressor = zstd.ZstdCompressor(level=level.value)
                result = compressor.compress(data)
            elif algorithm == CompressionAlgorithm.LZMA:
                result = lzma.compress(data, preset=level.value)
            elif algorithm == CompressionAlgorithm.DEFLATE:
                result = zlib.compress(data, level=level.value)
            elif algorithm == CompressionAlgorithm.BZIP2:
                result = bz2.compress(data, compresslevel=min(level.value, 9))
            else:
                result = data

            compression_time = time.perf_counter() - start_time

            return result

        except Exception as e:
            logger.error(f"Parallel compression error: {e}")
            return data

class CompressionEngine:
    """Advanced compression engine for API performance"""

    def __init__(self, config: CompressionConfig = None):
        self.config = config or CompressionConfig()
        self.adaptive_compressor = AdaptiveCompressor(self.config)
        self.streaming_compressor = None
        self.parallel_compressor = ParallelCompressor(self.config.max_parallel_workers)
        self.stats = CompressionStats()

        # Content negotiation cache
        self.accept_encoding_cache: Dict[str, List[CompressionAlgorithm]] = {}

    def parse_accept_encoding(self, accept_encoding: str) -> List[CompressionAlgorithm]:
        """Parse Accept-Encoding header"""
        if not accept_encoding:
            return [CompressionAlgorithm.NONE]

        # Check cache first
        if accept_encoding in self.accept_encoding_cache:
            return self.accept_encoding_cache[accept_encoding]

        # Parse Accept-Encoding header
        algorithms = []
        for encoding in accept_encoding.split(','):
            encoding = encoding.strip().split(';')[0].lower()

            if encoding == 'gzip':
                algorithms.append(CompressionAlgorithm.GZIP)
            elif encoding == 'deflate':
                algorithms.append(CompressionAlgorithm.DEFLATE)
            elif encoding == 'br':
                algorithms.append(CompressionAlgorithm.BROTLI)
            elif encoding == 'zstd':
                algorithms.append(CompressionAlgorithm.ZSTD)
            elif encoding == 'lzma':
                algorithms.append(CompressionAlgorithm.LZMA)
            elif encoding == 'bzip2':
                algorithms.append(CompressionAlgorithm.BZIP2)
            elif encoding != 'identity' and encoding != '*':
                algorithms.append(CompressionAlgorithm.NONE)

        # Cache result
        self.accept_encoding_cache[accept_encoding] = algorithms
        return algorithms

    async def compress_response(self, data: Union[bytes, str, dict], content_type: str,
                               accept_encoding: str = None) -> Tuple[bytes, str, CompressionResult]:
        """Compress response data"""
        start_time = time.perf_counter()

        # Convert data to bytes
        if isinstance(data, dict):
            original_bytes = orjson.dumps(data)
        elif isinstance(data, str):
            original_bytes = data.encode('utf-8')
        else:
            original_bytes = data

        original_size = len(original_bytes)

        # Check if compression is needed
        if not self.adaptive_compressor.should_compress(content_type, original_size):
            return original_bytes, "identity", CompressionResult(
                original_size=original_size,
                compressed_size=original_size,
                algorithm=CompressionAlgorithm.NONE,
                level=CompressionLevel.FASTEST,
                compression_time=0,
                compression_ratio=1.0,
                success=True
            )

        # Determine supported algorithms
        supported_algorithms = self.parse_accept_encoding(accept_encoding or "")
        if not supported_algorithms or CompressionAlgorithm.NONE in supported_algorithms:
            return original_bytes, "identity", CompressionResult(
                original_size=original_size,
                compressed_size=original_size,
                algorithm=CompressionAlgorithm.NONE,
                level=CompressionLevel.FASTEST,
                compression_time=0,
                compression_ratio=1.0,
                success=True
            )

        # Select optimal algorithm
        algorithm, level = self.adaptive_compressor.select_algorithm(content_type, original_size)

        # Find best supported algorithm
        best_algorithm = CompressionAlgorithm.NONE
        for supported in supported_algorithms:
            if supported == algorithm:
                best_algorithm = algorithm
                break
            elif supported != CompressionAlgorithm.NONE:
                best_algorithm = supported

        if best_algorithm == CompressionAlgorithm.NONE:
            return original_bytes, "identity", CompressionResult(
                original_size=original_size,
                compressed_size=original_size,
                algorithm=CompressionAlgorithm.NONE,
                level=CompressionLevel.FASTEST,
                compression_time=0,
                compression_ratio=1.0,
                success=True
            )

        # Compress data
        try:
            if self.config.enable_parallel_compression and original_size > 1024 * 1024:
                # Use parallel compression for large data
                compressed_bytes = await self.parallel_compressor.compress_parallel(
                    original_bytes, best_algorithm, level
                )
            else:
                # Use regular compression
                compressed_bytes = await self._compress_data(original_bytes, best_algorithm, level)

            compression_time = time.perf_counter() - start_time
            compressed_size = len(compressed_bytes)
            compression_ratio = compressed_size / original_size

            # Check if compression actually helped
            if compression_ratio >= 0.95:  # Less than 5% compression
                return original_bytes, "identity", CompressionResult(
                    original_size=original_size,
                    compressed_size=original_size,
                    algorithm=CompressionAlgorithm.NONE,
                    level=CompressionLevel.FASTEST,
                    compression_time=compression_time,
                    compression_ratio=1.0,
                    success=True
                )

            result = CompressionResult(
                original_size=original_size,
                compressed_size=compressed_size,
                algorithm=best_algorithm,
                level=level,
                compression_time=compression_time,
                compression_ratio=compression_ratio,
                success=True
            )

            # Update statistics
            self._update_stats(result)
            self.adaptive_compressor.update_performance_history(content_type, result)

            return compressed_bytes, best_algorithm.value, result

        except Exception as e:
            logger.error(f"Compression error: {e}")
            return original_bytes, "identity", CompressionResult(
                original_size=original_size,
                compressed_size=original_size,
                algorithm=CompressionAlgorithm.NONE,
                level=CompressionLevel.FASTEST,
                compression_time=time.perf_counter() - start_time,
                compression_ratio=1.0,
                success=False,
                error=str(e)
            )

    async def decompress_request(self, data: bytes, content_encoding: str) -> Tuple[bytes, bool]:
        """Decompress request data"""
        if not content_encoding or content_encoding == 'identity':
            return data, True

        try:
            if content_encoding == 'gzip':
                decompressed = gzip.decompress(data)
            elif content_encoding == 'deflate':
                decompressed = zlib.decompress(data)
            elif content_encoding == 'br':
                decompressed = brotli.decompress(data)
            elif content_encoding == 'zstd':
                decompressor = zstd.ZstdDecompressor()
                decompressed = decompressor.decompress(data)
            elif content_encoding == 'lzma':
                decompressed = lzma.decompress(data)
            elif content_encoding == 'bzip2':
                decompressed = bz2.decompress(data)
            else:
                return data, False

            self.stats.total_decompressions += 1
            return decompressed, True

        except Exception as e:
            logger.error(f"Decompression error: {e}")
            return data, False

    async def _compress_data(self, data: bytes, algorithm: CompressionAlgorithm,
                           level: CompressionLevel) -> bytes:
        """Compress data with specified algorithm"""
        if algorithm == CompressionAlgorithm.GZIP:
            return gzip.compress(data, compresslevel=level.value)
        elif algorithm == CompressionAlgorithm.BROTLI:
            return brotli.compress(data, quality=level.value)
        elif algorithm == CompressionAlgorithm.ZSTD:
            compressor = zstd.ZstdCompressor(level=level.value)
            return compressor.compress(data)
        elif algorithm == CompressionAlgorithm.LZMA:
            return lzma.compress(data, preset=level.value)
        elif algorithm == CompressionAlgorithm.DEFLATE:
            return zlib.compress(data, level=level.value)
        elif algorithm == CompressionAlgorithm.BZIP2:
            return bz2.compress(data, compresslevel=min(level.value, 9))
        else:
            return data

    def _update_stats(self, result: CompressionResult):
        """Update compression statistics"""
        self.stats.total_compressions += 1

        if result.success:
            self.stats.bytes_saved += result.original_size - result.compressed_size

            # Update algorithm usage
            algo_name = result.algorithm.value
            self.stats.algorithm_usage[algo_name] = self.stats.algorithm_usage.get(algo_name, 0) + 1

            # Update averages
            total_compressions = self.stats.total_compressions
            self.stats.average_compression_time = (
                (self.stats.average_compression_time * (total_compressions - 1) + result.compression_time)
                / total_compressions
            )
            self.stats.average_compression_ratio = (
                (self.stats.average_compression_ratio * (total_compressions - 1) + result.compression_ratio)
                / total_compressions
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        return asdict(self.stats)

    def reset_stats(self):
        """Reset compression statistics"""
        self.stats = CompressionStats()

# FastAPI middleware integration
class CompressionMiddleware:
    """FastAPI middleware for intelligent compression"""

    def __init__(self, app, engine: CompressionEngine):
        self.app = app
        self.engine = engine

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Store original send function
        original_send = send

        # Create response wrapper
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Compress response body
                headers = dict(message.get("headers", []))
                content_type = headers.get(b"content-type", b"").decode()
                accept_encoding = headers.get(b"accept-encoding", b"").decode()

                # This would need integration with actual response body handling
                pass

            await original_send(message)

        await self.app(scope, receive, send_wrapper)

# Utility function for easy integration
def create_compression_middleware(config: CompressionConfig = None):
    """Create compression middleware with default configuration"""
    engine = CompressionEngine(config)

    def middleware(app):
        return CompressionMiddleware(app, engine)

    return middleware, engine

if __name__ == "__main__":
    # Example usage
    async def main():
        config = CompressionConfig()
        engine = CompressionEngine(config)

        # Test compression
        test_data = {"message": "Hello, World!", "data": list(range(1000))}
        compressed, encoding, result = await engine.compress_response(
            test_data, "application/json", "gzip, deflate, br"
        )

        print(f"Original size: {result.original_size} bytes")
        print(f"Compressed size: {result.compressed_size} bytes")
        print(f"Compression ratio: {result.compression_ratio:.2%}")
        print(f"Algorithm: {result.algorithm.value}")
        print(f"Compression time: {result.compression_time:.4f}s")

        print("\nStats:", engine.get_stats())

    asyncio.run(main())