# Changelog

All notable changes to Fact Agent will be documented in this file.

## [0.12.0] - 2026-11-25 - Blender Scene Library Release

### Added
- **Blender Scene Library** (`blender_scenes.py`): Parameterized scene generation with 4 ready-to-use templates
- **Scene Templates**: Mystery Forest, Abstract Geometry, Product Showcase, Data Visualization
- **Scene Configuration** (`SceneConfig`): Resolution, frame range, render engine, camera, lighting
- **Render CLI Extensions** (`render_cli.py`): `generate-scene`, `list-scenes` commands
- **Scene Registry**: Extensible pattern for adding new scene types

### Changed
- **render_cli.py**: Added `generate-scene` and `list-scenes` commands
- **__init__.py**: Exports Blender scene classes and utilities
- **Version bump**: 0.12.0

### Technical Details
- Object-oriented scene generators with inheritance (`BlenderSceneGenerator` base class)
- Parameterized configs via `SceneConfig` dataclass
- Enum-based types: `SceneType`, `CameraType`, `RenderEngine`
- Auto-generates complete Blender Python scripts (bpy) with materials, lighting, camera, animation
- CLI generates scripts from templates with customizable parameters

## [0.11.0] - 2026-11-25 - Advanced Tools Release

### Added
- **Streaming Support** (`streaming.py`): Token-by-token response streaming via SSE
- **Streaming LLM Client** (`http_client.py`): `chat_completion_stream()` method with SSE parsing
- **Smart Tool + Streaming Pipeline** (`streaming.py`): Handles tool calls non-streaming, then streams final response
- **Agent Integration** (`agent.py`): `stream_response()` function streams tokens to console

### Changed
- **agent.py**: Uses `stream_response()` for real-time output
- **http_client.py**: Added `chat_completion_stream()` with SSE parsing
- **Version bump**: 0.10.0

### Technical Details
- SSE (Server-Sent Events) parsing for chunked responses
- Tool calls handled non-streaming first, then streams final answer
- Robust error handling for empty choices in stream chunks
- Generator-based token yielding for real-time console output

## [0.9.0] - 2026-11-25 - Memory Consolidation & Maintenance Release

### Added
- **Memory Consolidator** (`memory_consolidator.py`): LLM-based conversation summarization into structured facts
- **Memory Janitor** (`memory_consolidator.py`): TTL-based cleanup for conversations and long-term memories
- **Auto-consolidation**: Runs every 10 exchanges in agent loop, threshold-based triggering
- **Standard Categories**: 11 predefined categories (Project, Preference, Person, Fact, Task, Goal, Tool, Configuration, Issue, Decision, Summary)
- **Auto-categorization**: Keyword-based fact categorization
- **Consolidation CLI** (`fact-memory`): `consolidate`, `cleanup`, `categories` commands

### Changed
- **agent.py**: Integrated `MemoryConsolidator`, runs auto-consolidation every 10 exchanges
- **memory_cli.py**: Added consolidate, cleanup, categories commands
- **__init__.py**: Exports consolidation classes and utilities
- **Version bump**: 0.9.0

### Technical Details
- Consolidation prompt extracts summary, key_facts, decisions as structured JSON
- Marks processed messages with `consolidated` column in conversations table
- TTL policies: 90-day conversation retention, 365-day long-term, 100 max per category
- Per-category limit enforcement deletes oldest entries first

## [0.8.0] - 2026-11-25 - Packaging Release

### Added
- **Python Package Structure**: `fact_agent/` with proper `__init__.py` exports
- **Entry Points**: `fact-agent`, `fact-memory`, `fact-render` CLI commands
- **Editable Install**: `pip install -e .` works correctly
- **Selective Package Discovery**: Only `fact_agent` included in distribution
- **Clean Requirements**: Only `requests` + `python-dotenv` as core deps

### Changed
- **All imports**: Updated from local to package-relative (`fact_agent.module`)
- **Module Organization**: Core modules moved to `fact_agent/`, CLIs moved in
- **pyproject.toml**: Updated version to 0.8.0, fixed package discovery

### Technical Details
- Uses `tool.setuptools.packages.find` with explicit include
- No more pydantic/pydantic-settings (stdlib dataclasses only)
- All entry points point to `fact_agent.module:function`

## [0.7.0] - 2026-11-25 - Agent Tools Release

### Added
- **Tools Framework** (`tools.py`): Extensible tool system with OpenAI function calling format
- **Web Search Tool**: Bing HTML scraping with URL extraction, no API key required
- **Calculator Tool**: Safe math evaluation with functions (sqrt, sin, cos, log, etc.) and constants (pi, e)
- **File Operations Tool**: Read, write, list, delete, exists within workspace
- **ToolRegistry**: Central registry with function spec generation for LLM
- **LLM Tool Integration** (`http_client.py`): `chat_completion_with_tools()` handles tool calls automatically

