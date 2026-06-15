const COLORS = {
  reset: '\x1b[0m',
  cyan: '\x1b[36m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  dim: '\x1b[2m',
  magenta: '\x1b[35m',
};

const timestamp = () => {
  const now = new Date();
  return `${COLORS.dim}${now.toISOString()}${COLORS.reset}`;
};

const logger = {
  info: (tag, msg, data) => {
    console.log(`${timestamp()} ${COLORS.cyan}[${tag}]${COLORS.reset} ${msg}`, data ?? '');
  },
  success: (tag, msg, data) => {
    console.log(`${timestamp()} ${COLORS.green}[${tag}]${COLORS.reset} ${msg}`, data ?? '');
  },
  warn: (tag, msg, data) => {
    console.warn(`${timestamp()} ${COLORS.yellow}[${tag}]${COLORS.reset} ${msg}`, data ?? '');
  },
  error: (tag, msg, data) => {
    console.error(`${timestamp()} ${COLORS.red}[${tag}]${COLORS.reset} ${msg}`, data ?? '');
  },
  ws: (msg, data) => {
    console.log(`${timestamp()} ${COLORS.magenta}[WS]${COLORS.reset} ${msg}`, data ?? '');
  },
};

export default logger;
