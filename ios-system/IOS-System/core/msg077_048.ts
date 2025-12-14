/**
 * SDK Errors
 */

export class IOSError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'IOSError';
  }
}

export class AuthenticationError extends IOSError {
  constructor(message: string) {
    super(message);
    this.name = 'AuthenticationError';
  }
}

export class RateLimitError extends IOSError {
  retryAfter?: string;
  
  constructor(message: string, retryAfter?: string) {
    super(message);
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
  }
}

export class NotFoundError extends IOSError {
  constructor(message: string) {
    super(message);
    this.name = 'NotFoundError';
  }
}

export class ServerError extends IOSError {
  constructor(message: string) {
    super(message);
    this.name = 'ServerError';
  }
}