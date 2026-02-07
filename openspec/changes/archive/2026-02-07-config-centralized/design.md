## Context

DeckDex MTG currently has configuration scattered across multiple files:
- `main.py`: CLI argument defaults (batch_size=20, workers=4, api_delay=0.1, max_retries=5)
- `ProcessorConfig`: Dataclass defaults (same values repeated)
- `CardFetcher.__init__`: Hardcoded defaults (max_retries=3, retry_delay=0.5, openai_model="gpt-3.5-turbo")
- `SpreadsheetClient`: Internal constants (BATCH_SIZE=500, max_retries=5, base_delay=2)

This fragmentation makes it difficult to:
1. Tune performance for processing thousands of cards
2. Maintain consistent defaults across modules
3. Test with different configurations
4. Deploy with environment-specific settings (dev vs production)

The system currently supports environment variables for secrets (GOOGLE_API_CREDENTIALS, OPENAI_API_KEY) and CLI flags for runtime overrides, but lacks a centralized configuration file and profile support.

## Goals / Non-Goals

**Goals:**
- Centralize all configuration in a single YAML file with clear structure
- Support multiple profiles (default, development, production) for different optimization strategies
- Implement three-level override hierarchy: YAML → ENV vars → CLI flags
- Maintain 100% backwards compatibility (existing CLI and env vars continue working)
- Provide type-safe configuration with validation
- Make it easy to add new configuration parameters

**Non-Goals:**
- Dynamic configuration reloading (no hot-reload, changes require restart)
- Configuration UI or web interface
- Database-backed configuration
- Complex configuration composition (keep it simple: base + profile)
- Distributed configuration (no etcd, Consul, etc.)

## Decisions

### Decision 1: YAML over alternatives

**Choice:** Use YAML for configuration files

**Alternatives considered:**
- `.env` files: Too flat, no structure, mixes secrets with config
- Python config classes: Requires code changes for adjustments, less accessible
- JSON: Less human-friendly, no comments support
- TOML: Less familiar to Python community, similar complexity

**Rationale:**
- YAML supports nested structure (natural fit for our subsystem configs)
- Human-friendly with comments and multi-line strings
- Industry standard (Kubernetes, Docker Compose, GitHub Actions)
- `pyyaml` is mature and lightweight dependency
- Easy to version control and diff

### Decision 2: Profile-based structure

**Choice:** Use profile inheritance with explicit sections (default, development, production)

**Alternatives considered:**
- Single flat config with environment detection
- Multiple separate YAML files (config.dev.yaml, config.prod.yaml)
- Environment variable prefix convention only

**Rationale:**
- Single file keeps all config in one place
- Profiles are explicit and easy to understand
- Deep merge allows development/production to only override what differs
- Users can easily compare profile differences
- Aligns with common patterns (Rails, Spring Boot)

**Profile strategy:**
```yaml
default:           # Base configuration (current production values)
  processing:
    batch_size: 20
    
development:       # Overrides for dev (only differences)
  processing:
    batch_size: 10  # Smaller for debugging
    
production:        # Overrides for prod (aggressive optimization)
  processing:
    batch_size: 50  # Larger for throughput
```

### Decision 3: Nested configuration structure

**Choice:** Organize config into subsystem sections (processing, api.scryfall, api.google_sheets, api.openai)

**Alternatives considered:**
- Flat key-value structure with prefixes (scryfall_max_retries)
- Module-based sections (card_fetcher, spreadsheet_client)

**Rationale:**
- Groups related parameters logically
- Makes it clear which subsystem each parameter affects
- Easier to add new subsystems without namespace collisions
- Maps naturally to nested dataclasses in code
- Aligns with the "api" grouping for external services

**Structure:**
```
processing.*        → ProcessingConfig (worker/batch settings)
api.scryfall.*      → ScryfallConfig (Scryfall API settings)
api.google_sheets.* → GoogleSheetsConfig (Sheets API settings)
api.openai.*        → OpenAIConfig (OpenAI API settings)
```

### Decision 4: Environment variable mapping

**Choice:** Use `DECKDEX_<SECTION>_<KEY>` convention for environment variables

**Examples:**
- `DECKDEX_PROCESSING_BATCH_SIZE=30`
- `DECKDEX_SCRYFALL_MAX_RETRIES=5`
- `DECKDEX_OPENAI_ENABLED=true`

**Alternatives considered:**
- No env var support (YAML + CLI only)
- Generic prefixes (APP_BATCH_SIZE)
- Nested separators (DECKDEX__API__SCRYFALL__RETRIES)

**Rationale:**
- Clear namespace prevents collisions
- Single underscore is simpler than double underscore
- Matches common convention (MYAPP_SECTION_KEY)
- Auto-type conversion (int, float, bool detection)
- Preserves existing env vars (GOOGLE_API_CREDENTIALS, OPENAI_API_KEY) for secrets

### Decision 5: Backwards compatibility via deprecated properties

**Choice:** Keep legacy properties on ProcessorConfig as `@property` getters

**Example:**
```python
@property
def batch_size(self) -> int:
    """Deprecated: use processing.batch_size"""
    return self.processing.batch_size
```

**Rationale:**
- Existing code continues working without changes
- Gives time for gradual migration
- Clear deprecation path for future removal
- No runtime penalty (property access is fast)

