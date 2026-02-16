"""Portal configuration."""

import json
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Paths
    project_root: Path = Path(__file__).resolve().parents[3]  # GST Project root
    portal_root: Path = Path(__file__).resolve().parents[1]   # portal/backend/
    db_url: str = ""
    upload_dir: Path = Path("")

    # CORS
    frontend_url: str = "http://localhost:5173"

    def model_post_init(self, __context):
        data_dir = self.portal_root / "data"
        if not self.db_url:
            self.db_url = f"sqlite:///{data_dir / 'db' / 'portal.db'}"
        if not self.upload_dir or str(self.upload_dir) == ".":
            self.upload_dir = data_dir / "uploads"
        # Ensure directories exist
        (data_dir / "db").mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def load_gst_config(self) -> dict:
        """Load the main GST project config.json."""
        config_path = self.project_root / "config.json"
        with open(config_path) as f:
            return json.load(f)

    class Config:
        env_prefix = "GST_PORTAL_"


settings = Settings()
