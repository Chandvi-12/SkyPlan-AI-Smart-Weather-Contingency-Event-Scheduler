import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app import create_app

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    print(f"\n🚀 SkyPlan AI is running on http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop the server.\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
