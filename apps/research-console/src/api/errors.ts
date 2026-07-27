export class ApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly statusCode: number,
    public readonly requestId: string,
    public readonly resourceId: string | null = null,
    public readonly retryable: boolean = false,
    public readonly details: Record<string, unknown> = {}
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor(message = 'Network error') {
    super(message);
    this.name = 'NetworkError';
  }
}

export class ValidationError extends Error {
  constructor(message = 'Validation error') {
    super(message);
    this.name = 'ValidationError';
  }
}

export const parseError = async (response: Response): Promise<ApiError> => {
  let code = 'unknown';
  let message = `Request failed with status ${response.status}`;
  let requestId = '';
  let resourceId: string | null = null;
  let retryable = false;
  let details: Record<string, unknown> = {};

  try {
    const body = (await response.json()) as Record<string, unknown>;
    code = typeof body.code === 'string' ? body.code : code;
    message = typeof body.message === 'string' ? body.message : message;
    requestId = typeof body.request_id === 'string' ? body.request_id : requestId;
    resourceId = typeof body.resource_id === 'string' ? body.resource_id : null;
    retryable = Boolean(body.retryable);
    details = typeof body.details === 'object' && body.details !== null ? (body.details as Record<string, unknown>) : {};
  } catch {
    // fall back to status-based message
  }

  return new ApiError(code, message, response.status, requestId, resourceId, retryable, details);
};
