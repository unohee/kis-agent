/**
 * TypeScript Python Bridge - Node.js와 Python subprocess 간의 JSON 통신
 * 타임아웃, 예외 처리, Python 설치 감지 기능 포함
 */

import { spawn, execSync, execFileSync } from 'child_process';
import { EventEmitter } from 'events';
import type { ChildProcessWithoutNullStreams } from 'child_process';

interface BridgeRequest {
  method: string;
  params?: Record<string, any>;
  pretty?: boolean;
  timeout?: number;
}

interface BridgeResponse {
  success: boolean;
  data?: any; // cxt-ignore: type_safety
  error?: string;
  code?: string;
  _notice?: string;
}

interface PendingRequest {
  child: ChildProcessWithoutNullStreams;
  reject: (reason?: unknown) => void;
  resolve: (value: BridgeResponse | PromiseLike<BridgeResponse>) => void;
  stderr: string;
  timeoutHandle: NodeJS.Timeout;
}

interface PythonCheckResult {
  isInstalled: boolean;
  command?: string;
  version?: string;
}

export class PythonBridgeError extends Error {
  constructor(
    public code: string,
    message: string,
    public pythonError?: string
  ) {
    super(message);
    this.name = 'PythonBridgeError';
  }
}

export class PythonBridge extends EventEmitter {
  // Bounded buffers guard against unbounded memory growth from a misbehaving
  // bridge process (stderr floods / oversized stdout without a newline).
  private static readonly MAX_STDERR_BUFFER = 64 * 1024;
  private static readonly MAX_STDOUT_BUFFER = 1024 * 1024;

  private scriptPath: string;
  private timeout: number = 30000; // 기본 30000ms
  private pythonCommand: string = 'python3';
  private child: ChildProcessWithoutNullStreams | null = null;
  private stdoutBuffer = '';
  private pendingRequest: PendingRequest | null = null;

  constructor(scriptPath: string, timeout?: number) {
    super();
    this.scriptPath = scriptPath;
    if (timeout) {
      this.timeout = timeout;
    }
  }

  /**
   * Python 설치 여부 확인 (python3 또는 python)
   */
  static async checkPythonInstallation(): Promise<PythonCheckResult> {
    const pythonCommands = ['python3', 'python'];

    for (const cmd of pythonCommands) {
      try {
        const version = execSync(`${cmd} --version`, {
          encoding: 'utf-8',
          timeout: 5000,
          stdio: ['pipe', 'pipe', 'pipe'],
        }).trim();

        return {
          isInstalled: true,
          command: cmd,
          version,
        };
      } catch (error) { // cxt-ignore: exception_hiding
        continue;
      }
    }

    return {
      isInstalled: false,
    };
  }

  /**
   * Python 설치 여부 확인 (동기)
   */
  static checkPythonInstallationSync(): PythonCheckResult {
    const pythonCommands = ['python3', 'python'];

    for (const cmd of pythonCommands) {
      try {
        const version = execSync(`${cmd} --version`, {
          encoding: 'utf-8',
          timeout: 5000,
          stdio: ['pipe', 'pipe', 'pipe'],
        }).trim();

        return {
          isInstalled: true,
          command: cmd,
          version,
        };
      } catch (error) { // cxt-ignore: exception_hiding
        continue;
      }
    }

    return {
      isInstalled: false,
    };
  }

  /**
   * 초기화 — Python 설치 여부 확인 및 Python 명령어 결정
   */
  async initialize(): Promise<void> {
    const check = await PythonBridge.checkPythonInstallation();

    if (!check.isInstalled) {
      throw new PythonBridgeError(
        'PythonNotFound',
        'Python is not installed or not found in PATH. Please install Python 3.8+ and ensure it is accessible as "python3" or "python".'
      );
    }

    this.pythonCommand = check.command || 'python3';
    this.emit('initialized', { pythonCommand: this.pythonCommand, version: check.version });
  }

  /**
   * 동기 초기화 — Python 설치 여부 확인 및 Python 명령어 결정
   */
  initializeSync(): void {
    const check = PythonBridge.checkPythonInstallationSync();

    if (!check.isInstalled) {
      throw new PythonBridgeError(
        'PythonNotFound',
        'Python is not installed or not found in PATH. Please install Python 3.8+ and ensure it is accessible as "python3" or "python".'
      );
    }

    this.pythonCommand = check.command || 'python3';
    this.emit('initialized', { pythonCommand: this.pythonCommand, version: check.version });
  }