### Decision 6: Config loading pipeline

**Choice:** Implement config_loader.py with explicit load → merge → validate pipeline

**Pipeline:**
```
1. load_yaml_config(profile)
   ↓ (default + profile merge)
2. apply_env_overrides(config)
   ↓ (parse DECKDEX_* vars)
3. build_processor_config(config, cli_overrides)
   ↓ (create nested dataclasses)
4. Validation (via dataclass __post_init__)
   ↓
5. ProcessorConfig (ready to use)
```

**Rationale:**
- Separation of concerns (each step has one job)
- Easy to test each step independently
- Clear error messages (know which layer failed)
- Can introspect config at each stage

## Risks / Trade-offs

### Risk 1: YAML dependency
**Risk:** Adding pyyaml as a new dependency  
**Mitigation:** pyyaml is a standard library-quality package with no transitive dependencies, widely used and maintained

### Risk 2: Configuration drift
**Risk:** Config files could diverge across environments without validation  
**Mitigation:** 
- Provide config.example.yaml as canonical reference
- Add `--show-config` CLI flag to debug resolved configuration
- Schema validation in dataclass __post_init__ catches invalid values early

### Risk 3: Migration complexity
**Risk:** Refactoring CardFetcher and SpreadsheetClient could break existing code  
**Mitigation:**
- Maintain backwards compatibility via deprecated properties
- Add comprehensive tests for config loading
- Keep changes minimal (pass config objects, not individual params)
- Phased rollout: config loading first, then refactor callsites

### Risk 4: Override hierarchy confusion
**Risk:** Users might not understand which value is being used (YAML vs ENV vs CLI)  
**Mitigation:**
- Document priority clearly in README and config.example.yaml
- `--show-config` flag shows resolved values with source annotation
- Clear error messages when validation fails

### Trade-off 1: Simplicity vs Flexibility
**Choice:** Medium complexity - 3 profiles, simple merge, no composition  
**Trade-off:** Cannot mix profiles (e.g., "production + debug mode")  
**Justification:** 3 profiles cover 95% of use cases, composition adds significant complexity

### Trade-off 2: Type safety vs Dynamic config
**Choice:** Statically typed with dataclasses and validation  
**Trade-off:** Cannot add arbitrary keys at runtime  
**Justification:** Type safety prevents bugs, clear contract between config and code

### Trade-off 3: Single file vs Multiple files
**Choice:** Single config.yaml with all profiles  
**Trade-off:** File grows with more profiles  
**Justification:** Easy to compare profiles, simple mental model, version control friendly

## Migration Plan

### Phase 1: Add config infrastructure (no behavior change)
1. Add `pyyaml` to requirements.txt
2. Create `config.yaml` with default profile matching current hardcoded values
3. Create `config.example.yaml` as documented template
4. Implement `deckdex/config_loader.py` with load/merge/validate logic
5. Add nested config dataclasses to `deckdex/config.py`
6. Add `--profile`, `--config`, `--show-config` CLI flags to main.py
7. Wire config_loader into main.py (but keep using same values)

**Validation:** Run existing tests, verify `--show-config` displays correct values

### Phase 2: Refactor subsystems to use config
1. Refactor `CardFetcher.__init__` to accept `ScryfallConfig`
2. Refactor `SpreadsheetClient.__init__` to accept `GoogleSheetsConfig`
3. Update `MagicCardProcessor` to use nested configs (processing, scryfall, etc.)
4. Update callsites to pass config objects

**Validation:** Run integration tests, verify behavior unchanged

### Phase 3: Add development and production profiles
1. Add development profile to config.yaml (conservative settings)
2. Add production profile to config.yaml (aggressive settings)
3. Document profile usage in README
4. Add examples to CLI help text

**Validation:** Test with `--profile development` and `--profile production`

### Phase 4: Documentation and examples
1. Update README with configuration section
2. Document environment variable mapping
3. Add examples for common scenarios
4. Update openspec/specs/architecture.md with config system

**Rollback strategy:**
- Phase 1-2: Can revert commits without data loss (no user-facing changes)
- Phase 3-4: Can remove profiles, keep infrastructure
- Config files are optional (CLI defaults continue working)

## Open Questions

1. **Should we validate config.yaml syntax at startup?**
   - Pro: Fail fast with clear errors
   - Con: Adds startup overhead
   - **Decision needed:** Validate on load or lazy validate on use?

2. **Should --set support nested keys?**
   - Examples: `--set api.scryfall.max_retries=5` vs `--set scryfall_max_retries=5`
   - **Decision needed:** Full path or flat key?

3. **Should we support config file auto-discovery?**
   - Look in: `./config.yaml`, `~/.deckdex/config.yaml`, `/etc/deckdex/config.yaml`
   - **Decision needed:** Single location or search path?

4. **Should we add config schema validation (jsonschema)?**
   - Pro: Catch errors before Python code runs
   - Con: Another dependency, more complexity
   - **Decision needed:** Rely on dataclass validation or add schema layer?

5. **Should production profile be documented as "recommended for 1000+ cards"?**
   - Need to benchmark to validate performance claims
   - **Decision needed:** Run benchmarks or keep profiles as starting points?