### Changed
- **agent.py**: Uses tool-enabled completion, maintains tool registry
- **test_basic.py**: Added tool tests (calculator, file ops, registry)

### Technical Details
- Tool calling loop: LLM → tool calls → execute → results → LLM (max 5 calls)
- Bing HTML parsing with base64 URL decoding from tracking links
- Safe eval with restricted namespace for calculator
- Workspace-bounded file operations

## [0.6.0] - 2026-11-25 - Cloud Rendering Pipeline Release

### Added
- **Render Pipeline** (`render_pipeline.py`): Complete job submission, status polling, result download
- **Render CLI** (`render_cli.py`): Commands for submit, status, wait, download, render (full pipeline)
- **CloudRenderer Integration**: `submit_render_job`, `get_job_status`, `wait_for_job`, `download_result`, `render_scene`
- **RenderConfig** dataclass: Frame range, resolution, samples, engine, device, format, priority
- **JobStatus enum**: PENDING, QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED
- **Multipart file upload**: .blend file submission with config fields
- **Progress callbacks**: Real-time job monitoring
- **Auto-download**: Handles both single files and archives (ZIP, tar.gz)

### Changed
- **cloud_renderer.py**: Now wraps RenderPipeline, exposes all pipeline methods
- **render_cli.py**: Extended from 2 to 7 commands (account, estimate, submit, status, wait, download, render)

### Technical Details
- JANCTION API: `/v1/jobs` POST for submission, `/v1/jobs/{id}` GET for status
- Multipart/form-data for .blend upload with config parameters
- Polling with configurable interval/timeout
- Blender scene script → .blend generation via `blender --background --python`

## [0.5.0] - 2026-11-25 - Vector Memory Release

### Added
- **Vector Memory** (`vector_memory.py`): Local hash-based embeddings (256-dim) with cosine similarity search, no external ML dependencies
- **Vector Memory CLI integration**: Automatic embedding generation on fact extraction, vector search with keyword fallback
- **Config option**: `ENABLE_VECTOR_RETRIEVAL` (default: true)
- **Tests**: Vector embedding generation, similarity scoring, search accuracy

### Changed
- **memory_retriever.py**: New priority chain — Vector → Semantic → Keyword
- **memory_extractor.py**: Auto-generates vector embeddings for new facts
- **config.py**: Added `enable_vector_retrieval` setting

### Technical Details
- Local embeddings use MD5 hashing with multiple seeds for semantic distribution
- Embeddings stored as binary BLOBs in SQLite (`vector_memory.db`)
- Cosine similarity threshold: 0.25 (tuned for local embeddings)
- Graceful fallback: API embeddings → Local embeddings → Zero vector → Keyword

## [0.4.0] - 2026-11-25 - Foundation Release

### Added
- **Configuration Management** (`config.py`): Dataclass-based settings with `.env` support, environment variable overrides, path expansion
- **HTTP Client** (`http_client.py`): Retry logic with exponential backoff, structured error handling, LLM and Render clients
- **Logging** (`logging_setup.py`): Structured logging with console + rotating file handlers, configurable levels
- **Exceptions** (`exceptions.py`): Typed exception hierarchy (FactAgentError, ConfigurationError, MemoryError, LLMAPIError, RenderAPIError, AuthenticationError)
- **Memory CLI** (`memory_cli.py`): Commands for list, search, extract, stats, clear
- **Render CLI** (`render_cli.py`): Commands for account status, preview estimates
- **Tests** (`test_basic.py`): Unit tests for config, memory, retrieval, HTTP client
- **Documentation**: `README.md`, `CHANGELOG.md`, `.env.example`
- **Packaging**: `pyproject.toml`, `requirements.txt`

### Changed
- **agent.py**: Refactored to use new config, HTTP client, logging; added migration for `created_at` column
- **memory_extractor.py**: Rewritten with typed functions, validation, separate extract/store steps
- **memory_retriever.py**: Fixed JSON prompt escaping, improved error handling, better fallback logging
- **cloud_renderer.py**: Refactored to `CloudRenderer` class, uses new config/HTTP client

### Fixed
- SQLite migration for existing `memory.db` (adds `created_at` column)
- Semantic retrieval JSON parsing (escaped braces in prompt template)
- LLM response handling for malformed JSON

### Infrastructure
- All hardcoded values moved to `.env` / environment variables
- API keys no longer in source code (loaded from `.env` or key files)
- Modular imports - each component can be used independently
- Type hints throughout (compatible with mypy)

## [0.3.0] - Previous - Semantic Retrieval Added
- Added LLM-based semantic memory retrieval with keyword fallback
- Long-term memory extractor with deduplication

## [0.2.0] - Previous - Conversation Memory
- Added SQLite conversation memory (short-term)

## [0.1.0] - Initial
- Basic agent loop with LLM API