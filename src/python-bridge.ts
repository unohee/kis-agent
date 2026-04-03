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
  data?: any;
  error?: string;
  code?: string;
  _notice?: string;
}

interface PendingRequest {
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
      } catch (error) {
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
      } catch (error) {
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
      this.handleStdoutData(data);
    });

    child.stderr.on('data', (data: string) => {
      if (this.pendingRequest) {
        this.pendingRequest.stderr += data;
      }
      this.emit('stderr', data);
    });

    child.on('close', (code, signal) => {
      const pending = this.pendingRequest;
      this.child = null;
      this.pendingRequest = null;

      if (pending) {
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
      const pending = this.pendingRequest;
      this.child = null;
      this.pendingRequest = null;

      if (pending) {
        clearTimeout(pending.timeoutHandle);
        pending.reject(
          new PythonBridgeError(
            'ProcessError',
            `Failed to spawn Python process: ${error.message}`,
            pending.stderr
          )
        );
      }
    });

    return child;
  }

  private handleStdoutData(data: string): void {
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

      this.handleResponseLine(line);
    }
  }

  private handleResponseLine(line: string): void {
    const pending = this.pendingRequest;

    if (!pending) {
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
        this.pendingRequest = null;
        child.kill('SIGTERM');
        reject(
          new PythonBridgeError(
            'TimeoutError',
            `Request execution timed out after ${this.formatTimeout(timeout)}`
          )
        );
      }, timeout);

      this.pendingRequest = {
        resolve,
        reject,
        stderr: '',
        timeoutHandle,
      };

      // 요청 JSON을 stdin으로 전송
      const requestJson = JSON.stringify(request);
      child.stdin.write(requestJson + '\n');
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
      return response;
    } catch (error) {
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
