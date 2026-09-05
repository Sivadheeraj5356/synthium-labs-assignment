from __future__ import annotations

import argparse

from relay.config import Settings
from relay.server import serve


def main() -> None:
    parser = argparse.ArgumentParser(description="Webhook relay server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    httpd = serve(args.host, args.port, Settings.from_env())
    print(f"relay listening on http://{args.host}:{args.port}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
