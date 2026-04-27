"""Lightweight schema migrations. Runs idempotent ALTER TABLE statements on startup."""

from sqlalchemy import inspect, text


def apply_migrations(engine):
    insp = inspect(engine)

    # --- images table ---
    if "images" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("images")}

        if "is_favorite" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE images ADD COLUMN is_favorite BOOLEAN DEFAULT 0 NOT NULL"))

        if "share_token" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE images ADD COLUMN share_token VARCHAR(32)"))

        if "is_public" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE images ADD COLUMN is_public BOOLEAN DEFAULT 0 NOT NULL"))

        if "image_url" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE images ADD COLUMN image_url VARCHAR(500)"))

        # Make image_data nullable (images now stored in Cloudinary)
        if "image_data" in cols:
            image_data_col = next((c for c in insp.get_columns("images") if c["name"] == "image_data"), None)
            if image_data_col and not image_data_col.get("nullable", True):
                if engine.dialect.name == "sqlite":
                    # SQLite doesn't support ALTER COLUMN — rebuild the table.
                    with engine.begin() as conn:
                        conn.execute(text("PRAGMA foreign_keys=OFF"))
                        conn.execute(text("""
                            CREATE TABLE images_new (
                                id VARCHAR NOT NULL PRIMARY KEY,
                                prompt TEXT NOT NULL,
                                provider VARCHAR(50) NOT NULL,
                                model_key VARCHAR(100) NOT NULL,
                                model_name VARCHAR(200) NOT NULL DEFAULT '',
                                image_data BLOB,
                                image_url VARCHAR(500),
                                user_id VARCHAR,
                                is_favorite BOOLEAN NOT NULL DEFAULT 0,
                                share_token VARCHAR(32),
                                is_public BOOLEAN NOT NULL DEFAULT 0,
                                created_at DATETIME
                            )
                        """))
                        conn.execute(text("""
                            INSERT INTO images_new
                                (id, prompt, provider, model_key, model_name,
                                 image_data, image_url, user_id, is_favorite,
                                 share_token, is_public, created_at)
                            SELECT id, prompt, provider, model_key, model_name,
                                   image_data, image_url, user_id, is_favorite,
                                   share_token, is_public, created_at
                            FROM images
                        """))
                        conn.execute(text("DROP TABLE images"))
                        conn.execute(text("ALTER TABLE images_new RENAME TO images"))
                        conn.execute(text("CREATE UNIQUE INDEX ix_images_share_token ON images (share_token) WHERE share_token IS NOT NULL"))
                        conn.execute(text("PRAGMA foreign_keys=ON"))
                else:
                    try:
                        with engine.begin() as conn:
                            conn.execute(text("ALTER TABLE images ALTER COLUMN image_data DROP NOT NULL"))
                    except Exception:
                        pass

    # --- users table ---
    if "users" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("users")}
        if "email" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(200)"))

    # --- password_reset_tokens table ---
    if "password_reset_tokens" not in insp.get_table_names():
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE password_reset_tokens (
                    id VARCHAR PRIMARY KEY,
                    user_id VARCHAR NOT NULL,
                    token VARCHAR(64) NOT NULL UNIQUE,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT 0 NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX ix_prt_user_id ON password_reset_tokens (user_id)"))
            conn.execute(text("CREATE INDEX ix_prt_token ON password_reset_tokens (token)"))

    # --- image_tags table ---
    if "image_tags" not in insp.get_table_names():
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE image_tags (
                    id VARCHAR PRIMARY KEY,
                    image_id VARCHAR NOT NULL,
                    tag VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("CREATE INDEX ix_image_tags_image_id ON image_tags (image_id)"))
            conn.execute(text("CREATE INDEX ix_image_tags_tag ON image_tags (tag)"))
