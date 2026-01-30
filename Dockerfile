# Multi-stage build for optimized size
FROM python:3.11-slim as builder

WORKDIR /app

# Copy requirements and install build dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir build

# Copy source code and build the package
COPY . ./
RUN python -m build

# Runtime stage
FROM python:3.11-slim as runtime

WORKDIR /app

# Install only the built package and its runtime dependencies
COPY --from=builder /app/dist ./dist
RUN pip install --no-cache-dir nipoppy-mcp-*.whl

# # Set default environment variables
# ENV NIPOPPY_DATASET_ROOT=/data

# # Create volume for dataset mounting
# VOLUME ["/data"]

# Run the MCP server by default
CMD ["python", "-m", "nipoppy_mcp.server"]
