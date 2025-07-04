# DocuForge Production Configuration Guide

This guide provides detailed instructions and best practices for deploying DocuForge in production environments. It covers configuration, optimization, security, monitoring, and resource management.

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

For production deployments, install DocuForge with specific version pinning:

```bash
# Install core package
pip install docuforge==0.1.0

# Install with WeasyPrint support if needed
pip install docuforge[weasyprint]==0.1.0
```

### Docker Installation

DocuForge can also be deployed using Docker:

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

# Install DocuForge
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the application
CMD ["python", "your_app.py"]
```

Example requirements.txt:
```
docuforge==0.1.0
gunicorn==20.1.0
```

## Configuration

### Configuration Files

DocuForge supports configuration through JSON, YAML, or INI files. Create a `docuforge_config.json` file in your application root:

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
    "file": "/var/log/docuforge/docuforge.log",
    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  }
}
```

### Environment Variables

For containerized environments, use environment variables (which take precedence over config files):

```bash
# Page configuration
export DOCUFORGE_PAGE_WIDTH=595
export DOCUFORGE_PAGE_HEIGHT=842
export DOCUFORGE_PAGE_MARGIN=72

# Text configuration
export DOCUFORGE_TEXT_LINE_HEIGHT=14
export DOCUFORGE_TEXT_DEFAULT_FONT=Helvetica
export DOCUFORGE_TEXT_DEFAULT_SIZE=10

# Image limits
export DOCUFORGE_IMAGE_MAX_COUNT=10
export DOCUFORGE_IMAGE_MAX_SIZE_MB=5

# Engine configuration
export DOCUFORGE_ENGINE_DEFAULT=reportlab
export DOCUFORGE_ENGINE_TIMEOUT_SECONDS=60

# Cache settings
export DOCUFORGE_CACHE_ENABLED=true
export DOCUFORGE_CACHE_MAX_SIZE_MB=100
export DOCUFORGE_CACHE_TTL_SECONDS=3600

# Logging
export DOCUFORGE_LOG_LEVEL=INFO
export DOCUFORGE_LOG_FILE=/var/log/docuforge/docuforge.log
export DOCUFORGE_LOG_FORMAT="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
```

## Performance Optimization

### Font Preloading

Preload fonts to reduce PDF generation time:

```python
from docuforge.rendering.fonts import preload_fonts

# Preload common fonts at application startup
preload_fonts(['Helvetica', 'Times-Roman', 'Courier'])
```

### Template Caching

Cache templates for frequently used documents:

```python
from docuforge.templating.templates import DocumentTemplate, TemplateRegistry

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
from docuforge import generate_pdf

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

## Memory Management

### Resource Limits

Configure memory limits for PDF generation:

```python
import resource
from docuforge import generate_pdf

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
from docuforge.core.models import DocumentData, ImageData

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

Validate all input before passing to DocuForge:

```python
import json
import jsonschema
from docuforge import generate_pdf

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
from docuforge import generate_pdf

def sandboxed_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Save current directory
        original_dir = os.getcwd()
        
        try:
            # Change to a restricted directory
            os.chdir('/tmp/docuforge_sandbox')
            
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

Configure DocuForge's logging for structured output:

```python
import os
import json
import logging
from docuforge.utils.logging_config import init_logging

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
    log_file = os.environ.get('DOCUFORGE_LOG_FILE', '/var/log/docuforge/docuforge.log')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(JsonFormatter())
    
    init_logging(log_level=logging.INFO, handlers=[handler])
```

### Performance Metrics

Collect metrics for PDF generation:

```python
import time
import statsd
from docuforge import generate_pdf

# Initialize statsd client
statsd_client = statsd.StatsClient('localhost', 8125, prefix='docuforge')

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

Example of integrating DocuForge with Flask:

```python
from flask import Flask, request, send_file, jsonify
from io import BytesIO
from docuforge import generate_pdf

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
from docuforge import generate_pdf

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
        output_path = f"/var/docuforge/output/{doc_id}.pdf"
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
WARNING docuforge.rendering.fonts:fonts.py:246 Font not found or invalid path: DejaVuSans, None
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
   os.environ["DOCUFORGE_ENGINE_TIMEOUT_SECONDS"] = "120"
   ```
2. Split large documents into multiple smaller ones
3. Implement asynchronous generation with status updates

### Diagnostics

Enable debug logging for troubleshooting:

```python
import logging
from docuforge.utils.logging_config import init_logging

# Initialize with debug level
init_logging(log_level=logging.DEBUG)
```

Run diagnostics to check system compatibility:

```python
from docuforge.utils.diagnostics import run_diagnostics

# Check system compatibility
diagnostics_report = run_diagnostics()
print(diagnostics_report)
```

---

## Additional Resources

- [DocuForge API Documentation](https://docuforge.readthedocs.io/)
- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [WeasyPrint Documentation](https://weasyprint.readthedocs.io/)
- [PDF Performance Optimization Guide](https://example.com/pdf-optimization)
