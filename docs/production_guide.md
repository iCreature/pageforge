# PageForge Production Configuration Guide

This guide provides detailed instructions and best practices for deploying PageForge in production environments. It covers configuration, optimization, security, monitoring, and resource management.

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Performance Optimization](#performance-optimization)
4. [Memory Management](#memory-management)
5. [Security Considerations](#security-considerations)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Deployment Scenarios](#deployment-scenarios)
8. [Troubleshooting](#troubleshooting)

## Installation

### Production Installation

For production deployments, install PageForge with specific version pinning:

```bash
# Install core package
pip install pageforge==0.1.0

# Install with WeasyPrint support if needed
pip install pageforge[weasyprint]==0.1.0
```

### Docker Installation

PageForge can also be deployed using Docker:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for PDF generation
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Install PageForge
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the application
CMD ["python", "your_app.py"]
```

Example requirements.txt:
```
pageforge==0.1.0
gunicorn==20.1.0
```

## Configuration

### Configuration Files

PageForge supports configuration through JSON, YAML, or INI files. Create a `pageforge_config.json` file in your application root:

```json
{
  "page": {
    "width": 595,
    "height": 842,
    "margin": 72
  },
  "text": {
    "line_height": 14,
    "default_font": "Helvetica",
    "default_size": 10,
    "header_size": 14
  },
  "image": {
    "default_width": 400,
    "default_height": 300,
    "max_count": 10,
    "max_size_mb": 5
  },
  "fonts": {
    "cid": {
      "japanese": "HeiseiMin-W3",
      "korean": "HYSMyeongJo-Medium",
      "chinese": "STSong-Light"
    },
    "paths": {
      "custom_font": "/path/to/custom/font.ttf"
    }
  },
  "engines": {
    "default": "reportlab",
    "timeout_seconds": 60
  },
  "cache": {
    "enabled": true,
    "max_size_mb": 100,
    "ttl_seconds": 3600
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/pageforge/pageforge.log",
    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  }
}
```

### Environment Variables

For containerized environments, use environment variables (which take precedence over config files):

```bash
# Page configuration
export PAGEFORGE_PAGE_WIDTH=595
export PAGEFORGE_PAGE_HEIGHT=842
export PAGEFORGE_PAGE_MARGIN=72

# Text configuration
export PAGEFORGE_TEXT_LINE_HEIGHT=14
export PAGEFORGE_TEXT_DEFAULT_FONT=Helvetica
export PAGEFORGE_TEXT_DEFAULT_SIZE=10

# Image limits
export PAGEFORGE_IMAGE_MAX_COUNT=10
export PAGEFORGE_IMAGE_MAX_SIZE_MB=5

# Engine configuration
export PAGEFORGE_ENGINE_DEFAULT=reportlab
export PAGEFORGE_ENGINE_TIMEOUT_SECONDS=60

# Cache settings
export PAGEFORGE_CACHE_ENABLED=true
export PAGEFORGE_CACHE_MAX_SIZE_MB=100
export PAGEFORGE_CACHE_TTL_SECONDS=3600

# Logging
export PAGEFORGE_LOG_LEVEL=INFO
export PAGEFORGE_LOG_FILE=/var/log/pageforge/pageforge.log
export PAGEFORGE_LOG_FORMAT="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
```

## Performance Optimization

### Font Preloading

Preload fonts to reduce PDF generation time:

```python
from pageforge.rendering.fonts import preload_fonts

# Preload common fonts at application startup
preload_fonts(['Helvetica', 'Times-Roman', 'Courier'])
```

### Template Caching

Cache templates for frequently used documents:

```python
from pageforge.templating.templates import DocumentTemplate, TemplateRegistry

# Register templates at application startup
invoice_template = DocumentTemplate.from_dict({
    "id": "invoice-template",
    "name": "Invoice Template",
    "title": "Invoice #{invoice_number}",
    "sections": [...]
})
TemplateRegistry.get_instance().register_template(invoice_template)

# Then in your request handler:
def generate_invoice(invoice_data):
    template = TemplateRegistry.get_instance().get_template("invoice-template")
    filled_document = template.fill(invoice_data)
    return generate_pdf(filled_document)
```

### Thread and Process Pools

For high-throughput applications, use thread or process pools:

```python
from concurrent.futures import ProcessPoolExecutor
from pageforge import generate_pdf

# Create a process pool for parallel PDF generation
with ProcessPoolExecutor(max_workers=4) as executor:
    future_pdfs = {
        executor.submit(generate_pdf, doc): doc_id
        for doc_id, doc in documents.items()
    }
    
    for future in as_completed(future_pdfs):
        doc_id = future_pdfs[future]
        try:
            pdf_data = future.result()
            save_pdf(doc_id, pdf_data)
        except Exception as e:
            logger.error(f"Error generating PDF {doc_id}: {e}")
```

## High-Volume Usage Optimizations

For environments processing thousands of documents per day, these advanced optimizations can significantly improve throughput and reliability.

### Content Pre-Rendering

Pre-render common elements to reduce generation time:

```python
from pageforge.core.cache import RenderCache
from pageforge.core.models import Section

# Initialize a render cache
render_cache = RenderCache(max_size=100)

# Pre-render common headers, footers, and logos
header_section = Section(type="header", text="Company Letterhead")
footer_section = Section(type="footer", text="Page {page} of {total}")

# Store pre-rendered elements (these would be stored as flowables or similar)
render_cache.set("standard_header", header_section.to_flowable())
render_cache.set("standard_footer", footer_section.to_flowable())

# Use in document generation
def optimized_generate_pdf(doc_data, cache=render_cache):
    # Replace sections with cached versions where possible
    for i, section in enumerate(doc_data.sections):
        if section.type == "header" and section.text == "Company Letterhead":
            doc_data.sections[i] = cache.get("standard_header")
    # Continue with generation
    return generate_pdf(doc_data)
```

### Batched Processing

Implement batched processing for more efficient resource usage:

```python
from pageforge import generate_pdf
from pageforge.utils.resource_monitor import ResourceMonitor
import time

def batch_processor(queue, batch_size=10, max_memory_pct=70):
    """Process documents in batches to optimize throughput while managing resources."""
    resource_monitor = ResourceMonitor()
    
    while True:
        # Check if system has enough resources
        if resource_monitor.memory_usage_percent() > max_memory_pct:
            time.sleep(5)  # Back off if memory usage is high
            continue
            
        # Grab a batch of documents
        batch = []
        while len(batch) < batch_size and not queue.empty():
            try:
                batch.append(queue.get_nowait())
            except queue.Empty:
                break
                
        if not batch:
            time.sleep(1)  # Nothing to process yet
            continue
            
        # Process the batch
        results = []
        for doc_id, doc_data in batch:
            try:
                pdf_data = generate_pdf(doc_data)
                results.append((doc_id, pdf_data, None))  # Success
            except Exception as e:
                results.append((doc_id, None, str(e)))  # Error
                
        # Save results (to database, filesystem, etc.)
        save_batch_results(results)
        
        # Give resources a moment to be released
        time.sleep(0.1)
```

### Fragment Compilation

Compile document fragments ahead of time for commonly used components:

```python
from pageforge.templating.fragments import DocumentFragment, FragmentRegistry
from pageforge.utils.cache import LRUCache

# Initialize fragment registry and compilation cache
fragment_registry = FragmentRegistry.get_instance()
compilation_cache = LRUCache(max_size=50)

# Pre-compile common fragments
def precompile_fragments():
    common_fragments = [
        "header-fragment", "footer-fragment", "terms-conditions", 
        "signature-block", "payment-details"
    ]
    
    for fragment_id in common_fragments:
        fragment = fragment_registry.get_fragment(fragment_id)
        if fragment:
            compiled = fragment.compile()
            compilation_cache.set(fragment_id, compiled)
            
# Use pre-compiled fragments in template filling
def optimized_fill_template(template, data):
    # Replace fragment lookups with cached versions
    for placeholder, value in template.placeholders.items():
        if value.startswith("fragment:"):
            fragment_id = value.split(":")[1]
            if fragment_id in compilation_cache:
                template.placeholders[placeholder] = compilation_cache.get(fragment_id)
    
    # Continue with normal fill
    return template.fill(data)
```

### Connection Pooling

Implement connection pooling for database and external service connections:

```python
import psycopg2
from psycopg2 import pool
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Database connection pool
db_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=5,
    maxconn=20,
    host="db.example.com",
    database="pageforge",
    user="user",
    password="password"
)

# HTTP connection pool with retry logic
def create_http_client():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=1
    )
    adapter = HTTPAdapter(pool_connections=10, pool_maxsize=100, max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Use the connection pools
http_client = create_http_client()

def get_document_data(doc_id):
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT data FROM documents WHERE id = %s", (doc_id,))
            return cur.fetchone()[0]
    finally:
        db_pool.putconn(conn)
        
def fetch_external_resource(resource_url):
    response = http_client.get(resource_url, timeout=5)
    return response.content
```

### Intelligent Load Shedding

Implement load shedding to maintain service quality under extreme load:

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import time

@dataclass
class LoadMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_processing_time_ms: float = 0
    start_time: datetime = datetime.now()
    
    @property
    def requests_per_second(self):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if elapsed < 1:
            return self.total_requests
        return self.total_requests / elapsed
    
    @property
    def success_rate(self):
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

class LoadShedder:
    def __init__(self, max_rps=100, min_success_rate=0.95, recovery_period_seconds=60):
        self.max_rps = max_rps
        self.min_success_rate = min_success_rate
        self.recovery_period = timedelta(seconds=recovery_period_seconds)
        self.metrics = LoadMetrics()
        self.shedding_until = None
        self._lock = threading.RLock()
        
    def should_process(self, priority=0):
        """Determine if a new request should be processed based on current load."""
        with self._lock:
            # Always process high priority requests (e.g., priority > 0)
            if priority > 0:
                return True
                
            # Check if we're in a shedding period
            if self.shedding_until and datetime.now() < self.shedding_until:
                return False
                
            # Check if we should enter shedding mode
            if (self.metrics.requests_per_second > self.max_rps or 
                    self.metrics.success_rate < self.min_success_rate):
                self.shedding_until = datetime.now() + self.recovery_period
                return False
                
            return True
            
    def record_result(self, success, processing_time_ms):
        """Record metrics about a processed request."""
        with self._lock:
            self.metrics.total_requests += 1
            
            if success:
                self.metrics.successful_requests += 1
            else:
                self.metrics.failed_requests += 1
                
            # Update moving average of processing time
            if self.metrics.total_requests == 1:
                self.metrics.avg_processing_time_ms = processing_time_ms
            else:
                self.metrics.avg_processing_time_ms = (
                    0.95 * self.metrics.avg_processing_time_ms + 
                    0.05 * processing_time_ms
                )
                
            # Reset metrics periodically
            if (datetime.now() - self.metrics.start_time).total_seconds() > 3600:  # 1 hour
                self.metrics = LoadMetrics()

# Use the load shedder
load_shedder = LoadShedder(max_rps=200)

def handle_document_request(doc_data, priority=0):
    if not load_shedder.should_process(priority):
        return {"status": "overloaded", "retry_after": 30}
        
    start_time = time.time()
    success = False
    
    try:
        pdf_data = generate_pdf(doc_data)
        success = True
        return {"status": "success", "data": pdf_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        load_shedder.record_result(success, processing_time)
```

### Resource-Aware Scheduling

Implement resource-aware scheduling for optimized throughput:

```python
import os
import psutil
from concurrent.futures import ThreadPoolExecutor
import threading

class ResourceAwareExecutor:
    """Executor that adapts worker count based on system resources."""
    
    def __init__(self, min_workers=2, max_workers=16, target_cpu_pct=70, check_interval=5):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.target_cpu_pct = target_cpu_pct
        self.check_interval = check_interval
        
        self.current_workers = min_workers
        self._executor = ThreadPoolExecutor(max_workers=self.current_workers)
        self._monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        self._monitor_thread.start()
        
    def _monitor_resources(self):
        """Periodically adjust worker count based on CPU usage."""
        while True:
            # Get current CPU usage (5-second average)
            cpu_pct = psutil.cpu_percent(interval=5)
            
            # Adjust worker count
            if cpu_pct > self.target_cpu_pct + 10 and self.current_workers > self.min_workers:
                # Too much CPU usage, reduce workers
                self.current_workers = max(self.current_workers - 1, self.min_workers)
                self._update_executor()
            elif cpu_pct < self.target_cpu_pct - 10 and self.current_workers < self.max_workers:
                # Low CPU usage, add workers
                self.current_workers = min(self.current_workers + 1, self.max_workers)
                self._update_executor()
                
            time.sleep(self.check_interval)
            
    def _update_executor(self):
        """Replace the executor with one that has the updated worker count."""
        old_executor = self._executor
        self._executor = ThreadPoolExecutor(max_workers=self.current_workers)
        old_executor.shutdown(wait=False)
        
    def submit(self, fn, *args, **kwargs):
        """Submit a task to the executor."""
        return self._executor.submit(fn, *args, **kwargs)
        
    def shutdown(self, wait=True):
        """Shut down the executor."""
        self._executor.shutdown(wait=wait)

# Use the resource-aware executor
executor = ResourceAwareExecutor(min_workers=2, max_workers=os.cpu_count() * 2)

def process_document_batch(documents):
    futures = []
    for doc in documents:
        futures.append(executor.submit(generate_pdf, doc))
    
    # Wait for all to complete
    results = []
    for future in futures:
        try:
            results.append(future.result())
        except Exception as e:
            results.append(None)
            print(f"Error: {e}")
    
    return results
```

## Memory Management

### Resource Limits

Configure memory limits for PDF generation:

```python
import resource
from pageforge import generate_pdf

def limited_generate_pdf(doc_data):
    # Limit process to 500MB of memory
    resource.setrlimit(resource.RLIMIT_AS, (500 * 1024 * 1024, -1))
    return generate_pdf(doc_data)
```

### Image Optimization

Optimize images before embedding in PDFs:

```python
from PIL import Image
from io import BytesIO
from pageforge.core.models import DocumentData, ImageData

def optimize_image(image_data, max_width=800, max_height=600, quality=85, format="JPEG"):
    # Load image data
    img = Image.open(BytesIO(image_data))
    
    # Resize if needed
    if img.width > max_width or img.height > max_height:
        img.thumbnail((max_width, max_height))
    
    # Convert to RGB if RGBA
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    # Save optimized image
    buffer = BytesIO()
    img.save(buffer, format=format, optimize=True, quality=quality)
    return buffer.getvalue()

# Use in document generation
image_data = optimize_image(original_image_data)
doc = DocumentData(
    title="Document with Optimized Images",
    sections=[...],
    images=[ImageData(name="logo", data=image_data, format="JPEG")]
)
```

## Security Considerations

### Input Validation

Validate all input before passing to PageForge:

```python
import json
import jsonschema
from pageforge import generate_pdf

# Define a schema for document validation
DOCUMENT_SCHEMA = {
    "type": "object",
    "required": ["title", "sections"],
    "properties": {
        "title": {"type": "string", "maxLength": 200},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["type"],
                "properties": {
                    "type": {"type": "string", "enum": ["paragraph", "table", "header", "footer", "list", "heading"]},
                    "text": {"type": "string", "maxLength": 10000},
                    "rows": {"type": "array"},
                    "items": {"type": "array"},
                    "level": {"type": "integer", "minimum": 1, "maximum": 6}
                }
            },
            "maxItems": 1000
        },
        "images": {
            "type": "array",
            "maxItems": 10
        }
    }
}

def validate_and_generate_pdf(input_json):
    try:
        # Parse and validate the JSON input
        doc_data = json.loads(input_json)
        jsonschema.validate(instance=doc_data, schema=DOCUMENT_SCHEMA)
        
        # Generate the PDF
        return generate_pdf(doc_data)
    except (json.JSONDecodeError, jsonschema.exceptions.ValidationError) as e:
        # Handle validation errors
        raise ValueError(f"Invalid document format: {e}")
```

### Restricting External Resources

Limit file system access during PDF generation:

```python
import os
from functools import wraps
from pageforge import generate_pdf

def sandboxed_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Save current directory
        original_dir = os.getcwd()
        
        try:
            # Change to a restricted directory
            os.chdir('/tmp/pageforge_sandbox')
            
            # Execute the function
            result = func(*args, **kwargs)
            
            return result
        finally:
            # Restore original directory
            os.chdir(original_dir)
    
    return wrapper

@sandboxed_execution
def safe_generate_pdf(doc_data):
    return generate_pdf(doc_data)
```

## Monitoring and Logging

### Structured Logging

Configure PageForge's logging for structured output:

```python
import os
import json
import logging
from pageforge.utils.logging_config import init_logging

# Configure structured JSON logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "process": record.process
        }
        
        if hasattr(record, 'trace_id'):
            log_record["trace_id"] = record.trace_id
            
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

# Initialize with custom formatter
def setup_production_logging():
    log_file = os.environ.get('PAGEFORGE_LOG_FILE', '/var/log/pageforge/pageforge.log')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(JsonFormatter())
    
    init_logging(log_level=logging.INFO, handlers=[handler])
```

### Performance Metrics

Collect metrics for PDF generation:

```python
import time
import statsd
from pageforge import generate_pdf

# Initialize statsd client
statsd_client = statsd.StatsClient('localhost', 8125, prefix='pageforge')

def generate_pdf_with_metrics(doc_data, doc_type="generic"):
    start_time = time.time()
    pdf_size = 0
    success = False
    
    try:
        # Generate PDF
        pdf_bytes = generate_pdf(doc_data)
        pdf_size = len(pdf_bytes)
        success = True
        return pdf_bytes
    finally:
        # Record metrics
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Send metrics to StatsD
        statsd_client.timing(f'generate_time.{doc_type}', execution_time)
        statsd_client.gauge(f'pdf_size.{doc_type}', pdf_size)
        statsd_client.incr(f'generation.{"success" if success else "failure"}.{doc_type}')
```

## Deployment Scenarios

### Web Service Integration

Example of integrating PageForge with Flask:

```python
from flask import Flask, request, send_file, jsonify
from io import BytesIO
from pageforge import generate_pdf

app = Flask(__name__)

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf_endpoint():
    try:
        # Parse request JSON
        doc_data = request.json
        if not doc_data:
            return jsonify({"error": "No document data provided"}), 400
            
        # Generate PDF
        pdf_bytes = generate_pdf(doc_data)
        
        # Return PDF as downloadable file
        buffer = BytesIO(pdf_bytes)
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{doc_data.get('title', 'document')}.pdf"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Queue-based Architecture

For high-volume environments, use a message queue:

```python
# worker.py
import pika
import json
import os
import time
from pageforge import generate_pdf

def callback(ch, method, properties, body):
    try:
        # Parse job data
        job = json.loads(body)
        doc_id = job['id']
        doc_data = job['data']
        
        print(f"Processing document {doc_id}")
        
        # Generate PDF
        pdf_bytes = generate_pdf(doc_data)
        
        # Save to storage (e.g., S3, file system, etc.)
        output_path = f"/var/pageforge/output/{doc_id}.pdf"
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
            
        print(f"Successfully generated PDF for {doc_id}")
        
        # Acknowledge message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing job: {e}")
        # Reject message and requeue
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        time.sleep(1)  # Prevent tight loop on persistent errors

def start_worker():
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq')
    )
    channel = connection.channel()
    
    # Declare queue
    channel.queue_declare(queue='pdf_generation', durable=True)
    
    # Set prefetch count
    channel.basic_qos(prefetch_count=1)
    
    # Start consuming
    channel.basic_consume(queue='pdf_generation', on_message_callback=callback)
    
    print("Worker started, waiting for messages...")
    channel.start_consuming()

if __name__ == '__main__':
    start_worker()
```

## Troubleshooting

### Common Issues

#### Font Loading Issues

If you see font-related warnings:

```
WARNING pageforge.rendering.fonts:fonts.py:246 Font not found or invalid path: DejaVuSans, None
```

Solution:
1. Install the missing fonts on your system
2. Configure explicit font paths in your config:

```json
{
  "fonts": {
    "paths": {
      "DejaVuSans": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
      "Arial": "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf"
    }
  }
}
```

#### Memory Issues

If you encounter `MemoryError` exceptions:

1. Use the `optimize_image` function shown above
2. Set stricter limits on input document size
3. Increase the memory allocated to your application container
4. Add swap space if necessary

#### PDF Generation Timeout

For large documents that take too long to generate:

1. Increase the engine timeout:
   ```python
   os.environ["PAGEFORGE_ENGINE_TIMEOUT_SECONDS"] = "120"
   ```
2. Split large documents into multiple smaller ones
3. Implement asynchronous generation with status updates

### Diagnostics

Enable debug logging for troubleshooting:

```python
import logging
from pageforge.utils.logging_config import init_logging

# Initialize with debug level
init_logging(log_level=logging.DEBUG)
```

Run diagnostics to check system compatibility:

```python
from pageforge.utils.diagnostics import run_diagnostics

# Check system compatibility
diagnostics_report = run_diagnostics()
print(diagnostics_report)
```

---

## Additional Resources

- [PageForge API Documentation](https://pageforge.readthedocs.io/)
- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [WeasyPrint Documentation](https://weasyprint.readthedocs.io/)
- [PDF Performance Optimization Guide](https://example.com/pdf-optimization)
