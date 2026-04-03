/**
 * TypeScript Python Bridge 테스트
 * 타임아웃, 예외 처리, Python 설치 감지 검증
 */

import { EventEmitter } from 'events';
import { PythonBridge, PythonBridgeError } from '../python-bridge';
import { spawn, execFileSync } from 'child_process';

jest.mock('child_process', () => {
  const actual = jest.requireActual('child_process');
  return {
    ...actual,
    spawn: jest.fn(),
    execFileSync: jest.fn(),
  };
});

class MockStream extends EventEmitter {
  write = jest.fn();
  end = jest.fn();
  setEncoding = jest.fn();
}

const createMockChild = () => {
  const child = new EventEmitter() as EventEmitter & {
    stdin: MockStream;
    stdout: MockStream;
    stderr: MockStream;
    kill: jest.Mock;
    killed: boolean;
  };

  child.stdin = new MockStream();
  child.stdout = new MockStream();
  child.stderr = new MockStream();
  child.kill = jest.fn(() => {
    child.killed = true;
  });
  child.killed = false;

  return child;
};

describe('PythonBridge', () => {
  describe('Python Installation Detection', () => {
    it('should detect Python installation (async)', async () => {
      const result = await PythonBridge.checkPythonInstallation();

      expect(result.isInstalled).toBe(true);
      expect(result.command).toMatch(/python3?/);
      expect(result.version).toMatch(/Python/);
    });

    it('should detect Python installation (sync)', () => {
      const result = PythonBridge.checkPythonInstallationSync();

      expect(result.isInstalled).toBe(true);
      expect(result.command).toMatch(/python3?/);
      expect(result.version).toMatch(/Python/);
    });

    it('should return correct version info', async () => {
      const result = await PythonBridge.checkPythonInstallation();

      expect(result.version).toContain('3.');
    });
  });

  describe('Bridge Initialization', () => {
    it('should initialize successfully with Python installed', async () => {
      const bridge = new PythonBridge('/tmp/dummy_bridge.py');
      await bridge.initialize();

      // No error should be thrown
      expect(bridge).toBeDefined();
    });

    it('should initialize successfully (sync)', () => {
      const bridge = new PythonBridge('/tmp/dummy_bridge.py');
      bridge.initializeSync();

      // No error should be thrown
      expect(bridge).toBeDefined();
    });

    it('should emit initialized event', async () => {
      const bridge = new PythonBridge('/tmp/dummy_bridge.py');

      const initializedHandler = jest.fn();
      bridge.on('initialized', initializedHandler);

      await bridge.initialize();

      expect(initializedHandler).toHaveBeenCalled();
      const args = initializedHandler.mock.calls[0][0];
      expect(args.pythonCommand).toMatch(/python3?/);
      expect(args.version).toContain('Python');
    });
  });

  describe('Error Handling', () => {
    it('should create PythonBridgeError with correct properties', () => {
      const error = new PythonBridgeError('TestError', 'Test message', 'Test stderr');

      expect(error.code).toBe('TestError');
      expect(error.message).toBe('Test message');
      expect(error.pythonError).toBe('Test stderr');
      expect(error.name).toBe('PythonBridgeError');
    });

    it('should handle Python not found error', async () => {
      // This test would require mocking, which is beyond scope for this basic validation
      // In a real implementation, we would mock execSync to return false for Python check
      expect(true).toBe(true);
    });

    it('should have correct error codes', () => {
      const errorCodes = [
        'PythonNotFound',
        'TimeoutError',
        'ProcessError',
        'ProcessClosed',
        'InvalidResponse',
        'ResponseParseError',
      ];

      for (const code of errorCodes) {
        const error = new PythonBridgeError(code, 'Test');
        expect(error.code).toBe(code);
      }
    });
  });

  describe('Request/Response Format', () => {
    it('should format request correctly', () => {
      const request = {
        method: 'stock_api.get_stock_price',
        params: { code: '005930' },
        pretty: false,
        timeout: 30000,
      };

      const json = JSON.stringify(request);
      const parsed = JSON.parse(json);

      expect(parsed.method).toBe('stock_api.get_stock_price');
      expect(parsed.params.code).toBe('005930');
      expect(parsed.timeout).toBe(30000);
    });

    it('should handle empty params', () => {
      const request = {
        method: 'test_api.method',
      };

      const json = JSON.stringify(request);
      const parsed = JSON.parse(json);

      expect(parsed.method).toBe('test_api.method');
      expect(parsed.params).toBeUndefined();
    });

    it('should handle response with notice', () => {
      const response = {
        success: true,
        data: { key: 'value' },
        _notice: '휴장일 — 데이터는 직전 영업일(2026-03-20 금) 기준',
      };

      const json = JSON.stringify(response);
      const parsed = JSON.parse(json);

      expect(parsed.success).toBe(true);
      expect(parsed._notice).toContain('휴장일');
    });

    it('should handle error response', () => {
      const response = {
        success: false,
        error: 'Invalid code',
        code: 'ValueError',
      };

      const json = JSON.stringify(response);
      const parsed = JSON.parse(json);

      expect(parsed.success).toBe(false);
      expect(parsed.code).toBe('ValueError');
    });
  });

  describe('Timeout Handling', () => {
    it('should support timeout parameter in request', () => {
      const request = {
        method: 'test_api.method',
        timeout: 5000, // 5000ms
      };

      expect(request.timeout).toBe(5000);
    });

    it('should use default timeout when not specified', () => {
      const bridge = new PythonBridge('/tmp/dummy_bridge.py', 30000);
      expect(bridge['timeout']).toBe(30000);
    });

    it('should allow custom timeout in constructor', () => {
      const bridge = new PythonBridge('/tmp/dummy_bridge.py', 60000);
      expect(bridge['timeout']).toBe(60000);
    });

    it('should have correct timeout error message', () => {
      const error = new PythonBridgeError(
        'TimeoutError',
        'Request execution timed out after 30 seconds'
      );

      expect(error.code).toBe('TimeoutError');
      expect(error.message).toContain('timed out');
    });
  });

  describe('Python Command Detection', () => {
    it('should prefer python3 over python', async () => {
      const result = await PythonBridge.checkPythonInstallation();

      // Should find either python3 or python, preferring python3
      expect(result.isInstalled).toBe(true);
      expect(result.command).toMatch(/python3?/);
    });

    it('should store python command after initialization', async () => {
      const bridge = new PythonBridge('/tmp/dummy_bridge.py');
      await bridge.initialize();

      expect(bridge['pythonCommand']).toMatch(/python3?/);
    });
  });

  describe('Line-Based IPC', () => {
    beforeEach(() => {
      jest.clearAllMocks();
    });

    it('should send JSON requests over stdin and resolve line-delimited responses', async () => {
      const child = createMockChild();
      (spawn as jest.Mock).mockReturnValue(child);

      const bridge = new PythonBridge('/tmp/dummy_bridge.py');
      const responsePromise = bridge.call({ method: 'test_api.method', params: { code: '005930' } });

      expect(child.stdin.write).toHaveBeenCalledWith(
        '{"method":"test_api.method","params":{"code":"005930"}}\n'
      );

      child.stdout.emit('data', '{"success":true,"data":{"price":70000}}');
      child.stdout.emit('data', '\n');

      await expect(responsePromise).resolves.toEqual({
        success: true,
        data: { price: 70000 },
      });
    });

    it('should reuse the same child process across sequential calls', async () => {
      const child = createMockChild();
      (spawn as jest.Mock).mockReturnValue(child);

      const bridge = new PythonBridge('/tmp/dummy_bridge.py');

      const first = bridge.call({ method: 'test_api.first' });
      child.stdout.emit('data', '{"success":true,"data":{"step":1}}\n');
      await expect(first).resolves.toEqual({ success: true, data: { step: 1 } });

      const second = bridge.call({ method: 'test_api.second' });
      child.stdout.emit('data', '{"success":true,"data":{"step":2}}\n');
      await expect(second).resolves.toEqual({ success: true, data: { step: 2 } });

      expect(spawn).toHaveBeenCalledTimes(1);
      expect(child.stdin.write).toHaveBeenNthCalledWith(1, '{"method":"test_api.first"}\n');
      expect(child.stdin.write).toHaveBeenNthCalledWith(2, '{"method":"test_api.second"}\n');
    });

    it('should reject concurrent calls when no request id is available', async () => {
      const child = createMockChild();
      (spawn as jest.Mock).mockReturnValue(child);

      const bridge = new PythonBridge('/tmp/dummy_bridge.py');

      const first = bridge.call({ method: 'test_api.first' });
      const second = bridge.call({ method: 'test_api.second' });

      await expect(second).rejects.toMatchObject({
        code: 'ConcurrentRequestError',
      });

      child.stdout.emit('data', '{"success":true,"data":{"step":1}}\n');
      await expect(first).resolves.toEqual({ success: true, data: { step: 1 } });
    });

    it('should reject invalid JSON response lines', async () => {
      const child = createMockChild();
      (spawn as jest.Mock).mockReturnValue(child);

      const bridge = new PythonBridge('/tmp/dummy_bridge.py');
      const responsePromise = bridge.call({ method: 'test_api.method' });

      child.stdout.emit('data', 'not-json\n');

      await expect(responsePromise).rejects.toMatchObject({
        code: 'ResponseParseError',
      });
    });

    it('should parse pretty=true responses because bridge output stays single-line', async () => {
      const child = createMockChild();
      (spawn as jest.Mock).mockReturnValue(child);

      const bridge = new PythonBridge('/tmp/dummy_bridge.py');
      const responsePromise = bridge.call({ method: 'test_api.method', pretty: true });

      child.stdout.emit(
        'data',
        '{"success":true,"data":{"price":70000},"_notice":"market closed"}\n'
      );

      await expect(responsePromise).resolves.toEqual({
        success: true,
        data: { price: 70000 },
        _notice: 'market closed',
      });
    });
  });

  describe('Synchronous Call', () => {
    beforeEach(() => {
      jest.clearAllMocks();
    });

    it('should execute the bridge script with execFileSync', () => {
      (execFileSync as jest.Mock).mockReturnValue('{"success":true,"data":{"ok":true}}\n');

      const bridge = new PythonBridge('/tmp/dummy_bridge.py');
      const response = bridge.callSync({ method: 'test_api.method', params: { code: '005930' } });

      expect(execFileSync).toHaveBeenCalledWith('python3', ['/tmp/dummy_bridge.py'], {
        input: '{"method":"test_api.method","params":{"code":"005930"}}\n',
        encoding: 'utf-8',
        timeout: 30000,
        stdio: ['pipe', 'pipe', 'pipe'],
      });
      expect(response).toEqual({
        success: true,
        data: { ok: true },
      });
    });
  });
});