  private ensureProcess(): ChildProcessWithoutNullStreams {
    if (this.child && !this.child.killed) {
      return this.child;
    }

    const child = spawn(this.pythonCommand, [this.scriptPath], {
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    this.child = child;
    this.stdoutBuffer = '';

    child.stdout.setEncoding('utf-8');
    child.stderr.setEncoding('utf-8');

    child.stdout.on('data', (data: string) => {
      if (this.child !== child) {
        return;
      }
      this.handleStdoutData(data, child);
    });

    child.stderr.on('data', (data: string) => {
      if (this.child !== child) {
        return;
      }

      const pending = this.pendingRequest;
      if (pending && pending.child === child) {
        const combined = pending.stderr + data;
        // Keep the most recent bytes so the tail (usually the exception line) survives.
        const stderr =
          combined.length > PythonBridge.MAX_STDERR_BUFFER
            ? combined.slice(combined.length - PythonBridge.MAX_STDERR_BUFFER)
            : combined;
        pending.stderr = stderr;
      }
      this.emit('stderr', data);
    });

    // Without an 'error' listener an EPIPE (writing to a dead process) would be
    // thrown as an unhandled stream error and crash the Node process.
    child.stdin.on('error', (error: Error) => {
      this.failPendingRequest(
        new PythonBridgeError('StdinError', `Python bridge stdin stream error: ${error.message}`),
        child
      );
    });

    child.on('close', (code, signal) => {
      const pending = this.pendingRequest?.child === child ? this.pendingRequest : null;
      const isActiveChild = this.child === child;

      if (isActiveChild) {
        this.child = null;
        this.stdoutBuffer = '';
      }

      if (!pending && !isActiveChild) {
        return;
      }

      if (pending) {
        this.pendingRequest = null;
        clearTimeout(pending.timeoutHandle);
        pending.reject(
          new PythonBridgeError(
            'ProcessClosed',
            `Python bridge process closed before responding (code: ${code ?? 'null'}, signal: ${signal ?? 'null'})`,
            pending.stderr
          )
        );
      }

      this.emit('close', { code, signal });
    });

    child.on('error', (error) => {
      const pending = this.pendingRequest?.child === child ? this.pendingRequest : null;

      if (this.child === child) {
        this.child = null;
        this.stdoutBuffer = '';
      }

      if (!pending) {
        return;
      }

      this.pendingRequest = null;
      clearTimeout(pending.timeoutHandle);
      pending.reject(
        new PythonBridgeError(
          'ProcessError',
          `Failed to spawn Python process: ${error.message}`,
          pending.stderr
        )
      );
    });

    return child;
  }

  private handleStdoutData(data: string, child: ChildProcessWithoutNullStreams): void {
    this.stdoutBuffer += data;

    while (true) {
      const newlineIndex = this.stdoutBuffer.indexOf('\n');
      if (newlineIndex === -1) {
        break;
      }

      const line = this.stdoutBuffer.slice(0, newlineIndex).trim();
      this.stdoutBuffer = this.stdoutBuffer.slice(newlineIndex + 1);

      if (!line) {
        continue;
      }

      this.handleResponseLine(line, child);
    }

    // Guard against unbounded growth when no newline-delimited response ever
    // arrives (broken JSON fragment or an oversized single line from the bridge).
    if (this.stdoutBuffer.length > PythonBridge.MAX_STDOUT_BUFFER) {
      this.stdoutBuffer = '';
      this.failPendingRequest(
        new PythonBridgeError(
          'ResponseOverflow',
          `Python bridge stdout exceeded ${PythonBridge.MAX_STDOUT_BUFFER} bytes without a complete response line`
        ),
        child
      );
      if (this.child === child) {
        this.child = null;
        if (!child.killed) {
          child.kill('SIGTERM');
        }
      }
    }
  }

  /**
   * 진행 중인 요청을 정리하고 에러로 reject. pendingRequest가 없으면 no-op이므로
   * 여러 실패 경로(stdin write/error, stdout overflow)에서 중복 호출해도 안전하다.
   */
  private failPendingRequest(
    error: PythonBridgeError,
    child?: ChildProcessWithoutNullStreams
  ): void {
    const pending = this.pendingRequest;
    if (!pending) {
      return;
    }

    if (child && pending.child !== child) {
      return;
    }

    this.pendingRequest = null;
    clearTimeout(pending.timeoutHandle);

    if (error.pythonError === undefined && pending.stderr) {
      error.pythonError = pending.stderr;
    }

    pending.reject(error);
  }

  private handleResponseLine(line: string, child: ChildProcessWithoutNullStreams): void {
    const pending = this.pendingRequest;

    if (!pending || pending.child !== child) {
      this.emit('unhandledResponse', line);
      return;
    }

    this.pendingRequest = null;
    clearTimeout(pending.timeoutHandle);

    try {
      const response: BridgeResponse = JSON.parse(line);

      if (!response.success && response.code) {
        pending.reject(
          new PythonBridgeError(
            response.code,
            response.error || 'Unknown error from Python bridge',
            pending.stderr
          )
        );
        return;
      }

      pending.resolve(response);
    } catch (parseError) {
      const error = parseError instanceof Error ? parseError : new Error(String(parseError));
      pending.reject(
        new PythonBridgeError(
          'ResponseParseError',
          `Failed to parse Python response: ${error.message}`,
          pending.stderr
        )
      );
    }
  }

  close(): void {
    if (this.pendingRequest) {
      clearTimeout(this.pendingRequest.timeoutHandle);
      this.pendingRequest.reject(
        new PythonBridgeError('ProcessClosed', 'Python bridge was closed before responding')
      );
      this.pendingRequest = null;
    }

    if (this.child && !this.child.killed) {
      this.child.kill('SIGTERM');
    }

    this.child = null;
    this.stdoutBuffer = '';
  }

  /**
   * Python CLI Bridge로 메서드 호출
   */
  async call(request: BridgeRequest): Promise<BridgeResponse> {
    return new Promise((resolve, reject) => {
      if (this.pendingRequest) {
        reject(
          new PythonBridgeError(
            'ConcurrentRequestError',
            'PythonBridge does not support concurrent requests without request ids'
          )
        );
        return;
      }

      const child = this.ensureProcess();

      // 타임아웃 설정 (밀리초)
      const timeout = request.timeout || this.timeout;
      const timeoutHandle = setTimeout(() => {
        if (this.pendingRequest?.child !== child) {
          return;
        }

        this.pendingRequest = null;
        if (this.child === child) {
          this.child = null;
          this.stdoutBuffer = '';
        }
        if (!child.killed) {
          child.kill('SIGTERM');
        }
        reject(
          new PythonBridgeError(
            'TimeoutError',
            `Request execution timed out after ${this.formatTimeout(timeout)}`
          )
        );
      }, timeout);

      this.pendingRequest = {
        child,
        resolve,
        reject,
        stderr: '',
        timeoutHandle,
      };

      // 요청 JSON을 stdin으로 전송 — write 실패(닫힌 stdin, EPIPE)를 즉시 reject해
      // timeout까지 대기하지 않도록 한다.
      const requestJson = JSON.stringify(request);
      child.stdin.write(requestJson + '\n', (writeError) => {
        if (writeError) {
          this.failPendingRequest(
            new PythonBridgeError(
              'StdinWriteError',
              `Failed to write request to Python bridge stdin: ${writeError.message}`
            ),
            child
          );
        }
      });
    });
  }

  /**
   * Python CLI Bridge로 메서드 호출 (동기, 작은 timeout 권장)
   */
  callSync(request: BridgeRequest): BridgeResponse {
    try {
      const timeout = request.timeout || this.timeout;
      const output = execFileSync(
        this.pythonCommand,
        [this.scriptPath],
        {
          input: JSON.stringify(request) + '\n',
          encoding: 'utf-8',
          timeout,
          stdio: ['pipe', 'pipe', 'pipe'],
        }
      );

      const response: BridgeResponse = JSON.parse(output.trim());

      // async call()과 동일하게, 실패 응답은 성공 경로로 반환하지 않고 throw한다.
      if (!response.success && response.code) {
        throw new PythonBridgeError(
          response.code,
          response.error || 'Unknown error from Python bridge'
        );
      }

      return response;
    } catch (error) {
      // 위에서 던진 구조화된 에러는 ProcessError로 재포장하지 않고 그대로 전파.
      if (error instanceof PythonBridgeError) {
        throw error;
      }
      if (error instanceof Error) {
        if (error.message.includes('ETIMEDOUT')) {
          throw new PythonBridgeError(
            'TimeoutError',
            `Request execution timed out after ${this.formatTimeout(request.timeout || this.timeout)}`,
            error.message
          );
        }
        throw new PythonBridgeError(
          'ProcessError',
          `Failed to execute Python command: ${error.message}`,
          error.message
        );
      }
      throw error;
    }
  }

  private formatTimeout(timeoutMs: number): string {
    if (timeoutMs % 1000 === 0) {
      const seconds = timeoutMs / 1000;
      return `${seconds} ${seconds === 1 ? 'second' : 'seconds'}`;
    }

    return `${timeoutMs} ms`;
  }
}

export default PythonBridge;
