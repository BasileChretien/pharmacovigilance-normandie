// Static HTTP server for the phone-layout check: serves _site/ under the site's subpath,
// as GitHub Pages does (file:// breaks the search and root-relative links).
import { createReadStream, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize, resolve, sep } from "node:path";

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".xml": "application/xml; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".avif": "image/avif",
  ".gif": "image/gif",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
  ".ttf": "font/ttf",
  ".pdf": "application/pdf",
};

function isFile(path) {
  try {
    return statSync(path).isFile();
  } catch {
    return false;
  }
}

function isDirectory(path) {
  try {
    return statSync(path).isDirectory();
  } catch {
    return false;
  }
}

/**
 * Where a request goes, as on GitHub Pages: a file, a folder's index.html, a page without
 * its .html, a redirect for a folder without its final slash, or not found (404.html).
 * @param {string} root folder served (absolute)
 * @param {string} prefix subpath, such as "/pharmacovigilance-normandie/"
 * @param {string} url request URL (path and query)
 * @returns {{status: number, file?: string, location?: string}}
 */
export function route(root, prefix, url) {
  const notFound = { status: 404, file: isFile(join(root, "404.html")) ? join(root, "404.html") : undefined };
  let path;
  try {
    path = decodeURIComponent(new URL(url, "http://localhost").pathname);
  } catch {
    return { status: 400 };
  }
  if (path === prefix.slice(0, -1)) return { status: 301, location: prefix };
  if (!path.startsWith(prefix) || path.includes("\0")) return notFound;
  const relative = normalize(path.slice(prefix.length));
  const target = resolve(root, relative);
  if (target !== root && !target.startsWith(root + sep)) return notFound;
  if (isDirectory(target)) {
    if (!path.endsWith("/")) return { status: 301, location: `${path}/` };
    return isFile(join(target, "index.html")) ? { status: 200, file: join(target, "index.html") } : notFound;
  }
  if (isFile(target)) return { status: 200, file: target };
  if (!extname(target) && isFile(`${target}.html`)) return { status: 200, file: `${target}.html` };
  return notFound;
}

/**
 * Serves `root` under `prefix` on a free local port.
 * @returns {Promise<{url: string, close: () => Promise<void>}>} url ends with the prefix
 */
export function serve(root, prefix) {
  const base = resolve(root);
  const server = createServer((req, res) => {
    const answer = route(base, prefix, req.url || "/");
    if (answer.location) {
      res.writeHead(answer.status, { Location: answer.location }).end();
      return;
    }
    if (!answer.file) {
      res.writeHead(answer.status, { "Content-Type": TYPES[".txt"] }).end("Not found");
      return;
    }
    const type = TYPES[extname(answer.file).toLowerCase()] || "application/octet-stream";
    res.writeHead(answer.status, { "Content-Type": type, "Cache-Control": "max-age=3600" });
    createReadStream(answer.file).on("error", () => res.destroy()).pipe(res);
  });
  return new Promise((resolvePromise, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const { port } = server.address();
      resolvePromise({
        url: `http://127.0.0.1:${port}${prefix}`,
        close: () => new Promise((done) => {
          server.close(() => done());
          server.closeAllConnections();
        }),
      });
    });
  });
}
