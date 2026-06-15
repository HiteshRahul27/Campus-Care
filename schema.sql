CREATE TABLE IF NOT EXISTS users (
  id          BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  username    TEXT NOT NULL UNIQUE,
  full_name   TEXT,
  hashed_pw   TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS students (
  id           BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  name         TEXT NOT NULL,
  roll_number  TEXT NOT NULL UNIQUE,
  class_name   TEXT NOT NULL,
  gender       TEXT NOT NULL,
  dob          DATE NOT NULL,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS health_records (
  id            BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  student_id    BIGINT REFERENCES students(id) ON DELETE CASCADE,
  year          INT NOT NULL,
  height        NUMERIC(5,1),
  weight        NUMERIC(5,1),
  hemoglobin    NUMERIC(4,1),
  vision_left   TEXT,
  vision_right  TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);
