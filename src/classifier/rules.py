"""Rule-based pattern matching for failure classification."""


# Pattern format: (regex_pattern, reasoning)
# Patterns are case-insensitive

INPUT_DATA_PATTERNS: list[tuple[str, str]] = [
    # Validation errors
    (r"validation.*fail", "Validation failure"),
    (r"missing.*field", "Missing required field"),
    (r"required.*field", "Required field not provided"),
    (r"invalid.*format", "Invalid data format"),
    (r"schema.*mismatch", "Schema mismatch"),
    # Data issues
    (r"dataframe.*empty", "Empty dataframe input"),
    (r"no.*data.*found", "No data found"),
    (r"null.*value", "Null value in required field"),
    (r"empty.*input", "Empty input"),
    (r"empty.*result", "Empty result set"),
    # S3/File not found (missing input data)
    (r"headobject.*not found", "Input file not found in S3"),
    (r"404.*headobject", "Input file missing (S3 404)"),
    # DataFrame/column errors
    (r"dataframe.*must.*have.*column", "Missing required DataFrame column"),
    (r"column.*not.*found", "Column not found in DataFrame"),
    # Type errors
    (r"type.*error.*expected", "Type mismatch"),
    (r"parse.*error", "Data parsing error"),
    (r"invalid.*input", "Invalid input data"),
    (r"conversion.*error", "Data conversion error"),
    # Custom exceptions
    (r"RequiredInputError", "Required input missing"),
    (r"MultipleInputError", "Multiple input error"),
    (r"DatasetException", "Dataset exception"),
]

THIRD_PARTY_PATTERNS: list[tuple[str, str]] = [
    # Provider-specific
    (r"xledger", "Xledger API error"),
    (r"visma", "Visma API error"),
    (r"agrando", "Agrando API error"),
    (r"adra", "Adra API error"),
    (r"giantleap", "GiantLeap API error"),
    # Protocol errors
    (r"soap.*error", "SOAP service error"),
    (r"graphql.*error", "GraphQL API error"),
    (r"rest.*error", "REST API error"),
    # HTTP errors
    (r"http.*[4-5]\d{2}", "HTTP error response"),
    (r"status.*code.*[4-5]\d{2}", "HTTP status code error"),
    (r"status_code.*[4-5]\d{2}", "HTTP status code error"),
    # Connection issues
    (r"connection.*refused", "Connection refused"),
    (r"connection.*timeout", "Connection timeout"),
    (r"read.*timeout", "Read timeout"),
    (r"timeout.*exceeded", "Timeout exceeded"),
    (r"connect.*timeout", "Connection timeout"),
    # Auth issues
    (r"authentication.*fail", "Authentication failure"),
    (r"unauthorized", "Unauthorized access"),
    (r"forbidden", "Forbidden access"),
    (r"invalid.*credentials", "Invalid credentials"),
    (r"token.*expired", "Token expired"),
    # Generic external
    (r"api.*error", "API error"),
    (r"external.*service", "External service error"),
    (r"ClientError", "AWS/External client error"),
    (r"botocore.*exception", "AWS service error"),
    # Rate limiting
    (r"rate.*limit", "Rate limit exceeded"),
    (r"quota.*exceeded", "Quota exceeded"),
    (r"too.*many.*requests", "Too many requests"),
    (r"throttl", "Request throttled"),
    # Service availability
    (r"service.*unavailable", "Service unavailable"),
    (r"bad.*gateway", "Bad gateway"),
    (r"gateway.*timeout", "Gateway timeout"),
    # Custom exceptions
    (r"ConcurrentRequestException", "Concurrent request limit"),
    (r"InvalidQueryException", "Invalid external query"),
    (r"GraphQLException", "GraphQL exception"),
    (r"IOException", "IO exception"),
]

WORKFLOW_ENGINE_PATTERNS: list[tuple[str, str]] = [
    # Activity errors
    (r"activity.*not.*found", "Activity not found"),
    (r"ActivityNotFoundError", "Activity not found"),
    (r"InvalidActivityError", "Invalid activity configuration"),
    (r"invalid.*activity", "Invalid activity"),
    (r"an error occurred while running the activity", "Activity execution error"),
    # Pipeline errors
    (r"pipeline.*exception", "Pipeline exception"),
    (r"PipelineException", "Pipeline exception"),
    (r"PipelineRunTimeoutException", "Pipeline timeout"),
    (r"pipeline.*timeout", "Pipeline timeout"),
    # Context errors
    (r"context.*not.*found", "Context not found"),
    (r"ContextNotFoundException", "Context not found"),
    # Dependency errors
    (r"upstream.*fail", "Upstream activity failed"),
    (r"ActivityUpstreamFailedError", "Upstream failed"),
    (r"circular.*dependency", "Circular dependency"),
    (r"dag.*error", "DAG construction error"),
    (r"dependency.*error", "Dependency error"),
    # Condition errors
    (r"condition.*not.*met", "Run condition not met"),
    (r"skip.*condition", "Skip condition triggered"),
    # Plugin errors
    (r"plugin.*error", "Plugin error"),
    (r"PluginException", "Plugin exception"),
    (r"builtin.*error", "Builtin error"),
    (r"BuiltinsException", "Builtins exception"),
    # Internal errors
    (r"internal.*server.*error", "Internal server error"),
    (r"unexpected.*error", "Unexpected error"),
    # KeyError in activity execution (common workflow engine issue)
    (r"KeyError.*not in index", "Missing key in activity data"),
]
